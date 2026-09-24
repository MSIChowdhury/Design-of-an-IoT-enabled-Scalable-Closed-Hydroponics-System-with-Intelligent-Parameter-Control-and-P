"""Freeze requirements, select historical inputs, and collect local timing traces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.execution_instrumentation import clock_exchange, clock_metadata, rpc
from aasvr.telemetry import Controller, direction

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/instrumented_execution"
CFG = ROOT / "configs/experiments/instrumented_execution.yaml"


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(CFG)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    helper = runpy.run_path(str(ROOT / "scripts/41_telemetry_feasibility.py"))
    times, source, values, absolute, _ = helper["load_block"]("evaluation", common)
    events = []
    for s in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors:
        if s.name not in common["sensors"]:
            continue
        controller = Controller()
        for i, t in enumerate(times):
            value = values[s.name][i]
            d = (
                direction(value, s.control_low, s.control_high)
                if t - source[i] <= 120 and np.isfinite(value)
                else 0
            )
            action = controller.step(t, d)
            if action and 600 <= t <= times[-1] - 192:
                events.append(
                    dict(
                        sensor=s.name,
                        value=float(value),
                        action=int(action),
                        historical_source_utc=pd.Timestamp(
                            source[i] + absolute[0], unit="s", tz="UTC"
                        ).isoformat(),
                        historical_reference_utc=pd.Timestamp(
                            absolute[i], unit="s", tz="UTC"
                        ).isoformat(),
                    )
                )
    events.sort(key=lambda e: (e["historical_reference_utc"], e["sensor"]))
    count = cfg["measured_transactions_per_profile"] + cfg["warmup_transactions_per_profile"]
    chosen = [events[i] for i in np.linspace(0, len(events) - 1, count, dtype=int)]
    (OUT / "historical_inputs.json").write_text(json.dumps(chosen, indent=2))
    files = [
        "configs/experiments/instrumented_execution.yaml",
        "src/aasvr/execution_instrumentation.py",
        "src/aasvr/recovery_contract.py",
        "src/aasvr/timing_feasibility.py",
        "src/aasvr/measured_trace_replay.py",
        "src/aasvr/reliable_events.py",
        "src/aasvr/telemetry.py",
        "scripts/54_instrumented_endpoints.py",
        "scripts/55_instrumented_execution.py",
        "scripts/56_replay_execution_traces.py",
        "scripts/57_report_instrumented_execution.py",
        "configs/methods/aasvr.yaml",
        "configs/experiments/telemetry.yaml",
        "configs/experiments/timing_feasibility.yaml",
        "docs/instrumented_execution/PROTOCOL.md",
        "scripts/58_run_instrumented_execution.sh",
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
    print("Requirements, candidates, source selection, and instrumentation frozen.", flush=True)


def ready(address):
    for _ in range(80):
        try:
            return rpc(address, dict(kind="meta"), 0.1)
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.05)
    raise TimeoutError(f"Endpoint did not start: {address}")


def collect(receiver_host, mock_host):
    cfg = load_yaml(CFG)
    receiver = (socket.gethostbyname(receiver_host), 9531)
    mock = (socket.gethostbyname(mock_host), 9532)
    local = clock_metadata()
    remote = ready(receiver)
    actuator = ready(mock)
    if len({m["clock_domain"] for m in (local, remote, actuator)}) != 1:
        (OUT / "clock_domain_failure.json").write_text(
            json.dumps(dict(sender=local, receiver=remote, mock=actuator), indent=2)
        )
        raise RuntimeError("This local protocol requires a verified shared monotonic clock domain")
    (OUT / "environment.json").write_text(
        json.dumps(
            dict(
                sender=local,
                receiver=remote,
                mock=actuator,
                python=sys.version,
                uname=list(os.uname()),
                scope="three local Docker containers; one clock domain",
            ),
            indent=2,
        )
    )
    inputs = json.loads((OUT / "historical_inputs.json").read_text())
    rows, exchanges, unknown_checks = [], [], []
    for profile in cfg["profiles"]:
        load = None
        try:
            if profile["cpu_load"]:
                cpu = remote["cpu_affinity"][0]
                code = f"import os\nos.sched_setaffinity(0,{{{cpu}}})\nx=0\nwhile True: x=(x+1)%1000003\n"
                load = subprocess.Popen([sys.executable, "-c", code])
            for i in range(cfg["clock_exchanges_per_profile"]):
                t0 = time.time_ns()
                answer = rpc(receiver, dict(kind="clock"))
                t3 = time.time_ns()
                exchanges.append(
                    dict(
                        profile=profile["name"],
                        sample=i,
                        t0_ns=t0,
                        t3_ns=t3,
                        **answer,
                        **clock_exchange(t0, answer["receive_wall_ns"], answer["send_wall_ns"], t3),
                    )
                )
            for i, item in enumerate(inputs):
                stream = f"{profile['name']}_{i}"
                sample = time.monotonic_ns()
                created = time.monotonic_ns()
                due = created + int(cfg["sender_timer_seconds"] * 1e9)
                time.sleep(max(0, (due - time.monotonic_ns()) / 1e9))
                sent = time.monotonic_ns()
                drop = bool(profile["drop_every"] and (i + 1) % profile["drop_every"] == 0)
                drop_ack = bool(
                    profile["drop_ack_every"] and (i + 1) % profile["drop_ack_every"] == 0
                )
                message = dict(
                    kind="command",
                    stream=stream,
                    id=1,
                    sample_ns=sample,
                    created_ns=created,
                    action=item["action"],
                    ingress_delay=profile["ingress_delay_seconds"],
                    receiver_timer=cfg["receiver_timer_seconds"],
                    drop_ack=drop_ack,
                    adapter_timeout=cfg["adapter_timeout_seconds"],
                )
                row = dict(
                    profile=profile["name"],
                    sample=i,
                    measured=i >= cfg["warmup_transactions_per_profile"],
                    stream=stream,
                    **item,
                    sample_ns=sample,
                    created_ns=created,
                    sender_due_ns=due,
                    sent_ns=sent,
                    received=not drop,
                    injected_drop=drop,
                    injected_ack_drop=drop_ack,
                    sender_lateness_s=(sent - due) / 1e9,
                )
                if not drop:
                    reply = rpc(receiver, message, cfg["rpc_timeout_seconds"])
                    row.update(reply)
                    evidence = rpc(mock, dict(kind="lookup", stream=stream, id=1))
                    row["independent_recorded"] = evidence["recorded"]
                    row["mock_output_ns"] = evidence["output_ns"]
                    row["clock_domain_verified"] = True
                    journal = reply["journal_timings"]
                    reserve = sum(
                        (r["end_ns"] - r["start_ns"]) / 1e9
                        for r in journal
                        if r["status"] == "reserved"
                    )
                    row.update(
                        network_s=(reply["received_ns"] - sent) / 1e9,
                        acceptance_s=(reply["accepted_ns"] - reply["received_ns"]) / 1e9,
                        acceptance_journal_s=sum(
                            (r["end_ns"] - r["start_ns"]) / 1e9
                            for r in journal
                            if r["end_ns"] <= reply["accepted_ns"]
                        ),
                        reserve_s=reserve,
                        timer_lateness_s=max(
                            0, (reply["authorization_ns"] - reply["timer_due_ns"]) / 1e9
                        ),
                        output_delay_s=(evidence["output_ns"] - reply["authorization_ns"]) / 1e9
                        if evidence["recorded"]
                        else None,
                        adapter_roundtrip_s=(reply["ack_received_ns"] - reply["adapter_send_ns"])
                        / 1e9
                        if reply["ack_received_ns"]
                        else None,
                        journal_total_s=sum((r["end_ns"] - r["start_ns"]) / 1e9 for r in journal),
                    )
                    if reply["blocked"]:
                        # Inspect and offer a new ID. Independent lookup is evidence only;
                        # no automatic reconciliation/reset is implemented.
                        state = rpc(receiver, dict(kind="inspect", stream=stream))
                        later = dict(
                            message,
                            id=2,
                            sample_ns=time.monotonic_ns(),
                            created_ns=time.monotonic_ns(),
                            drop_ack=False,
                        )
                        follow = rpc(receiver, later)
                        second = rpc(mock, dict(kind="lookup", stream=stream, id=2))
                        unknown_checks.append(
                            dict(
                                stream=stream,
                                independent_first=evidence["recorded"],
                                recovered_status=state["status"],
                                still_blocked=follow["blocked"],
                                second_output=second["recorded"],
                                second_attempts=second["attempts"],
                            )
                        )
                rows.append(row)
            print(
                f"Collected {profile['name']}: {len(inputs)} transactions incl. warmup", flush=True
            )
        finally:
            if load is not None:
                load.terminate()
                load.wait()
    (OUT / "transactions.json").write_text(json.dumps(rows, indent=2))
    pd.DataFrame([{k: v for k, v in r.items() if k != "journal_timings"} for r in rows]).to_csv(
        OUT / "transactions.csv", index=False
    )
    pd.DataFrame(exchanges).to_csv(OUT / "clock_exchanges.csv", index=False)
    pd.DataFrame(unknown_checks).to_csv(OUT / "uncertain_checks.csv", index=False)
    crashes = []
    for stage in cfg["crash_stages"]:
        for i in range(cfg["crash_repeats"]):
            stream = f"crash_{stage}_{i}"
            oldpid = ready(receiver)
            stamp = time.monotonic_ns()
            message = dict(
                kind="command",
                stream=stream,
                id=1,
                sample_ns=stamp,
                created_ns=stamp,
                action=1,
                crash_stage=stage,
                receiver_timer=cfg["receiver_timer_seconds"],
            )
            timed_out = False
            try:
                rpc(receiver, message, cfg["rpc_timeout_seconds"])
            except socket.timeout:
                timed_out = True
            restarted = ready(receiver)
            state = rpc(receiver, dict(kind="inspect", stream=stream))
            effect = rpc(mock, dict(kind="lookup", stream=stream, id=1))
            retry = dict(message)
            retry.pop("crash_stage")
            reply = rpc(receiver, retry)
            after = rpc(mock, dict(kind="lookup", stream=stream, id=1))
            expected = stage in ("after_output", "after_commit")
            unknown = stage in ("after_reserve", "after_output")
            passed = (
                timed_out
                and oldpid["pid"] != restarted["pid"]
                and effect["recorded"] == expected
                and state["blocked"] == unknown
            )
            if stage != "before_receive":
                passed = (
                    passed
                    and after["recorded"] == effect["recorded"]
                    and after["attempts"] == effect["attempts"]
                )
            else:
                passed = passed and after["recorded"] and after["attempts"] == 1
            crashes.append(
                dict(
                    stage=stage,
                    trial=i,
                    timed_out=timed_out,
                    status=state["status"],
                    blocked=state["blocked"],
                    independent_output_before_retry=effect["recorded"],
                    independent_output_after_retry=after["recorded"],
                    retry_status=reply["status"],
                    attempts_before_retry=effect["attempts"],
                    attempts_after_retry=after["attempts"],
                    receiver_pid_before=oldpid["pid"],
                    receiver_pid=state["pid"],
                    clock_domain=oldpid["clock_domain"],
                    passed=passed,
                )
            )
    pd.DataFrame(crashes).to_csv(OUT / "restart_checks.csv", index=False)
    assert all(r["passed"] for r in crashes), crashes
    assert all(
        r["still_blocked"] and not r["second_output"] and r["second_attempts"] == 0
        for r in unknown_checks
    )
    print(
        f"Actual receiver restarts passed: {len(crashes)}; uncertain followups blocked: {len(unknown_checks)}",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--receiver")
    parser.add_argument("--mock")
    args = parser.parse_args()
    prepare() if args.prepare else collect(args.receiver, args.mock)
