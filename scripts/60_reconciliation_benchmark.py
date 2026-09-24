"""Frozen baseline reproduction and paired reconciliation evidence challenges."""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.reconciled_trace_replay import ReplayReconciliation, replay
from aasvr.timing_feasibility import score_and_explain

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reconciliation"
OLD = ROOT / "results/metrics/instrumented_execution"


def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [
        "src/aasvr/reconciliation.py",
        "src/aasvr/reconciliation_mock.py",
        "src/aasvr/reconciled_trace_replay.py",
        "src/aasvr/measured_trace_replay.py",
        "src/aasvr/recovery_contract.py",
        "src/aasvr/timing_feasibility.py",
        "src/aasvr/telemetry.py",
        "src/aasvr/reliable_events.py",
        "src/aasvr/execution_instrumentation.py",
        "configs/experiments/reconciliation.yaml",
        "configs/experiments/instrumented_execution.yaml",
        "configs/experiments/timing_feasibility.yaml",
        "configs/experiments/telemetry.yaml",
        "configs/methods/aasvr.yaml",
        "scripts/59_reconciliation_local.py",
        "scripts/60_reconciliation_benchmark.py",
        "scripts/61_report_reconciliation.py",
        "scripts/62_run_reconciliation.sh",
        "docs/reconciliation/PROTOCOL.md",
        "data/processed/hydro_exp1_measurements.parquet",
        "results/metrics/instrumented_execution/transactions.json",
        "results/metrics/instrumented_execution/replay_detail.csv",
    ]
    (OUT / "frozen_manifest.json").write_text(
        json.dumps(
            {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}, indent=2
        )
    )
    print("Reconciliation protocol and existing measurements frozen.", flush=True)


def verify():
    for path, digest in json.loads((OUT / "frozen_manifest.json").read_text()).items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path


def job(candidate, sensor_name):
    instrument = load_yaml(ROOT / "configs/experiments/instrumented_execution.yaml")
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    timing = load_yaml(ROOT / "configs/experiments/timing_feasibility.yaml")
    policy = load_yaml(ROOT / "configs/experiments/reconciliation.yaml")
    assert (
        policy["query_interval_seconds"],
        policy["query_attempts"],
        policy["query_horizon_seconds"],
        policy["reply_latency_seconds"],
    ) == (16, 4, 64, 16)
    helper = runpy.run_path(str(ROOT / "scripts/41_telemetry_feasibility.py"))
    times, source, values, absolute, _ = helper["load_block"]("evaluation", common)
    days = pd.to_datetime(absolute, unit="s", utc=True).strftime("%Y-%m-%d").to_numpy()
    sensor = next(
        s
        for s in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors
        if s.name == sensor_name
    )
    traces = json.loads((OLD / "transactions.json").read_text())
    rows, clusters = [], []
    for profile in instrument["profiles"]:
        trace = [r for r in traces if r["measured"] and r["profile"] == profile["name"]]
        conditions = ["blocking"]
        if candidate["stage"] != "current":
            conditions += (
                policy["conditions"] if profile["name"] == "injected_delay_loss" else ["available"]
            )
        for condition in conditions:
            for phase in instrument["trace_phases"]:
                factory = (
                    None
                    if condition == "blocking"
                    else lambda r: ReplayReconciliation(r, condition)
                )
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
                    reconciliation=factory,
                )
                scored, bad = score_and_explain(
                    times, result, common["warmup_seconds"], common["tail_seconds"]
                )
                frame = pd.DataFrame(scored)
                meta = dict(
                    candidate=candidate["name"],
                    profile=profile["name"],
                    condition=condition,
                    sensor=sensor_name,
                    phase=phase,
                )
                count = sum(
                    common["warmup_seconds"] <= o["time"] <= times[-1] - common["tail_seconds"]
                    for o in result["outputs"]
                )
                rows.append(
                    dict(
                        **meta,
                        **result["counters"],
                        opportunities=len(frame),
                        matched=int(frame.matched.sum()),
                        undesirable=bad,
                        evaluated_outputs=count,
                    )
                )
                frame["day"] = [days[int(i)] for i in frame.event_id]
                for day, g in frame.groupby("day"):
                    clusters.append(
                        dict(**meta, day=day, opportunities=len(g), matched=int(g.matched.sum()))
                    )
                for k, v in meta.items():
                    frame[k] = v
                frame.to_csv(
                    OUT
                    / "ledgers"
                    / f"{candidate['name']}_{sensor_name}_{profile['name']}_{condition}_{phase}.csv.gz",
                    index=False,
                )
    return rows, clusters


def main():
    verify()
    (OUT / "ledgers").mkdir(exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/instrumented_execution.yaml")
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    rows, clusters = [], []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(job, c, s) for c in cfg["replay_candidates"] for s in common["sensors"]
        ]
        for i, future in enumerate(as_completed(futures)):
            a, b = future.result()
            rows.extend(a)
            clusters.extend(b)
            print(f"Reconciliation benchmark jobs: {i + 1}/{len(futures)}", flush=True)
    detail = pd.DataFrame(rows).fillna(0)
    keys = ["candidate", "profile", "sensor", "phase"]
    prior = pd.read_csv(OLD / "replay_detail.csv").set_index(keys).sort_index()
    baseline = detail[detail.condition == "blocking"].set_index(keys).sort_index()
    for column in prior.columns:
        pd.testing.assert_series_equal(
            baseline[column], prior[column], check_dtype=False, check_names=False
        )
    detail.to_csv(OUT / "detail.csv", index=False)
    pd.DataFrame(clusters).to_csv(OUT / "clusters.csv", index=False)
    verify()
    print(
        f"{len(detail)} replays complete; all 270 prior baseline rows reproduced exactly.",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    freeze() if args.freeze else main()
