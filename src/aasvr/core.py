from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from aasvr.robust_scale import robust_delta_scale, tolerance
from aasvr.states import SensorState


@dataclass(frozen=True)
class SensorConfig:
    name: str
    physical_min: float
    physical_max: float
    control_low: float
    control_high: float
    rate_limit: float
    uncertainty: float = 0.0
    xi_min: float = 1e-6
    window: int = 9
    confirm_samples: int = 3
    cooldown_samples: int = 3
    trend_window: int = 9
    trend_threshold_multiplier: float = 1.0
    trend_min_monotonic_fraction: float = 0.75
    actuators: tuple[str, ...] = ()
    expected_direction: str = "unknown"


@dataclass(frozen=True)
class AASVRConfig:
    sensors: tuple[SensorConfig, ...]
    q_min: float = 0.7
    scale_multiplier: float = 3.0
    transient_limit: int = 2
    persistent_limit: int = 5
    rectification_mode: str = "hold"


@dataclass(frozen=True)
class AASVRDecision:
    timestamp: Any
    sensor: str
    raw_value: float
    trusted_value: float
    state: SensorState
    trust_score: float
    gate_result: str
    rectification_action: str
    actuation_authorized: bool
    alert: bool
    actuator_consistency: float = 1.0
    unsafe_band: bool = False
    reason_codes: tuple[str, ...] = ()
    trust_components: tuple[str, ...] = ()


@dataclass
class _SensorRuntime:
    config: SensorConfig
    history: deque[float] = field(default_factory=deque)
    trusted_value: float | None = None
    last_raw_value: float | None = None
    state: SensorState = SensorState.NORMAL
    failed_count: int = 0
    accepted_count: int = 0
    band_violation_count: int = 0
    cooldown_remaining: int = 0
    last_authorized_value: float | None = None


