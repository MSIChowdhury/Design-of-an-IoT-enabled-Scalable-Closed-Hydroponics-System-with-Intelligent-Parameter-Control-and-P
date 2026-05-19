from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config, run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    run()


def run() -> None:
    frame = pd.read_parquet(ROOT / "data/processed/hydro_exp1_measurements.parquet")[
        ["timestamp", *HYDRO_PRIMARY_SENSORS]
    ].copy()
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    aasvr_config = AASVRConfig(
        sensors=sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
    )
    starts = _candidate_starts(frame, sensors)
    rows = []
    methods = ("aasvr", "local_outlier_factor", "kalman", "hampel")
    for sensor in HYDRO_PRIMARY_SENSORS:
        for fault_type, magnitudes in {
            "drift": (0.25, 0.50, 1.00),
            "gain_drift": (0.02, 0.05, 0.10),
            "nonlinear_drift": (0.25, 0.50, 1.00),
        }.items():
            for magnitude in magnitudes:
                for rep, global_start in enumerate(starts[sensor][:10]):
                    duration = 60
                    start = max(global_start - 90, 0)
                    end = min(global_start + duration + 120, len(frame))
                    local_start = global_start - start
                    window = frame.iloc[start:end].reset_index(drop=True)
                    spec = FaultSpec(
                        sensor=sensor,
                        fault_type=fault_type,
                        start=local_start,
                        duration=duration,
                        magnitude=float(magnitude),
                        seed=20260519 + rep,
                    )
                    faulted, labels = inject_fault(window, spec)
                    for method in methods:
                        if method == "aasvr":
                            decisions = run_aasvr_with_config(faulted, aasvr_config)
                            prediction_mode = "gate_reject"
                        else:
                            decisions = run_baseline_on_frame(faulted, sensors, method)
                            prediction_mode = "auto"
                        metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
                        row = {
                            "sensor": sensor,
                            "fault_type": fault_type,
                            "magnitude": magnitude,
                            "replicate": rep,
                            "method": method,
                        }
                        row.update(metrics.__dict__)
                        rows.append(row)
    detail = pd.DataFrame(rows)
    summary = (
        detail.groupby(["method", "fault_type"], as_index=False)[
            ["balanced_accuracy", "recall", "specificity", "false_actuations", "mean_detection_delay_samples"]
        ]
        .mean()
        .sort_values(["fault_type", "balanced_accuracy"], ascending=[True, False])
    )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(out_dir / "hydro_exp1_drift_stress_detail.csv", index=False)
    summary.to_csv(out_dir / "hydro_exp1_drift_stress.csv", index=False)
    print(f"Wrote {out_dir / 'hydro_exp1_drift_stress.csv'}")


def _candidate_starts(frame: pd.DataFrame, sensors) -> dict[str, list[int]]:
    starts = {}
    for sensor in sensors:
        values = pd.to_numeric(frame[sensor.name], errors="coerce")
        stable = values.rolling(20, min_periods=20).std().fillna(999) <= max(sensor.uncertainty * 2, sensor.xi_min)
        candidates = stable[stable].index.to_list()
        candidates = [idx for idx in candidates if 120 <= idx < len(frame) - 200]
        if len(candidates) < 10:
            candidates = list(range(120, min(len(frame) - 200, 120 + 50)))
        step = max(len(candidates) // 10, 1)
        starts[sensor.name] = candidates[::step][:10]
    return starts


if __name__ == "__main__":
    main()
