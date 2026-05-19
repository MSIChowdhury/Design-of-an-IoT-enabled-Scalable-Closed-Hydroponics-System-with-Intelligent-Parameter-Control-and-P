from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ACTUATOR_LOG_COLUMNS = (
    "timestamp",
    "actuator_id",
    "actuator_type",
    "commanded_state",
    "measured_state",
    "command_source",
    "target_sensor",
    "expected_direction",
    "dose_or_runtime",
    "lockout_active",
    "manual_override",
)

REFERENCE_MEASUREMENT_COLUMNS = (
    "timestamp",
    "sensor",
    "raw_value",
    "reference_value",
    "reference_device",
    "operator",
    "notes",
)

WATER_LEVEL_CALIBRATION_COLUMNS = (
    "timestamp",
    "raw_water_level",
    "reference_level_cm",
    "reference_method",
    "operator",
    "notes",
)


@dataclass(frozen=True)
class OptionalEvidenceStatus:
    name: str
    path: Path
    available: bool
    rows: int
    message: str


@dataclass(frozen=True)
class WaterLevelCalibration:
    slope: float
    intercept: float
    rmse_cm: float
    r2: float
    n: int


def template_frame(columns: tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def write_templates(out_dir: str | Path = "configs/templates") -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = [
        out / "actuator_state_log_template.csv",
        out / "reference_measurements_template.csv",
        out / "water_level_calibration_template.csv",
    ]
    template_frame(ACTUATOR_LOG_COLUMNS).to_csv(paths[0], index=False)
    template_frame(REFERENCE_MEASUREMENT_COLUMNS).to_csv(paths[1], index=False)
    template_frame(WATER_LEVEL_CALIBRATION_COLUMNS).to_csv(paths[2], index=False)
    return paths


def load_optional_actuator_log(path: str | Path) -> tuple[pd.DataFrame, OptionalEvidenceStatus]:
    path = Path(path)
    if not path.exists():
        return (
            template_frame(ACTUATOR_LOG_COLUMNS),
            OptionalEvidenceStatus(
                name="actuator_state_log",
                path=path,
                available=False,
                rows=0,
                message="Optional actuator-state log is absent; response scoring remains counterfactual.",
            ),
        )
    frame = pd.read_csv(path)
    _require_columns(frame, ACTUATOR_LOG_COLUMNS, "actuator-state log")
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    if frame["timestamp"].isna().any():
        raise ValueError("Actuator-state log contains unparsable timestamps.")
    frame["target_sensor"] = frame["target_sensor"].astype(str)
    frame["expected_direction"] = frame["expected_direction"].map(_direction_sign)
    return (
        frame.sort_values("timestamp").reset_index(drop=True),
        OptionalEvidenceStatus(
            name="actuator_state_log",
            path=path,
            available=True,
            rows=len(frame),
            message="Optional actuator-state log loaded.",
        ),
    )


def load_optional_reference_measurements(path: str | Path) -> tuple[pd.DataFrame, OptionalEvidenceStatus]:
    path = Path(path)
    if not path.exists():
        return (
            template_frame(REFERENCE_MEASUREMENT_COLUMNS),
            OptionalEvidenceStatus(
                name="reference_measurements",
                path=path,
                available=False,
                rows=0,
                message="Optional reference measurements are absent; sensor truth remains replay/injection based.",
            ),
        )
    frame = pd.read_csv(path)
    _require_columns(frame, REFERENCE_MEASUREMENT_COLUMNS, "reference measurement file")
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    for column in ("raw_value", "reference_value"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame["timestamp"].isna().any() or frame[["raw_value", "reference_value"]].isna().any().any():
        raise ValueError("Reference measurement file contains unparsable timestamps or values.")
    return (
        frame.sort_values(["sensor", "timestamp"]).reset_index(drop=True),
        OptionalEvidenceStatus(
            name="reference_measurements",
            path=path,
            available=True,
            rows=len(frame),
            message="Optional reference measurements loaded.",
        ),
    )


def score_actuator_response_log(
    measurements: pd.DataFrame,
    actuator_log: pd.DataFrame,
    *,
    timestamp_column: str = "timestamp",
    response_window_samples: int = 4,
    min_delta: float = 0.0,
) -> pd.DataFrame:
    if actuator_log.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "actuator_id",
                "target_sensor",
                "expected_direction",
                "baseline_value",
                "response_value",
                "directional_delta",
                "response_confirmed",
            ]
        )
    measurements = measurements.copy()
    measurements[timestamp_column] = pd.to_datetime(measurements[timestamp_column], errors="coerce", utc=True)
    measurements = measurements.sort_values(timestamp_column).reset_index(drop=True)
    rows: list[dict[str, object]] = []
    for _, event in actuator_log.iterrows():
        sensor = str(event["target_sensor"])
        if sensor not in measurements:
            continue
        direction = _direction_sign(event["expected_direction"])
        before = measurements[measurements[timestamp_column].le(event["timestamp"])]
        after = measurements[measurements[timestamp_column].gt(event["timestamp"])].head(response_window_samples)
        if before.empty or after.empty:
            continue
        baseline = pd.to_numeric(before[sensor], errors="coerce").dropna()
        response = pd.to_numeric(after[sensor], errors="coerce").dropna()
        if baseline.empty or response.empty:
            continue
        baseline_value = float(baseline.iloc[-1])
        response_value = float(response.iloc[-1])
        directional_delta = direction * (response_value - baseline_value)
        rows.append(
            {
                "timestamp": event["timestamp"],
                "actuator_id": event["actuator_id"],
                "target_sensor": sensor,
                "expected_direction": direction,
                "baseline_value": baseline_value,
                "response_value": response_value,
                "directional_delta": directional_delta,
                "response_confirmed": bool(directional_delta >= min_delta),
            }
        )
    return pd.DataFrame(rows)


def fit_water_level_calibration(calibration_frame: pd.DataFrame) -> WaterLevelCalibration:
    _require_columns(calibration_frame, WATER_LEVEL_CALIBRATION_COLUMNS, "water-level calibration file")
    raw = pd.to_numeric(calibration_frame["raw_water_level"], errors="coerce")
    reference = pd.to_numeric(calibration_frame["reference_level_cm"], errors="coerce")
    valid = pd.DataFrame({"raw": raw, "reference": reference}).dropna()
    if len(valid) < 3:
        raise ValueError("Water-level calibration requires at least three paired raw/reference measurements.")
    slope, intercept = np.polyfit(valid["raw"], valid["reference"], deg=1)
    predicted = slope * valid["raw"] + intercept
    residual = valid["reference"] - predicted
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    denom = float(np.sum(np.square(valid["reference"] - valid["reference"].mean())))
    r2 = 1.0 if denom == 0.0 else float(1.0 - np.sum(np.square(residual)) / denom)
    return WaterLevelCalibration(
        slope=float(slope),
        intercept=float(intercept),
        rmse_cm=rmse,
        r2=r2,
        n=int(len(valid)),
    )


def apply_water_level_calibration(raw_values: pd.Series, calibration: WaterLevelCalibration) -> pd.Series:
    values = pd.to_numeric(raw_values, errors="coerce")
    return calibration.slope * values + calibration.intercept


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _direction_sign(value: object) -> int:
    if isinstance(value, (int, float)) and np.isfinite(value):
        if value > 0:
            return 1
        if value < 0:
            return -1
    text = str(value).strip().lower()
    if text in {"1", "+1", "increase", "increasing", "up", "positive"}:
        return 1
    if text in {"-1", "decrease", "decreasing", "down", "negative"}:
        return -1
    return 0
