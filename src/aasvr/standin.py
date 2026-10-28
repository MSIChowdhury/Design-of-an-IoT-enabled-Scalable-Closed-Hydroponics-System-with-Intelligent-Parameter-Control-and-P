"""Synthetic stand-in for the request-only hydroponic sensor log.

The generator is fitted to aggregate statistics only (hour-of-day medians,
lag-1 residual dynamics, quantization, spike/gap rates). It reproduces the
shape of the deployment feed so the pipeline runs end to end; it is not the
measured data and must not be used for reported results.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CADENCE_SECONDS = 16.0
SPIKE_SCALE = 8.0  # robust z threshold on deviation from a 9-sample median


def _clean(x, low, high):
    x = np.asarray(x, dtype=float)
    return np.where((x >= low) & (x <= high), x, np.nan)


def _spikes(x):
    s = pd.Series(x)
    deviation = s - s.rolling(9, center=True, min_periods=3).median()
    mad = np.nanmedian(np.abs(deviation - np.nanmedian(deviation))) * 1.4826
    if not np.isfinite(mad) or mad == 0:
        mad = np.nanstd(deviation) or 1.0
    return (np.abs(deviation) > SPIKE_SCALE * mad).to_numpy(), deviation.to_numpy(), mad


def fit_profile(frame: pd.DataFrame, ranges: dict[str, tuple[float, float]]) -> dict:
    """Aggregate per-channel statistics; no sample-level values are retained."""
    frame = frame.sort_values("timestamp")
    t = frame.timestamp.astype("int64").to_numpy() / 1e9
    dt = np.diff(t)
    long_gaps = dt[dt > 120]
    profile = {"rows": int(len(frame)), "span_seconds": float(t[-1] - t[0]),
               "gap_rate_per_sample": float(len(long_gaps) / max(len(dt), 1)),
               "gap_log_mean": float(np.log(long_gaps).mean()) if len(long_gaps) else 0.0,
               "gap_log_sd": float(np.log(long_gaps).std()) if len(long_gaps) else 0.0,
               "channels": {}}
    hours = frame.timestamp.dt.hour.to_numpy()
    for name, (low, high) in ranges.items():
        raw = frame[name].to_numpy(dtype=float)
        x = _clean(raw, low, high)
        flagged, deviation, _ = _spikes(x)
        base = np.where(flagged, np.nan, x)
        hourly = pd.Series(base).groupby(hours).median().reindex(range(24)).interpolate(limit_direction="both")
        residual = base - hourly.to_numpy()[hours]
        r = residual[np.isfinite(residual)]
        r0, r1 = residual[:-1], residual[1:]
        ok = np.isfinite(r0) & np.isfinite(r1)
        phi = float(np.clip(np.corrcoef(r0[ok], r1[ok])[0, 1], 0, 0.9995)) if ok.sum() > 10 else 0.0
        steps = np.abs(np.diff(np.unique(np.round(x[np.isfinite(x)], 6))))
        profile["channels"][name] = {
            "hourly_median": [float(v) for v in hourly],
            # Robust spread so rare long excursions do not widen the whole feed.
            "residual_sd": float(np.subtract(*np.percentile(r, [75, 25])) / 1.349) if len(r) else 0.0,
            "phi": phi,
            "quantum": float(np.min(steps[steps > 0])) if np.any(steps > 0) else 0.0,
            "clip": [float(np.nanmin(x)), float(np.nanmax(x))],
            "spike_rate": float(np.nanmean(flagged)),
            "spike_abs_median": float(np.nanmedian(np.abs(deviation[flagged]))) if flagged.any() else 0.0,
            "out_of_range_rate": float(np.mean(~np.isnan(raw) & np.isnan(x))),
        }
    return profile


def generate(profile: dict, seed: int = 0, start="2024-01-01T00:00:00Z") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = profile["rows"]
    dt = np.full(n - 1, CADENCE_SECONDS)
    gaps = rng.random(n - 1) < profile["gap_rate_per_sample"]
    dt[gaps] = np.exp(rng.normal(profile["gap_log_mean"], profile["gap_log_sd"], gaps.sum())).clip(121)
    seconds = np.r_[0.0, np.cumsum(dt)]
    timestamp = pd.Timestamp(start) + pd.to_timedelta(seconds, unit="s")
    hours = timestamp.hour.to_numpy()
    out = {"timestamp": timestamp, "entry_id": np.arange(1, n + 1)}
    for name, c in profile["channels"].items():
        phi, sd = c["phi"], c["residual_sd"]
        innovation = rng.normal(0, sd * np.sqrt(1 - phi ** 2), n)
        noise = np.empty(n)
        noise[0] = rng.normal(0, sd)
        for i in range(1, n):
            noise[i] = phi * noise[i - 1] + innovation[i]
        x = np.asarray(c["hourly_median"])[hours] + noise
        x = np.clip(x, *c["clip"])
        if c["quantum"] > 0:
            x = np.round(x / c["quantum"]) * c["quantum"]
        spikes = rng.random(n) < c["spike_rate"]
        x[spikes] += rng.choice([-1, 1], spikes.sum()) * c["spike_abs_median"] * rng.lognormal(0, .5, spikes.sum())
        wild = rng.random(n) < c["out_of_range_rate"]
        x[wild] = c["clip"][1] * rng.uniform(2, 50, wild.sum())
        out[name] = x
    return pd.DataFrame(out)


def summary(frame: pd.DataFrame, ranges: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """Aggregate statistics used to compare the stand-in with the source feed."""
    t = frame.timestamp.astype("int64").to_numpy() / 1e9
    rows = []
    for name, (low, high) in ranges.items():
        raw = frame[name].to_numpy(dtype=float)
        x = _clean(raw, low, high)
        flagged, _, _ = _spikes(x)
        a, b = x[:-1], x[1:]
        ok = np.isfinite(a) & np.isfinite(b)
        rows.append({"sensor": name, "rows": len(frame), "median": np.nanmedian(x),
                     "iqr": np.subtract(*np.nanpercentile(x, [75, 25])),
                     "lag1_autocorrelation": np.corrcoef(a[ok], b[ok])[0, 1] if ok.sum() > 10 else np.nan,
                     "spike_rate": np.nanmean(flagged), "out_of_range_rate": np.mean(~np.isnan(raw) & np.isnan(x)),
                     "gaps_above_120_s": int((np.diff(t) > 120).sum())})
    return pd.DataFrame(rows)
