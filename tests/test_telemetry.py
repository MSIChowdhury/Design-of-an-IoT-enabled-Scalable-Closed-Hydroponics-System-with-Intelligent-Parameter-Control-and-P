import numpy as np
import pytest

from aasvr.telemetry import Link, Receiver, pack, replay, score


def sample(seq, t, value=7.0):
    return pack(dict(kind="sample", seq=seq, time=t, value=value))


def event(seq, t, event_id=1):
    return pack(dict(kind="event", seq=seq, time=t, action=-1, event_id=event_id, event_time=t))


def test_ideal_full_stateful_and_edge_events_reproduce_reference():
    t = np.arange(0, 4000, 16.0)
    x = np.where((t > 500) & (t < 1500), 7.0, 6.0)
    for policy in ("full", "stateful", "edge_events", "threshold"):
        r = replay(t, t, x, 5.8, 6.5, policy, 64, Link("ideal"))
        assert np.array_equal(r["reference"], r["actions"]), policy


def test_expired_duplicate_and_reordered_messages_cannot_refresh_evidence():
    r = Receiver(5.8, 6.5)
    r.receive(sample(2, 32), 32)
    r.receive(sample(1, 16, 6.0), 48)
    r.receive(sample(2, 32), 64)
    assert r.source_time == 32 and r.value == 7.0
    r.receive(sample(3, 0), 160)
    assert r.source_time == 32
    assert r.step(160) == 0
    assert r.stats["duplicate_or_reordered"] == 2 and r.stats["expired"] == 1


def test_event_identity_expiry_and_cooldown_are_independent():
    r = Receiver(5.8, 6.5)
    assert r.receive(event(1, 0), 0) == -1
    assert r.receive(event(2, 16), 16) == 0
    assert r.receive(event(3, 32, 2), 32) == 0
    assert r.receive(event(4, 100, 3), 700) == 0
    assert r.stats["duplicate_event"] == 1
    assert r.stats["lockout_veto"] == 1
    assert r.stats["expired"] == 1


def test_snapshot_cannot_erase_output_lockout():
    r = Receiver(5.8, 6.5)
    assert r.receive(event(1, 0), 0) == -1
    snapshot = dict(
        kind="snapshot",
        seq=2,
        time=16.0,
        value=7.0,
        direction=-1,
        since=-100.0,
        next_allowed=0.0,
        action=0,
    )
    r.receive(pack(snapshot), 16)
    assert r.step(16) == 0
    assert r.output_next_allowed == 600


def test_long_source_gap_expires_and_resets_persistence():
    t = np.arange(0, 2000, 16.0)
    src = t.copy()
    src[(t >= 100) & (t < 1000)] = 96
    values = np.full(len(t), 7.0)
    r = replay(t, src, values, 5.8, 6.5, "full", 16, Link("ideal"))
    assert not r["actions"][(t > 216) & (t < 1000)].any()
    assert np.array_equal(r["reference"], r["actions"])


def test_scoring_has_one_to_one_matching_and_zero_opportunities():
    t = np.arange(0, 2000, 16.0)
    ref = np.zeros(len(t), int)
    act = ref.copy()
    d = np.full(len(t), -1)
    ref[50] = -1
    act[52] = -1
    act[53] = -1
    m = score(t, ref, act, d)
    assert m["opportunities"] == 1 and m["matched"] == 1
    m = score(t, np.zeros(len(t), int), act, np.zeros(len(t), int))
    assert m["opportunities"] == 0 and m["unnecessary"] == 2


def test_monotonic_clock_required():
    r = Receiver(5.8, 6.5)
    r.step(20)
    with pytest.raises(ValueError, match="monotonic"):
        r.step(10)


def test_delayed_event_waits_for_lockout_without_losing_its_identity():
    r = Receiver(5.8, 6.5)
    assert r.receive(event(1, 0), 32) == -1
    assert r.receive(event(2, 608, 2), 624) == 0
    assert r.step(640, events_only=True) == -1
    assert r.step(656, events_only=True) == 0
    assert r.receive(event(3, 608, 2), 656) == 0


def test_pending_event_cannot_outlive_its_expiry():
    r = Receiver(5.8, 6.5)
    r.receive(event(1, 0), 32)
    r.receive(event(2, 400, 2), 416)
    assert r.step(640, events_only=True) == 0
    assert r.pending is None


def test_duplicate_reordering_and_loss_never_shorten_output_lockout():
    t = np.arange(0, 10000, 16.0)
    x = np.full(len(t), 7.0)
    link = Link("stress", loss=0.1, delay=8, jitter=56, duplicate=0.4)
    for policy in ("full", "stateful", "edge_events", "threshold"):
        r = replay(t, t, x, 5.8, 6.5, policy, 64, link, seed=9)
        event_times = t[r["actions"] != 0]
        assert np.all(np.diff(event_times) >= 600)


def test_future_values_cannot_change_past_sender_or_receiver_decisions():
    t = np.arange(0, 4000, 16.0)
    x = np.full(len(t), 6.0)
    changed = x.copy()
    changed[150:] = 7.0
    link = Link("stress", loss=0.1, delay=8, jitter=56, duplicate=0.3)
    for policy in ("full", "periodic", "delta", "threshold", "edge_events", "stateful"):
        a = replay(t, t, x, 5.8, 6.5, policy, 64, link, seed=10)
        b = replay(t, t, changed, 5.8, 6.5, policy, 64, link, seed=10)
        assert np.array_equal(a["actions"][:150], b["actions"][:150])
        assert np.array_equal(a["reference"][:150], b["reference"][:150])
