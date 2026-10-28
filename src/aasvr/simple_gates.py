"""Transparent task-specific gates for the post-hoc LiveGate follow-up.

These gates do not alter the locked LiveGate method or its original benchmark.
"""
from __future__ import annotations

import numpy as np


def fixed_run_length(values, times, low, high, *, max_run=8, max_gap=120.0):
    """Accept up to ``max_run`` consecutive identical in-range readings.

    The first reading has run length one. A gap, invalid reading, or changed
    value starts a new run; rejected repeats continue the run until it ends.
    The cap is fixed across channels, and selected only on validation data.
    """
    if int(max_run) != max_run or max_run < 1:
        raise ValueError("max_run must be a positive integer")
    values, times = np.asarray(values, float), np.asarray(times, float)
    if values.shape != times.shape or values.ndim != 1:
        raise ValueError("values and times must be aligned one-dimensional arrays")
    accepted = np.zeros(len(values), bool)
    run, previous = 0, np.nan
    for i, value in enumerate(values):
        if not np.isfinite(value) or not low <= value <= high:
            run, previous = 0, np.nan
            continue
        contiguous = not i or times[i] - times[i - 1] <= max_gap
        run = run + 1 if contiguous and value == previous else 1
        previous = value
        accepted[i] = run <= max_run
    return accepted


def physical_bound_rejection(values, low, high):
    """Reject invalid readings and readings exactly at either declared bound."""
    values = np.asarray(values, float)
    return np.isfinite(values) & (values > low) & (values < high)
