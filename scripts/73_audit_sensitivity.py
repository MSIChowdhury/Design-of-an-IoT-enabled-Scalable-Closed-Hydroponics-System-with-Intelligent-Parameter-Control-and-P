"""Post-hoc sensitivity of executable authorizations; no tuning or data changes."""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import resource
import time

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.reanalysis import Timing, authorize, hold_estimate
from aasvr.standin import _spikes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/sensitivity"


def source_counts(source, acted, in_range, bound, spike):
    src = source[acted]
    assert np.all(src >= 0), "An authorization has no accepted source"
    out = int((~in_range[src]).sum())
    at_bound = int((in_range[src] & bound[src]).sum())
    spiking = int((in_range[src] & ~bound[src] & spike[src]).sum())
    assert out + at_bound + spiking <= int(acted.sum())
    return out, at_bound, spiking


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("pilot", "full"), required=True)
    stage = parser.parse_args().stage
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat()
    spec = importlib.util.spec_from_file_location("deployment_audit", ROOT / "scripts/68_deployment_audit.py")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    cfg = load_yaml(audit.CONFIG)
    frame = pd.read_parquet(audit.SOURCE).sort_values("timestamp").reset_index(drop=True)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    sensors = [replace(s, control_low=cfg["setpoints"][s.name][0], control_high=cfg["setpoints"][s.name][1])
               for s in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors if s.name in cfg["sensors"]]
    persistences = (32,) if stage == "pilot" else (16, 32, 64, 96)
    ages = (64,) if stage == "pilot" else (32, 64, 128)
    rows = []
    for sensor in sensors:
        x = frame[sensor.name].to_numpy(dtype=float)
        in_range = (x >= sensor.physical_min) & (x <= sensor.physical_max)
        bound = (x == sensor.physical_min) | (x == sensor.physical_max)
        _, deviations, scale = _spikes(np.where(in_range, x, np.nan))
        for arm in ("naive", "range", "range_persistence"):
            accepted = np.isfinite(x) if arm == "naive" else in_range
            estimate, age = hold_estimate(times, x, accepted, max_gap=120)
            source = np.maximum.accumulate(np.where(accepted, np.arange(len(x)), -1))
            for persistence, max_age, cooldown in product(persistences, ages, (300, 600, 1200)):
                timing = Timing(persistence=persistence if arm == "range_persistence" else 0,
                                max_age=max_age, cooldown=cooldown, max_gap=120)
                actions = authorize(times, estimate, age <= max_age, sensor.control_low, sensor.control_high,
                                    timing, allowed_directions=audit.ACTIONABLE[sensor.name])
                acted = actions != 0
                assert np.all(age[acted] <= max_age)
                for cutoff in (6, 8, 10):
                    counts = source_counts(source, acted, in_range, bound, np.abs(deviations) > cutoff * scale)
                    rows.append({"sensor": sensor.name, "arm": arm, "grid_persistence_s": persistence,
                                 "actual_persistence_s": timing.persistence, "max_age_s": max_age,
                                 "cooldown_s": cooldown, "spike_cutoff": cutoff,
                                 "commands": int(acted.sum()), "out_of_range_commands": counts[0],
                                 "bound_commands": counts[1], "spike_commands": counts[2],
                                 "flagged_commands": sum(counts)})
    result = pd.DataFrame(rows)
    result["flagged_fraction"] = result.flagged_commands / result.commands.replace(0, np.nan)
    keys = ["sensor", "grid_persistence_s", "max_age_s", "cooldown_s", "spike_cutoff"]
    naive = result[result.arm == "naive"].set_index(keys).commands
    result["authorization_retention_vs_naive"] = result.commands.to_numpy() / naive.reindex(pd.MultiIndex.from_frame(result[keys])).to_numpy()
    original = pd.read_csv(audit.TABLE).set_index(["sensor", "arm"])
    original_arms = {"naive": "Naive threshold (experiment-1 style)", "range": "Range check",
                     "range_persistence": "Range check + 32 s persistence"}
    locked = result[(result.grid_persistence_s == 32) & (result.max_age_s == 64)
                    & (result.cooldown_s == 600) & (result.spike_cutoff == 8)]
    for row in locked.itertuples():
        expected = original.loc[(row.sensor, original_arms[row.arm])]
        for name in ("commands", "out_of_range_commands", "spike_commands", "flagged_commands"):
            assert getattr(row, name) == expected[name], f"Original setting mismatch: {row.sensor} {row.arm} {name}"
        assert row.bound_commands == expected.full_scale_commands
    OUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT / f"{stage}_cells.csv", index=False)
    result.groupby(["sensor", "arm"])[["commands", "flagged_commands", "out_of_range_commands", "bound_commands", "spike_commands", "flagged_fraction", "authorization_retention_vs_naive"]].agg(["min", "max"]).to_csv(OUT / f"{stage}_envelopes.csv")
    failures = result[(result.arm == "range_persistence") & result.sensor.isin(["pH", "EC"]) & (result.flagged_commands > 0)]
    failures.to_csv(OUT / f"{stage}_nonzero_ph_ec.csv", index=False)
    paths = [audit.SOURCE, audit.CONFIG, ROOT / "configs/methods/aasvr.yaml", Path(__file__),
             ROOT / "scripts/68_deployment_audit.py", ROOT / "src/aasvr/reanalysis.py", ROOT / "src/aasvr/standin.py",
             ROOT / "docs/research/CYCLE_02_PROTOCOL.md"]
    def hashes(paths):
        return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    report = {"stage": stage, "started_utc": started_utc, "finished_utc": datetime.now(timezone.utc).isoformat(),
              "elapsed_seconds": time.monotonic() - started, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "source_rows": len(frame), "sensors": len(sensors), "cells": len(result), "locked_cells_reproduced": len(locked),
              "nonzero_ph_ec_cells": len(failures), "randomness": "none; deterministic whole-log replay",
              "input_hashes": hashes(paths), "output_hashes": hashes(sorted(OUT.glob(f"{stage}_*.csv")))}
    (OUT / f"{stage}_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if not key.endswith("hashes")}, indent=2))


if __name__ == "__main__":
    main()
