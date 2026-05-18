from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from aasvr.core import AASVRDecision, SensorConfig
from aasvr.states import SensorState


@dataclass(frozen=True)
class BaselineConfig:
    method: str
    window: int = 5
    threshold_multiplier: float = 3.0
    alpha: float = 0.2


class StreamingBaseline:
    def __init__(
        self,
        sensors: tuple[SensorConfig, ...],
        config: BaselineConfig,
        *,
        dt_seconds: float = 15.0,
    ) -> None:
        self.sensors = sensors
        self.config = config
        self.dt_seconds = dt_seconds
        self._history = {s.name: deque(maxlen=max(config.window, 3)) for s in sensors}
        self._trusted: dict[str, float | None] = {s.name: None for s in sensors}
        self._violations = {s.name: 0 for s in sensors}

    def update(self, sample: dict[str, Any]) -> list[AASVRDecision]:
        return [self._update_sensor(sensor, sample) for sensor in self.sensors]

    def _update_sensor(self, sensor: SensorConfig, sample: dict[str, Any]) -> AASVRDecision:
        y = _to_float(sample.get(sensor.name))
        hist = self._history[sensor.name]
        if np.isfinite(y):
            hist.append(y)
        trusted = self._filter_value(sensor.name, y, hist)
        self._trusted[sensor.name] = trusted
        anomaly = not np.isfinite(y) or not (sensor.physical_min <= y <= sensor.physical_max)
        authorized = self._authorize(sensor, trusted)
        return AASVRDecision(
            timestamp=sample.get("timestamp"),
            sensor=sensor.name,
            raw_value=y,
            trusted_value=trusted,
            state=SensorState.FAULT_ALERT if anomaly else SensorState.NORMAL,
            trust_score=0.0 if anomaly else 1.0,
            gate_result="reject" if anomaly else "accept",
            rectification_action=self.config.method,
            actuation_authorized=authorized,
            alert=anomaly,
            reason_codes=("baseline_anomaly",) if anomaly else (),
        )

    def _filter_value(self, name: str, y: float, hist: deque[float]) -> float:
        if not np.isfinite(y):
            return self._trusted[name] if self._trusted[name] is not None else float("nan")
        values = np.asarray(hist, dtype=float)
        if self.config.method in {"raw_threshold", "original"}:
            return y
        if self.config.method == "moving_average":
            return float(np.mean(values))
        if self.config.method == "moving_median":
            return float(np.median(values))
        if self.config.method == "hampel":
            median = float(np.median(values))
            mad = float(np.median(np.abs(values - median)))
            sigma = 1.4826 * mad
            return median if sigma > 0 and abs(y - median) > self.config.threshold_multiplier * sigma else y
        if self.config.method in {"ewma", "kalman"}:
            previous = self._trusted[name]
            return y if previous is None or not np.isfinite(previous) else self.config.alpha * y + (1 - self.config.alpha) * previous
        if self.config.method == "cusum":
            return y
        if self.config.method == "pca":
            return y
        raise ValueError(f"Unknown baseline method: {self.config.method}")

    def _authorize(self, sensor: SensorConfig, trusted: float) -> bool:
        if not np.isfinite(trusted):
            self._violations[sensor.name] = 0
            return False
        violation = trusted < sensor.control_low or trusted > sensor.control_high
        self._violations[sensor.name] = self._violations[sensor.name] + 1 if violation else 0
        if self._violations[sensor.name] >= sensor.confirm_samples:
            self._violations[sensor.name] = 0
            return True
        return False


def decisions_to_frame(decisions: list[AASVRDecision]) -> pd.DataFrame:
    return pd.DataFrame([decision.__dict__ for decision in decisions])


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")

