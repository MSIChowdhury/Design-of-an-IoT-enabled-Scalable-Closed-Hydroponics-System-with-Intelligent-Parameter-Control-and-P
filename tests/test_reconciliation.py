import pytest

from aasvr.execution_instrumentation import pack
from aasvr.reconciliation import Reconciler, command_digest
from aasvr.reconciliation_mock import MockLedger
from aasvr.recovery_contract import Contract, Journal
from aasvr.timing_feasibility import AblationReceiver


def reserved(tmp_path, now=10, cooldown=600):
    journal = Journal(tmp_path / "receiver.sqlite")
    receiver = AblationReceiver(
        journal, 0, Contract(clock_bound=0, dispatch_bound=1, cooldown=cooldown), False
    )
    command = dict(kind="command", id=1, rev=0, created=now, source=now, action=1)
    receiver.receive(pack(command), now)

    def lost(_):
        raise TimeoutError()

    with pytest.raises(TimeoutError):
        receiver.step(now, lost)
    reconciler = Reconciler(receiver, "stream", "domain")
    return receiver, reconciler, command


def evidence(command, **updates):
    result = dict(
        stream="stream",
        id=command["id"],
        digest=command_digest(command),
        clock_domain="domain",
        status="completed",
        output_time=10.5,
        fenced=False,
    )
    result.update(updates)
    return result


def test_completion_preserves_cooldown_and_requires_new_source(tmp_path):
    receiver, reconciler, m = reserved(tmp_path)
    assert reconciler.request(11)
    assert reconciler.apply(evidence(m), 12)
    assert receiver.state["next_allowed"] == 611
    stale = dict(m, id=2, created=13)
    assert receiver.receive(pack(stale), 13) == "recovery_reject"
    fresh = dict(m, id=3, created=14, source=14)
    receiver.receive(pack(fresh), 14)
    assert receiver.step(15, lambda _: pytest.fail("early output")) == 0
    receiver.journal.close()


@pytest.mark.parametrize(
    "updates",
    [
        dict(id=2),
        dict(stream="other"),
        dict(digest="wrong"),
        dict(clock_domain="other"),
        dict(status="not_found"),
        dict(status="pending"),
        dict(status="unavailable"),
        dict(fenced=True),
        dict(output_time=float("nan")),
        dict(output_time=100),
        dict(output_time=9),
        dict(status="cancelled", fenced=True),
        dict(status="cancelled", output_time=None, fenced=False),
    ],
)
def test_bad_evidence_cannot_restore_authority(tmp_path, updates):
    receiver, reconciler, m = reserved(tmp_path)
    reconciler.request(11)
    assert not reconciler.apply(evidence(m, **updates), 12)
    assert receiver.state["blocked"]
    receiver.journal.close()


def test_not_found_then_delayed_output_is_not_retried(tmp_path):
    receiver, reconciler, m = reserved(tmp_path)
    mock = MockLedger(tmp_path / "mock.sqlite", "domain")
    reconciler.request(11)
    assert not reconciler.apply(mock.lookup("stream", 1), 11)
    mock.submit("stream", m, 15)
    mock.advance(15)
    assert receiver.state["blocked"]
    assert reconciler.request(27)
    assert reconciler.apply(mock.lookup("stream", 1), 27)
    assert receiver.state["next_allowed"] == 615
    assert mock.effect_count("stream", 1) == 1
    mock.close()
    receiver.journal.close()


@pytest.mark.parametrize("submit_first", [False, True])
def test_cancellation_tombstone_prevents_delayed_execution(tmp_path, submit_first):
    receiver, reconciler, m = reserved(tmp_path)
    mock = MockLedger(tmp_path / "mock.sqlite", "domain")
    if submit_first:
        mock.submit("stream", m, 20)
    terminal = mock.cancel("stream", m)
    mock.close()
    mock = MockLedger(tmp_path / "mock.sqlite", "domain")
    mock.submit("stream", m, 20)
    mock.advance(20)
    assert mock.effect_count("stream", 1) == 0
    reconciler.request(21)
    assert reconciler.apply(terminal, 21)
    assert not receiver.state["blocked"]
    assert receiver.receive(pack(m), 22) == "duplicate"
    mock.close()
    receiver.journal.close()


