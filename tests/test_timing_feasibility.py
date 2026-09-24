import numpy as np
import pytest

from aasvr.config import load_yaml
from aasvr.recovery_replay import run
from aasvr.telemetry import score
from aasvr.timing_feasibility import interval, replay, score_and_explain, variants

CFG = load_yaml("configs/experiments/timing_feasibility.yaml")


def variant(stage, bound, scheduler):
    return next(
        v
        for v in variants(CFG)
        if (v["stage"], v["bound"], v["scheduler"]) == (stage, bound, scheduler)
    )


def test_six_second_interval_is_missed_by_polling():
    earliest, latest = interval(640, 640, 640, 665, 16, 1)
    assert (earliest, latest) == (681, 687)
    assert np.ceil(earliest / 16) * 16 > latest
    assert interval(640, 640, 640, 681, 16, 1)[0] > latest


def test_deadline_scheduler_uses_feasible_gap_without_new_measurement():
    times = np.arange(0, 1800, 16.0)
    values = np.zeros(len(times))
    poll = replay(
        times, times, values, 1, 2, dict(name="ideal"), variant("clock", 16, "poll"), CFG, 0
    )
    deadline = replay(
        times, times, values, 1, 2, dict(name="ideal"), variant("clock", 16, "deadline"), CFG, 0
    )
    assert 681 in [o["time"] for o in deadline["outputs"]]
    assert not any(o["event_id"] == 40 for o in poll["outputs"])
    assert next(o for o in deadline["outputs"] if o["event_id"] == 40)["time"] == 681
    rows, _ = score_and_explain(times, poll, warmup=0, tail=0)
    assert (
        next(r for r in rows if r["event_id"] == 40)["reason"] == "polling_missed_feasible_interval"
    )


def test_full_recovery_poll_reproduces_existing_implementation():
    times = np.arange(0, 5000, 16.0)
    values = np.where((times > 900) & (times < 1000), 3.0, 0.0)
    scenario = dict(name="loss", loss=0.1, delay=8, jitter=24)
    original_cfg = load_yaml("configs/experiments/recovery_contract.yaml")
    a = run(times, times, values, 1, 2, scenario, "recovery_v2", original_cfg, 123)
    b = replay(times, times, values, 1, 2, scenario, variant("recovery", 16, "poll"), CFG, 123)
    np.testing.assert_array_equal(a["reference"], b["reference"])
    assert np.array_equal(times[np.flatnonzero(a["actions"])], [o["time"] for o in b["outputs"]])
    assert a["bytes"] == b["counters"]["bytes"]
    rows, errors = score_and_explain(times, b)
    old = score(times, a["reference"], a["actions"], a["directions"])
    assert sum(r["matched"] for r in rows) == old["matched"]
    assert errors == old["unnecessary"] + old["wrong_direction"]


@pytest.mark.parametrize("scheduler", ["poll", "deadline"])
def test_cancellation_arriving_at_output_tick_takes_precedence(scheduler):
    times = np.arange(0, 160, 16.0)
    values = np.where(times >= 48, 1.5, 0.0)
    r = replay(
        times, times, values, 1, 2, dict(name="ideal"), variant("clock", 16, scheduler), CFG, 1
    )
    assert not r["outputs"]


def test_durable_stage_blocks_uncertainty_while_current_loses_state():
    times = np.arange(0, 2600, 16.0)
    scenario = dict(name="crash", crash_after_output_seconds=1)
    durable = replay(
        times, times, np.zeros(len(times)), 1, 2, scenario, variant("durable", 0, "poll"), CFG, 0
    )
    current = replay(
        times, times, np.zeros(len(times)), 1, 2, scenario, variant("current", 0, "poll"), CFG, 0
    )
    assert len(durable["outputs"]) == 1
    assert current["counters"]["repeated_outputs"] >= 1
    rows, _ = score_and_explain(times, durable, warmup=0, tail=0)
    assert all(r["reason"] == "unresolved_execution" for r in rows if not r["matched"])


def test_future_values_do_not_change_earlier_outputs():
    times = np.arange(0, 3000, 16.0)
    before = np.zeros(len(times))
    after = before.copy()
    after[times > 1600] = 3
    a = replay(
        times, times, before, 1, 2, dict(name="ideal"), variant("recovery", 8, "deadline"), CFG, 0
    )
    b = replay(
        times, times, after, 1, 2, dict(name="ideal"), variant("recovery", 8, "deadline"), CFG, 0
    )
    assert [o for o in a["outputs"] if o["time"] <= 1600] == [
        o for o in b["outputs"] if o["time"] <= 1600
    ]
