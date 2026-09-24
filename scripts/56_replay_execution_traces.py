"""Replay frozen candidates with repeated, paired local measurement traces."""

from __future__ import annotations

import hashlib
import json
import runpy
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.measured_trace_replay import replay
from aasvr.timing_feasibility import score_and_explain

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/instrumented_execution"


def verify_manifest():
    manifest = json.loads((OUT / "frozen_manifest.json").read_text())
    for path, expected in manifest["sha256"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Frozen input changed: {path}")


def job(candidate, sensor_name):
    cfg = load_yaml(ROOT / "configs/experiments/instrumented_execution.yaml")
    timing = load_yaml(ROOT / "configs/experiments/timing_feasibility.yaml")
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    helper = runpy.run_path(str(ROOT / "scripts/41_telemetry_feasibility.py"))
    times, source, values, absolute, _ = helper["load_block"]("evaluation", common)
    days = pd.to_datetime(absolute, unit="s", utc=True).strftime("%Y-%m-%d").to_numpy()
    sensor = next(
        s
        for s in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors
        if s.name == sensor_name
    )
    traces = json.loads((OUT / "transactions.json").read_text())
    summaries, clusters = [], []
    for profile in cfg["profiles"]:
        trace = [r for r in traces if r["profile"] == profile["name"] and r["measured"]]
        for phase in cfg["trace_phases"]:
            result = replay(
                times,
                source,
                values[sensor_name],
                sensor.control_low,
                sensor.control_high,
                trace,
                candidate,
                timing,
                phase,
            )
            rows, undesirable = score_and_explain(
                times, result, common["warmup_seconds"], common["tail_seconds"]
            )
            frame = pd.DataFrame(rows)
            meta = dict(
                candidate=candidate["name"],
                sensor=sensor_name,
                profile=profile["name"],
                phase=phase,
            )
            frame["day"] = [days[int(i)] for i in frame.event_id]
            evaluated_outputs = sum(
                common["warmup_seconds"] <= o["time"] <= times[-1] - common["tail_seconds"]
                for o in result["outputs"]
            )
            summaries.append(
                dict(
                    **meta,
                    **result["counters"],
                    opportunities=len(rows),
                    matched=int(frame.matched.sum()),
                    undesirable=undesirable,
                    evaluated_outputs=evaluated_outputs,
                )
            )
            for day, group in frame.groupby("day"):
                clusters.append(
                    dict(
                        **meta, day=day, opportunities=len(group), matched=int(group.matched.sum())
                    )
                )
            for key, value in meta.items():
                frame[key] = value
            frame.to_csv(
                OUT
                / "ledgers"
                / f"{candidate['name']}_{sensor_name}_{profile['name']}_{phase}.csv.gz",
                index=False,
            )
    return summaries, clusters


def main():
    verify_manifest()
    (OUT / "ledgers").mkdir(exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/instrumented_execution.yaml")
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    summaries, clusters = [], []
    with ProcessPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(job, c, s) for c in cfg["replay_candidates"] for s in common["sensors"]]
        for i, future in enumerate(as_completed(jobs)):
            a, b = future.result()
            summaries.extend(a)
            clusters.extend(b)
            print(f"Trace replay jobs: {i + 1}/{len(jobs)}", flush=True)
    pd.DataFrame(summaries).sort_values(["candidate", "profile", "sensor", "phase"]).to_csv(
        OUT / "replay_detail.csv", index=False
    )
    pd.DataFrame(clusters).to_csv(OUT / "replay_clusters.csv", index=False)
    verify_manifest()


if __name__ == "__main__":
    main()