def test_completion_wins_cancel_race(tmp_path):
    receiver, reconciler, m = reserved(tmp_path)
    mock = MockLedger(tmp_path / "mock.sqlite", "domain")
    mock.submit("stream", m, 11)
    mock.advance(11)
    terminal = mock.cancel("stream", m)
    assert terminal["status"] == "completed"
    reconciler.request(12)
    assert reconciler.apply(terminal, 12)
    mock.close()
    receiver.journal.close()


def test_attempt_budget_survives_restart_and_time_cannot_reset_it(tmp_path):
    receiver, reconciler, m = reserved(tmp_path)
    for now in (11, 27, 43, 59):
        assert reconciler.request(now)
    receiver.journal.close()
    journal = Journal(tmp_path / "receiver.sqlite")
    receiver = AblationReceiver(journal, 60, Contract(clock_bound=0, dispatch_bound=1), False)
    reconciler = Reconciler(receiver, "stream", "domain")
    assert reconciler.request(10000) is None
    assert not reconciler.apply(evidence(m), 10000)
    assert receiver.state["blocked"]
    journal.close()


def test_clock_invalid_cannot_be_cleared_by_execution_evidence(tmp_path):
    receiver, reconciler, m = reserved(tmp_path)
    reconciler.request(11)
    receiver.tick(9)
    assert not reconciler.apply(evidence(m), 12)
    assert receiver.state["blocked"]
    receiver.journal.close()


def test_foreign_stream_cannot_bind_same_journal(tmp_path):
    receiver, _, _ = reserved(tmp_path)
    with pytest.raises(ValueError):
        Reconciler(receiver, "other", "domain")
    receiver.journal.close()


def test_completed_reconciliation_barrier_survives_reopen(tmp_path):
    receiver, reconciler, m = reserved(tmp_path)
    reconciler.request(11)
    assert reconciler.apply(evidence(m), 12)
    receiver.journal.close()
    journal = Journal(tmp_path / "receiver.sqlite")
    receiver = AblationReceiver(journal, 13, Contract(clock_bound=0, dispatch_bound=1), False)
    Reconciler(receiver, "stream", "domain")
    assert receiver.receive(pack(dict(m, id=2, created=14)), 14) == "recovery_reject"
    future = dict(m, id=3, created=612, source=612)
    assert receiver.receive(pack(future), 612) == "pending"
    outputs = []
    assert receiver.step(612, outputs.append) == 1
    assert len(outputs) == 1 and outputs[0]["id"] == 3
    journal.close()


def test_trace_counts_unresolved_for_blocking_baseline():
    import numpy as np
    from aasvr.config import load_yaml
    from aasvr.reconciled_trace_replay import replay

    trace = [
        dict(
            received=True,
            independent_recorded=True,
            network_s=0.0,
            acceptance_s=0.0,
            acceptance_journal_s=0.0,
            reserve_s=0.0,
            timer_lateness_s=0.0,
            output_delay_s=0.0,
            ack_lost=True,
        )
    ]
    times = np.arange(0, 2048, 16, dtype=float)
    result = replay(
        times,
        times,
        np.full(len(times), 2.0),
        0,
        0.5,
        trace,
        dict(stage="durable", bound=0, scheduler="poll"),
        load_yaml("configs/experiments/timing_feasibility.yaml"),
    )
    assert result["counters"]["unresolved"] == 1
    assert len(result["outputs"]) == 1


def test_new_event_requires_its_own_persisted_lookup(tmp_path):
    receiver, reconciler, m = reserved(tmp_path, cooldown=1)
    reconciler.request(11)
    assert reconciler.apply(evidence(m), 11)
    second = dict(m, id=2, created=13, source=13)
    receiver.receive(pack(second), 13)

    def lost(_):
        raise TimeoutError()

    with pytest.raises(TimeoutError):
        receiver.step(13, lost)
    proof = evidence(second, output_time=13.5)
    assert not reconciler.apply(proof, 14)
    assert receiver.state["blocked"]
    assert reconciler.request(14)
    assert reconciler.apply(proof, 14)
    receiver.journal.close()
