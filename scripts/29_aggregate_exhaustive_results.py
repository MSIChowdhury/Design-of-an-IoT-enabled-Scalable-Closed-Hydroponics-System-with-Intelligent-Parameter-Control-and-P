from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

METRICS = [
    "precision",
    "recall",
    "specificity",
    "balanced_accuracy",
    "false_actuations",
    "missed_actuations",
    "unsafe_samples",
    "decision_count",
    "unsafe_rate",
    "missed_authorization_rate",
    "mean_detection_delay_samples",
    "false_alarm_events",
    "alerts",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["mini", "paper", "exhaustive"], default="mini")
    parser.add_argument("--split", default="test", choices=["tune", "validation", "test", "all"])
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    aggregate(args)


def aggregate(args: argparse.Namespace) -> None:
    metrics_dir = ROOT / "results/metrics/exhaustive"
    pattern = f"hydro_exp1_{args.profile}_{args.split}_shard*.csv"
    frames = [pd.read_csv(path) for path in sorted(metrics_dir.glob(pattern))]
    if not frames:
        raise SystemExit(f"No exhaustive benchmark shards found for {pattern}")
    detail = pd.concat(frames, ignore_index=True)
    out_dir = ROOT / "results/metrics"
    table_dir = ROOT / "results/tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    summary = _summary(detail, ["method"])
    by_fault = _summary(detail, ["method", "fault_type"])
    by_sensor = _summary(detail, ["method", "sensor"])
    by_cell = _summary(detail, ["method", "sensor", "fault_type"])
    ci = _bootstrap_ci(detail, args.bootstrap)
    prefix = f"hydro_exp1_exhaustive_{args.profile}_{args.split}"
    outputs = {
        f"{prefix}_detail.csv": detail,
        f"{prefix}_summary.csv": summary,
        f"{prefix}_by_fault_type.csv": by_fault,
        f"{prefix}_by_sensor.csv": by_sensor,
        f"{prefix}_by_sensor_fault_type.csv": by_cell,
        f"{prefix}_bootstrap_ci.csv": ci,
    }
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
        frame.to_csv(table_dir / filename, index=False)
        print(f"Wrote {out_dir / filename}")


def _summary(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    aggregations = {metric: ["mean", "median", "std"] for metric in METRICS if metric in frame}
    out = frame.groupby(group_cols, as_index=False).agg(aggregations)
    out.columns = ["_".join(col).rstrip("_") for col in out.columns.to_flat_index()]
    count = frame.groupby(group_cols, as_index=False)["trial_id"].nunique().rename(
        columns={"trial_id": "n_trials"}
    )
    return count.merge(out, on=group_cols).sort_values(
        [*group_cols[:-1], "balanced_accuracy_mean"] if group_cols else ["balanced_accuracy_mean"],
        ascending=[True] * max(0, len(group_cols) - 1) + [False],
    )


def _bootstrap_ci(frame: pd.DataFrame, n_resamples: int) -> pd.DataFrame:
    rng = np.random.default_rng(20260519)
    rows = []
    for method, method_frame in frame.groupby("method"):
        trial_ids = method_frame["trial_id"].drop_duplicates().to_numpy()
        if len(trial_ids) == 0:
            continue
        values = []
        for _ in range(n_resamples):
            sample_ids = rng.choice(trial_ids, size=len(trial_ids), replace=True)
            sample = method_frame[method_frame["trial_id"].isin(sample_ids)]
            values.append(sample[["balanced_accuracy", "false_actuations"]].mean().to_numpy())
        arr = np.asarray(values, dtype=float)
        rows.append(
            {
                "method": method,
                "n_trials": len(trial_ids),
                "balanced_accuracy_mean": float(method_frame["balanced_accuracy"].mean()),
                "balanced_accuracy_ci_low": float(np.quantile(arr[:, 0], 0.025)),
                "balanced_accuracy_ci_high": float(np.quantile(arr[:, 0], 0.975)),
                "false_actuations_mean": float(method_frame["false_actuations"].mean()),
                "false_actuations_ci_low": float(np.quantile(arr[:, 1], 0.025)),
                "false_actuations_ci_high": float(np.quantile(arr[:, 1], 0.975)),
            }
        )
    return pd.DataFrame(rows).sort_values("balanced_accuracy_mean", ascending=False)


if __name__ == "__main__":
    main()
