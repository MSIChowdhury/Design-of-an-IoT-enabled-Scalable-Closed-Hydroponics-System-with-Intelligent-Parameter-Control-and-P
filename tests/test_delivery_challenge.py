import numpy as np

from aasvr.delivery_challenge import Challenge, Transport, assumption_checks, delivery_for, replay
from aasvr.reliable_events import Delivery, replay_reliable
from aasvr.telemetry import Link


def test_ideal_matches_original_replay():
    times = np.arange(0, 2400, 16.0)
    values = np.where((times > 700) & (times < 900), 3.0, 0.0)
    delivery = Delivery(retry_seconds=32, max_attempts=2, acknowledgments=False)
    original = replay_reliable(times, times, values, 1, 2, Link("ideal"), delivery, seed=42)
    challenge = replay(times, times, values, 1, 2, Challenge("ideal"), delivery, seed=42)
    for key in ("reference", "actions", "directions"):
        np.testing.assert_array_equal(original[key], challenge[key])
    assert challenge["bytes"] == original["forward_bytes"]


def test_outage_phase_and_correlated_reproducibility():
    c = Challenge("outage", burst_duration=64, burst_phase=317)
    transport = Transport(c, 100, 3)
    assert transport.lag(320, 20, 0) is None
    assert transport.lag(384, 24, 0) == 0
    a = Transport(Challenge("correlated", bad_seconds=96), 10000, 4)
    b = Transport(Challenge("correlated", bad_seconds=96), 10000, 4)
    np.testing.assert_array_equal(a.bad, b.bad)
    assert 0.05 < a.bad.mean() < 0.15
    assert np.any(a.bad[:, 1:] & a.bad[:, :-1])


def test_reverse_impairment_does_not_change_forward_channel():
    c = Challenge("reverse", reverse_loss=1, reverse_delay=80)
    transport = Transport(c, 4, 1)
    assert transport.lag(0, 0, 0) == 0
    assert transport.lag(0, 0, 1) is None


def test_stronger_baseline_only_changes_cancellation():
    cfg = dict(retry_seconds=32, max_attempts=2, expiry_seconds=64, freshness_seconds=120)
    candidate, plain = (delivery_for(p, cfg) for p in ("candidate", "plain_repetition"))
    assert candidate.cancellation and not plain.cancellation
    assert not candidate.acknowledgments and not plain.acknowledgments
    assert candidate.retry_seconds == plain.retry_seconds == 32
    assert candidate.max_attempts == plain.max_attempts == 2


def test_assumption_failures_are_exposed():
    checks = assumption_checks()
    assert checks["restart_reexecutes_same_id"]
    assert checks["negative_clock_offset_can_execute_truly_expired_command"]


def test_replay_offset_observer_uses_true_time():
    times = np.arange(0, 200, 16.0)
    result = replay(
        times,
        times,
        np.zeros(len(times)),
        1,
        2,
        Challenge("late", delay=96, offset=-64),
        Delivery(retry_seconds=32, max_attempts=2, acknowledgments=False),
        0,
    )
    assert result["expired_outputs"] == 1
