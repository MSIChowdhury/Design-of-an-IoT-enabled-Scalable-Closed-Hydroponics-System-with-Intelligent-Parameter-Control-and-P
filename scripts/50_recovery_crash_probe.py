"""Actual SIGKILL/reopen tests on disk-backed journals and a durable mock output log."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_yaml
from aasvr.recovery_contract import Journal, RecoveryReceiver
from aasvr.telemetry import pack

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/recovery_contract"


def command(event_id, created):
    return pack(dict(kind="command", id=event_id, rev=0, created=created, source=created, action=1))


def heartbeat(now):
    return pack(dict(kind="heartbeat", created=now, source=now))


def append_output(path, m):
    with open(path, "a") as f:
        f.write(json.dumps(m) + "\n")
        f.flush()
        os.fsync(f.fileno())


def child(directory, stage):
    p = Path(directory)
    journal = Journal(p / "state.sqlite")
    receiver = RecoveryReceiver(journal, 0)
    receiver.receive(heartbeat(32), 32)

    def hook(point):
        if point == stage:
            os.kill(os.getpid(), signal.SIGKILL)

    hook("before_receive")
    receiver.receive(command(1, 32), 32)
    hook("after_accept")
    receiver.step(48, lambda m: append_output(p / "outputs.jsonl", m), hook)
    raise AssertionError("Crash hook was not reached")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/recovery_contract.yaml")
    rows = []
    with tempfile.TemporaryDirectory(prefix="recovery-contract-") as directory:
        root = Path(directory)
        for stage in cfg["crash_stages"]:
            for trial in range(cfg["crash_trials_per_stage"]):
                p = root / f"{stage}_{trial}"
                p.mkdir()
                result = subprocess.run(
                    [sys.executable, __file__, "--child", str(p), "--stage", stage],
                    capture_output=True,
                )
                assert result.returncode == -signal.SIGKILL, result.stderr.decode()
                j = Journal(p / "state.sqlite")
                recovered = RecoveryReceiver(j, 64)
                state = recovered.state.copy()
                # Identical old command cannot be executed after reboot.
                recovered.receive(command(1, 32), 80)
                recovered.step(80, lambda m: append_output(p / "outputs.jsonl", m))
                # A much later new command remains blocked if execution is unknown.
                recovered.receive(heartbeat(800), 800)
                recovered.receive(command(2, 800), 800)
                recovered.step(832, lambda m: append_output(p / "outputs.jsonl", m))
                lines = (
                    [json.loads(s) for s in (p / "outputs.jsonl").read_text().splitlines()]
                    if (p / "outputs.jsonl").exists()
                    else []
                )
                ids = [m["id"] for m in lines]
                unknown = stage in ("after_reserve", "after_output")
                expected_old = int(stage in ("after_output", "after_commit"))
                passed = (
                    ids.count(1) == expected_old
                    and ids.count(2) == int(not unknown)
                    and state["blocked"] == unknown
                )
                rows.append(
                    dict(
                        stage=stage,
                        trial=trial,
                        sigkill=True,
                        recovered_status=state["status"],
                        uncertain=unknown,
                        old_outputs=ids.count(1),
                        new_outputs=ids.count(2),
                        passed=passed,
                    )
                )
                j.close()
        # Disk-backed reserve/output/commit latency, each trial a fresh journal.
        latencies = []
        for trial in range(110):
            p = root / f"timing_{trial}"
            p.mkdir()
            j = Journal(p / "state.sqlite")
            r = RecoveryReceiver(j, 0)
            r.receive(heartbeat(32), 32)
            r.receive(command(1, 32), 32)
            before = time.perf_counter()
            r.step(48, lambda m: append_output(p / "outputs.jsonl", m))
            elapsed = time.perf_counter() - before
            assert elapsed < cfg["dispatch_bound"], (
                "Measured adapter/commit path exceeded declared bound"
            )
            if trial >= 10:
                latencies.append(elapsed * 1000)
            j.close()
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "crash_probe.csv", index=False)
    (OUT / "journal_latency.json").write_text(
        json.dumps(
            dict(
                samples=len(latencies),
                warmup=10,
                median_ms=float(np.median(latencies)),
                p95_ms=float(np.quantile(latencies, 0.95)),
                p99_ms=float(np.quantile(latencies, 0.99)),
                max_ms=max(latencies),
                hardware=list(os.uname()),
                python=sys.version,
                scope="disk SQLite FULL + fsynced mock output file; not physical actuator execution",
            ),
            indent=2,
        )
    )
    assert frame.passed.all(), frame.to_string()
    print(f"Actual SIGKILL/reopen cases passed: {frame.passed.sum()}/{len(frame)}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child")
    parser.add_argument("--stage")
    args = parser.parse_args()
    child(args.child, args.stage) if args.child else main()
