"""Fault-to-actuation audit of the measured experiment-2 log.

Replays the deployed threshold control law (setpoints, 10-min cooldown, and only
the directions the deployed actuators can execute) on the unmodified log under six gating arms and counts commands triggered by certain
faults (out-of-range or exactly-full-scale readings) and by isolated spikes.
Also reports time in band per controlled channel. No synthetic faults.

The deployed error-resilience rule is reconstructed from the original system
description (sensing-reliability gate, 50-rejection reset, repeatability count)
with its published gamma = 0.75 beta values; xi and psi are re-estimated on the
development period because the experiment-1 data they came from is unavailable.
The liveness arm uses the LiveGate run-length model fitted on the development
period; the large CO2 full-scale episodes lie in that period but were excluded
from fitting by the declared-bound rule. Run in Docker.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr import livegate
from aasvr.config import load_aasvr_config, load_yaml
from aasvr.reanalysis import Timing, authorize, hold_estimate
from aasvr.standin import _spikes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/hydro_exp1_measurements.parquet"
CONFIG = ROOT / "configs/experiments/livegate.yaml"
TABLE = ROOT / "results/tables/deployment_audit.csv"
BAND = ROOT / "results/tables/deployment_time_in_band.csv"
# Published gamma = 0.75 beta values of the deployed error-resilience rule.
DEPLOYED_BETA = {"EC": 0.0002, "pH": 0.0005, "Air_Temp": 0.0022, "Water_Temp": 0.0009, "CO2": 0.0010}
PERSISTENCE = 32.0
# Directions the deployed actuators can execute: +1 raises the quantity, -1 lowers it.
# pH (acid/base) and EC (nutrient/water) are two-sided; CO2 is injection only;
# water and air temperature are cooling only.
ACTIONABLE = {"pH": (1, -1), "EC": (1, -1), "CO2": (1,), "Water_Temp": (-1,), "Air_Temp": (-1,)}
LIVENESS_EPSILON = 0.05


def deployed_rule(x, beta, xi, psi):
    """Accepted readings of the reconstructed sensing loop plus its repeatability count."""
    accepted = np.zeros(len(x), dtype=bool)
    trusted, rejections = np.nan, 0
    for i, y in enumerate(x):
        if not np.isfinite(y):
            continue
        if not np.isfinite(trusted) or abs(y - trusted) <= (1 + beta) * xi or rejections >= 50:
            trusted, rejections = y, 0
            accepted[i] = True
        else:
            rejections += 1
    return accepted, psi


def liveness(model, x, epsilon):
    accepted = np.zeros(len(x), dtype=bool)
    run = 0
    for i, y in enumerate(x):
        run = run + 1 if i and y == x[i - 1] else 1
        accepted[i] = model.survival(run) >= epsilon
    return accepted


def main():
    cfg = load_yaml(CONFIG)
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = [replace(s, control_low=cfg["setpoints"][s.name][0], control_high=cfg["setpoints"][s.name][1])
               for s in base.sensors if s.name in cfg["sensors"]]
    frame = pd.read_parquet(SOURCE).sort_values("timestamp").reset_index(drop=True)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    development = frame[times < times[0] + cfg["split_fractions"][0] * (times[-1] - times[0])]
    models = livegate.fit(development, sensors, calibration_fraction=cfg["livegate"]["calibration_fraction"],
                          max_gap=cfg["max_gap_seconds"])
    timing = Timing(cooldown=cfg["cooldown_seconds"], max_gap=cfg["max_gap_seconds"], max_age=64.0)
    rows, band_rows = [], []
    for s in sensors:
        x = frame[s.name].to_numpy(dtype=float)
        in_range = (x >= s.physical_min) & (x <= s.physical_max)
        full_scale = (x == s.physical_max) | (x == s.physical_min)
        spike, _, _ = _spikes(np.where(in_range, x, np.nan))
        certain = ~in_range | full_scale
        valid = x[in_range & ~full_scale]
        band_rows.append({"sensor": s.name, "setpoint_low": s.control_low, "setpoint_high": s.control_high,
                          "fraction_in_band": float(np.mean((valid >= s.control_low) & (valid <= s.control_high))),
                          "fraction_below": float(np.mean(valid < s.control_low)),
                          "fraction_above": float(np.mean(valid > s.control_high)),
                          "median": float(np.median(valid))})
        dev = development[s.name].to_numpy(dtype=float)
        dev = dev[(dev >= s.physical_min) & (dev < s.physical_max)]
        xi = np.sum(np.abs(np.diff(dev))) / len(dev)
        within = np.abs(np.diff(dev)) <= 2 * xi
        edges = np.diff(np.r_[0, within.astype(int), 0])
        psi = int(np.floor(np.mean(np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1))))
        deployed, _ = deployed_rule(x, DEPLOYED_BETA[s.name], xi, psi)
        alive = liveness(models[s.name], x, LIVENESS_EPSILON)
        arms = {
            "Naive threshold (experiment-1 style)": (np.isfinite(x), 0.0),
            "Range check": (in_range, 0.0),
            "Range check + 32 s persistence": (in_range, PERSISTENCE),
            "Deployed rule, reconstructed (experiment 2)": (deployed, psi * 16.0),
            "Range + persistence + liveness": (in_range & alive, PERSISTENCE),
            "Range + persistence + full-scale rejection": (in_range & ~full_scale, PERSISTENCE),
        }
        for arm, (accepted, persistence) in arms.items():
            estimate, age = hold_estimate(times, x, accepted, max_gap=timing.max_gap)
            actions = authorize(times, estimate, age <= timing.max_age, s.control_low, s.control_high,
                                replace(timing, persistence=persistence))
            acted = np.isin(actions, ACTIONABLE[s.name])
            # Attribute each command to the reading that supplied its held estimate.
            source = np.maximum.accumulate(np.where(accepted, np.arange(len(x)), -1))
            src = source[acted]
            rows.append({"sensor": s.name, "arm": arm, "commands": int(acted.sum()),
                         "certain_fault_commands": int(certain[src].sum()),
                         "spike_commands": int((spike[src] & ~certain[src]).sum()),
                         "persistence_seconds": persistence,
                         "xi": xi if "Deployed" in arm else np.nan,
                         "psi": psi if "Deployed" in arm else np.nan})
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows)
    table["fault_command_fraction"] = (table.certain_fault_commands + table.spike_commands) / table.commands
    table.to_csv(TABLE, index=False, float_format="%.5g")
    pd.DataFrame(band_rows).to_csv(BAND, index=False, float_format="%.4g")
    pd.set_option("display.width", 200)
    print(table.to_string(index=False))
    print(pd.DataFrame(band_rows).to_string(index=False))


if __name__ == "__main__":
    main()
