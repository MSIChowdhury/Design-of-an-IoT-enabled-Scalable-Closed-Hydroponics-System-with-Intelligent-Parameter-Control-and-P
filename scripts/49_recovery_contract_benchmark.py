"""Freeze new recovery version and run previously unused schedules; no tuning."""

from __future__ import annotations

import hashlib
import json
import runpy
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.recovery_replay import run
from aasvr.telemetry import score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/recovery_contract"
CFG = ROOT / "configs/experiments/recovery_contract.yaml"


def job(scenario, sensor_name):
    cfg = load_yaml(CFG)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    helper = runpy.run_path(str(ROOT / "scripts/41_telemetry_feasibility.py"))
    times, source, values, absolute, _ = helper["load_block"]("evaluation", common)
    days = pd.to_datetime(absolute, unit="s", utc=True).strftime("%Y-%m-%d").to_numpy()
    sensor = next(
        s
        for s in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors
        if s.name == sensor_name
    )
    rows, clusters = [], []
    for seed in cfg["seeds"]:
        for policy in cfg["policies"]:
            result = run(
                times,
                source,
                values[sensor_name],
                sensor.control_low,
                sensor.control_high,
                scenario,
                policy,
                cfg,
                cfg["seed"] + seed,
            )
            scored = score(
                times,
                result["reference"],
                result["actions"],
                result["directions"],
                64,
                common["warmup_seconds"],
                common["tail_seconds"],
            )
            meta = dict(
                scenario=scenario["name"],
                in_contract=scenario.get("in_contract", True),
                sensor=sensor_name,
                seed=seed,
                policy=policy,
            )
            rows.append(
                {
                    **meta,
                    **{k: v for k, v in result.items() if np.isscalar(v)},
                    **{k: v for k, v in scored.items() if np.isscalar(v)},
                }
            )
            for day in np.unique(days):
                mask = days == day
                clusters.append(
                    {
                        **meta,
                        "day": day,
                        "opportunities": int(scored["reference_mask"][mask].sum()),
                        "matched": int(scored["matched_mask"][mask].sum()),
                        "undesirable": int(
                            (scored["wrong_mask"][mask] | scored["unnecessary_mask"][mask]).sum()
                        ),
                    }
                )
    return rows, clusters


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(CFG)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    files = [
        "configs/experiments/recovery_contract.yaml",
        "configs/experiments/telemetry.yaml",
        "configs/methods/aasvr.yaml",
        "src/aasvr/recovery_contract.py",
        "src/aasvr/recovery_replay.py",
        "src/aasvr/delivery_challenge.py",
        "src/aasvr/reliable_events.py",
        "src/aasvr/telemetry.py",
        "scripts/49_recovery_contract_benchmark.py",
        "scripts/50_recovery_crash_probe.py",
        "scripts/51_report_recovery_contract.py",
        "data/processed/hydro_exp1_measurements.parquet",
    ]
    (OUT / "frozen_manifest.json").write_text(
        json.dumps(
            dict(
                config=cfg,
                sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
            ),
            indent=2,
        )
    )
    print("Recovery contract and new challenge frozen before execution.", flush=True)
    rows, clusters = [], []
    with ProcessPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(job, c, s) for c in cfg["scenarios"] for s in common["sensors"]]
        for i, future in enumerate(as_completed(jobs)):
            a, b = future.result()
            rows.extend(a)
            clusters.extend(b)
            if (i + 1) % 6 == 0:
                print(f"Recovery benchmark: {i + 1}/{len(jobs)} jobs", flush=True)
    pd.DataFrame(rows).sort_values(["scenario", "sensor", "seed", "policy"]).to_csv(
        OUT / "detail.csv", index=False
    )
    pd.DataFrame(clusters).sort_values(["scenario", "sensor", "seed", "policy", "day"]).to_csv(
        OUT / "clusters.csv", index=False
    )


if __name__ == "__main__":
    main()
