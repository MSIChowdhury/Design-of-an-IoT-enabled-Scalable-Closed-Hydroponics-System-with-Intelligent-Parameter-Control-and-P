from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = tuple(round(value / 100, 2) for value in range(10, 95, 5))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="*", default=("hai", "skab"))
    args = parser.parse_args()
    rows = []
    for dataset in args.datasets:
        rows.extend(_scan_dataset(dataset))
    if not rows:
        print("No external AASVR threshold-adaptation rows were generated.")
        return
    frame = pd.DataFrame(rows).sort_values(["dataset", "threshold", "split"])
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / "external_aasvr_tuning.csv"
    best_path = out_dir / "external_aasvr_tuning_best.csv"
    frame.to_csv(detail_path, index=False)
    validation_best = (
        frame[frame["split"].eq("validation")]
        .sort_values(["dataset", "balanced_accuracy"], ascending=[True, False])
        .groupby("dataset", as_index=False)
        .head(1)[["dataset", "threshold"]]
        .rename(columns={"threshold": "selected_threshold"})
    )
    best = frame[frame["split"].eq("test")].merge(validation_best, on="dataset", how="inner")
    best = best[best["threshold"].eq(best["selected_threshold"])].sort_values(
        ["dataset", "balanced_accuracy"], ascending=[True, False]
    )
    best.to_csv(best_path, index=False)
    print(f"Wrote {detail_path}")
    print(f"Wrote {best_path}")


def _scan_dataset(dataset: str) -> list[dict[str, object]]:
    labels_path = ROOT / f"data/processed/{dataset}_labels.parquet"
    decisions_path = ROOT / f"results/metrics/{dataset}_aasvr_decisions.csv"
    if not labels_path.exists() or not decisions_path.exists():
        print(f"Skipping {dataset}; labels or AASVR decisions are unavailable.")
        return []
    labels = pd.read_parquet(labels_path)
    if not labels["sensor"].fillna("").astype(str).str.len().eq(0).all():
        print(f"Skipping {dataset}; labels are not timestamp-level native labels.")
        return []
    actual = (
        labels.assign(timestamp=labels["timestamp"].astype(str))
        .groupby("timestamp")["fault"]
        .max()
        .astype(bool)
    )
    decisions = pd.read_csv(decisions_path)
    scores = (
        decisions.assign(predicted=decisions["gate_result"].eq("reject"))
        .groupby(decisions["timestamp"].astype(str))["predicted"]
        .mean()
        .reindex(actual.index)
        .fillna(False)
    )
    split_mask = _validation_test_mask(actual.index)
    rows = []
    for threshold in THRESHOLDS:
        predicted = scores >= threshold
        for split_name, mask in split_mask.items():
            row = _classification_row(actual[mask], predicted[mask])
            row.update(
                {
                    "dataset": dataset,
                    "method": "aasvr_threshold_adapted",
                    "threshold": threshold,
                    "split": split_name,
                    "evaluation_unit": "timestamp",
                    "aggregation": "sensor_fraction",
                    "youden_j": row["recall"] + row["specificity"] - 1.0,
                }
            )
            rows.append(row)
    return rows


def _validation_test_mask(index: pd.Index) -> dict[str, np.ndarray]:
    n = len(index)
    midpoint = max(1, n // 2)
    validation = np.zeros(n, dtype=bool)
    validation[:midpoint] = True
    test = ~validation
    if not test.any():
        test = validation.copy()
    return {"validation": validation, "test": test}


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
