from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aasvr.baselines import BaselineConfig
from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig, SensorConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config, run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS
from aasvr.robust_scale import tolerance

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
    grid = pd.read_csv(ROOT / "data/synthetic/hydro_exp1_fault_grid.csv")
    grid = grid[grid["split"].eq("test")].reset_index(drop=True)
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    full_config = AASVRConfig(
        sensors=sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
    )
    no_cooldown_config = replace(
        full_config,
        sensors=tuple(replace(sensor, cooldown_samples=0) for sensor in sensors),
    )
    no_confirm_config = replace(
        full_config,
        sensors=tuple(replace(sensor, confirm_samples=1, cooldown_samples=0) for sensor in sensors),
    )
    state_no_supervisor_config = replace(
        full_config,
        sensors=tuple(replace(sensor, confirm_samples=1, cooldown_samples=0) for sensor in sensors),
    )
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
        variants = {
            "raw_threshold_supervisor": run_baseline_on_frame(
                faulted,
                sensors,
                "raw_threshold",
                config=BaselineConfig(method="raw_threshold"),
            ),
            "robust_gate_hold": _run_robust_gate_variant(
                faulted,
                sensors,
                scale_multiplier=full_config.scale_multiplier,
                require_trust=False,
            ),
            "robust_gate_trust_hold": _run_robust_gate_variant(
                faulted,
                sensors,
                scale_multiplier=full_config.scale_multiplier,
                require_trust=True,
                q_min=full_config.q_min,
            ),
            "gate_trust_state_no_supervisor": run_aasvr_with_config(faulted, state_no_supervisor_config),
            "aasvr_no_confirmation_or_cooldown": run_aasvr_with_config(faulted, no_confirm_config),
            "aasvr_no_cooldown": run_aasvr_with_config(faulted, no_cooldown_config),
            "full_aasvr": run_aasvr_with_config(faulted, full_config),
        }
        for variant, decisions in variants.items():
            prediction_mode = "gate_reject" if "aasvr" in variant or "robust_gate" in variant else "auto"
            metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
            row = {
                "dataset": "hydro_exp1",
                "trial_id": trial.trial_id,
                "sensor": trial.sensor,
                "fault_type": trial.fault_type,
                "variant": variant,
            }
            row.update(metrics.__dict__)
            rows.append(row)
    detail = pd.DataFrame(rows)
    metric_cols = [
        "precision",
        "recall",
        "specificity",
        "balanced_accuracy",
        "mean_detection_delay_samples",
        "false_alarm_events",
        "false_actuations",
        "alerts",
    ]
    summary = detail.groupby("variant", as_index=False)[metric_cols].agg(["mean", "median"])
    summary.columns = ["_".join(col).rstrip("_") for col in summary.columns.to_flat_index()]
    summary = summary.rename(columns={"variant_": "variant"})
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(out_dir / "hydro_exp1_component_contribution_detail.csv", index=False)
    summary.sort_values("false_actuations_mean").to_csv(
        out_dir / "hydro_exp1_component_contribution.csv",
        index=False,
    )
    print(f"Wrote {out_dir / 'hydro_exp1_component_contribution.csv'}")


def _run_robust_gate_variant(
    frame: pd.DataFrame,
    sensors: tuple[SensorConfig, ...],
    *,
    scale_multiplier: float,
    require_trust: bool,
    q_min: float = 0.7,
) -> pd.DataFrame:
    state: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "history": deque(maxlen=15),
            "trusted": None,
            "last_raw": None,
            "violations": 0,
            "cooldown": 0,
            "failed": 0,
        }
    )
    sensor_lookup = {sensor.name: sensor for sensor in sensors}
    rows = []
    for sample in frame.to_dict(orient="records"):
        for name, sensor in sensor_lookup.items():
            s = state[name]
            y = _to_float(sample.get(name))
            reasons: list[str] = []
            plausible = np.isfinite(y) and sensor.physical_min <= y <= sensor.physical_max
            if not plausible:
                reasons.append("range_or_missing")
            trusted = s["trusted"] if s["trusted"] is not None else y
            xi = tolerance(
                [*s["history"], y] if np.isfinite(y) else list(s["history"]),
                xi_min=sensor.xi_min,
                scale_multiplier=scale_multiplier,
                rate_limit=sensor.rate_limit,
                dt_seconds=15.0,
                uncertainty=sensor.uncertainty,
            )
            if plausible and s["trusted"] is not None and abs(y - trusted) > xi:
                plausible = False
                reasons.append("trusted_delta")
            if plausible and s["last_raw"] is not None and np.isfinite(s["last_raw"]):
                rate = abs(y - s["last_raw"]) / 15.0
                if rate > sensor.rate_limit:
                    plausible = False
                    reasons.append("rate_limit")
            if plausible:
                s["trusted"] = y
                s["failed"] = 0
            else:
                s["failed"] += 1
            if np.isfinite(y):
                s["history"].append(y)
                s["last_raw"] = y
            trust = max(0.0, 1.0 - 0.25 * s["failed"])
            authorized = _supervisor_authorize(
                sensor,
                s,
                anomaly_free=plausible and (trust >= q_min if require_trust else True),
            )
            rows.append(
                {
                    "timestamp": sample.get("timestamp"),
                    "sensor": name,
                    "raw_value": y,
                    "trusted_value": float(s["trusted"]) if s["trusted"] is not None else float("nan"),
                    "state": "Normal" if plausible else "Suspect transient",
                    "trust_score": trust,
                    "gate_result": "accept" if plausible else "reject",
                    "rectification_action": "accept" if plausible else "hold",
                    "actuation_authorized": authorized,
                    "alert": not plausible,
                    "unsafe_band": _unsafe(sensor, s["trusted"]),
                    "reason_codes": tuple(reasons),
                }
            )
    return pd.DataFrame(rows)


def _supervisor_authorize(sensor: SensorConfig, state: dict[str, Any], *, anomaly_free: bool) -> bool:
    if state["cooldown"] > 0:
        state["cooldown"] -= 1
        state["violations"] = 0
        return False
    trusted = state["trusted"]
    if not anomaly_free or trusted is None or not np.isfinite(trusted):
        state["violations"] = 0
        return False
    violation = trusted < sensor.control_low or trusted > sensor.control_high
    state["violations"] = state["violations"] + 1 if violation else 0
    if state["violations"] >= sensor.confirm_samples:
        state["violations"] = 0
        state["cooldown"] = sensor.cooldown_samples
        return True
    return False


def _unsafe(sensor: SensorConfig, trusted: float | None) -> bool:
    return bool(trusted is not None and np.isfinite(trusted) and (trusted < sensor.control_low or trusted > sensor.control_high))


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    main()
