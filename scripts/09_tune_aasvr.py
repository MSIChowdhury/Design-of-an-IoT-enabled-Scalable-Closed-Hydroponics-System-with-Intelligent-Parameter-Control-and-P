from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true", help="Tune AASVR on hydroponic synthetic faults.")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    tune_hydro_exp1()


def tune_hydro_exp1() -> None:
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    grid_path = ROOT / "data/synthetic/hydro_exp1_fault_grid.csv"
    if not frame_path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    if not grid_path.exists():
        raise SystemExit("Missing hydro_exp1 fault grid; run scripts/05_inject_faults.py --hydro-exp1.")

    frame = pd.read_parquet(frame_path)[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    grid = pd.read_csv(grid_path)
    if "split" in grid.columns:
        grid = grid[grid["split"].eq("validation")].reset_index(drop=True)
    if len(grid) > 90:
        grid = grid.sample(n=90, random_state=20260518).reset_index(drop=True)
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    base_sensors = tuple(sensor for sensor in base.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)

    rows = []
    for scale_multiplier in (4.0, 5.0):
        for q_min in (0.7, 0.85):
            for transient_limit in (2, 3):
                config = AASVRConfig(
                    sensors=base_sensors,
                    q_min=q_min,
                    scale_multiplier=scale_multiplier,
                    transient_limit=transient_limit,
                    persistent_limit=base.persistent_limit,
                    rectification_mode=base.rectification_mode,
                )
                metrics = run_trials(frame, grid, config)
                row = {
                    "dataset": "hydro_exp1",
                    "scale_multiplier": scale_multiplier,
                    "q_min": q_min,
                    "transient_limit": transient_limit,
                }
                row.update(metrics)
                row["control_objective"] = (
                    row["balanced_accuracy"]
                    - 0.01 * row["false_actuations"]
                    - 0.0005 * row["false_alarm_events"]
                    - 0.001 * row["mean_detection_delay_samples"]
                )
                rows.append(row)

    results = pd.DataFrame(rows).sort_values("control_objective", ascending=False)
    out_dir = ROOT / "results/metrics"
    table_dir = ROOT / "results/tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "hydro_exp1_aasvr_tuning.csv"
    table = table_dir / "hydro_exp1_aasvr_tuning_top.csv"
    results.to_csv(out, index=False)
    results.head(10).to_csv(table, index=False)
    print(f"Wrote {out}")
    print(f"Wrote {table}")
    print(results.head(10).to_string(index=False))


def run_trials(frame: pd.DataFrame, grid: pd.DataFrame, config: AASVRConfig) -> dict[str, float]:
    rows = []
    for trial in grid.itertuples(index=False):
        global_start = int(trial.start)
        start = max(global_start - 90, 0)
        end = min(global_start + int(trial.duration) + 120, len(frame))
        local_start = global_start - start
        window = frame.iloc[start:end].reset_index(drop=True)
        spec = FaultSpec(
            sensor=trial.sensor,
            fault_type=trial.fault_type,
            start=local_start,
            duration=int(trial.duration),
            magnitude=float(trial.magnitude),
            seed=101,
        )
        faulted, labels = inject_fault(window, spec)
        decisions = run_aasvr_with_config(faulted, config)
        metrics = compute_metrics(decisions, labels, prediction_mode="gate_reject")
        rows.append(metrics.__dict__)
    frame_metrics = pd.DataFrame(rows)
    return {
        "precision": float(frame_metrics["precision"].mean()),
        "recall": float(frame_metrics["recall"].mean()),
        "f1": float(frame_metrics["f1"].mean()),
        "specificity": float(frame_metrics["specificity"].mean()),
        "balanced_accuracy": float(frame_metrics["balanced_accuracy"].mean()),
        "false_positive_rate": float(frame_metrics["false_positive_rate"].mean()),
        "false_negative_rate": float(frame_metrics["false_negative_rate"].mean()),
        "event_recall": float(frame_metrics["event_recall"].mean()),
        "mean_detection_delay_samples": float(frame_metrics["mean_detection_delay_samples"].mean()),
        "false_alarm_events": float(frame_metrics["false_alarm_events"].mean()),
        "false_actuations": float(frame_metrics["false_actuations"].mean()),
        "alerts": float(frame_metrics["alerts"].mean()),
    }


if __name__ == "__main__":
    main()
