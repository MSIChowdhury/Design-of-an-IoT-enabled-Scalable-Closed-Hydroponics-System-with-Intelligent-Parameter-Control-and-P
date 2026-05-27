from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
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

RISK_PROFILES = {
    "permissive": {"eta_min_high": 0.60, "eta_min_medium": 0.50, "eta_min_low": 0.30},
    "manuscript": {"eta_min_high": 0.75, "eta_min_medium": 0.65, "eta_min_low": 0.50},
    "conservative": {"eta_min_high": 0.90, "eta_min_medium": 0.80, "eta_min_low": 0.60},
}

_WORKER_FRAME: pd.DataFrame | None = None
_WORKER_GRID: pd.DataFrame | None = None
_WORKER_BASE: AASVRConfig | None = None
_WORKER_SENSORS: tuple[SensorConfig, ...] | None = None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true")
    parser.add_argument("--evidence-status", action="store_true")
    parser.add_argument("--operating-tradeoff", action="store_true")
    parser.add_argument("--max-settings", type=int, default=0)
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    run_evidence = args.evidence_status or not args.operating_tradeoff
    run_tradeoff = args.operating_tradeoff or not args.evidence_status
    if run_evidence:
        write_evidence_status()
    if run_tradeoff:
        write_operating_tradeoff(max_settings=args.max_settings, jobs=args.jobs)


def write_evidence_status() -> pd.DataFrame:
    metrics_dir = ROOT / "results/metrics"
    table_dir = ROOT / "results/tables"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    sensor_rows = _parquet_rows(ROOT / "data/processed/hydro_exp1_measurements.parquet")
    grid_path = ROOT / "data/synthetic/hydro_exp1_fault_grid.csv"
    synthetic_rows = int(len(pd.read_csv(grid_path))) if grid_path.exists() else 0
    optional = _optional_status()
    water = _water_status()

    rows = [
        {
            "evidence_source": "Hydroponic sensor feed",
            "availability": "available",
            "available": True,
            "rows": sensor_rows,
            "current_use": "Real signal background for replay and synthetic-fault injection.",
            "claim_boundary": "Supports replay validation, not independent sensor metrology.",
            "next_deployment_requirement": "Keep raw feed export with timezone-stable timestamps.",
        },
        {
            "evidence_source": "Synthetic fault labels",
            "availability": "available",
            "available": synthetic_rows > 0,
            "rows": synthetic_rows,
            "current_use": "Controlled held-out labels for fault detection and authorization scoring.",
            "claim_boundary": "Injected faults cannot represent every real hardware failure.",
            "next_deployment_requirement": "Retain deterministic seeds and fault protocol metadata.",
        },
        {
            "evidence_source": "Actuator command/state log",
            "availability": "not retained",
            "available": optional.get("actuator_state_log", {}).get("available", False),
            "rows": optional.get("actuator_state_log", {}).get("rows", 0),
            "current_use": "Unavailable; response scoring remains replay-derived.",
            "claim_boundary": "No measured physical actuator-response or dosing-improvement claim.",
            "next_deployment_requirement": (
                "Record timestamp, actuator_id, command source, commanded state, measured relay "
                "state, target sensor, expected response direction, runtime/dose, lockout, and override."
            ),
        },
        {
            "evidence_source": "Independent reference measurements",
            "availability": "not available continuously",
            "available": optional.get("reference_measurements", {}).get("available", False),
            "rows": optional.get("reference_measurements", {}).get("rows", 0),
            "current_use": "Unavailable for continuous scoring.",
            "claim_boundary": "No full metrology ground truth for plausible bias, drift, or stuck values.",
            "next_deployment_requirement": (
                "Pair sensor values with calibrated handheld or benchtop reference measurements."
            ),
        },
        {
            "evidence_source": "Water-level calibration",
            "availability": "not available",
            "available": water.get("available", False),
            "rows": water.get("rows", 0),
            "current_use": "Water_Level excluded from the primary analysis.",
            "claim_boundary": "No water-level fault or control-performance claim.",
            "next_deployment_requirement": "Collect paired ultrasonic raw readings and physical levels in cm.",
        },
    ]
    frame = pd.DataFrame(rows)
    for out_dir in (metrics_dir, table_dir):
        out = out_dir / "hydro_exp1_evidence_status.csv"
        frame.to_csv(out, index=False)
        print(f"Wrote {out}")
    return frame


