import math

from aasvr.core import AASVR, AASVRConfig, SensorConfig
from aasvr.robust_scale import robust_delta_scale
from aasvr.states import SensorState


def sensor() -> SensorConfig:
    return SensorConfig(
        name="pH",
        physical_min=0,
        physical_max=14,
        control_low=5.8,
        control_high=6.5,
        rate_limit=0.02,
        uncertainty=0.01,
        xi_min=0.05,
        confirm_samples=2,
        cooldown_samples=2,
    )


def test_robust_delta_scale_ignores_single_outlier() -> None:
    scale = robust_delta_scale([1, 1.01, 1.02, 9, 1.03, 1.04])
    assert math.isfinite(scale)
    assert scale < 0.05


def test_aasvr_rejects_single_physical_range_fault_without_actuation() -> None:
    model = AASVR(AASVRConfig(sensors=(sensor(),), q_min=0.7))
    model.update({"timestamp": 1, "pH": 6.1})
    decision = model.update({"timestamp": 2, "pH": 99})[0]
    assert decision.gate_result == "reject"
    assert decision.state == SensorState.SUSPECT_TRANSIENT
    assert not decision.actuation_authorized
    assert decision.trusted_value == 6.1
    assert any(component.startswith("range=") for component in decision.trust_components)


def test_aasvr_authorizes_persistent_trusted_control_violation() -> None:
    model = AASVR(AASVRConfig(sensors=(sensor(),), q_min=0.7))
    decisions = []
    for i in range(4):
        decisions.append(model.update({"timestamp": i, "pH": 6.55})[0])
    assert any(decision.actuation_authorized for decision in decisions)


def test_aasvr_escalates_persistent_fault() -> None:
    model = AASVR(AASVRConfig(sensors=(sensor(),), persistent_limit=3))
    model.update({"timestamp": 0, "pH": 6.1})
    decisions = [model.update({"timestamp": i, "pH": 99})[0] for i in range(1, 5)]
    assert decisions[-1].state == SensorState.FAULT_ALERT
    assert decisions[-1].alert


def test_aasvr_penalizes_actuator_inconsistent_response() -> None:
    cfg = sensor()
    cfg = SensorConfig(
        **{
            **cfg.__dict__,
            "actuators": ("acid_doser",),
            "expected_direction": "decreasing",
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7))
    model.update({"timestamp": 0, "pH": 6.1})
    decision = model.update({"timestamp": 1, "pH": 6.2, "acid_doser": 1})[0]
    assert decision.actuator_consistency == 0.0
    assert decision.trust_score < 0.7


def test_aasvr_rejects_slow_uncommanded_trend() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "trend_window": 4,
            "trend_threshold_multiplier": 1.0,
            "trend_min_monotonic_fraction": 0.75,
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7, scale_multiplier=1.0))
    decisions = [model.update({"timestamp": idx, "pH": value})[0] for idx, value in enumerate([6.0, 6.03, 6.06, 6.09])]
    assert decisions[-1].gate_result == "reject"
    assert "uncommanded_trend" in decisions[-1].reason_codes
