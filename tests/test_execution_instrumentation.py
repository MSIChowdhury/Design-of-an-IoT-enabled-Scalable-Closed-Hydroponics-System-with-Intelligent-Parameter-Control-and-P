"""Clock, measured-trace handling, and unchanged-receiver regression checks."""

import numpy as np
import pytest

from aasvr.config import load_yaml
from aasvr.execution_instrumentation import TimedJournal, clock_exchange, verify_ack
from aasvr.measured_trace_replay import ingress_delay, replay, validate_trace
from aasvr.timing_feasibility import replay as original_replay


def observation(**updates):
    return dict(
        received=True,
        independent_recorded=True,
        network_s=0.0,
        acceptance_s=0.0,
        acceptance_journal_s=0.0,
        reserve_s=0.0,
        timer_lateness_s=0.0,
        output_delay_s=0.0,
        ack_lost=False,
        **updates,
    )


def config():
    return load_yaml("configs/experiments/timing_feasibility.yaml")


def run(trace, stage="durable", scheduler="poll", bound=0):
    times = np.arange(0, 4016, 16, dtype=float)
    result = replay(
        times,
        times,
        np.ones(len(times)) * 2,
        0,
        0.5,
        trace,
        dict(stage=stage, scheduler=scheduler, bound=bound),
        config(),
    )
    return result


def test_asymmetric_exchange_contains_offset_without_assuming_symmetry():
    result = clock_exchange(0, 110, 130, 70)  # true offset=100; forward10, return40
    assert result["offset_low_ns"] == 60
    assert result["offset_high_ns"] == 110
    assert result["network_rtt_ns"] == 50
    assert result["midpoint_ns"] != 100


@pytest.mark.parametrize("stamps", [(10, 20, 19, 30), (10, 20, 21, 9), (0, 0, 20, 10)])
def test_invalid_clock_exchanges(stamps):
    with pytest.raises(ValueError):
        clock_exchange(*stamps)


def test_ack_requires_matching_event_and_status():
    verify_ack(dict(stream="a", id=1, status="recorded"), "a", 1)
    for wrong in [
        dict(stream="b", id=1, status="recorded"),
        dict(stream="a", id=2, status="recorded"),
        dict(stream="a", id=1, status="accepted"),
    ]:
        with pytest.raises(ValueError):
            verify_ack(wrong, "a", 1)


def test_timed_journal_reopens_durable_record(tmp_path):
    path = tmp_path / "journal.sqlite"
    journal = TimedJournal(path)
    journal.save(dict(status="reserved", blocked=True))
    journal.close()
    assert journal.timings[0]["end_ns"] >= journal.timings[0]["start_ns"]
    reopened = TimedJournal(path)
    assert reopened.read() == dict(status="reserved", blocked=True)
    reopened.close()


@pytest.mark.parametrize(
    "stage,bound,scheduler",
    [
        ("current", 0, "poll"),
        ("durable", 0, "poll"),
        ("recovery", 16, "poll"),
        ("recovery", 16, "deadline"),
        ("recovery", 1, "deadline"),
    ],
)
def test_zero_trace_preserves_prior_frozen_replay(stage, bound, scheduler):
    times = np.arange(0, 4016, 16, dtype=float)
    values = np.ones(len(times)) * 2
    variant = dict(stage=stage, bound=bound, scheduler=scheduler)
    prior = original_replay(times, times, values, 0, 0.5, {"name": "ideal"}, variant, config(), 42)
    measured = replay(times, times, values, 0, 0.5, [observation()], variant, config())
    assert measured["outputs"] == prior["outputs"]
    np.testing.assert_array_equal(measured["reference"], prior["reference"])
    assert measured["counters"]["bytes"] == prior["counters"]["bytes"]


def test_missing_forward_packet_is_not_zero_latency():
    row = dict(received=False)
    assert ingress_delay(row, True) is None
    assert run([row])["outputs"] == []


def test_missing_ack_blocks_durable_but_volatile_has_no_block():
    row = observation()
    row["ack_lost"] = True
    durable = run([row])
    volatile = run([row], stage="current")
    assert len(durable["outputs"]) == 1
    assert durable["counters"]["missing_output_acks"] == 1
    assert len(volatile["outputs"]) > 1


def test_timer_and_effect_delay_applied_once():
    row = observation()
    row.update(timer_lateness_s=0.003, output_delay_s=0.002)
    result = run([row])
    assert result["outputs"][0]["time"] == pytest.approx(32.005)


def test_positive_ingress_is_deferred_by_fixed_intake_polling():
    row = observation()
    row["network_s"] = 0.0001
    assert run([row])["outputs"][0]["time"] == 48


def test_unknown_or_excess_timing_is_rejected():
    for changes in [
        dict(independent_recorded=False),
        dict(output_delay_s=float("nan")),
        dict(network_s=16),
        dict(timer_lateness_s=1),
    ]:
        row = observation()
        row.update(changes)
        with pytest.raises(ValueError):
            validate_trace([row])


def test_late_wakeup_rechecks_expiry_in_unchanged_receiver():
    times = np.arange(0, 256, 16, dtype=float)
    cfg = config()
    cfg["expiry"] = 33
    variant = dict(stage="recovery", scheduler="deadline", bound=16)
    zero = replay(times, times, np.full(len(times), 2.0), 0, 0.5, [observation()], variant, cfg)
    row = observation()
    row["timer_lateness_s"] = 0.01
    late = replay(times, times, np.full(len(times), 2.0), 0, 0.5, [row], variant, cfg)
    assert len(zero["outputs"]) == 1
    assert late["outputs"] == []
