from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aasvr.baselines import BaselineConfig
from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig, SensorConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config, run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["mini", "paper", "exhaustive"], default="mini")
    parser.add_argument("--split", default="test", choices=["tune", "validation", "test", "all"])
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument(
        "--methods",
        default="aasvr_r,aasvr_no_response,raw_threshold,lockout_only,cusum_only",
        help="Comma-separated method list.",
    )
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
    if args.split != "all":
        grid = grid[grid["split"].eq(args.split)].reset_index(drop=True)
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("--shard-index must be in [0, shard-count).")
    grid = grid.iloc[args.shard_index :: args.shard_count].reset_index(drop=True)
    base = _primary_sensor_config(load_aasvr_config(ROOT / "configs/methods/aasvr.yaml"))
    methods = tuple(name.strip() for name in args.methods.split(",") if name.strip())
    rows = []
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
        for method in methods:
            decisions, prediction_mode = _run_method(faulted, base, method)
            metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
            row = {
                "dataset": "hydro_exp1",
                "profile": args.profile,
                "split": trial.split,
                "shard_index": args.shard_index,
                "shard_count": args.shard_count,
                "method": method,
                "trial_id": trial.trial_id,
                "fault_protocol_id": trial.fault_protocol_id,
                "sensor": trial.sensor,
                "fault_type": trial.fault_type,
                "sigma_multiplier": float(trial.sigma_multiplier),
                "duration": int(trial.duration),
            }
            row.update(metrics.__dict__)
            rows.append(row)
    out_dir = ROOT / "results/metrics/exhaustive"
    out_dir.mkdir(parents=True, exist_ok=True)
    split_name = args.split
    out = out_dir / (
        f"hydro_exp1_{args.profile}_{split_name}_"
        f"shard{args.shard_index:04d}-of-{args.shard_count:04d}.csv"
    )
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out} ({len(rows)} method-trials)")


def _run_method(frame: pd.DataFrame, base: AASVRConfig, method: str) -> tuple[pd.DataFrame, str]:
    sensors = base.sensors
    if method == "aasvr_r":
        return run_aasvr_with_config(frame, base), "gate_reject"
    if method == "aasvr_no_response":
        config = replace(
            base,
            sensors=tuple(replace(sensor, response_window=0) for sensor in sensors),
            enable_response_residual=False,
            eta_min_high=0.0,
            eta_min_medium=0.0,
            eta_min_low=0.0,
        )
        return run_aasvr_with_config(frame, config), "gate_reject"
    if method == "no_cusum":
        config = replace(
            base,
            sensors=tuple(
                replace(sensor, cusum_drift_multiplier=0.0, cusum_threshold_multiplier=0.0)
                for sensor in sensors
            ),
        )
        return run_aasvr_with_config(frame, config), "gate_reject"
    if method == "lockout_only":
        return _run_lockout_only(frame, sensors), "gate_reject"
    if method == "cusum_only":
        config = BaselineConfig(method="cusum")
        return run_baseline_on_frame(frame, sensors, "cusum", config=config), "auto"
    if method in {
        "raw_threshold",
        "moving_average",
        "moving_median",
        "hampel",
        "kalman",
        "ewma",
        "cusum",
        "glr",
        "recursive_pca",
        "isolation_forest",
        "one_class_svm",
        "local_outlier_factor",
    }:
        return run_baseline_on_frame(frame, sensors, method, config=BaselineConfig(method=method)), "auto"
    raise ValueError(f"Unknown exhaustive method: {method}")


def _primary_sensor_config(config: AASVRConfig) -> AASVRConfig:
    return replace(config, sensors=tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS))


def _run_lockout_only(frame: pd.DataFrame, sensors: tuple[SensorConfig, ...]) -> pd.DataFrame:
    """Controller persistence/cooldown without any anomaly detector.

    This isolates how much false-actuation reduction is supplied by the existing
    lockout/supervisor alone, independent of validation logic.
    """

    rows = []
    state = {sensor.name: {"violations": 0, "cooldown": 0} for sensor in sensors}
    for sample in frame.to_dict(orient="records"):
        for sensor in sensors:
            y = float(sample.get(sensor.name, float("nan")))
            trusted = y
            s = state[sensor.name]
            authorized = False
            if s["cooldown"] > 0:
                s["cooldown"] -= 1
                s["violations"] = 0
            elif pd.notna(trusted):
                violation = trusted < sensor.control_low or trusted > sensor.control_high
                s["violations"] = s["violations"] + 1 if violation else 0
                if s["violations"] >= sensor.confirm_samples:
                    authorized = True
                    s["violations"] = 0
                    s["cooldown"] = sensor.cooldown_samples
            rows.append(
                {
                    "timestamp": sample.get("timestamp"),
                    "sensor": sensor.name,
                    "raw_value": y,
                    "trusted_value": trusted,
                    "state": "Normal",
                    "trust_score": 1.0,
                    "gate_result": "accept",
                    "rectification_action": "lockout_only",
                    "actuation_authorized": authorized,
                    "alert": False,
                    "unsafe_band": bool(
                        pd.notna(trusted)
                        and (trusted < sensor.control_low or trusted > sensor.control_high)
                    ),
                    "reason_codes": (),
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
