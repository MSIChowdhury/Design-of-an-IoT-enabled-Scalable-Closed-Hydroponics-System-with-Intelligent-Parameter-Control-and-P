import json

import pytest

from aasvr.recovery_contract import Contract, Journal, RecoveryReceiver
from aasvr.telemetry import pack


def command(event_id=1, created=32, source=None):
    return pack(
        dict(
            kind="command",
            id=event_id,
            rev=0,
            created=created,
            source=created if source is None else source,
            action=1,
        )
    )


def heartbeat(now):
    return pack(dict(kind="heartbeat", created=now, source=now))


def ready_receiver(journal=None):
    journal = journal or Journal()
    r = RecoveryReceiver(journal, 0)
    r.receive(heartbeat(32), 32)
    return r, journal


def test_reservation_precedes_output_and_survives_reopen(tmp_path):
    path = tmp_path / "journal.sqlite"
    r, j = ready_receiver(Journal(path))
    r.receive(command(), 32)

    def emit(m):
        saved = j.read()
        assert saved["status"] == "reserved" and saved["blocked"]
        assert saved["event_id"] == m["id"]

    assert r.step(48, emit) == 1
    j.close()
    j = Journal(path)
    restarted = RecoveryReceiver(j, 64)
    restarted.receive(command(), 80)
    assert restarted.step(80, lambda m: pytest.fail("duplicate output")) == 0
    assert restarted.state["next_allowed"] == 665
    j.close()


def test_clock_interval_expiry_and_delayed_eligibility():
    r, _ = ready_receiver()
    r.receive(command(), 32)
    assert r.step(32, lambda m: pytest.fail("too early for interval")) == 0
    assert r.step(80, lambda m: pytest.fail("not valid throughout dispatch interval")) == 0
    assert r.state["status"] == "expired"


def test_recovery_abandons_pending_and_requires_new_source():
    r, j = ready_receiver()
    r.receive(command(), 32)
    r = RecoveryReceiver(j, 40)
    r.receive(heartbeat(32), 48)
    assert not r.ready
    r.receive(command(2, 64, source=32), 64)
    assert r.state["status"] == "recovery_reject"
    r.receive(heartbeat(80), 80)
    r.receive(command(3, 80), 80)
    assert r.step(96, lambda m: None) == 1


def test_watchdog_drops_old_intent_without_refreshing_expiry():
    r, _ = ready_receiver()
    r.tick(144)
    assert not r.ready
    r.receive(heartbeat(144), 144)
    assert not r.ready  # Evidence predates recovery barrier at 160.
    r.receive(heartbeat(176), 176)
    assert r.ready
    r.receive(command(2, 144), 176)
    assert r.state["status"] == "recovery_reject"
    r.receive(command(3, 176), 176)
    assert r.step(192, lambda m: None) == 1


@pytest.mark.parametrize("stage", ["after_reserve", "after_output"])
def test_unknown_execution_blocks_new_commands(stage):
    r, j = ready_receiver()
    r.receive(command(), 32)
    emitted = []

    def crash(point):
        if point == stage:
            raise RuntimeError("crash")

    with pytest.raises(RuntimeError):
        r.step(48, lambda m: emitted.append(m), crash)
    r = RecoveryReceiver(j, 64)
    assert r.state["status"] == "uncertain" and r.state["blocked"]
    assert len(emitted) == int(stage == "after_output")
    r.receive(heartbeat(800), 800)
    r.receive(command(2, 800), 800)
    assert r.step(832, lambda m: pytest.fail("uncertainty auto-reset")) == 0


def test_cooldown_interval_survives_restart_and_clock_change():
    r, j = ready_receiver()
    r.receive(command(), 32)
    assert r.step(48, lambda m: None) == 1
    r = RecoveryReceiver(j, 64)
    r.receive(heartbeat(656), 656)
    r.receive(command(2, 656), 656)
    assert r.step(672, lambda m: pytest.fail("cooldown shortened")) == 0
    assert r.step(688, lambda m: None) == 1


@pytest.mark.parametrize("now,valid", [(16, True), (48, False), (float("nan"), True)])
def test_invalid_clock_fails_closed_persistently(now, valid):
    r, j = ready_receiver()
    r.tick(now, clock_valid=valid)
    assert j.read()["blocked"]
    restarted = RecoveryReceiver(j, 800)
    restarted.receive(heartbeat(832), 832)
    assert restarted.state["blocked"]


def test_cancellation_before_command_is_durable():
    r, j = ready_receiver()
    r.receive(pack(dict(kind="cancel", id=1, rev=1)), 32)
    r = RecoveryReceiver(j, 40)
    r.receive(command(), 48)
    assert r.step(48, lambda m: pytest.fail("cancelled command")) == 0


def test_configuration_mismatch_rejected():
    _, j = ready_receiver()
    with pytest.raises(ValueError, match="mismatch"):
        RecoveryReceiver(j, 64, Contract(clock_bound=0))


def test_emit_failure_does_not_permit_another_command_in_same_process():
    r, _ = ready_receiver()
    r.receive(command(), 32)

    def fail(m):
        raise OSError("adapter status unknown")

    with pytest.raises(OSError):
        r.step(48, fail)
    assert r.receive(command(2, 800), 800) == "blocked"
    assert r.step(832, lambda m: pytest.fail("output after adapter error")) == 0


def test_no_output_after_expiry_for_all_supported_offsets():
    for offset in range(-16, 17, 8):
        for arrival in range(32, 145, 8):
            r = RecoveryReceiver(Journal(), offset)
            r.receive(heartbeat(32), 32 + offset)
            r.receive(command(), arrival + offset)
            emitted = []
            for true_time in range(arrival, 160, 8):
                r.step(true_time + offset, lambda m: emitted.append(true_time))
            assert all(32 <= t <= 96 for t in emitted)
            assert len(emitted) <= 1


def test_journal_contains_parseable_state(tmp_path):
    r, j = ready_receiver(Journal(tmp_path / "journal.sqlite"))
    assert json.loads(j.db.execute("SELECT body FROM state").fetchone()[0])["version"] == 1
    j.close()


def test_completion_write_failure_remains_blocked(monkeypatch):
    r, j = ready_receiver()
    r.receive(command(), 32)
    save = j.save

    def failing_save(state):
        if state["status"] == "emitted":
            raise OSError("completion write failed")
        save(state)

    monkeypatch.setattr(j, "save", failing_save)
    with pytest.raises(OSError):
        r.step(48, lambda m: None)
    assert r.state["blocked"] and r.state["status"] == "reserved"
    assert r.receive(command(2, 800), 800) == "blocked"


def test_delayed_first_contact_cannot_restore_precontact_intent():
    r, _ = ready_receiver()
    r.tick(144)
    # This heartbeat was generated after timeout but before actual recontact.
    r.receive(heartbeat(176), 208)
    assert not r.ready
    assert r.state["recovery_floor"] == 224
    r.receive(command(2, 192), 208)
    assert r.state["status"] == "recovery_reject"
    r.receive(heartbeat(240), 240)
    r.receive(command(3, 240), 240)
    assert r.step(256, lambda m: None) == 1
