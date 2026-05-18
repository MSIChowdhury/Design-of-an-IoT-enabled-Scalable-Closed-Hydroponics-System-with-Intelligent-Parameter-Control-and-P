from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = tuple(round(value / 100, 2) for value in range(10, 95, 5))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=None,
        help="Datasets to scan. Defaults to every prepared dataset with timestamp-level labels.",
    )
    args = parser.parse_args()
    datasets = args.datasets or _timestamp_level_datasets()
    if not datasets:
        print("No timestamp-level native-label datasets are available.")
        return
    rows = []
    for dataset in datasets:
        rows.extend(_scan_dataset(dataset))
    if not rows:
        print("No threshold sensitivity rows were generated.")
        return
    frame = pd.DataFrame(rows).sort_values(["dataset", "method", "threshold"])
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / "external_native_threshold_sensitivity.csv"
    best_path = out_dir / "external_native_threshold_best.csv"
    frame.to_csv(detail_path, index=False)
    best = (
        frame.sort_values(["dataset", "method", "balanced_accuracy"], ascending=[True, True, False])
        .groupby(["dataset", "method"], as_index=False)
        .head(1)
        .sort_values(["dataset", "balanced_accuracy"], ascending=[True, False])
    )
    best.to_csv(best_path, index=False)
    print(f"Wrote {detail_path}")
    print(f"Wrote {best_path}")


def _timestamp_level_datasets() -> list[str]:
    datasets = []
    for path in sorted((ROOT / "results/metrics").glob("*_native_event_summary.csv")):
        dataset = path.name.removesuffix("_native_event_summary.csv")
        label_path = ROOT / f"data/processed/{dataset}_labels.parquet"
        if not label_path.exists():
            continue
        labels = pd.read_parquet(label_path, columns=["sensor"])
        if labels["sensor"].fillna("").astype(str).str.len().eq(0).all():
            datasets.append(dataset)
    if datasets:
        return datasets
    for path in sorted((ROOT / "data/processed").glob("*_labels.parquet")):
        labels = pd.read_parquet(path, columns=["sensor"])
        if labels["sensor"].fillna("").astype(str).str.len().eq(0).all():
            datasets.append(path.name.removesuffix("_labels.parquet"))
    return datasets


def _scan_dataset(dataset: str) -> list[dict[str, object]]:
    labels_path = ROOT / f"data/processed/{dataset}_labels.parquet"
    if not labels_path.exists():
        return []
    labels = pd.read_parquet(labels_path)
    if not labels["sensor"].fillna("").astype(str).str.len().eq(0).all():
        return []
    actual = (
        labels.assign(timestamp=labels["timestamp"].astype(str))
        .groupby("timestamp")["fault"]
        .max()
        .astype(bool)
    )
    rows = []
    for path in sorted((ROOT / "results/metrics").glob(f"{dataset}_*_decisions.csv")):
        method = path.name.removeprefix(f"{dataset}_").removesuffix("_decisions.csv")
        decisions = pd.read_csv(path)
        if method == "aasvr":
            flag = decisions.get("gate_result", pd.Series("", index=decisions.index)).eq("reject")
        else:
            flag = decisions.get("alert", pd.Series(False, index=decisions.index)).astype(bool)
        scores = (
            decisions.assign(predicted=flag)
            .groupby(decisions["timestamp"].astype(str))["predicted"]
            .mean()
            .reindex(actual.index)
            .fillna(False)
        )
        for threshold in THRESHOLDS:
            row = _classification_row(actual, scores >= threshold)
            row.update(
                {
                    "dataset": dataset,
                    "method": method,
                    "threshold": threshold,
                    "evaluation_unit": "timestamp",
                    "aggregation": "sensor_fraction",
                    "youden_j": row["recall"] + row["specificity"] - 1.0,
                }
            )
            rows.append(row)
    return rows


def _classification_row(actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
    actual = actual.astype(bool)
    predicted = predicted.astype(bool)
    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    tn = int((~predicted & ~actual).sum())
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    return {
        "precision": precision,
        "recall": recall,
        "f1": _safe_div(2 * precision * recall, precision + recall),
        "specificity": specificity,
        "balanced_accuracy": (recall + specificity) / 2,
        "false_positive_rate": _safe_div(fp, fp + tn),
        "false_negative_rate": _safe_div(fn, fn + tp),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
    }


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


if __name__ == "__main__":
    main()
