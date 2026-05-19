from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig, SensorConfig
from aasvr.pipeline import run_aasvr_with_config
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]

FAULT_TYPES = ("healthy", "no_response", "weak_response", "wrong_direction", "delayed_response", "stuck_after_command")
SIDES = ("high", "low")


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
    base_config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in base_config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    sensors_r2 = _calibrated_sensors(frame, sensors)
    aasvr_r2 = _primary_config(base_config, sensors=sensors_r2, enable_response=True, r2=True)
    aasvr_r = _primary_config(base_config, sensors=sensors, enable_response=True)
    aasvr_base = _primary_config(base_config, sensors=sensors, enable_response=False)
    baseline_sample = _baseline_sample(frame)

    rows: list[dict[str, object]] = []
    decisions_rows: list[pd.DataFrame] = []
    for sensor in sensors:
        if sensor.response_window <= 0:
            continue
        for side in SIDES:
            if side == "low" and sensor.expected_direction == "decreasing":
                continue
            if side == "high" and sensor.expected_direction == "increasing":
                continue
            for fault_type in FAULT_TYPES:
                scenario = _make_scenario(sensor, side, fault_type, baseline_sample)
                for method, config in (("aasvr", aasvr_base), ("aasvr_r", aasvr_r), ("aasvr_r2", aasvr_r2)):
                    decisions = run_aasvr_with_config(scenario, config)
                    subset = decisions[decisions["sensor"].eq(sensor.name)].reset_index(drop=True)
                    metrics = _response_metrics(subset, fault_type=fault_type)
                    rows.append(
                        {
                            "method": method,
                            "sensor": sensor.name,
                            "side": side,
                            "fault_type": fault_type,
                            **metrics,
                        }
                    )
                    tagged = subset.copy()
                    tagged.insert(0, "method", method)
                    tagged.insert(1, "scenario_sensor", sensor.name)
                    tagged.insert(2, "side", side)
                    tagged.insert(3, "fault_type", fault_type)
                    decisions_rows.append(tagged)

    detail = pd.DataFrame(rows)
    summary = (
        detail.groupby("method", as_index=False)[
            [
                "response_fault_detected",
                "response_fault_alert",
                "response_correct",
                "response_fault_delay",
                "authorizations",
                "repeated_authorizations_after_fault",
                "final_response_reliability",
            ]
        ]
        .mean()
        .sort_values("response_fault_detected", ascending=False)
    )
    by_fault = (
        detail.groupby(["method", "fault_type"], as_index=False)[
            [
                "response_fault_detected",
                "response_fault_alert",
                "response_correct",
                "response_fault_delay",
                "authorizations",
                "repeated_authorizations_after_fault",
                "final_response_reliability",
            ]
        ]
        .mean()
        .sort_values(["fault_type", "method"])
    )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(out_dir / "hydro_exp1_response_replay_detail.csv", index=False)
    summary.to_csv(out_dir / "hydro_exp1_response_replay_summary.csv", index=False)
    by_fault.to_csv(out_dir / "hydro_exp1_response_replay_by_fault_type.csv", index=False)
    pd.concat(decisions_rows, ignore_index=True).to_csv(
        out_dir / "hydro_exp1_response_replay_decisions.csv",
        index=False,
    )
    print(f"Wrote {out_dir / 'hydro_exp1_response_replay_summary.csv'}")