class AASVR:
    """Streaming AASVR validator.

    The class intentionally keeps actuator logic lightweight. Real deployments
    can wrap this decision layer around an existing controller.
    """

    def __init__(self, config: AASVRConfig, *, dt_seconds: float = 15.0) -> None:
        self.config = config
        self.dt_seconds = dt_seconds
        self._sensors = {
            sensor.name: _SensorRuntime(
                config=sensor,
                history=deque(maxlen=max(sensor.window, 3)),
            )
            for sensor in config.sensors
        }

    def update(self, sample: dict[str, Any]) -> list[AASVRDecision]:
        timestamp = sample.get("timestamp")
        decisions = []
        for name, runtime in self._sensors.items():
            decisions.append(self._update_sensor(runtime, sample, sample.get(name), timestamp))
        return decisions

    def _update_sensor(
        self, runtime: _SensorRuntime, sample: dict[str, Any], raw: Any, timestamp: Any
    ) -> AASVRDecision:
        cfg = runtime.config
        y = _to_float(raw)
        reasons: list[str] = []

        if not np.isfinite(y):
            reasons.append("missing")
            plausible = False
        else:
            plausible = True

        if plausible and not (cfg.physical_min <= y <= cfg.physical_max):
            reasons.append("physical_range")
            plausible = False

        trusted_reference = runtime.trusted_value if runtime.trusted_value is not None else y
        xi = tolerance(
            list(runtime.history) + ([y] if np.isfinite(y) else []),
            xi_min=cfg.xi_min,
            scale_multiplier=self.config.scale_multiplier,
            rate_limit=cfg.rate_limit,
            dt_seconds=self.dt_seconds,
            uncertainty=cfg.uncertainty,
        )

        if plausible and runtime.trusted_value is not None:
            if abs(y - trusted_reference) > xi:
                reasons.append("trusted_delta")
                plausible = False

        if plausible and runtime.last_raw_value is not None and np.isfinite(runtime.last_raw_value):
            rate = abs(y - runtime.last_raw_value) / max(self.dt_seconds, 1e-9)
            if rate > cfg.rate_limit:
                reasons.append("rate_limit")
                plausible = False

        if plausible and self._uncommanded_trend(runtime, sample, y, xi):
            reasons.append("uncommanded_trend")
            plausible = False

        actuator_consistency = self._actuator_consistency(runtime, sample, y)

        if plausible:
            runtime.failed_count = 0
            runtime.accepted_count += 1
            runtime.trusted_value = y
            runtime.state = (
                SensorState.ACCEPTED_REGIME_SHIFT
                if runtime.state == SensorState.PERSISTENT_DEVIATION
                and runtime.accepted_count >= cfg.confirm_samples
                else SensorState.NORMAL
            )
            rectification_action = "accept"
            gate_result = "accept"
        else:
            runtime.failed_count += 1
            runtime.accepted_count = 0
            runtime.state = self._next_failed_state(runtime)
            runtime.trusted_value = self._rectify(runtime, y)
            rectification_action = (
                "alert"
                if runtime.state == SensorState.FAULT_ALERT
                else "bounded_prediction"
                if self.config.rectification_mode == "bounded_prediction"
                else "hold"
            )
            gate_result = "reject"

        if np.isfinite(y):
            runtime.history.append(y)
            runtime.last_raw_value = y

        trust_score, components = self._trust_score(
            runtime,
            plausible,
            reasons,
            actuator_consistency,
        )
        authorized = self._authorize(runtime, trust_score)
        if authorized:
            runtime.last_authorized_value = runtime.trusted_value
        alert = runtime.state == SensorState.FAULT_ALERT
        unsafe_band = self._unsafe_band(runtime)
        return AASVRDecision(
            timestamp=timestamp,
            sensor=cfg.name,
            raw_value=y,
            trusted_value=float(runtime.trusted_value)
            if runtime.trusted_value is not None
            else float("nan"),
            state=runtime.state,
            trust_score=trust_score,
            gate_result=gate_result,
            rectification_action=rectification_action,
            actuation_authorized=authorized,
            alert=alert,
            actuator_consistency=actuator_consistency,
            unsafe_band=unsafe_band,
            reason_codes=tuple(reasons),
            trust_components=components,
        )

    def _next_failed_state(self, runtime: _SensorRuntime) -> SensorState:
        if runtime.failed_count >= self.config.persistent_limit:
            return SensorState.FAULT_ALERT
        if runtime.failed_count > self.config.transient_limit:
            return SensorState.PERSISTENT_DEVIATION
        return SensorState.SUSPECT_TRANSIENT

    def _rectify(self, runtime: _SensorRuntime, y: float) -> float:
        if runtime.trusted_value is None:
            return y if np.isfinite(y) else float("nan")
        if self.config.rectification_mode != "bounded_prediction" or not np.isfinite(y):
            return runtime.trusted_value
        max_step = runtime.config.rate_limit * self.dt_seconds
        step = float(np.clip(y - runtime.trusted_value, -max_step, max_step))
        return runtime.trusted_value + step

    def _trust_score(
        self,
        runtime: _SensorRuntime,
        plausible: bool,
        reasons: list[str],
        actuator_consistency: float,
    ) -> tuple[float, tuple[str, ...]]:
        range_score = 0.0 if "physical_range" in reasons else 1.0
        rate_score = 0.0 if "rate_limit" in reasons else 1.0
        delta_score = 0.0 if "trusted_delta" in reasons else 1.0
        trend_score = 0.0 if "uncommanded_trend" in reasons else 1.0
        missing_score = 0.0 if "missing" in reasons else 1.0
        persistence_score = float(np.clip(1.0 - 0.2 * runtime.failed_count, 0.0, 1.0))
        plausibility_score = 1.0 if plausible else 0.35 * min(
            range_score,
            rate_score,
            delta_score,
            trend_score,
            missing_score,
        )
        weighted = (
            0.25 * range_score
            + 0.20 * rate_score
            + 0.20 * persistence_score
            + 0.20 * actuator_consistency
            + 0.15 * missing_score
        )
        if actuator_consistency < 0.5:
            weighted = min(weighted, 0.65)
        score = min(weighted, plausibility_score if not plausible else weighted)
        components = (
            f"range={range_score:.3f}",
            f"rate={rate_score:.3f}",
            f"trend={trend_score:.3f}",
            f"persistence={persistence_score:.3f}",
            f"actuator_consistency={actuator_consistency:.3f}",
            f"missingness={missing_score:.3f}",
        )
        return float(np.clip(score, 0.0, 1.0)), components

    def _uncommanded_trend(
        self,
        runtime: _SensorRuntime,
        sample: dict[str, Any],
        y: float,
        xi: float,
    ) -> bool:
        cfg = runtime.config
        if cfg.trend_window <= 1 or self._has_active_actuator(cfg, sample):
            return False
        values = [value for value in list(runtime.history)[-(cfg.trend_window - 1) :] if np.isfinite(value)]
        values.append(y)
        if len(values) < cfg.trend_window:
            return False
        arr = np.asarray(values, dtype=float)
        net_delta = arr[-1] - arr[0]
        local_scale = robust_delta_scale(arr)
        threshold = max(cfg.xi_min, cfg.uncertainty, cfg.trend_threshold_multiplier * local_scale)
        if abs(net_delta) <= threshold:
            return False
        diffs = np.diff(arr)
        if not np.any(np.abs(diffs) > max(cfg.uncertainty, cfg.xi_min) * 0.1):
            return False
        direction = np.sign(net_delta)
        same_direction = np.sum(np.sign(diffs) == direction)
        monotonic_fraction = same_direction / max(len(diffs), 1)
        return bool(monotonic_fraction >= cfg.trend_min_monotonic_fraction)

    def _actuator_consistency(
        self,
        runtime: _SensorRuntime,
        sample: dict[str, Any],
        y: float,
    ) -> float:
        cfg = runtime.config
        if not cfg.actuators or runtime.last_raw_value is None or not np.isfinite(y):
            return 1.0
        if not self._has_active_actuator(cfg, sample):
            return 1.0
        delta = y - runtime.last_raw_value
        if cfg.expected_direction == "decreasing":
            return 1.0 if delta <= max(cfg.uncertainty, cfg.xi_min) else 0.0
        if cfg.expected_direction == "increasing":
            return 1.0 if delta >= -max(cfg.uncertainty, cfg.xi_min) else 0.0
        return 1.0 if abs(delta) <= max(cfg.rate_limit * self.dt_seconds, cfg.xi_min) else 0.5

    def _has_active_actuator(self, cfg: SensorConfig, sample: dict[str, Any]) -> bool:
        return bool(cfg.actuators and any(_truthy(sample.get(actuator)) for actuator in cfg.actuators))

    def _authorize(self, runtime: _SensorRuntime, trust_score: float) -> bool:
        cfg = runtime.config
        trusted = runtime.trusted_value
        if runtime.cooldown_remaining > 0:
            runtime.cooldown_remaining -= 1
            return False
        if trusted is None or not np.isfinite(trusted):
            runtime.band_violation_count = 0
            return False
        violation = trusted < cfg.control_low or trusted > cfg.control_high
        state_ok = runtime.state in {SensorState.NORMAL, SensorState.ACCEPTED_REGIME_SHIFT}
        if violation and state_ok and trust_score >= self.config.q_min:
            runtime.band_violation_count += 1
        else:
            runtime.band_violation_count = 0
        if runtime.band_violation_count >= cfg.confirm_samples:
            runtime.cooldown_remaining = cfg.cooldown_samples
            runtime.band_violation_count = 0
            return True
        return False

    def _unsafe_band(self, runtime: _SensorRuntime) -> bool:
        trusted = runtime.trusted_value
        if trusted is None or not np.isfinite(trusted):
            return False
        cfg = runtime.config
        return bool(trusted < cfg.control_low or trusted > cfg.control_high)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "on", "open", "active", "yes"}
    return bool(value)
