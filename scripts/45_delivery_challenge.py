"""Run a frozen, stronger-baseline challenge. No tuning stage exists here."""

from __future__ import annotations

import hashlib
import json
import runpy
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.delivery_challenge import assumption_checks, delivery_for, replay, scenarios
from aasvr.telemetry import Controller, direction, score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/delivery_challenge"
CFG = ROOT / "configs/experiments/delivery_challenge.yaml"


def job(challenge, sensor_name):
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
            result = replay(
                times,
                source,
                values[sensor_name],
                sensor.control_low,
                sensor.control_high,
                challenge,
                delivery_for(policy, cfg),
                cfg["seed"] + seed,
            )
            scored = score(
                times,
                result["reference"],
                result["actions"],
                result["directions"],
                cfg["deadline_seconds"],
                common["warmup_seconds"],
                common["tail_seconds"],
            )
            meta = dict(scenario=challenge.name, sensor=sensor_name, seed=seed, policy=policy)
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


def probe_windows(common, cfg):
    helper = runpy.run_path(str(ROOT / "scripts/41_telemetry_feasibility.py"))
    times, source, values, absolute, _ = helper["load_block"]("evaluation", common)
    n = int(cfg["probe"]["duration_seconds"] / common["controller_tick_seconds"])
    streams, metadata = {}, []
    for sensor in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors:
        if sensor.name not in common["sensors"]:
            continue
        v = values[sensor.name]
        directions = np.array(
            [
                direction(x, sensor.control_low, sensor.control_high)
                if times[i] - source[i] <= 120
                else 0
                for i, x in enumerate(v)
            ]
        )
        # Select before protocol execution: most direction transitions among fixed windows
        # containing a reference action; earliest tie. This is a purposive execution probe.
        candidates = []
        for start in range(0, len(times) - n, n):
            c = Controller()
            refs = [c.step(j * 16, int(d)) for j, d in enumerate(directions[start : start + n])]
            if any(refs):
                changes = np.count_nonzero(np.diff(directions[start : start + n]))
                candidates.append((-changes, start))
        _, start = min(candidates)
        streams[sensor.name] = {
            "values": v[start : start + n].tolist(),
            "source": (source[start : start + n] - times[start]).tolist(),
            "low": sensor.control_low,
            "high": sensor.control_high,
        }
        metadata.append(
            dict(
                sensor=sensor.name,
                source_start=float(absolute[start]),
                transitions=int(np.count_nonzero(np.diff(directions[start : start + n]))),
            )
        )
    (OUT / "probe_input.json").write_text(
        json.dumps(dict(tick=16, streams=streams, metadata=metadata))
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(CFG)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    files = [
        "configs/experiments/delivery_challenge.yaml",
        "configs/experiments/telemetry.yaml",
        "configs/methods/aasvr.yaml",
        "src/aasvr/delivery_challenge.py",
        "src/aasvr/reliable_events.py",
        "src/aasvr/telemetry.py",
        "scripts/45_delivery_challenge.py",
        "scripts/46_delivery_network_probe.py",
        "scripts/47_report_delivery_challenge.py",
        "data/processed/hydro_exp1_measurements.parquet",
    ]
    manifest = dict(
        config=cfg,
        scenarios=[asdict(c) for c in scenarios(cfg)],
        sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
    )
    (OUT / "frozen_manifest.json").write_text(json.dumps(manifest, indent=2))
    probe_windows(common, cfg)
    (OUT / "assumption_checks.json").write_text(json.dumps(assumption_checks(), indent=2))
    print(
        "Protocol, scenarios, source fingerprints and probe windows frozen before execution.",
        flush=True,
    )
    rows, clusters = [], []
    with ProcessPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(job, c, s) for c in scenarios(cfg) for s in common["sensors"]]
        for i, future in enumerate(as_completed(tasks)):
            a, b = future.result()
            rows.extend(a)
            clusters.extend(b)
            if (i + 1) % 6 == 0:
                print(f"Challenge: {i + 1}/{len(tasks)} jobs complete", flush=True)
    pd.DataFrame(rows).sort_values(["scenario", "sensor", "seed", "policy"]).to_csv(
        OUT / "detail.csv", index=False
    )
    pd.DataFrame(clusters).sort_values(["scenario", "sensor", "seed", "policy", "day"]).to_csv(
        OUT / "clusters.csv", index=False
    )
    print("Frozen challenge completed.", flush=True)


if __name__ == "__main__":
    main()
