import numpy as np
import pytest

from aasvr.reanalysis import Timing, authorize, hold_estimate
from aasvr.simple_gates import fixed_run_length, physical_bound_rejection


def test_fixed_run_rejects_persistent_repeats_and_recovers_on_change():
    values = [6.8] * 6 + [6.9, 6.9, 6.9]
    result = fixed_run_length(values, np.arange(len(values)) * 16, 0, 14, max_run=2)
    assert result.tolist() == [True, True, False, False, False, False, True, True, False]


def test_gaps_and_invalid_readings_break_fixed_runs():
    values = [6., 6., 6., 6., np.nan, 6., 99., 6.]
    times = [0, 16, 32, 200, 216, 232, 248, 264]
    assert fixed_run_length(values, times, 0, 14, max_run=1).tolist() == [
        True, False, False, True, False, True, False, True]


def test_bound_gate_rejects_both_endpoints_not_nearby_valid_values():
    values = [np.nan, -1, 0, .001, 13.999, 14, 15]
    assert physical_bound_rejection(values, 0, 14).tolist() == [
        False, False, False, True, True, False, False]


def test_fixed_run_hold_expires_before_later_cooldown_opportunity():
    times = np.arange(80) * 16.
    values = np.full(len(times), 6.8)
    accepted = fixed_run_length(values, times, 0, 14, max_run=2)
    estimate, age = hold_estimate(times, values, accepted)
    actions = authorize(times, estimate, age <= 64, 5.8, 6.5, Timing(persistence=32))
    # A detector rejection does not itself discard the common controller's hold.
    assert np.flatnonzero(actions).tolist() == [2]


def test_invalid_fixed_run_cap_rejected():
    for cap in (0, -1, 1.5):
        with pytest.raises(ValueError):
            fixed_run_length([6.], [0.], 0, 14, max_run=cap)
