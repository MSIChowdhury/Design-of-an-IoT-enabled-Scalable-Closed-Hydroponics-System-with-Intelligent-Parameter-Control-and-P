from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.core import AASVRConfig, SensorConfig
from aasvr.pipeline import run_aasvr_on_frame, run_aasvr_with_config, run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS
from aasvr.registry import sensors_from_metadata
from aasvr.toydata import make_toy_hydroponic_data

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Run methods on generated toy data.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Run methods on prepared hydroponic Experiment 1.")
    parser.add_argument(
        "--dataset",
        choices=[
            "hydro_exp1",
            "tep",
            "tep_csv",
            "wur",
            "hai",
            "skab",
            "metropt3",
            "batadal",
            "swat",
            "wadi",
            "damadics",
        ],
        help="Run methods on a prepared real/external dataset.",
    )
    args = parser.parse_args()
    if args.hydro_exp1 or args.dataset == "hydro_exp1":
        run_hydro_exp1()
        return
    if args.dataset:
        run_prepared_dataset(args.dataset)
        return
    if not args.toy:
        print("Use --toy, --hydro-exp1, or --dataset hydro_exp1.")
        return
    frame = make_toy_hydroponic_data()
    config_path = ROOT / "configs/methods/aasvr.yaml"
    aasvr_out = run_aasvr_on_frame(frame, config_path)
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    aasvr_out.to_csv(out_dir / "toy_aasvr_decisions.csv", index=False)

    sensors = load_aasvr_config(config_path).sensors
    baselines = load_yaml(ROOT / "configs/methods/baselines.yaml")["required"]
    for method in baselines:
        baseline_out = run_baseline_on_frame(frame, sensors, method)
        baseline_out.to_csv(out_dir / f"toy_{method}_decisions.csv", index=False)
    print(f"Wrote decisions to {out_dir}")


def run_hydro_exp1() -> None:
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    if not frame_path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    frame = pd.read_parquet(frame_path)
    frame = frame[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    r2_sensors = _calibrated_sensors(frame, sensors)
    r2_config = AASVRConfig(
        sensors=r2_sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
        eta_decay=config.eta_decay,
        eta_min_low=config.eta_min_low,
        eta_min_medium=config.eta_min_medium,
        eta_min_high=config.eta_min_high,
        enable_response_residual=True,
        response_mode="sequential",
        reliability_mode="beta",
        beta_prior_success=config.beta_prior_success,
        beta_prior_failure=config.beta_prior_failure,
        beta_lcb_z=config.beta_lcb_z,
        compact_diagnostics=True,
    )
    response_config = AASVRConfig(
        sensors=sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
        eta_decay=config.eta_decay,
        eta_min_low=config.eta_min_low,
        eta_min_medium=config.eta_min_medium,
        eta_min_high=config.eta_min_high,
        enable_response_residual=config.enable_response_residual,
        response_mode=config.response_mode,
        reliability_mode=config.reliability_mode,
        beta_prior_success=config.beta_prior_success,
        beta_prior_failure=config.beta_prior_failure,
        beta_lcb_z=config.beta_lcb_z,
        compact_diagnostics=config.compact_diagnostics,
    )
    base_config = AASVRConfig(
        sensors=tuple(replace(sensor, response_window=0) for sensor in sensors),
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
        eta_decay=config.eta_decay,
        eta_min_low=0.0,
        eta_min_medium=0.0,
        eta_min_high=0.0,
        enable_response_residual=False,
    )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_aasvr_with_config(frame, r2_config).to_csv(out_dir / "hydro_exp1_aasvr_r2_decisions.csv", index=False)
    run_aasvr_with_config(frame, response_config).to_csv(out_dir / "hydro_exp1_aasvr_r_decisions.csv", index=False)
    run_aasvr_with_config(frame, base_config).to_csv(out_dir / "hydro_exp1_aasvr_decisions.csv", index=False)
    baseline_config = load_yaml(ROOT / "configs/methods/baselines.yaml")
    baselines = baseline_config.get("full_replay", baseline_config["required"])
    for method in baselines:
        baseline_out = run_baseline_on_frame(frame, sensors, method)
        baseline_out.to_csv(out_dir / f"hydro_exp1_{method}_decisions.csv", index=False)
    print(f"Wrote hydro_exp1 decisions to {out_dir}")


def _calibrated_sensors(frame: pd.DataFrame, sensors: tuple[SensorConfig, ...]) -> tuple[SensorConfig, ...]:
    calibration = frame.iloc[: max(200, int(len(frame) * 0.20))]
    out = []
    for sensor in sensors:
        values = pd.to_numeric(calibration[sensor.name], errors="coerce")
        deltas = values.diff().abs().dropna()
        calibrated = None
        if not deltas.empty:
            calibrated = float(max(sensor.xi_min, sensor.uncertainty, deltas.quantile(0.995)))
        out.append(replace(sensor, calibrated_xi=calibrated))
    return tuple(out)


def run_prepared_dataset(dataset: str) -> None:
    frame_path = ROOT / f"data/processed/{dataset}_measurements.parquet"
    metadata_path = ROOT / f"data/processed/{dataset}_metadata.csv"
    if not frame_path.exists() or not metadata_path.exists():
        print(f"Skipping {dataset}; prepared measurements/metadata are not available.")
        return
    frame = pd.read_parquet(frame_path)
    metadata = pd.read_csv(metadata_path)
    sensors = sensors_from_metadata(metadata)
    if not sensors:
        print(f"Skipping {dataset}; metadata contains no sensor variables.")
        return
    sensor_names = [sensor.name for sensor in sensors if sensor.name in frame.columns]
    frame = frame[["timestamp", *sensor_names]].copy()
    sensors = tuple(sensor for sensor in sensors if sensor.name in sensor_names)
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    config = AASVRConfig(
        sensors=sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
    )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_aasvr_with_config(frame, config).to_csv(out_dir / f"{dataset}_aasvr_decisions.csv", index=False)
    baselines = load_yaml(ROOT / "configs/methods/baselines.yaml")["required"]
    for method in baselines:
        baseline_out = run_baseline_on_frame(frame, sensors, method)
        baseline_out.to_csv(out_dir / f"{dataset}_{method}_decisions.csv", index=False)
    print(f"Wrote {dataset} decisions to {out_dir}")


if __name__ == "__main__":
    main()
