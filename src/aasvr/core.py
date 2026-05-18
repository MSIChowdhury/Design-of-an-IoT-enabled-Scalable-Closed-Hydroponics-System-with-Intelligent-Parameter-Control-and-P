from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from aasvr.robust_scale import tolerance
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
    reason_codes: tuple[str, ...] = ()


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
            decisions.append(self._update_sensor(runtime, sample.get(name), timestamp))
        return decisions

    def _update_sensor(
        self, runtime: _SensorRuntime, raw: Any, timestamp: Any
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

        trust_score = self._trust_score(runtime, plausible, reasons)
        authorized = self._authorize(runtime, trust_score)
        alert = runtime.state == SensorState.FAULT_ALERT
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
            reason_codes=tuple(reasons),
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

    def _trust_score(self, runtime: _SensorRuntime, plausible: bool, reasons: list[str]) -> float:
        if plausible:
            return 1.0
        penalties = {
            "missing": 0.4,
            "physical_range": 0.5,
            "rate_limit": 0.25,
            "trusted_delta": 0.25,
        }
        score = 1.0 - sum(penalties.get(reason, 0.2) for reason in reasons)
        if runtime.failed_count:
            score -= min(0.4, 0.1 * runtime.failed_count)
        return float(np.clip(score, 0.0, 1.0))

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


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")

