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


def test_aasvr_flags_missing_actuator_response_after_window() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "actuators": ("acid_doser",),
            "expected_direction": "decreasing",
            "response_window": 2,
            "response_min_delta": 0.03,
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7))
    model.update({"timestamp": 0, "pH": 6.2})
    model.update({"timestamp": 1, "pH": 6.2, "acid_doser": 1})
    model.update({"timestamp": 2, "pH": 6.2})
    decision = model.update({"timestamp": 3, "pH": 6.2})[0]
    assert "actuator_response_residual" in decision.reason_codes
    assert decision.gate_result == "reject"
    assert decision.response_reliability < 1.0


def test_aasvr_r_starts_response_window_after_authorization() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "actuators": ("acid_doser",),
            "expected_direction": "bidirectional",
            "response_window": 2,
            "response_min_delta": 0.03,
            "risk_level": "high",
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7, eta_decay=0.8))
    decisions = [model.update({"timestamp": idx, "pH": 6.7})[0] for idx in range(3)]
    assert any(decision.actuation_authorized for decision in decisions)
    response = model.update({"timestamp": 3, "pH": 6.63})[0]
    assert "actuator_response_residual" not in response.reason_codes
    assert response.response_reliability == 1.0


def test_aasvr_r_suppresses_high_risk_authorization_after_failed_response() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "actuators": ("acid_doser",),
            "expected_direction": "bidirectional",
            "response_window": 1,
            "response_min_delta": 0.03,
            "risk_level": "high",
        }
    )
    model = AASVR(
        AASVRConfig(
            sensors=(cfg,),
            q_min=0.7,
            eta_decay=0.0,
            eta_min_high=0.75,
        )
    )
    first = [model.update({"timestamp": idx, "pH": 6.7})[0] for idx in range(3)]
    assert any(decision.actuation_authorized for decision in first)
    failed = first[-1]
    assert "actuator_response_residual" in failed.reason_codes
    later = [model.update({"timestamp": idx, "pH": 6.7})[0] for idx in range(4, 10)]
    assert not any(decision.actuation_authorized for decision in later)


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


def test_aasvr_rejects_plausible_stuck_at_fault() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "stuck_window": 4,
            "stuck_sigma_min": 1e-9,
            "stuck_min_unique": 1,
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7))
    model.update({"timestamp": 0, "pH": 6.0})
    decisions = [model.update({"timestamp": idx, "pH": 6.1})[0] for idx in range(1, 6)]
    stuck_decisions = [decision for decision in decisions if "stuck_at" in decision.reason_codes]
    assert stuck_decisions
    assert stuck_decisions[0].gate_result == "reject"
    assert not stuck_decisions[0].actuation_authorized


def test_aasvr_does_not_flag_stable_noisy_signal_as_stuck() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "stuck_window": 4,
            "stuck_sigma_min": 1e-9,
            "stuck_min_unique": 1,
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7))
    decisions = [
        model.update({"timestamp": idx, "pH": value})[0]
        for idx, value in enumerate([6.10, 6.11, 6.10, 6.12, 6.11])
    ]
    assert "stuck_at" not in decisions[-1].reason_codes


def test_aasvr_uses_calibrated_xi_when_larger_than_rolling_scale() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "calibrated_xi": 0.5,
            "rate_limit": 0.05,
        }
    )
    model = AASVR(AASVRConfig(sensors=(cfg,), q_min=0.7, scale_multiplier=1.0))
    model.update({"timestamp": 0, "pH": 6.0})
    decision = model.update({"timestamp": 1, "pH": 6.3})[0]
    assert decision.gate_result == "accept"
    assert decision.trusted_value == 6.3


def test_aasvr_r2_sequential_response_accumulates_directional_evidence() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "actuators": ("acid_doser",),
            "expected_direction": "bidirectional",
            "response_window": 3,
            "response_min_delta": 0.06,
            "risk_level": "high",
        }
    )
    model = AASVR(
        AASVRConfig(
            sensors=(cfg,),
            q_min=0.7,
            response_mode="sequential",
            reliability_mode="beta",
            beta_prior_success=2.0,
            beta_prior_failure=1.0,
        )
    )
    decisions = [model.update({"timestamp": idx, "pH": 6.7})[0] for idx in range(3)]
    assert any(decision.actuation_authorized for decision in decisions)
    response = model.update({"timestamp": 3, "pH": 6.63})[0]
    assert "actuator_response_residual" not in response.reason_codes
    assert response.response_reliability > 0.6


def test_aasvr_r2_beta_reliability_blocks_high_risk_after_failure() -> None:
    cfg = SensorConfig(
        **{
            **sensor().__dict__,
            "actuators": ("acid_doser",),
            "expected_direction": "bidirectional",
            "response_window": 1,
            "response_min_delta": 0.03,
            "risk_level": "high",
        }
    )
    model = AASVR(
        AASVRConfig(
            sensors=(cfg,),
            q_min=0.7,
            response_mode="sequential",
            reliability_mode="beta",
            beta_prior_success=1.0,
            beta_prior_failure=1.0,
            eta_min_high=0.75,
        )
    )
    first = [model.update({"timestamp": idx, "pH": 6.7})[0] for idx in range(3)]
    assert any(decision.actuation_authorized for decision in first)
    assert "actuator_response_residual" in first[-1].reason_codes
    later = [model.update({"timestamp": idx, "pH": 6.7})[0] for idx in range(4, 10)]
    assert not any(decision.actuation_authorized for decision in later)


def test_aasvr_compact_diagnostics_omits_component_strings() -> None:
    model = AASVR(AASVRConfig(sensors=(sensor(),), q_min=0.7, compact_diagnostics=True))
    decision = model.update({"timestamp": 0, "pH": 6.1})[0]
    assert decision.trust_components == ()
