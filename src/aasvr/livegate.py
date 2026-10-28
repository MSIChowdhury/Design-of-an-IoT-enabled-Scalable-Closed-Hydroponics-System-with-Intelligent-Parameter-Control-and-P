"""LiveGate: learned consistency and liveness gating with conformal calibration.

A reading may drive actuation only if (1) it is consistent with a learned
one-step forecast from the trusted state, time of day, and the other channels,
and (2) the sensor is alive: the current run of identical readings is not
longer than the learned run-length distribution of a working sensor allows.
Both thresholds come from one user-chosen error level epsilon: the consistency
threshold is a split-conformal quantile of clean calibration scores, and the
liveness threshold rejects runs whose empirical survival is below epsilon.
Surprising but live readings can re-anchor the trusted state after a number of
mutually consistent confirmations that grows with the onset surprise.

Models are fitted on development data only. Readings outside the physical range
are never used for fitting; runs pinned at a declared physical bound are
treated as saturation, not as evidence of normal sensor behavior.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

from aasvr.standin import _spikes


@dataclass(frozen=True)
class LiveGateModel:
    name: str
    others: tuple[str, ...]
    coef: np.ndarray
    intercept: float
    center: np.ndarray  # feature centers for the context channels
    clip: np.ndarray  # (len(others), 2) winsorizing bounds for context channels
    scale: float
    calibration_scores: np.ndarray  # sorted clean conformal scores
    run_lengths: np.ndarray  # sorted identical-reading run lengths of a live sensor
    bounds: tuple[float, float]

    def threshold(self, epsilon: float) -> float:
        """Split-conformal (1 - epsilon) quantile with finite-sample correction."""
        n = len(self.calibration_scores)
        k = int(np.ceil((n + 1) * (1 - epsilon)))
        return float(self.calibration_scores[min(k, n) - 1])

    def survival(self, run: int) -> float:
        """Smoothed P(a live sensor's identical-reading run is at least this long)."""
        longer = len(self.run_lengths) - np.searchsorted(self.run_lengths, run, side="left")
        return (longer + 1) / (len(self.run_lengths) + 1)


LEVEL_SAMPLES = 5  # trusted level = mean of the last accepted readings


def _features(trend, hour, context, center, clip):
    hour = np.asarray(hour, dtype=float)
    ctx = np.clip(context, clip[:, 0], clip[:, 1]) - center
    return np.column_stack([trend, np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24), ctx])


def _history(x, clean, k=LEVEL_SAMPLES):
    """Level and trend of the k most recent clean readings strictly before each sample."""
    s = pd.Series(np.where(clean, x, np.nan)).dropna()
    n = len(x)
    level = s.rolling(k, min_periods=k).mean().reindex(range(n)).ffill().shift(1).to_numpy()
    trend = (s - s.shift(k - 1)).reindex(range(n)).ffill().shift(1).to_numpy()
    return level, trend


def _runs(values):
    runs, count = [], 1
    for a, b in zip(values[:-1], values[1:]):
        if a == b:
            count += 1
        else:
            runs.append(count)
            count = 1
    runs.append(count)
    return np.asarray(runs)


def fit(frame: pd.DataFrame, sensors, *, calibration_fraction: float = 0.25,
        max_gap: float = 120.0) -> dict[str, LiveGateModel]:
    """Fit one forecaster, conformal score set, and liveness model per sensor."""
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    hours = (frame.timestamp.dt.hour + frame.timestamp.dt.minute / 60).to_numpy()
    contiguous = np.r_[False, np.diff(times) <= max_gap]
    names = [s.name for s in sensors]
    clean = {}
    for s in sensors:
        x = frame[s.name].to_numpy(dtype=float)
        ok = (x > s.physical_min) & (x < s.physical_max)
        spike, _, _ = _spikes(np.where(ok, x, np.nan))
        clean[s.name] = ok & ~spike
    split = int(len(frame) * (1 - calibration_fraction))
    models = {}
    for s in sensors:
        others = tuple(n for n in names if n != s.name)
        x = frame[s.name].to_numpy(dtype=float)
        # Teacher forcing: the trusted level is built from clean readings only.
        level, trend = _history(x, clean[s.name])
        context = np.column_stack([frame[o].to_numpy(dtype=float) for o in others])
        ctx_clean = np.column_stack([np.where(clean[o], frame[o], np.nan) for o in others])
        clip = np.column_stack([np.nanpercentile(ctx_clean, 1, axis=0),
                                np.nanpercentile(ctx_clean, 99, axis=0)])
        center = np.nanmedian(ctx_clean, axis=0)
        X = _features(trend, hours, context, center, clip)
        usable = (clean[s.name] & contiguous & np.r_[False, contiguous[:-1]]
                  & np.isfinite(X).all(axis=1))
        train = usable & (np.arange(len(x)) < split)
        calib = usable & (np.arange(len(x)) >= split)
        usable &= np.isfinite(level)
        train &= usable
        calib &= usable
        # Learn the deviation from the trusted level so the persistence term is explicit.
        regressor = HuberRegressor(max_iter=500).fit(X[train], x[train] - level[train])
        residual = x - level - regressor.predict(np.nan_to_num(X))
        scale = float(np.median(np.abs(residual[train])) * 1.4826) or float(np.std(residual[train])) or 1e-6
        runs = _runs(x[:split][clean[s.name][:split]])
        models[s.name] = LiveGateModel(
            name=s.name, others=others, coef=regressor.coef_, intercept=float(regressor.intercept_),
            center=center, clip=clip, scale=scale,
            calibration_scores=np.sort(np.abs(residual[calib]) / scale),
            run_lengths=np.sort(runs), bounds=(s.physical_min, s.physical_max))
    return models


def gate(model: LiveGateModel, x, times, hours, context, *, epsilon: float,
         use_forecast: bool = True, use_liveness: bool = True, max_confirm: int = 8,
         max_gap: float = 120.0) -> np.ndarray:
    """Streaming accept/reject decisions for one sensor."""
    x = np.asarray(x, dtype=float)
    q = model.threshold(epsilon)
    accepted = np.zeros(len(x), dtype=bool)
    history = deque(maxlen=LEVEL_SAMPLES)
    run, candidate, needed = 0, [], 0
    for i, y in enumerate(x):
        if i and times[i] - times[i - 1] > max_gap:
            history.clear()
            candidate = []
        run = run + 1 if i and y == x[i - 1] else 1
        valid = np.isfinite(y) and model.bounds[0] <= y <= model.bounds[1]
        alive = not use_liveness or model.survival(run) >= epsilon
        if not (valid and alive):
            candidate = []
            continue
        if not history:
            history.append(y)
            accepted[i] = True
            continue
        if use_forecast:
            features = _features(np.array([history[-1] - history[0]]), np.array([hours[i]]),
                                 np.asarray(context[i], dtype=float)[None, :], model.center, model.clip)
            forecast = np.mean(history) + float(features[0] @ model.coef + model.intercept)
            score = abs(y - forecast) / model.scale
        else:
            score = 0.0
        if score <= q:
            history.append(y)
            accepted[i] = True
            candidate = []
            continue
        # Surprising but live: confirm a new level with readings consistent with each other.
        if candidate and abs(y - np.median(candidate)) / model.scale <= q:
            candidate.append(y)
        else:
            candidate = [y]
            needed = int(np.clip(1 + np.ceil(np.log2(score / q)), 2, max_confirm))
        if len(candidate) >= needed:
            history.clear()
            history.extend(candidate[-LEVEL_SAMPLES:])
            accepted[i] = True
            candidate = []
    return accepted
