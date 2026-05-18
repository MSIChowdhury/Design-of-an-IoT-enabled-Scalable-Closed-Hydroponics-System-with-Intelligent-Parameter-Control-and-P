from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METRICS = [
    "precision",
    "recall",
    "f1",
    "specificity",
    "balanced_accuracy",
    "false_positive_rate",
    "false_negative_rate",
    "event_recall",
    "mean_detection_delay_samples",
    "false_alarm_events",
    "false_actuations",
    "alerts",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true", help="Analyze hydro Exp. 1 synthetic results.")
    parser.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples.")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    analyze_hydro_exp1(bootstrap=args.bootstrap)


def analyze_hydro_exp1(*, bootstrap: int) -> None:
    detail_path = ROOT / "results/metrics/hydro_exp1_synthetic_detail.csv"
    if not detail_path.exists():
        raise SystemExit("Missing synthetic detail; run scripts/06_compute_metrics.py --hydro-exp1.")
    detail = pd.read_csv(detail_path)
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)

    _bootstrap_ci(detail, bootstrap=bootstrap).to_csv(
        out_dir / "hydro_exp1_bootstrap_ci.csv", index=False
    )
    _method_ranks(detail).to_csv(out_dir / "hydro_exp1_method_ranks.csv", index=False)
    _group_summary(detail, ["method", "sensor"]).to_csv(
        out_dir / "hydro_exp1_synthetic_by_sensor.csv", index=False
    )
    _group_summary(detail, ["method", "sensor", "fault_type"]).to_csv(
        out_dir / "hydro_exp1_synthetic_by_sensor_fault_type.csv", index=False
    )
    print(f"Wrote {out_dir / 'hydro_exp1_bootstrap_ci.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_method_ranks.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_sensor.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_sensor_fault_type.csv'}")


def _bootstrap_ci(detail: pd.DataFrame, *, bootstrap: int) -> pd.DataFrame:
    rng = np.random.default_rng(20260518)
    trial_ids = detail["trial_id"].drop_duplicates().to_numpy()
    rows = []
    for method, method_frame in detail.groupby("method"):
        trial_lookup = {trial_id: group for trial_id, group in method_frame.groupby("trial_id")}
        estimates = {metric: [] for metric in METRICS if metric in method_frame.columns}
        for _ in range(bootstrap):
            sample_ids = rng.choice(trial_ids, size=len(trial_ids), replace=True)
            sample = pd.concat([trial_lookup[trial_id] for trial_id in sample_ids], ignore_index=True)
            for metric in estimates:
                estimates[metric].append(float(sample[metric].mean()))
        for metric, values in estimates.items():
            arr = np.asarray(values, dtype=float)
            rows.append(
                {
                    "method": method,
                    "metric": metric,
                    "mean": float(method_frame[metric].mean()),
                    "ci_low": float(np.quantile(arr, 0.025)),
                    "ci_high": float(np.quantile(arr, 0.975)),
                    "bootstrap_samples": bootstrap,
                }
            )
    return pd.DataFrame(rows).sort_values(["metric", "mean"], ascending=[True, False])


def _method_ranks(detail: pd.DataFrame) -> pd.DataFrame:
    rank_specs = {
        "balanced_accuracy": False,
        "recall": False,
        "specificity": False,
        "false_actuations": True,
        "false_alarm_events": True,
        "alerts": True,
    }
    rows = []
    for trial_id, trial_frame in detail.groupby("trial_id"):
        for metric, ascending in rank_specs.items():
            ranked = trial_frame[["method", metric]].copy()
            ranked["rank"] = ranked[metric].rank(method="average", ascending=ascending)
            ranked["trial_id"] = trial_id
            ranked["metric"] = metric
            rows.append(ranked[["trial_id", "method", "metric", "rank"]])
    ranks = pd.concat(rows, ignore_index=True)
    summary = (
        ranks.groupby(["method", "metric"], as_index=False)["rank"]
        .mean()
        .rename(columns={"rank": "mean_rank"})
    )
    return summary.sort_values(["metric", "mean_rank"])


def _group_summary(detail: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    available = [metric for metric in METRICS if metric in detail.columns]
    return (
        detail.groupby(group_cols, as_index=False)[available]
        .mean()
        .sort_values([*group_cols[:-1], "balanced_accuracy"], ascending=[*[True] * (len(group_cols) - 1), False])
    )


if __name__ == "__main__":
    main()
