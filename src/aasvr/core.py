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
    stuck_window: int = 0
    stuck_sigma_min: float = 1e-9
    stuck_min_unique: int = 1
    stuck_latch_samples: int = 0
    response_window: int = 0
    response_min_delta: float = 0.0
    calibrated_xi: float | None = None
    scale_multiplier: float | None = None
    cusum_drift_multiplier: float = 0.0
    cusum_threshold_multiplier: float = 0.0
    risk_level: str = "medium"
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
    eta_decay: float = 0.90
    eta_min_low: float = 0.50
    eta_min_medium: float = 0.65
    eta_min_high: float = 0.75
    enable_response_residual: bool = True
    response_mode: str = "window"
    reliability_mode: str = "ema"
    beta_prior_success: float = 2.0
    beta_prior_failure: float = 1.0
    beta_lcb_z: float = 1.64
    compact_diagnostics: bool = False


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
    response_reliability: float = 1.0
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
    response_countdown: int = 0
    response_reference: float | None = None
    response_direction: int = 0
    response_evidence: float = 0.0
    response_reliability: float = 1.0
    response_fault_count: int = 0
    beta_success: float = 2.0
    beta_failure: float = 1.0
    response_observations: int = 0
    cusum_positive: float = 0.0
    cusum_negative: float = 0.0
    stuck_active_value: float | None = None
    stuck_latch_remaining: int = 0
    stuck_exhausted_value: float | None = None


