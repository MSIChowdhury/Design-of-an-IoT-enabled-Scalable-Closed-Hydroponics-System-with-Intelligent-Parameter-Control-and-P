"""Actual local UDP lookup/ACK loss and SIGKILL during reconciliation commits."""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import signal
import socket
import time
from pathlib import Path

import pandas as pd

from aasvr.execution_instrumentation import clock_metadata, pack, rpc
from aasvr.reconciliation import Reconciler
from aasvr.reconciliation_mock import MockLedger
from aasvr.recovery_contract import Contract, Journal
from aasvr.timing_feasibility import AblationReceiver

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reconciliation"


def serve(path, connection):
    domain = clock_metadata()["clock_domain"]
    ledger = MockLedger(path, domain)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(0.002)
    connection.send(sock.getsockname())
    connection.close()
    delayed = []
    while True:
        now = time.monotonic()
        for item in list(delayed):
            due, stream, command = item
            if now >= due:
                ledger.submit(stream, command, due)
                delayed.remove(item)
        ledger.advance(now)
        try:
            data, address = sock.recvfrom(65535)
        except socket.timeout:
            continue
        m = json.loads(data)
        if m["kind"] == "stop":
            break
        stream = m["stream"]
        event = m["id"]
        if m["kind"] == "submit":
            ledger.submit(stream, m["command"], time.monotonic() + m.get("delay", 0))
            ledger.advance(time.monotonic())
        elif m["kind"] == "defer_submit":
            delayed.append((time.monotonic() + m["delay"], stream, m["command"]))
        elif m["kind"] == "cancel":
            ledger.cancel(stream, m["command"])
        reply = ledger.lookup(stream, event)
        reply["effect_count"] = ledger.effect_count(stream, event)
        if not m.get("drop_reply", False):
            sock.sendto(pack(reply), address)
    ledger.close()
    sock.close()


