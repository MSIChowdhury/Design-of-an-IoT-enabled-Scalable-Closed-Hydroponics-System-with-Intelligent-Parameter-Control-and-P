from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig, SensorConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true", help="Run AASVR ablations on hydro Exp. 1.")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    run_hydro_exp1_ablation()


def run_hydro_exp1_ablation() -> None:
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    grid_path = ROOT / "data/synthetic/hydro_exp1_fault_grid.csv"
    if not frame_path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    if not grid_path.exists():
        raise SystemExit("Missing hydro_exp1 fault grid; run scripts/05_inject_faults.py --hydro-exp1.")

    frame = pd.read_parquet(frame_path)[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    grid = pd.read_csv(grid_path)
    if "split" in grid.columns:
        grid = grid[grid["split"].eq("test")].reset_index(drop=True)
    if len(grid) > 120:
        grid = grid.sample(n=120, random_state=20260518).reset_index(drop=True)
    full_config = _primary_sensor_config(load_aasvr_config(ROOT / "configs/methods/aasvr.yaml"))
    variants = _ablation_variants(full_config)

    rows = []
    half_window_before = 90
    half_window_after = 120
    for trial in grid.itertuples(index=False):
        global_start = int(trial.start)
        start = max(global_start - half_window_before, 0)
        end = min(global_start + int(trial.duration) + half_window_after, len(frame))
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
        for variant_name, config, prediction_mode in variants:
            decisions = run_aasvr_with_config(faulted, config)
            metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
            row = {
                "dataset": "hydro_exp1",
                "variant": variant_name,
                "trial_id": trial.trial_id,
                "split": getattr(trial, "split", "test"),
                "fault_protocol_id": getattr(trial, "fault_protocol_id", ""),
                "sensor": trial.sensor,
                "fault_type": trial.fault_type,
                "duration": int(trial.duration),
                "magnitude": float(trial.magnitude),
                "prediction_mode": prediction_mode,
            }
            row.update(metrics.__dict__)
            rows.append(row)

    detail = pd.DataFrame(rows)
    metric_cols = [
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
        "missed_actuations",
        "unsafe_samples",
        "alerts",
    ]
    summary = (
        detail.groupby(["variant", "prediction_mode"], as_index=False)[metric_cols]
        .mean()
        .sort_values("balanced_accuracy", ascending=False)
    )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / "hydro_exp1_ablation_detail.csv"
    summary_path = out_dir / "hydro_exp1_ablation_summary.csv"
    detail.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)
    print(f"Wrote {detail_path}")
    print(f"Wrote {summary_path}")


def _primary_sensor_config(config: AASVRConfig) -> AASVRConfig:
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    return replace(config, sensors=sensors)


def _ablation_variants(config: AASVRConfig) -> list[tuple[str, AASVRConfig, str]]:
    no_confirmation = replace(config, sensors=_replace_sensors(config.sensors, confirm_samples=1))
    no_cooldown = replace(config, sensors=_replace_sensors(config.sensors, cooldown_samples=0))
    no_trend_guard = replace(config, sensors=_replace_sensors(config.sensors, trend_window=0))
    no_stuck_detector = replace(config, sensors=_replace_sensors(config.sensors, stuck_window=0))
    slow_escalation = replace(config, transient_limit=999, persistent_limit=1000)
    return [
        ("full_aasvr", config, "gate_reject"),
        ("alert_only_scoring", config, "alert"),
        ("no_robust_mad_scale", replace(config, scale_multiplier=0.0), "gate_reject"),
        ("no_uncommanded_trend_guard", no_trend_guard, "gate_reject"),
        ("no_stuck_detector", no_stuck_detector, "gate_reject"),
        ("no_persistence_escalation", slow_escalation, "gate_reject"),
        ("no_actuation_confirmation", no_confirmation, "gate_reject"),
        ("no_cooldown", no_cooldown, "gate_reject"),
        ("bounded_prediction_rectification", replace(config, rectification_mode="bounded_prediction"), "gate_reject"),
    ]


def _replace_sensors(sensors: tuple[SensorConfig, ...], **kwargs: int) -> tuple[SensorConfig, ...]:
    return tuple(replace(sensor, **kwargs) for sensor in sensors)


if __name__ == "__main__":
    main()
