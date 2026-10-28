"""Characterize faults that actually occur in the 30-day deployment log.

Counts out-of-physical-range readings, isolated spikes, flat-line runs,
time at the in-range ceiling, and logging gaps per sensor, plus a sensor-by-day
event heatmap. Descriptive only: no labels are inferred. Run in Docker.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.standin import _spikes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/hydro_exp1_measurements.parquet"
TABLE = ROOT / "results/tables/real_fault_characterization.csv"
DAILY = ROOT / "results/metrics/real_fault_daily_events.csv"
FIG = ROOT / "results/figures/real_fault_heatmap"
SENSORS = ("EC", "pH", "Humidity", "Air_Temp", "Water_Temp", "CO2")
FLATLINE_SECONDS = 3600
GAP_SECONDS = 120
# Sequential blue ramp (steps 100 -> 650) from the shared chart palette.
RAMP = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#104281"]


def flatlines(values, times):
    """Runs of identical in-range readings lasting at least FLATLINE_SECONDS."""
    runs, start = [], 0
    for i in range(1, len(values) + 1):
        if i == len(values) or values[i] != values[start] or times[i] - times[i - 1] > GAP_SECONDS:
            if np.isfinite(values[start]) and times[i - 1] - times[start] >= FLATLINE_SECONDS:
                runs.append((start, i))
            start = i
    return runs


def main():
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    ranges = {s.name: (s.physical_min, s.physical_max) for s in base.sensors if s.name in SENSORS}
    frame = pd.read_parquet(SOURCE).sort_values("timestamp").reset_index(drop=True)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    dt = np.diff(times)
    day = frame.timestamp.dt.date.astype(str).to_numpy()
    rows, events = [], {}
    for name in SENSORS:
        low, high = ranges[name]
        raw = frame[name].to_numpy(dtype=float)
        in_range = (raw >= low) & (raw <= high)
        x = np.where(in_range, raw, np.nan)
        spike, _, _ = _spikes(x)
        runs = flatlines(x, times)
        flat = np.zeros(len(x), dtype=bool)
        for a, b in runs:
            flat[a:b] = True
        ceiling = np.nanmax(x)
        mode = pd.Series(x).mode().iloc[0]
        rows.append({
            "sensor": name, "samples": len(raw), "missing": int(np.isnan(raw).sum()),
            "out_of_range": int((~in_range & ~np.isnan(raw)).sum()),
            "max_out_of_range_value": float(raw[~in_range].max()) if (~in_range).any() else np.nan,
            "isolated_spikes": int(spike.sum()),
            "flatline_runs_ge_1h": len(runs),
            "longest_flatline_hours": max(((times[b - 1] - times[a]) / 3600 for a, b in runs), default=0.0),
            "fraction_in_flatline": float(flat.mean()),
            "in_range_ceiling": float(ceiling), "fraction_at_ceiling": float(np.mean(x == ceiling)),
            "most_frequent_value": float(mode), "fraction_at_most_frequent": float(np.mean(x == mode)),
        })
        # One event per anomalous sample; flat-lines count once per run.
        flags = (~in_range & ~np.isnan(raw)) | spike
        counts = pd.Series(flags).groupby(day).sum()
        starts = pd.Series(np.zeros(len(x), dtype=int))
        for a, _ in runs:
            starts.iloc[a] = 1
        events[name] = counts + starts.groupby(day).sum()
    table = pd.DataFrame(rows)
    gaps = dt[dt > GAP_SECONDS]
    table["gaps_above_120_s"] = len(gaps)
    table["longest_gap_hours"] = gaps.max() / 3600 if len(gaps) else 0.0
    table["fraction_time_in_gaps"] = gaps.sum() / (times[-1] - times[0])
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE, index=False, float_format="%.5g")
    daily = pd.DataFrame(events).T
    daily.to_csv(DAILY)
    print(table.T.to_string(header=False))
    plot(daily)


def plot(daily):
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 2.8))
    shown = daily.replace(0, np.nan)
    cmap = LinearSegmentedColormap.from_list("blue", RAMP)
    cmap.set_bad("#f0efec")
    image = ax.imshow(shown.to_numpy(dtype=float), aspect="auto", cmap=cmap,
                      norm=LogNorm(vmin=1, vmax=max(np.nanmax(shown.to_numpy(dtype=float)), 2)))
    ax.set_yticks(range(len(daily.index)), [s.replace("_", " ") for s in daily.index])
    labels = [d[5:] for d in daily.columns]
    step = max(len(labels) // 10, 1)
    ax.set_xticks(range(0, len(labels), step), labels[::step], fontsize=8)
    ax.set_xlabel("Deployment day (month-day, UTC); gray = no detected events")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    bar = fig.colorbar(image, ax=ax, pad=.01)
    bar.set_label("Fault events / day (log)")
    ax.set_title("Out-of-range readings, isolated spikes, and ≥1 h flat-line onsets in the deployment log",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(FIG.with_suffix(".pdf"))
    fig.savefig(FIG.with_suffix(".png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