def _primary_config(
    config: AASVRConfig,
    *,
    sensors: tuple[SensorConfig, ...],
    enable_response: bool,
    r2: bool = False,
) -> AASVRConfig:
    if enable_response:
        return AASVRConfig(
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
            enable_response_residual=True,
            response_mode="sequential" if r2 else config.response_mode,
            reliability_mode="beta" if r2 else config.reliability_mode,
            beta_prior_success=config.beta_prior_success,
            beta_prior_failure=config.beta_prior_failure,
            beta_lcb_z=config.beta_lcb_z,
            compact_diagnostics=r2,
        )
    disabled = tuple(replace(sensor, response_window=0) for sensor in sensors)
    return AASVRConfig(
        sensors=disabled,
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


def _baseline_sample(frame: pd.DataFrame) -> dict[str, float]:
    values = {}
    for sensor in HYDRO_PRIMARY_SENSORS:
        series = pd.to_numeric(frame[sensor], errors="coerce")
        values[sensor] = float(series.dropna().median())
    return values


def _make_scenario(
    sensor: SensorConfig,
    side: str,
    fault_type: str,
    baseline_sample: dict[str, float],
    *,
    rows: int = 42,
) -> pd.DataFrame:
    samples = []
    start_value = _outside_band_value(sensor, side)
    direction = -1 if side == "high" else 1
    response_unit = max(sensor.response_min_delta, sensor.uncertainty, sensor.xi_min)
    band_distance = (
        start_value - sensor.control_high
        if side == "high"
        else sensor.control_low - start_value
    )
    response_delta = band_distance + 1.2 * response_unit
    command_index = max(sensor.confirm_samples - 1, 0)
    for idx in range(rows):
        row = {"timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(seconds=15 * idx)}
        row.update(baseline_sample)
        row[sensor.name] = _scenario_value(
            start_value=start_value,
            direction=direction,
            response_delta=response_delta,
            fault_type=fault_type,
            idx=idx,
            command_index=command_index,
            response_window=sensor.response_window,
        )
        samples.append(row)
    return pd.DataFrame(samples)


def _outside_band_value(sensor: SensorConfig, side: str) -> float:
    width = max(sensor.control_high - sensor.control_low, sensor.xi_min)
    response = max(sensor.response_min_delta, sensor.uncertainty, sensor.xi_min)
    margin = max(2.0 * response, 0.1 * width)
    if side == "high":
        return min(sensor.physical_max - sensor.xi_min, sensor.control_high + margin)
    return max(sensor.physical_min + sensor.xi_min, sensor.control_low - margin)


def _scenario_value(
    *,
    start_value: float,
    direction: int,
    response_delta: float,
    fault_type: str,
    idx: int,
    command_index: int,
    response_window: int,
) -> float:
    if idx <= command_index:
        return start_value
    elapsed = idx - command_index
    if fault_type in {"no_response", "stuck_after_command"}:
        return start_value
    if fault_type == "weak_response":
        final_delta = response_delta * 0.35
        return start_value + direction * min(final_delta, final_delta * elapsed / max(response_window, 1))
    if fault_type == "wrong_direction":
        return start_value - direction * min(response_delta, response_delta * elapsed / max(response_window, 1))
    if fault_type == "delayed_response":
        if elapsed <= response_window + 2:
            return start_value
        delayed_elapsed = elapsed - response_window - 2
        return start_value + direction * min(response_delta, response_delta * delayed_elapsed / max(response_window, 1))
    return start_value + direction * min(response_delta, response_delta * elapsed / max(response_window, 1))


def _response_metrics(decisions: pd.DataFrame, *, fault_type: str) -> dict[str, float]:
    reasons = decisions.get("reason_codes", pd.Series("", index=decisions.index)).astype(str)
    response_failures = reasons.str.contains("actuator_response_residual", regex=False)
    response_alert = bool(response_failures.any())
    is_fault = fault_type != "healthy"
    authorizations = decisions["actuation_authorized"].astype(bool)
    reliabilities = pd.to_numeric(decisions.get("response_reliability", pd.Series(1.0)), errors="coerce").fillna(1.0)
    first_failure = int(np.flatnonzero(response_failures)[0]) if response_failures.any() else -1
    repeated_after_fault = 0
    if first_failure >= 0:
        repeated_after_fault = int(authorizations.iloc[first_failure + 1 :].sum())
    return {
        "is_fault": float(is_fault),
        "response_fault_alert": float(response_alert),
        "response_fault_detected": float(response_alert) if is_fault else float("nan"),
        "response_correct": float(response_alert) if is_fault else float(not response_alert),
        "response_fault_delay": float(first_failure) if first_failure >= 0 else float("nan"),
        "authorizations": float(authorizations.sum()),
        "repeated_authorizations_after_fault": float(repeated_after_fault),
        "final_response_reliability": float(reliabilities.iloc[-1]),
    }


if __name__ == "__main__":
    main()
