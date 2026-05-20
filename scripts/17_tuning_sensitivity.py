from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


WEIGHT_PROFILES = {
    "ba_only": {
        "balanced_accuracy": 1.0,
        "false_actuations": 0.0,
        "false_alarm_events": 0.0,
        "mean_detection_delay_samples": 0.0,
    },
    "reported": {
        "balanced_accuracy": 1.0,
        "false_actuations": -0.01,
        "false_alarm_events": -0.0005,
        "mean_detection_delay_samples": -0.001,
    },
    "actuation_medium": {
        "balanced_accuracy": 1.0,
        "false_actuations": -0.05,
        "false_alarm_events": -0.0005,
        "mean_detection_delay_samples": -0.001,
    },
    "actuation_high": {
        "balanced_accuracy": 1.0,
        "false_actuations": -0.10,
        "false_alarm_events": -0.0005,
        "mean_detection_delay_samples": -0.001,
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true")
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    run(top_n=args.top_n)


def run(*, top_n: int) -> None:
    tuning_path = ROOT / "results/metrics/hydro_exp1_aasvr_tuning.csv"
    if not tuning_path.exists():
        raise SystemExit("Missing AASVR tuning table; run scripts/09_tune_aasvr.py --hydro-exp1.")
    tuning = pd.read_csv(tuning_path).copy()
    top = tuning.sort_values("control_objective", ascending=False).head(top_n).reset_index(drop=True)

    frame = pd.read_parquet(ROOT / "data/processed/hydro_exp1_measurements.parquet")[
        ["timestamp", *HYDRO_PRIMARY_SENSORS]
    ].copy()
    grid = pd.read_csv(ROOT / "data/synthetic/hydro_exp1_fault_grid.csv")
    test_grid = grid[grid["split"].eq("test")].reset_index(drop=True)
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in base.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    rows = []
    for idx, row in top.iterrows():
        config = replace(
            base,
            sensors=sensors,
            q_min=float(row["q_min"]),
            scale_multiplier=float(row["scale_multiplier"]),
            transient_limit=int(row["transient_limit"]),
        )
        test_metrics = _run_trials(frame, test_grid, config)
        out = {
            "setting_rank": int(idx + 1),
            "scale_multiplier": float(row["scale_multiplier"]),
            "q_min": float(row["q_min"]),
            "transient_limit": int(row["transient_limit"]),
            "validation_balanced_accuracy": float(row["balanced_accuracy"]),
            "validation_false_actuations": float(row["false_actuations"]),
            "validation_false_alarm_events": float(row["false_alarm_events"]),
            "validation_mean_detection_delay_samples": float(row["mean_detection_delay_samples"]),
        }
        out.update({f"test_{key}": value for key, value in test_metrics.items()})
        rows.append(out)
    transfer = pd.DataFrame(rows)
    for profile, weights in WEIGHT_PROFILES.items():
        tuning[f"objective_{profile}"] = _objective(tuning, weights)
    sensitivity_rows = []
    for profile in WEIGHT_PROFILES:
        selected = tuning.sort_values(f"objective_{profile}", ascending=False).head(1).iloc[0]
        match = transfer[
            transfer["scale_multiplier"].eq(selected["scale_multiplier"])
            & transfer["q_min"].eq(selected["q_min"])
            & transfer["transient_limit"].eq(selected["transient_limit"])
        ]
        source = match.iloc[0].to_dict() if not match.empty else {}
        sensitivity_rows.append(
            {
                "profile": profile,
                "scale_multiplier": float(selected["scale_multiplier"]),
                "q_min": float(selected["q_min"]),
                "transient_limit": int(selected["transient_limit"]),
                "validation_objective": float(selected[f"objective_{profile}"]),
                "validation_balanced_accuracy": float(selected["balanced_accuracy"]),
                "validation_false_actuations": float(selected["false_actuations"]),
                "test_balanced_accuracy": source.get("test_balanced_accuracy", float("nan")),
                "test_false_actuations": source.get("test_false_actuations", float("nan")),
                "test_false_alarm_events": source.get("test_false_alarm_events", float("nan")),
            }
        )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    transfer.to_csv(out_dir / "hydro_exp1_tuning_transfer.csv", index=False)
    pd.DataFrame(sensitivity_rows).to_csv(
        out_dir / "hydro_exp1_objective_sensitivity.csv",
        index=False,
    )
    print(f"Wrote {out_dir / 'hydro_exp1_tuning_transfer.csv'}", flush=True)
    print(f"Wrote {out_dir / 'hydro_exp1_objective_sensitivity.csv'}", flush=True)
    _cusum_sensitivity(frame, grid, base, sensors).to_csv(
        out_dir / "hydro_exp1_cusum_sensitivity.csv",
        index=False,
    )
    print(f"Wrote {out_dir / 'hydro_exp1_cusum_sensitivity.csv'}", flush=True)
    _response_memory_sensitivity(frame, grid, base, sensors).to_csv(
        out_dir / "hydro_exp1_response_memory_sensitivity.csv",
        index=False,
    )
    print(f"Wrote {out_dir / 'hydro_exp1_response_memory_sensitivity.csv'}", flush=True)


def _run_trials(frame: pd.DataFrame, grid: pd.DataFrame, config: AASVRConfig) -> dict[str, float]:
    rows = []
    for trial in grid.itertuples(index=False):
        start = max(int(trial.start) - 90, 0)
        end = min(int(trial.start) + int(trial.duration) + 120, len(frame))
        local_start = int(trial.start) - start
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
        rows.append(compute_metrics(decisions, labels, prediction_mode="gate_reject").__dict__)
    metrics = pd.DataFrame(rows)
    return {
        "balanced_accuracy": float(metrics["balanced_accuracy"].mean()),
        "false_actuations": float(metrics["false_actuations"].mean()),
        "false_alarm_events": float(metrics["false_alarm_events"].mean()),
        "mean_detection_delay_samples": float(metrics["mean_detection_delay_samples"].mean()),
    }


def _cusum_sensitivity(
    frame: pd.DataFrame,
    grid: pd.DataFrame,
    base: AASVRConfig,
    sensors: tuple,
) -> pd.DataFrame:
    rows = []
    validation_grid = grid[grid["split"].eq("validation")].reset_index(drop=True)
    test_grid = grid[grid["split"].eq("test")].reset_index(drop=True)
    for drift in (0.0, 0.05, 0.10, 0.20, 0.40):
        for threshold in (0.40, 0.60, 1.00, 2.00, 5.00):
            metrics = _run_trials(
                frame,
                validation_grid,
                _config_with_cusum(base, sensors, drift, threshold),
            )
            rows.append(
                {
                    "split": "validation",
                    "cusum_drift_multiplier": drift,
                    "cusum_threshold_multiplier": threshold,
                    **metrics,
                    "control_objective": _control_objective(metrics),
                }
            )
    validation = pd.DataFrame(rows).sort_values("control_objective", ascending=False)
    selected_pairs = {
        (float(base.sensors[0].cusum_drift_multiplier), float(base.sensors[0].cusum_threshold_multiplier)),
        *[
            (float(row.cusum_drift_multiplier), float(row.cusum_threshold_multiplier))
            for row in validation.head(3).itertuples(index=False)
        ],
    }
    for drift, threshold in sorted(selected_pairs):
        metrics = _run_trials(
            frame,
            test_grid,
            _config_with_cusum(base, sensors, drift, threshold),
        )
        rows.append(
            {
                "split": "test_selected",
                "cusum_drift_multiplier": drift,
                "cusum_threshold_multiplier": threshold,
                **metrics,
                "control_objective": _control_objective(metrics),
            }
        )
    return pd.DataFrame(rows).sort_values(["split", "control_objective"], ascending=[True, False])


def _config_with_cusum(
    base: AASVRConfig,
    sensors: tuple,
    drift: float,
    threshold: float,
) -> AASVRConfig:
    tuned_sensors = tuple(
        replace(
            sensor,
            cusum_drift_multiplier=drift,
            cusum_threshold_multiplier=threshold,
        )
        for sensor in sensors
    )
    return replace(base, sensors=tuned_sensors)


def _response_memory_sensitivity(
    frame: pd.DataFrame,
    grid: pd.DataFrame,
    base: AASVRConfig,
    sensors: tuple,
) -> pd.DataFrame:
    rows = []
    for split in ("validation", "test"):
        split_grid = grid[grid["split"].eq(split)].reset_index(drop=True)
        for eta_decay in (0.50, 0.70, 0.80, 0.90, 0.95):
            config = replace(base, sensors=sensors, eta_decay=eta_decay)
            metrics = _run_trials(frame, split_grid, config)
            rows.append(
                {
                    "split": split,
                    "eta_decay": eta_decay,
                    **metrics,
                    "control_objective": _control_objective(metrics),
                }
            )
    return pd.DataFrame(rows).sort_values(["split", "control_objective"], ascending=[True, False])


def _control_objective(metrics: dict[str, float]) -> float:
    return float(
        metrics["balanced_accuracy"]
        - 0.01 * metrics["false_actuations"]
        - 0.0005 * metrics["false_alarm_events"]
        - 0.001 * metrics["mean_detection_delay_samples"]
    )


def _objective(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    total = pd.Series(0.0, index=frame.index)
    for metric, weight in weights.items():
        total = total + float(weight) * frame[metric].astype(float)
    return total


if __name__ == "__main__":
    main()
