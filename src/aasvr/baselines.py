from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
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
    cusum_drift: float = 0.5
    cusum_threshold: float = 5.0
    kalman_process_var: float = 0.01
    kalman_measurement_var: float = 1.0


@dataclass
class _BaselineRuntime:
    trusted: float | None = None
    covariance: float = 1.0
    cusum_pos: float = 0.0
    cusum_neg: float = 0.0
    violations: int = 0
    history: deque[float] = field(default_factory=deque)


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
        self._runtime = {
            s.name: _BaselineRuntime(history=deque(maxlen=max(config.window, 5))) for s in sensors
        }

    def update(self, sample: dict[str, Any]) -> list[AASVRDecision]:
        return [self._update_sensor(sensor, sample) for sensor in self.sensors]

    def _update_sensor(self, sensor: SensorConfig, sample: dict[str, Any]) -> AASVRDecision:
        y = _to_float(sample.get(sensor.name))
        runtime = self._runtime[sensor.name]
        hist = runtime.history
        if np.isfinite(y):
            hist.append(y)
        trusted, method_anomaly = self._filter_value(sensor, y, runtime)
        runtime.trusted = trusted
        anomaly = (
            method_anomaly
            or not np.isfinite(y)
            or not (sensor.physical_min <= y <= sensor.physical_max)
        )
        authorized = self._authorize(sensor, trusted, runtime)
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

    def _filter_value(
        self,
        sensor: SensorConfig,
        y: float,
        runtime: _BaselineRuntime,
    ) -> tuple[float, bool]:
        hist = runtime.history
        if not np.isfinite(y):
            return runtime.trusted if runtime.trusted is not None else float("nan"), True
        values = np.asarray(hist, dtype=float)
        if self.config.method in {"raw_threshold", "original"}:
            return y, not (sensor.physical_min <= y <= sensor.physical_max)
        if self.config.method == "moving_average":
            trusted = float(np.mean(values))
            return trusted, _robust_anomaly(y, values, self.config.threshold_multiplier)
        if self.config.method == "moving_median":
            trusted = float(np.median(values))
            return trusted, _robust_anomaly(y, values, self.config.threshold_multiplier)
        if self.config.method == "hampel":
            median = float(np.median(values))
            mad = float(np.median(np.abs(values - median)))
            sigma = 1.4826 * mad
            anomaly = sigma > 0 and abs(y - median) > self.config.threshold_multiplier * sigma
            return median if anomaly else y, bool(anomaly)
        if self.config.method == "ewma":
            previous = runtime.trusted
            trusted = y if previous is None or not np.isfinite(previous) else self.config.alpha * y + (1 - self.config.alpha) * previous
            residual_values = np.asarray([*values[:-1], trusted], dtype=float)
            return trusted, _robust_anomaly(y, residual_values, self.config.threshold_multiplier)
        if self.config.method == "kalman":
            return self._kalman(y, runtime)
        if self.config.method == "cusum":
            return self._cusum(y, runtime)
        if self.config.method == "pca":
            # Streaming univariate proxy for PCA/SPE in the toy and per-sensor interface.
            return y, _robust_anomaly(y, values, self.config.threshold_multiplier)
        raise ValueError(f"Unknown baseline method: {self.config.method}")

    def _kalman(self, y: float, runtime: _BaselineRuntime) -> tuple[float, bool]:
        previous = y if runtime.trusted is None or not np.isfinite(runtime.trusted) else runtime.trusted
        predicted_cov = runtime.covariance + self.config.kalman_process_var
        gain = predicted_cov / (predicted_cov + self.config.kalman_measurement_var)
        trusted = previous + gain * (y - previous)
        runtime.covariance = (1.0 - gain) * predicted_cov
        innovation_sigma = np.sqrt(predicted_cov + self.config.kalman_measurement_var)
        anomaly = abs(y - previous) > self.config.threshold_multiplier * innovation_sigma
        return float(trusted), bool(anomaly)

    def _cusum(self, y: float, runtime: _BaselineRuntime) -> tuple[float, bool]:
        values = np.asarray(runtime.history, dtype=float)
        center = float(np.median(values)) if len(values) else y
        scale = _mad_sigma(values)
        z = 0.0 if scale <= 0 else (y - center) / scale
        runtime.cusum_pos = max(0.0, runtime.cusum_pos + z - self.config.cusum_drift)
        runtime.cusum_neg = min(0.0, runtime.cusum_neg + z + self.config.cusum_drift)
        anomaly = runtime.cusum_pos > self.config.cusum_threshold or abs(runtime.cusum_neg) > self.config.cusum_threshold
        if anomaly:
            runtime.cusum_pos = 0.0
            runtime.cusum_neg = 0.0
        return y, bool(anomaly)

    def _authorize(self, sensor: SensorConfig, trusted: float, runtime: _BaselineRuntime) -> bool:
        if not np.isfinite(trusted):
            runtime.violations = 0
            return False
        violation = trusted < sensor.control_low or trusted > sensor.control_high
        runtime.violations = runtime.violations + 1 if violation else 0
        if runtime.violations >= sensor.confirm_samples:
            runtime.violations = 0
            return True
        return False


def decisions_to_frame(decisions: list[AASVRDecision]) -> pd.DataFrame:
    return pd.DataFrame([decision.__dict__ for decision in decisions])


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _mad_sigma(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if len(finite) < 3:
        return 0.0
    median = float(np.median(finite))
    return float(1.4826 * np.median(np.abs(finite - median)))


def _robust_anomaly(y: float, values: np.ndarray, multiplier: float) -> bool:
    sigma = _mad_sigma(values)
    if sigma <= 0:
        return False
    median = float(np.median(values[np.isfinite(values)]))
    return bool(abs(y - median) > multiplier * sigma)
