import json
import numpy as np
import pytest

from aasvr.reliable_events import Delivery, EventReceiver, EventSender, replay_reliable
from aasvr.telemetry import Link, pack


def command(event_id=1, created=0, source=0, action=-1):
    return pack(
        dict(kind="command", id=event_id, rev=0, created=created, source=source, action=action)
    )


def cancel(event_id=1):
    return pack(dict(kind="cancel", id=event_id, rev=1))


def test_cancel_before_command_is_a_tombstone():
    r = EventReceiver()
    r.receive(cancel(), 16)
    r.receive(command(), 32)
    assert r.step(32) == 0
    assert r.status == "cancelled"


def test_execution_is_idempotent_and_cannot_be_undone():
    r = EventReceiver()
    r.receive(command(), 0)
    assert r.step(0) == -1
    r.receive(command(), 16)
    assert r.step(16) == 0
    r.receive(cancel(), 32)
    assert r.status == "executed" and r.stats["late_cancellations"] == 1
    r.receive(command(), 48)
    assert r.step(48) == 0


def test_retries_do_not_extend_expiry_or_refresh_evidence():
    r = EventReceiver()
    r.receive(command(), 65)
    assert r.step(65) == 0 and r.status == "expired"
    r.receive(command(), 80)
    assert r.step(80) == 0
    r.receive(command(2, created=160, source=0), 160)
    assert r.step(160) == 0


def test_cancellation_revokes_deferred_command_without_resetting_cooldown():
    r = EventReceiver()
    r.receive(command(), 32)
    assert r.step(32) == -1
    r.receive(command(2, 608, 608), 624)
    assert r.step(624) == 0
    r.receive(cancel(2), 640)
    assert r.step(640) == 0 and r.next_allowed == 632


def test_deferred_command_executes_if_still_valid():
    r = EventReceiver()
    r.receive(command(), 32)
    r.step(32)
    r.receive(command(2, 608, 608), 624)
    assert r.step(624) == 0
    assert r.step(640) == -1


def test_old_ack_cannot_stop_cancellation_retries():
    s = EventSender()
    s.observe(0, 0, -1, -1, 1)
    original = s.send(0)
    assert json.loads(original)["rev"] == 0
    s.observe(16, 16, 0, 0, 2)
    s.acknowledge(pack(dict(kind="ack", id=1, rev=0, status="pending")))
    assert json.loads(s.send(16))["kind"] == "cancel"
    s.acknowledge(pack(dict(kind="ack", id=1, rev=1, status="cancelled")))
    assert s.send(32) is None


def test_lost_ack_retries_are_bounded_and_identical():
    s = EventSender(Delivery(max_attempts=3))
    s.observe(0, 0, -1, -1, 1)
    packets = [s.send(t) for t in (0, 16, 32, 48, 64, 80)]
    assert packets[0] == packets[1] == packets[2]
    assert packets[3:] == [None, None, None]


def test_ideal_replay_matches_reference_and_counts_ack_bytes():
    t = np.arange(0, 4000, 16.0)
    x = np.where((t > 500) & (t < 1500), 7.0, 6.0)
    r = replay_reliable(t, t, x, 5.8, 6.5, Link("ideal"))
    assert np.array_equal(r["reference"], r["actions"])
    assert r["ack_bytes"] > 0 and r["forward_bytes"] > 0


def test_network_reordering_preserves_cooldown_and_at_most_once():
    t = np.arange(0, 10000, 16.0)
    x = np.full(len(t), 7.0)
    r = replay_reliable(
        t, t, x, 5.8, 6.5, Link("stress", loss=0.1, delay=8, jitter=56, duplicate=0.5), seed=7
    )
    assert np.all(np.diff(t[r["actions"] != 0]) >= 600)
    assert r["receiver_executed"] <= r["sender_commands"]


def test_receiver_requires_monotonic_time():
    r = EventReceiver()
    r.step(30)
    with pytest.raises(ValueError, match="monotonic"):
        r.step(20)


def test_retry_recovers_initial_loss_without_extending_command_life():
    t = np.arange(0, 2000, 16.0)
    x = np.full(len(t), 7.0)
    link = Link("initial_outage", burst_period=3600, burst_duration=48)
    r = replay_reliable(t, t, x, 5.8, 6.5, link, Delivery(retry_seconds=32, max_attempts=2))
    first_ref = t[np.flatnonzero(r["reference"])[0]]
    first_output = t[np.flatnonzero(r["actions"])[0]]
    assert first_ref == 32 and first_output == 64
    assert r["lost_forward"] > 0 and r["sender_retries"] > 0


def test_future_measurements_do_not_change_past_actions():
    t = np.arange(0, 3000, 16.0)
    x = np.full(len(t), 7.0)
    future = x.copy()
    future[100:] = 6.0
    link = Link("stress", loss=0.1, delay=8, jitter=56, duplicate=0.2)
    a = replay_reliable(t, t, x, 5.8, 6.5, link, seed=9)
    b = replay_reliable(t, t, future, 5.8, 6.5, link, seed=9)
    assert np.array_equal(a["actions"][:100], b["actions"][:100])
    assert np.array_equal(a["reference"][:100], b["reference"][:100])
