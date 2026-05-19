from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.evaluation import compute_metrics
from aasvr.exhaustive import build_sweep_grid, config_from_sweep_row, load_exhaustive_protocol
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["mini", "paper", "exhaustive"], default="mini")
    parser.add_argument("--split", default="validation", choices=["tune", "validation", "test"])
    parser.add_argument("--max-settings", type=int, default=0, help="0 means evaluate every setting.")
    parser.add_argument("--setting-shard-index", type=int, default=0)
    parser.add_argument("--setting-shard-count", type=int, default=1)
    parser.add_argument("--trial-shard-index", type=int, default=0)
    parser.add_argument("--trial-shard-count", type=int, default=1)
    args = parser.parse_args()
    run(args)


def run(args: argparse.Namespace) -> None:
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    grid_path = ROOT / f"data/synthetic/hydro_exp1_fault_grid_{args.profile}.csv"
    if not frame_path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    if not grid_path.exists():
        raise SystemExit(
            f"Missing {grid_path}; run scripts/26_build_exhaustive_fault_grid.py --profile {args.profile}."
        )
    frame = pd.read_parquet(frame_path)[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    grid = pd.read_csv(grid_path)
    grid = grid[grid["split"].eq(args.split)].reset_index(drop=True)
    grid = grid.iloc[args.trial_shard_index :: args.trial_shard_count].reset_index(drop=True)
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    base = base.__class__(
        **{
            **base.__dict__,
            "sensors": tuple(sensor for sensor in base.sensors if sensor.name in HYDRO_PRIMARY_SENSORS),
        }
    )
    _protocol, sweep = load_exhaustive_protocol(
        ROOT / "configs/experiments/exhaustive_hydro.yaml",
        profile=args.profile,
    )
    settings = build_sweep_grid(sweep, profile=args.profile)
    if args.max_settings and len(settings) > args.max_settings:
        settings = settings.head(args.max_settings).reset_index(drop=True)
    settings = settings.iloc[args.setting_shard_index :: args.setting_shard_count].reset_index(drop=True)

    rows = []
    for setting in settings.to_dict(orient="records"):
        config = config_from_sweep_row(base, setting)
        metrics_rows = []
        for trial in grid.itertuples(index=False):
            start = max(int(trial.start) - int(trial.pre_fault_samples), 0)
            end = min(
                int(trial.start) + int(trial.duration) + int(trial.post_fault_samples),
                len(frame),
            )
            window = frame.iloc[start:end].reset_index(drop=True)
            spec = FaultSpec(
                sensor=trial.sensor,
                fault_type=trial.fault_type,
                start=int(trial.start) - start,
                duration=int(trial.duration),
                magnitude=float(trial.magnitude),
                seed=int(trial.seed),
                physical_min=float(trial.physical_min),
                physical_max=float(trial.physical_max),
            )
            faulted, labels = inject_fault(window, spec)
            decisions = run_aasvr_with_config(faulted, config)
            metrics = compute_metrics(decisions, labels, prediction_mode="gate_reject")
            metrics_rows.append(metrics.__dict__)
        metric_frame = pd.DataFrame(metrics_rows)
        row = dict(setting)
        row.update(
            {
                "split": args.split,
                "trial_count": len(metric_frame),
                "precision": float(metric_frame["precision"].mean()),
                "recall": float(metric_frame["recall"].mean()),
                "specificity": float(metric_frame["specificity"].mean()),
                "balanced_accuracy": float(metric_frame["balanced_accuracy"].mean()),
                "mean_detection_delay_samples": float(
                    metric_frame["mean_detection_delay_samples"].mean()
                ),
                "false_alarm_events": float(metric_frame["false_alarm_events"].mean()),
                "false_actuations": float(metric_frame["false_actuations"].mean()),
                "missed_actuations": float(metric_frame["missed_actuations"].mean()),
            }
        )
        row["control_objective"] = (
            row["balanced_accuracy"]
            - 0.01 * row["false_actuations"]
            - 0.0005 * row["false_alarm_events"]
            - 0.001 * row["mean_detection_delay_samples"]
        )
        rows.append(row)
    out_dir = ROOT / "results/metrics/exhaustive"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (
        f"hydro_exp1_{args.profile}_{args.split}_sweep_"
        f"settings{args.setting_shard_index:04d}-of-{args.setting_shard_count:04d}_"
        f"trials{args.trial_shard_index:04d}-of-{args.trial_shard_count:04d}.csv"
    )
    pd.DataFrame(rows).sort_values("control_objective", ascending=False).to_csv(out, index=False)
    print(f"Wrote {out} ({len(rows)} settings)")


if __name__ == "__main__":
    main()