def write_operating_tradeoff(*, max_settings: int = 0, jobs: int = 1) -> pd.DataFrame:
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    grid_path = ROOT / "data/synthetic/hydro_exp1_fault_grid.csv"
    if not frame_path.exists():
        raise SystemExit("Missing hydro_exp1 measurements; run scripts/02_prepare_datasets.py --hydro-exp1.")
    if not grid_path.exists():
        raise SystemExit("Missing compact fault grid; run scripts/05_inject_faults.py --hydro-exp1.")
    frame = pd.read_parquet(frame_path)[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    grid = pd.read_csv(grid_path)
    test_grid = grid[grid["split"].eq("test")].reset_index(drop=True)
    if test_grid.empty:
        raise SystemExit("Compact fault grid has no held-out test rows.")

    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in base.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    settings = _operating_settings()
    if max_settings:
        settings = settings[:max_settings]

    global _WORKER_FRAME, _WORKER_GRID, _WORKER_BASE, _WORKER_SENSORS
    _WORKER_FRAME = frame
    _WORKER_GRID = test_grid
    _WORKER_BASE = base
    _WORKER_SENSORS = sensors
    rows = []
    total = len(settings)
    if jobs <= 1:
        for idx, setting in enumerate(settings, start=1):
            rows.append(_evaluate_setting(setting))
            if idx == 1 or idx % 25 == 0 or idx == total:
                print(f"Evaluated operating setting {idx}/{total}", flush=True)
    else:
        completed = 0
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            futures = [executor.submit(_evaluate_setting, setting) for setting in settings]
            for future in as_completed(futures):
                rows.append(future.result())
                completed += 1
                if completed == 1 or completed % 25 == 0 or completed == total:
                    print(f"Evaluated operating setting {completed}/{total}", flush=True)

    result = pd.DataFrame(rows)
    result["pareto_efficient"] = _pareto_mask(result)
    result = result.sort_values(
        ["is_manuscript_setting", "control_objective", "balanced_accuracy"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    selected = _selected_rows(result)

    metrics_dir = ROOT / "results/metrics"
    table_dir = ROOT / "results/tables"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    for out_dir in (metrics_dir, table_dir):
        result.to_csv(out_dir / "hydro_exp1_operating_tradeoff.csv", index=False)
        selected.to_csv(out_dir / "hydro_exp1_operating_tradeoff_selected.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_operating_tradeoff.csv'}")
        print(f"Wrote {out_dir / 'hydro_exp1_operating_tradeoff_selected.csv'}")
    return result


def _evaluate_setting(setting: dict[str, float | int | str]) -> dict[str, float | int | str | bool]:
    if (
        _WORKER_FRAME is None
        or _WORKER_GRID is None
        or _WORKER_BASE is None
        or _WORKER_SENSORS is None
    ):
        raise RuntimeError("Operating-tradeoff worker was not initialized.")
    config = _config_from_setting(_WORKER_BASE, _WORKER_SENSORS, setting)
    metrics = _run_trials(_WORKER_FRAME, _WORKER_GRID, config)
    row = {**setting, **metrics}
    row["control_objective"] = _control_objective(row)
    row["is_manuscript_setting"] = (
        row["q_min"] == 0.70
        and row["confirm_samples"] == 3
        and row["cooldown_samples"] == 4
        and row["risk_profile"] == "manuscript"
    )
    row["pareto_efficient"] = False
    return row


def _operating_settings() -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for q_min in (0.50, 0.60, 0.70, 0.80, 0.90):
        for confirm_samples in (1, 2, 3, 5, 8):
            for cooldown_samples in (0, 1, 2, 4, 8, 16, 40):
                for risk_profile, thresholds in RISK_PROFILES.items():
                    rows.append(
                        {
                            "q_min": q_min,
                            "confirm_samples": confirm_samples,
                            "cooldown_samples": cooldown_samples,
                            "risk_profile": risk_profile,
                            **thresholds,
                        }
                    )
    return rows


def _config_from_setting(
    base: AASVRConfig,
    sensors: tuple[SensorConfig, ...],
    setting: dict[str, float | int | str],
) -> AASVRConfig:
    tuned_sensors = tuple(
        replace(
            sensor,
            confirm_samples=int(setting["confirm_samples"]),
            cooldown_samples=int(setting["cooldown_samples"]),
        )
        for sensor in sensors
    )
    return replace(
        base,
        sensors=tuned_sensors,
        q_min=float(setting["q_min"]),
        eta_min_high=float(setting["eta_min_high"]),
        eta_min_medium=float(setting["eta_min_medium"]),
        eta_min_low=float(setting["eta_min_low"]),
    )


def _run_trials(frame: pd.DataFrame, grid: pd.DataFrame, config: AASVRConfig) -> dict[str, float]:
    rows = []
    for trial in grid.itertuples(index=False):
        start = max(int(trial.start) - 90, 0)
        end = min(int(trial.start) + int(trial.duration) + 120, len(frame))
        window = frame.iloc[start:end].reset_index(drop=True)
        spec = FaultSpec(
            sensor=trial.sensor,
            fault_type=trial.fault_type,
            start=int(trial.start) - start,
            duration=int(trial.duration),
            magnitude=float(trial.magnitude),
            seed=101,
        )
        faulted, labels = inject_fault(window, spec)
        decisions = run_aasvr_with_config(faulted, config)
        rows.append(compute_metrics(decisions, labels, prediction_mode="gate_reject").__dict__)
    metrics = pd.DataFrame(rows)
    return {
        "n_trials": float(len(metrics)),
        "recall": float(metrics["recall"].mean()),
        "specificity": float(metrics["specificity"].mean()),
        "balanced_accuracy": float(metrics["balanced_accuracy"].mean()),
        "false_positive_rate": float(metrics["false_positive_rate"].mean()),
        "false_negative_rate": float(metrics["false_negative_rate"].mean()),
        "replay_false_authorized_actuations": float(metrics["false_actuations"].mean()),
        "missed_actuations": float(metrics["missed_actuations"].mean()),
        "unsafe_samples": float(metrics["unsafe_samples"].mean()),
        "unsafe_rate": float(metrics["unsafe_rate"].mean()),
        "missed_authorization_rate": float(metrics["missed_authorization_rate"].mean()),
        "mean_detection_delay_samples": float(metrics["mean_detection_delay_samples"].mean()),
        "false_alarm_events": float(metrics["false_alarm_events"].mean()),
        "alerts": float(metrics["alerts"].mean()),
    }


def _control_objective(row: dict[str, float]) -> float:
    return float(
        row["balanced_accuracy"]
        - 0.01 * row["replay_false_authorized_actuations"]
        - 0.05 * row["missed_authorization_rate"]
        - 0.02 * row["unsafe_rate"]
        - 0.0005 * row["false_alarm_events"]
        - 0.001 * row["mean_detection_delay_samples"]
    )


def _pareto_mask(frame: pd.DataFrame) -> list[bool]:
    values = frame[
        [
            "balanced_accuracy",
            "replay_false_authorized_actuations",
            "missed_authorization_rate",
            "alerts",
        ]
    ].to_numpy(dtype=float)
    keep = []
    for idx, row in enumerate(values):
        dominated = False
        for other_idx, other in enumerate(values):
            if idx == other_idx:
                continue
            no_worse = (
                other[0] >= row[0]
                and other[1] <= row[1]
                and other[2] <= row[2]
                and other[3] <= row[3]
            )
            strictly_better = (
                other[0] > row[0]
                or other[1] < row[1]
                or other[2] < row[2]
                or other[3] < row[3]
            )
            if no_worse and strictly_better:
                dominated = True
                break
        keep.append(not dominated)
    return keep


def _selected_rows(frame: pd.DataFrame) -> pd.DataFrame:
    selected = []
    selectors = {
        "manuscript_setting": frame["is_manuscript_setting"],
        "best_control_objective": frame["control_objective"].eq(frame["control_objective"].max()),
        "best_balanced_accuracy": frame["balanced_accuracy"].eq(frame["balanced_accuracy"].max()),
        "lowest_replay_false_authorized_actuation": frame[
            "replay_false_authorized_actuations"
        ].eq(frame["replay_false_authorized_actuations"].min()),
        "lowest_missed_authorization_rate": frame["missed_authorization_rate"].eq(
            frame["missed_authorization_rate"].min()
        ),
    }
    for label, mask in selectors.items():
        if mask.any():
            row = frame[mask].sort_values(
                [
                    "control_objective",
                    "balanced_accuracy",
                    "replay_false_authorized_actuations",
                    "missed_authorization_rate",
                ],
                ascending=[False, False, True, True],
            ).head(1).copy()
            row.insert(0, "selection", label)
            selected.append(row)
    pareto = frame[frame["pareto_efficient"]].copy()
    pareto = pareto.sort_values(
        ["control_objective", "balanced_accuracy"],
        ascending=[False, False],
    ).head(10)
    if not pareto.empty:
        pareto.insert(0, "selection", "pareto_top")
        selected.append(pareto)
    return pd.concat(selected, ignore_index=True).drop_duplicates(
        subset=["selection", "q_min", "confirm_samples", "cooldown_samples", "risk_profile"]
    )


def _optional_status() -> dict[str, dict[str, int | bool]]:
    path = ROOT / "results/run_metadata/hydro_exp1_optional_evidence_status.csv"
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    out = {}
    for row in frame.to_dict(orient="records"):
        out[str(row["name"])] = {
            "available": bool(row.get("available", False)),
            "rows": int(row.get("rows", 0)),
        }
    return out


def _water_status() -> dict[str, int | bool]:
    path = ROOT / "results/run_metadata/hydro_water_level_calibration_status.csv"
    if not path.exists():
        return {"available": False, "rows": 0}
    row = pd.read_csv(path).iloc[0].to_dict()
    return {"available": bool(row.get("available", False)), "rows": int(row.get("n", 0))}


def _parquet_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return int(len(pd.read_parquet(path, columns=["timestamp"])))


if __name__ == "__main__":
    main()
