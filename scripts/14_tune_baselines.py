from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import pandas as pd

from aasvr.baselines import BaselineConfig
from aasvr.config import load_aasvr_config, load_yaml
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true", help="Tune baselines on validation faults.")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    tune_hydro_exp1_baselines()


def tune_hydro_exp1_baselines() -> None:
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
    aasvr = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in aasvr.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    base = load_yaml(ROOT / "configs/methods/baselines.yaml")
    weights = base.get("tuning", {}).get("objective_weights", {})
    rows = []
    for method in base["required"]:
        for config in _candidate_configs(method, base):
            metrics = _run_trials(frame, grid, sensors, config)
            row = {"dataset": "hydro_exp1", "method": method, **_config_row(config), **metrics}
            row["control_objective"] = _objective(row, weights)
            rows.append(row)

    results = pd.DataFrame(rows).sort_values(["method", "control_objective"], ascending=[True, False])
    best = results.groupby("method", as_index=False).head(1).sort_values(
        "control_objective", ascending=False
    )
    out_dir = ROOT / "results/metrics"
    table_dir = ROOT / "results/tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_dir / "hydro_exp1_baseline_tuning.csv", index=False)
    best.to_csv(out_dir / "hydro_exp1_baseline_tuning_best.csv", index=False)
    best.to_csv(table_dir / "hydro_exp1_baseline_tuning_best.csv", index=False)
    print(f"Wrote {out_dir / 'hydro_exp1_baseline_tuning.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_baseline_tuning_best.csv'}")


def _candidate_configs(method: str, base: dict) -> list[BaselineConfig]:
    defaults = base.get("defaults", {})
    grids = base.get("tuning", {}).get("grids", {})
    kwargs = {"method": method, **defaults}
    if method in {"raw_threshold", "original"}:
        return [BaselineConfig(**_baseline_kwargs(kwargs))]
    if method in {"moving_average", "moving_median", "hampel", "pca"}:
        return [
            BaselineConfig(**_baseline_kwargs({**kwargs, "window": window, "threshold_multiplier": threshold}))
            for window, threshold in product(grids["window"], grids["threshold_multiplier"])
        ]
    if method == "ewma":
        return [
            BaselineConfig(**_baseline_kwargs({**kwargs, "alpha": alpha, "threshold_multiplier": threshold}))
            for alpha, threshold in product(grids["alpha"], grids["threshold_multiplier"])
        ]
    if method == "cusum":
        return [
            BaselineConfig(**_baseline_kwargs({**kwargs, "cusum_drift": drift, "cusum_threshold": threshold}))
            for drift, threshold in product(grids["cusum_drift"], grids["cusum_threshold"])
        ]
    if method == "kalman":
        return [
            BaselineConfig(
                **_baseline_kwargs(
                    {
                        **kwargs,
                        "kalman_process_var": process_var,
                        "kalman_measurement_var": measurement_var,
                        "threshold_multiplier": threshold,
                    }
                )
            )
            for process_var, measurement_var, threshold in product(
                grids["kalman_process_var"],
                grids["kalman_measurement_var"],
                grids["threshold_multiplier"],
            )
        ]
    if method == "glr":
        return [
            BaselineConfig(**_baseline_kwargs({**kwargs, "glr_window": window, "glr_threshold": threshold}))
            for window, threshold in product(grids["glr_window"], grids["glr_threshold"])
        ]
    if method == "recursive_pca":
        return [
            BaselineConfig(
                **_baseline_kwargs(
                    {**kwargs, "recursive_pca_window": window, "recursive_pca_threshold": threshold}
                )
            )
            for window, threshold in product(grids["recursive_pca_window"], grids["recursive_pca_threshold"])
        ]
    if method in {"isolation_forest", "one_class_svm"}:
        return [
            BaselineConfig(**_baseline_kwargs({**kwargs, "ml_contamination": contamination}))
            for contamination in grids["ml_contamination"]
        ]
    if method == "local_outlier_factor":
        return [
            BaselineConfig(
                **_baseline_kwargs({**kwargs, "ml_contamination": contamination, "ml_neighbors": neighbors})
            )
            for contamination, neighbors in product(grids["ml_contamination"], grids["ml_neighbors"])
        ]
    return [BaselineConfig(**_baseline_kwargs(kwargs))]


def _baseline_kwargs(kwargs: dict) -> dict:
    valid = BaselineConfig.__dataclass_fields__.keys()
    return {key: value for key, value in kwargs.items() if key in valid}


def _run_trials(
    frame: pd.DataFrame,
    grid: pd.DataFrame,
    sensors,
    config: BaselineConfig,
) -> dict[str, float]:
    rows = []
    for trial in grid.itertuples(index=False):
        start, end, local_start = _window_bounds(frame, trial)
        window = frame.iloc[start:end].reset_index(drop=True)
        spec = FaultSpec(
            sensor=trial.sensor,
            fault_type=trial.fault_type,
            start=local_start,
            duration=int(trial.duration),
            magnitude=float(trial.magnitude),
            seed=int(getattr(trial, "seed", 101)),
        )
        faulted, labels = inject_fault(window, spec)
        decisions = run_baseline_on_frame(faulted, sensors, config.method, config=config)
        rows.append(compute_metrics(decisions, labels, prediction_mode="auto").__dict__)
    metrics = pd.DataFrame(rows)
    return {
        "precision": float(metrics["precision"].mean()),
        "recall": float(metrics["recall"].mean()),
        "specificity": float(metrics["specificity"].mean()),
        "balanced_accuracy": float(metrics["balanced_accuracy"].mean()),
        "false_alarm_events": float(metrics["false_alarm_events"].mean()),
        "false_actuations": float(metrics["false_actuations"].mean()),
        "missed_actuations": float(metrics["missed_actuations"].mean()),
        "unsafe_samples": float(metrics["unsafe_samples"].mean()),
        "decision_count": float(metrics["decision_count"].mean()),
        "unsafe_rate": float(metrics["unsafe_rate"].mean()),
        "missed_authorization_rate": float(metrics["missed_authorization_rate"].mean()),
        "mean_detection_delay_samples": float(metrics["mean_detection_delay_samples"].mean()),
    }


def _window_bounds(frame: pd.DataFrame, trial) -> tuple[int, int, int]:
    global_start = int(trial.start)
    start = max(global_start - 90, 0)
    end = min(global_start + int(trial.duration) + 120, len(frame))
    return start, end, global_start - start


def _config_row(config: BaselineConfig) -> dict[str, float | int | str]:
    return {
        key: value
        for key, value in config.__dict__.items()
        if key != "method" and isinstance(value, int | float | str)
    }


def _objective(row: dict, weights: dict) -> float:
    if not weights:
        weights = {
            "balanced_accuracy": 1.0,
            "false_actuations": -0.01,
            "missed_authorization_rate": -0.05,
            "unsafe_rate": -0.02,
            "false_alarm_events": -0.0005,
            "mean_detection_delay_samples": -0.001,
        }
    return float(sum(float(row.get(metric, 0.0)) * float(weight) for metric, weight in weights.items()))


if __name__ == "__main__":
    main()