def reopen(path):
    journal = Journal(path)
    receiver = AblationReceiver(
        journal, time.monotonic(), Contract(clock_bound=0, dispatch_bound=1, cooldown=0.2), False
    )
    return journal, receiver


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runtime = OUT / f"runtime_{time.time_ns()}"
    runtime.mkdir()
    parent, child = mp.Pipe()
    process = mp.Process(target=serve, args=(runtime / "mock.sqlite", child))
    process.start()
    address = parent.recv()
    domain = clock_metadata()["clock_domain"]
    rows = []
    scenarios = [
        "lost_ack",
        "delayed_after_not_found",
        "cancel_before_arrival",
        "cancel_after_accept",
        "mock_restart_pending",
        "unavailable",
        "wrong_id",
        "contradictory",
        "before_reconcile_commit",
        "after_reconcile_commit",
    ]
    try:
        for case in scenarios:
            for repeat in range(3):
                # Separate ledger stream per case, with receiver evidence bound to it.
                stream = f"{case}_{repeat}"
                path = runtime / f"{stream}.sqlite"
                journal, receiver = reopen(path)
                stamp = time.monotonic()
                command = dict(kind="command", id=1, rev=0, action=1, created=stamp, source=stamp)
                receiver.receive(pack(command), stamp)

                def emit(m):
                    kind = (
                        "defer_submit"
                        if case in ("delayed_after_not_found", "cancel_before_arrival")
                        else "submit"
                    )
                    delay = (
                        0.25
                        if kind == "defer_submit"
                        or case in ("cancel_after_accept", "mock_restart_pending")
                        else 0
                    )
                    rpc(
                        address,
                        dict(
                            kind=kind, stream=stream, id=1, command=m, delay=delay, drop_reply=True
                        ),
                        0.03,
                    )

                try:
                    receiver.step(time.monotonic(), emit)
                except socket.timeout:
                    pass
                assert receiver.state["blocked"]
                blocked_at = time.monotonic()
                reconciler = Reconciler(receiver, stream, domain, interval=0.01, horizon=5)
                request = reconciler.request(time.monotonic())
                lookup_start = time.monotonic()
                proof = rpc(address, request)
                lookup_seconds = time.monotonic() - lookup_start
                initial_status = proof["status"]
                if case in ("delayed_after_not_found", "cancel_before_arrival"):
                    assert proof["status"] == "not_found"
                    assert not reconciler.apply(proof, time.monotonic())
                if case.startswith("cancel_"):
                    proof = rpc(address, dict(kind="cancel", stream=stream, id=1, command=command))
                    assert proof["status"] == "cancelled"
                if case == "delayed_after_not_found":
                    time.sleep(0.28)
                    assert reconciler.request(time.monotonic())
                    proof = rpc(address, dict(kind="lookup", stream=stream, id=1))
                if case == "mock_restart_pending":
                    assert proof["status"] == "pending"
                    process.kill()
                    process.join()
                    parent, child = mp.Pipe()
                    process = mp.Process(target=serve, args=(runtime / "mock.sqlite", child))
                    process.start()
                    address = parent.recv()
                    time.sleep(0.28)
                    assert reconciler.request(time.monotonic())
                    proof = rpc(address, dict(kind="lookup", stream=stream, id=1))
                if case == "unavailable":
                    try:
                        rpc(
                            address, dict(kind="lookup", stream=stream, id=1, drop_reply=True), 0.03
                        )
                        raise AssertionError("Lookup should have timed out")
                    except socket.timeout:
                        proof = dict(status="unavailable")
                if case == "wrong_id":
                    proof = dict(proof, id=999)
                if case == "contradictory":
                    proof = dict(proof, fenced=True)
                crashed = False
                if "reconcile_commit" in case:
                    # Child binding uses the same persisted stream; never rename it.
                    journal.close()
                    worker = mp.Process(
                        target=crash_bound, args=(path, domain, proof, case, stream)
                    )
                    worker.start()
                    worker.join(5)
                    assert worker.exitcode == -signal.SIGKILL
                    crashed = True
                    journal, receiver = reopen(path)
                    reconciler = Reconciler(receiver, stream, domain, interval=0.01, horizon=5)
                    if case == "before_reconcile_commit":
                        assert receiver.state["blocked"]
                    else:
                        assert not receiver.state["blocked"]
                resolved = (
                    reconciler.apply(proof, time.monotonic()) if receiver.state["blocked"] else True
                )
                bad = case in ("unavailable", "wrong_id", "contradictory")
                assert resolved != bad, (case, proof, receiver.state)
                assert receiver.state["blocked"] == bad
                # Same command cannot re-enter output, even after completed recovery.
                receiver.receive(pack(command), time.monotonic())
                assert (
                    receiver.step(
                        time.monotonic(),
                        lambda _: (_ for _ in ()).throw(
                            AssertionError("duplicate adapter invocation")
                        ),
                    )
                    == 0
                )
                if case.startswith("cancel_"):
                    time.sleep(0.28)
                actual = rpc(address, dict(kind="lookup", stream=stream, id=1))
                expected = 0 if case.startswith("cancel_") else 1
                assert actual["effect_count"] == expected
                rows.append(
                    dict(
                        case=case,
                        repeat=repeat,
                        initial_status=initial_status,
                        resolved=resolved,
                        blocked=receiver.state["blocked"],
                        effects=actual["effect_count"],
                        crashed=crashed,
                        lookup_seconds=lookup_seconds,
                        recovery_seconds=time.monotonic() - blocked_at if resolved else None,
                        passed=True,
                    )
                )
                journal.close()
        pd.DataFrame(rows).to_csv(OUT / "local_checks.csv", index=False)
        print(
            f"Local cases passed: {len(rows)}; actual reconciliation SIGKILLs: {sum(r['crashed'] for r in rows)}",
            flush=True,
        )
    finally:
        process.terminate()
        process.join()


def crash_bound(path, domain, proof, stage, stream):
    journal, receiver = reopen(path)
    reconciler = Reconciler(receiver, stream, domain, interval=0.01, horizon=5)

    def crash(point):
        if point == stage:
            os.kill(os.getpid(), signal.SIGKILL)

    reconciler.apply(proof, time.monotonic(), crash)
    journal.close()


if __name__ == "__main__":
    main()
