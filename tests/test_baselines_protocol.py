from __future__ import annotations

from aasvr.baselines import BaselineConfig, StreamingBaseline
from aasvr.core import SensorConfig


def test_baseline_supervisor_blocks_anomalous_actuation() -> None:
    sensor = SensorConfig(
        name="pH",
        physical_min=0.0,
        physical_max=14.0,
        control_low=5.8,
        control_high=6.5,
        rate_limit=1.0,
        confirm_samples=1,
        cooldown_samples=2,
    )
    model = StreamingBaseline((sensor,), BaselineConfig(method="raw_threshold"))
    decision = model.update({"timestamp": "t0", "pH": 20.0})[0]
    assert decision.alert
    assert not decision.actuation_authorized


def test_baseline_supervisor_applies_cooldown_after_authorization() -> None:
    sensor = SensorConfig(
        name="pH",
        physical_min=0.0,
        physical_max=14.0,
        control_low=5.8,
        control_high=6.5,
        rate_limit=1.0,
        confirm_samples=1,
        cooldown_samples=2,
    )
    model = StreamingBaseline((sensor,), BaselineConfig(method="raw_threshold"))
    first = model.update({"timestamp": "t0", "pH": 7.0})[0]
    second = model.update({"timestamp": "t1", "pH": 7.0})[0]
    assert first.actuation_authorized
    assert not second.actuation_authorized
