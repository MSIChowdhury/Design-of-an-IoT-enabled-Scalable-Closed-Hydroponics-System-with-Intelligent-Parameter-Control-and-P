"""Frozen component/scheduling grid; full per-command ledgers, no tuning."""

from __future__ import annotations

import hashlib
import json
import runpy
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.timing_feasibility import replay, score_and_explain, variants

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/timing_feasibility"
CFG = ROOT / "configs/experiments/timing_feasibility.yaml"


def job(variant, sensor_name):
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
    summaries, clusters, ledgers, examples = [], [], [], []
    for scenario in cfg["scenarios"]:
        for seed in cfg["seeds"]:
            result = replay(
                times,
                source,
                values[sensor_name],
                sensor.control_low,
                sensor.control_high,
                scenario,
                variant,
                cfg,
                cfg["seed"] + seed,
            )
            rows, undesirable = score_and_explain(
                times, result, common["warmup_seconds"], common["tail_seconds"]
            )
            meta = dict(**variant, scenario=scenario["name"], sensor=sensor_name, seed=seed)
            frame = pd.DataFrame(rows)
            for k, v in meta.items():
                frame[k] = v
            frame["day"] = [days[int(i)] for i in frame.event_id]
            summaries.append(
                dict(
                    **meta,
                    **result["counters"],
                    opportunities=len(rows),
                    matched=int(frame.matched.sum()),
                    undesirable=undesirable,
                )
            )
            # Match attribution is anchored on the reference day. Undesirable outputs
            # are anchored on their actual output day, retaining paired sensor/seed cells.
            bad_by_day = {}
            for o in result["outputs"]:
                if common["warmup_seconds"] <= o["time"] <= times[-1] - common["tail_seconds"]:
                    i = np.searchsorted(times, o["time"], side="right") - 1
                    if result["directions"][i] == 0 or result["directions"][i] != o["action"]:
                        bad_by_day[days[i]] = bad_by_day.get(days[i], 0) + 1
            for day, g in frame.groupby("day"):
                clusters.append(
                    dict(
                        **meta,
                        day=day,
                        opportunities=len(g),
                        matched=int(g.matched.sum()),
                        undesirable=bad_by_day.get(day, 0),
                    )
                )
            ledgers.append(frame)
            # Earliest case per reason, rather than selecting visually favorable cases.
            for reason, g in frame.groupby("reason", sort=True):
                row = g.iloc[0].to_dict()
                start = row["created"] - 64
                stop = row["created"] + 96
                mask = (times >= start) & (times <= stop)
                examples.append(
                    dict(
                        **meta,
                        reason=reason,
                        command=row,
                        times=times[mask].tolist(),
                        values=values[sensor_name][mask].tolist(),
                        directions=result["directions"][mask].tolist(),
                        reference=result["reference"][mask].tolist(),
                        outputs=[o for o in result["outputs"] if start <= o["time"] <= stop],
                    )
                )
    pd.concat(ledgers, ignore_index=True).to_csv(
        OUT / "ledgers" / f"{variant['variant']}_{sensor_name}.csv.gz", index=False
    )
    (OUT / "examples" / f"{variant['variant']}_{sensor_name}.json").write_text(json.dumps(examples))
    return summaries, clusters


def main():
    for p in (OUT, OUT / "ledgers", OUT / "examples"):
        p.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(CFG)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    files = [
        "configs/experiments/timing_feasibility.yaml",
        "configs/experiments/telemetry.yaml",
        "configs/methods/aasvr.yaml",
        "src/aasvr/timing_feasibility.py",
        "src/aasvr/recovery_contract.py",
        "src/aasvr/reliable_events.py",
        "src/aasvr/telemetry.py",
        "src/aasvr/delivery_challenge.py",
        "scripts/52_timing_feasibility.py",
        "scripts/53_report_timing_feasibility.py",
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
    print("Frozen timing sensitivity grid; no deployment setting will be selected.", flush=True)
    rows, clusters = [], []
    with ProcessPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(job, v, s) for v in variants(cfg) for s in common["sensors"]]
        for i, future in enumerate(as_completed(tasks)):
            a, b = future.result()
            rows.extend(a)
            clusters.extend(b)
            if (i + 1) % 6 == 0:
                print(f"Timing study: {i + 1}/{len(tasks)} jobs complete", flush=True)
    pd.DataFrame(rows).sort_values(["variant", "scenario", "sensor", "seed"]).to_csv(
        OUT / "detail.csv", index=False
    )
    pd.DataFrame(clusters).sort_values(["variant", "scenario", "sensor", "seed", "day"]).to_csv(
        OUT / "clusters.csv", index=False
    )


if __name__ == "__main__":
    main()
