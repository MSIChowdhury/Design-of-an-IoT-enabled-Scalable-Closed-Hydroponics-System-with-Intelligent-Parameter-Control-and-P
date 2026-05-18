from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def mad(values: Sequence[float]) -> float:
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if arr.size == 0:
        return 0.0
    median = np.median(arr)
    return float(np.median(np.abs(arr - median)))


def robust_delta_scale(values: Sequence[float]) -> float:
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if arr.size < 3:
        return 0.0
    return 1.4826 * mad(np.diff(arr))


def tolerance(
    values: Sequence[float],
    *,
    xi_min: float,
    scale_multiplier: float,
    rate_limit: float,
    dt_seconds: float,
    uncertainty: float,
) -> float:
    return float(
        max(
            xi_min,
            scale_multiplier * robust_delta_scale(values),
            rate_limit * dt_seconds,
            uncertainty,
        )
    )

