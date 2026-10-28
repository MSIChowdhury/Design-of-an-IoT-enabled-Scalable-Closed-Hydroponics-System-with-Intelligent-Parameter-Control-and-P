"""Executable-direction regressions for the retrospective deployment audit."""

import numpy as np

from aasvr.reanalysis import Timing, authorize


def test_unavailable_lowering_cannot_delay_co2_injection():
    times = np.array([0.0, 16.0, 32.0, 48.0])
    values = np.array([5000.0, 1800.0, 1800.0, 1800.0])
    actions = authorize(times, values, np.ones(4, dtype=bool), 1900, 2100,
                        Timing(persistence=32), allowed_directions=(1,))
    assert actions.tolist() == [0, 0, 0, 1]


def test_unavailable_raising_cannot_delay_cooling():
    times = np.array([0.0, 16.0])
    values = np.array([15.0, 30.0])
    actions = authorize(times, values, np.ones(2, dtype=bool), 20, 26,
                        Timing(persistence=0), allowed_directions=(-1,))
    assert actions.tolist() == [0, -1]


def test_unavailable_direction_resets_persistence():
    times = np.array([0.0, 16.0, 32.0, 48.0, 64.0])
    values = np.array([1800.0, 5000.0, 1800.0, 1800.0, 1800.0])
    actions = authorize(times, values, np.ones(5, dtype=bool), 1900, 2100,
                        Timing(persistence=32), allowed_directions=(1,))
    assert actions.tolist() == [0, 0, 0, 0, 1]


def test_unavailable_direction_does_not_clear_real_cooldown():
    times = np.array([0.0, 16.0, 32.0, 600.0])
    values = np.array([1800.0, 5000.0, 1800.0, 1800.0])
    actions = authorize(times, values, np.ones(4, dtype=bool), 1900, 2100,
                        Timing(persistence=0), allowed_directions=(1,))
    assert actions.tolist() == [1, 0, 0, 1]


def test_default_preserves_bidirectional_benchmark_cooldown():
    times = np.array([0.0, 16.0, 600.0, 616.0])
    values = np.array([5000.0, 1800.0, 1800.0, 5000.0])
    actions = authorize(times, values, np.ones(4, dtype=bool), 1900, 2100,
                        Timing(persistence=0))
    assert actions.tolist() == [-1, 0, 1, 0]