class AASVR:
    """Streaming AASVR validator.

    The class intentionally keeps actuator logic lightweight. Real deployments
    can wrap this decision layer around an existing controller.
    """

    def __init__(self, config: AASVRConfig, *, dt_seconds: float = 15.0) -> None:
        self.config = config
        self.dt_seconds = dt_seconds
        self._sensors = {}
        for sensor in config.sensors:
            runtime = _SensorRuntime(
                config=sensor,
                history=deque(maxlen=max(sensor.window, sensor.trend_window, sensor.stuck_window, 3)),
            )
            runtime.beta_success = config.beta_prior_success
            runtime.beta_failure = config.beta_prior_failure
            runtime.response_reliability = self._beta_mean(runtime) if config.reliability_mode == "beta" else 1.0
            self._sensors[sensor.name] = runtime

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
        scale_multiplier = (
            cfg.scale_multiplier
            if cfg.scale_multiplier is not None and np.isfinite(cfg.scale_multiplier)
            else self.config.scale_multiplier
        )
        xi = tolerance(
            list(runtime.history) + ([y] if np.isfinite(y) else []),
            xi_min=cfg.xi_min,
            scale_multiplier=scale_multiplier,
            rate_limit=cfg.rate_limit,
            dt_seconds=self.dt_seconds,
            uncertainty=cfg.uncertainty,
        )
        if cfg.calibrated_xi is not None and np.isfinite(cfg.calibrated_xi):
            xi = max(cfg.xi_min, cfg.calibrated_xi, cfg.rate_limit * self.dt_seconds, cfg.uncertainty)

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

        if plausible and self._stuck_at(runtime, y):
            reasons.append("stuck_at")
            plausible = False

        if plausible and self._cusum_residual_shift(runtime, y, xi):
            reasons.append("cusum_residual")
            plausible = False

        actuator_consistency = self._actuator_consistency(runtime, sample, y)
        response_residual = self._actuator_response_residual(runtime, sample, y)
        if plausible and response_residual:
            reasons.append("actuator_response_residual")
            plausible = False

        if plausible:
            runtime.cusum_positive *= 0.95
            runtime.cusum_negative *= 0.95
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
            runtime.cusum_positive = 0.0
            runtime.cusum_negative = 0.0
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
            response_reliability=runtime.response_reliability,
            unsafe_band=unsafe_band,
            reason_codes=tuple(reasons),
            trust_components=components if not self.config.compact_diagnostics else (),
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
        stuck_score = 0.0 if "stuck_at" in reasons else 1.0
        response_score = 0.0 if "actuator_response_residual" in reasons else 1.0
        cusum_score = 0.0 if "cusum_residual" in reasons else 1.0
        missing_score = 0.0 if "missing" in reasons else 1.0
        persistence_score = float(np.clip(1.0 - 0.2 * runtime.failed_count, 0.0, 1.0))
        plausibility_score = 1.0 if plausible else 0.35 * min(
            range_score,
            rate_score,
            delta_score,
            trend_score,
            stuck_score,
            response_score,
            cusum_score,
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
        if runtime.response_observations > 0 and runtime.response_reliability < self._eta_min(runtime.config):
            weighted = min(weighted, runtime.response_reliability)
        score = min(weighted, plausibility_score if not plausible else weighted)
        components = ()
        if not self.config.compact_diagnostics:
            components = (
                f"range={range_score:.3f}",
                f"rate={rate_score:.3f}",
                f"trend={trend_score:.3f}",
                f"stuck={stuck_score:.3f}",
                f"cusum={cusum_score:.3f}",
                f"response={response_score:.3f}",
                f"persistence={persistence_score:.3f}",
                f"actuator_consistency={actuator_consistency:.3f}",
                f"response_reliability={runtime.response_reliability:.3f}",
                f"missingness={missing_score:.3f}",
            )
        return float(np.clip(score, 0.0, 1.0)), components

    def _stuck_at(self, runtime: _SensorRuntime, y: float) -> bool:
        cfg = runtime.config
        if cfg.stuck_window <= 1 or not np.isfinite(y):
            runtime.stuck_active_value = None
            runtime.stuck_latch_remaining = 0
            runtime.stuck_exhausted_value = None
            return False
        if runtime.stuck_exhausted_value is not None:
            same_exhausted_value = abs(y - runtime.stuck_exhausted_value) <= max(cfg.uncertainty, cfg.xi_min) * 1e-6
            if same_exhausted_value:
                return False
            runtime.stuck_exhausted_value = None
        if runtime.stuck_active_value is not None:
            same_latched_value = abs(y - runtime.stuck_active_value) <= max(cfg.uncertainty, cfg.xi_min) * 1e-6
            if same_latched_value and runtime.stuck_latch_remaining > 0:
                runtime.stuck_latch_remaining -= 1
                return True
            if same_latched_value:
                runtime.stuck_exhausted_value = runtime.stuck_active_value
            runtime.stuck_active_value = None
            runtime.stuck_latch_remaining = 0
        values = [value for value in list(runtime.history)[-(cfg.stuck_window - 1) :] if np.isfinite(value)]
        values.append(y)
        if len(values) < cfg.stuck_window:
            return False
        arr = np.asarray(values, dtype=float)
        rounded = np.round(arr, decimals=9)
        unique_count = len(np.unique(rounded))
        if unique_count > cfg.stuck_min_unique:
            return False
        if float(np.std(arr)) > cfg.stuck_sigma_min:
            return False
        history = [value for value in runtime.history if np.isfinite(value)]
        if len(history) < cfg.stuck_window:
            runtime.stuck_active_value = float(arr[-1])
            runtime.stuck_latch_remaining = max(0, cfg.stuck_latch_samples)
            return True
        previous = history[-cfg.stuck_window]
        change_threshold = max(cfg.uncertainty, cfg.xi_min) * 0.1
        detected = bool(abs(previous - arr[0]) > change_threshold)
        if detected:
            runtime.stuck_active_value = float(arr[-1])
            runtime.stuck_latch_remaining = max(0, cfg.stuck_latch_samples)
        return detected

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

    def _cusum_residual_shift(self, runtime: _SensorRuntime, y: float, xi: float) -> bool:
        cfg = runtime.config
        if (
            cfg.cusum_drift_multiplier <= 0
            or cfg.cusum_threshold_multiplier <= 0
            or runtime.trusted_value is None
            or not np.isfinite(y)
        ):
            return False
        reference = float(runtime.trusted_value)
        residual = y - reference
        allowance = max(cfg.uncertainty, cfg.xi_min, cfg.cusum_drift_multiplier * xi)
        threshold = max(allowance, cfg.cusum_threshold_multiplier * xi)
        runtime.cusum_positive = max(0.0, runtime.cusum_positive + residual - allowance)
        runtime.cusum_negative = max(0.0, runtime.cusum_negative - residual - allowance)
        return bool(runtime.cusum_positive > threshold or runtime.cusum_negative > threshold)

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

    def _actuator_response_residual(
        self,
        runtime: _SensorRuntime,
        sample: dict[str, Any],
        y: float,
    ) -> bool:
        cfg = runtime.config
        if (
            not self.config.enable_response_residual
            or cfg.response_window <= 0
            or not np.isfinite(y)
        ):
            return False
        active = self._has_active_actuator(cfg, sample)
        if active and runtime.response_countdown <= 0:
            runtime.response_countdown = cfg.response_window
            runtime.response_reference = runtime.last_raw_value if runtime.last_raw_value is not None else y
            runtime.response_direction = self._expected_response_direction(cfg, runtime.trusted_value)
            runtime.response_evidence = 0.0
            return False
        if runtime.response_countdown <= 0 or runtime.response_reference is None:
            return False

        delta = y - runtime.response_reference
        threshold = max(cfg.response_min_delta, cfg.uncertainty, cfg.xi_min)
        if self.config.response_mode == "sequential":
            directional_delta = (
                runtime.response_direction * delta
                if runtime.response_direction
                else abs(delta)
            )
            runtime.response_evidence = max(runtime.response_evidence, float(directional_delta))
            satisfied = runtime.response_evidence >= threshold
        elif runtime.response_direction < 0:
            satisfied = delta <= -threshold
        elif runtime.response_direction > 0:
            satisfied = delta >= threshold
        else:
            satisfied = abs(delta) >= threshold
        if satisfied:
            runtime.response_countdown = 0
            runtime.response_reference = None
            runtime.response_direction = 0
            runtime.response_evidence = 0.0
            self._update_response_reliability(runtime, confirmed=True)
            return False

        runtime.response_countdown -= 1
        if runtime.response_countdown <= 0:
            runtime.response_reference = None
            runtime.response_direction = 0
            runtime.response_evidence = 0.0
            self._update_response_reliability(runtime, confirmed=False)
            return True
        return False

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
        eta_ok = self._eta_for_authorization(runtime) >= self._eta_min(cfg)
        if violation and state_ok and trust_score >= self.config.q_min and eta_ok:
            runtime.band_violation_count += 1
        else:
            runtime.band_violation_count = 0
        if runtime.band_violation_count >= cfg.confirm_samples:
            runtime.cooldown_remaining = cfg.cooldown_samples
            runtime.band_violation_count = 0
            self._start_authorized_response(runtime)
            return True
        return False

    def _unsafe_band(self, runtime: _SensorRuntime) -> bool:
        trusted = runtime.trusted_value
        if trusted is None or not np.isfinite(trusted):
            return False
        cfg = runtime.config
        return bool(trusted < cfg.control_low or trusted > cfg.control_high)

    def _start_authorized_response(self, runtime: _SensorRuntime) -> None:
        cfg = runtime.config
        if not self.config.enable_response_residual or cfg.response_window <= 0:
            return
        trusted = runtime.trusted_value
        if trusted is None or not np.isfinite(trusted):
            return
        runtime.response_countdown = cfg.response_window
        runtime.response_reference = trusted
        runtime.response_direction = self._expected_response_direction(cfg, trusted)
        runtime.response_evidence = 0.0

    def _expected_response_direction(self, cfg: SensorConfig, trusted: float | None) -> int:
        if cfg.expected_direction == "decreasing":
            return -1
        if cfg.expected_direction == "increasing":
            return 1
        if trusted is not None and np.isfinite(trusted):
            if trusted > cfg.control_high:
                return -1
            if trusted < cfg.control_low:
                return 1
        return 0

    def _update_response_reliability(self, runtime: _SensorRuntime, *, confirmed: bool) -> None:
        runtime.response_observations += 1
        if self.config.reliability_mode == "beta":
            if confirmed:
                runtime.beta_success += 1.0
                runtime.response_fault_count = 0
            else:
                runtime.beta_failure += 1.0
                runtime.response_fault_count += 1
            runtime.response_reliability = self._beta_mean(runtime)
            return
        observation = 1.0 if confirmed else 0.0
        runtime.response_reliability = float(
            np.clip(
                self.config.eta_decay * runtime.response_reliability
                + (1.0 - self.config.eta_decay) * observation,
                0.0,
                1.0,
            )
        )
        if confirmed:
            runtime.response_fault_count = 0
        else:
            runtime.response_fault_count += 1

    def _eta_min(self, cfg: SensorConfig) -> float:
        risk = cfg.risk_level.lower()
        if risk == "high":
            return self.config.eta_min_high
        if risk == "low":
            return self.config.eta_min_low
        return self.config.eta_min_medium

    def _eta_for_authorization(self, runtime: _SensorRuntime) -> float:
        if runtime.response_observations == 0:
            return 1.0
        if self.config.reliability_mode == "beta" and runtime.config.risk_level.lower() == "high":
            return self._beta_lcb(runtime)
        return runtime.response_reliability

    def _beta_mean(self, runtime: _SensorRuntime) -> float:
        total = runtime.beta_success + runtime.beta_failure
        return float(runtime.beta_success / total) if total > 0 else 1.0

    def _beta_lcb(self, runtime: _SensorRuntime) -> float:
        total = runtime.beta_success + runtime.beta_failure
        if total <= 0:
            return 0.0
        mean = self._beta_mean(runtime)
        variance = (mean * (1.0 - mean)) / (total + 1.0)
        return float(max(0.0, mean - self.config.beta_lcb_z * np.sqrt(max(variance, 0.0))))


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "on", "open", "active", "yes"}
    return bool(value)
