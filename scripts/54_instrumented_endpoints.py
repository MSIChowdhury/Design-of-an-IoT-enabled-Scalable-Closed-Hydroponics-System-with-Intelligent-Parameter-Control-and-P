"""Separate-container receiver and independent durable mock actuator services."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from aasvr.execution_instrumentation import TimedJournal, clock_metadata, pack, rpc, verify_ack
from aasvr.recovery_contract import Contract
from aasvr.timing_feasibility import AblationReceiver

PORT = 9531
MOCK_PORT = 9532


def common(sock, message, address, received_wall):
    if message["kind"] == "meta":
        sock.sendto(pack(clock_metadata()), address)
        return True
    if message["kind"] == "clock":
        sock.sendto(pack(dict(receive_wall_ns=received_wall, send_wall_ns=time.time_ns())), address)
        return True
    return False


def mock(root):
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "mock.sqlite")
    db.execute("PRAGMA synchronous=FULL")
    db.execute(
        "CREATE TABLE IF NOT EXISTS outputs (stream TEXT, id INTEGER, received_ns INTEGER, output_ns INTEGER, PRIMARY KEY(stream,id))"
    )
    db.execute("CREATE TABLE IF NOT EXISTS attempts (stream TEXT, id INTEGER, received_ns INTEGER)")
    db.commit()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", MOCK_PORT))
    while True:
        payload, address = sock.recvfrom(65535)
        received = time.monotonic_ns()
        wall = time.time_ns()
        m = json.loads(payload)
        if common(sock, m, address, wall):
            continue
        row = db.execute(
            "SELECT received_ns,output_ns FROM outputs WHERE stream=? AND id=?",
            (m["stream"], m["id"]),
        ).fetchone()
        if m["kind"] == "lookup":
            sock.sendto(
                pack(
                    dict(
                        stream=m["stream"],
                        id=m["id"],
                        recorded=row is not None,
                        attempts=db.execute(
                            "SELECT COUNT(*) FROM attempts WHERE stream=? AND id=?",
                            (m["stream"], m["id"]),
                        ).fetchone()[0],
                        received_ns=row[0] if row else None,
                        output_ns=row[1] if row else None,
                    )
                ),
                address,
            )
            continue
        if m["kind"] != "output":
            raise ValueError("Unknown mock operation")
        with db:
            db.execute("INSERT INTO attempts VALUES (?,?,?)", (m["stream"], m["id"], received))
        duplicate = row is not None
        if row is None:
            # This record is the mock effect. The following commit makes it durable;
            # its timestamp is not a physical actuator measurement.
            stamp = time.monotonic_ns()
            with db:
                db.execute(
                    "INSERT INTO outputs VALUES (?,?,?,?)", (m["stream"], m["id"], received, stamp)
                )
            row = (received, stamp)
        committed = time.monotonic_ns()
        if not m.get("drop_ack", False):
            sock.sendto(
                pack(
                    dict(
                        status="recorded",
                        stream=m["stream"],
                        id=m["id"],
                        received_ns=row[0],
                        output_ns=row[1],
                        ack_sent_ns=committed,
                        duplicate=duplicate,
                    )
                ),
                address,
            )


def receiver(root, mock_host):
    # Contention profile pins an additional busy process to this same allowed CPU.
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    root.mkdir(parents=True, exist_ok=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    actuator = (socket.gethostbyname(mock_host), MOCK_PORT)
    while True:
        payload, address = sock.recvfrom(65535)
        socket_received = time.monotonic_ns()
        wall = time.time_ns()
        m = json.loads(payload)
        if common(sock, m, address, wall):
            continue
        stream = m["stream"]
        if not stream.replace("_", "").isalnum():
            raise ValueError("Invalid stream identifier")
        path = root / f"{stream}.sqlite"
        if m["kind"] == "inspect":
            if not path.exists():
                reply = dict(status="not_received", blocked=False, pid=os.getpid())
            else:
                journal = TimedJournal(path)
                r = AblationReceiver(
                    journal, time.monotonic(), Contract(clock_bound=0, dispatch_bound=1), False
                )
                reply = dict(status=r.state["status"], blocked=r.state["blocked"], pid=os.getpid())
                journal.close()
            sock.sendto(pack(reply), address)
            continue
        stage = m.get("crash_stage")

        def crash(point):
            if point == stage:
                os.kill(os.getpid(), signal.SIGKILL)

        crash("before_receive")
        time.sleep(m.get("ingress_delay", 0))
        received = time.monotonic_ns()
        journal = TimedJournal(path)
        r = AblationReceiver(
            journal, time.monotonic(), Contract(clock_bound=0, dispatch_bound=1), False
        )
        before_receive = time.monotonic_ns()
        status = r.receive(
            pack(
                dict(
                    kind="command",
                    id=m["id"],
                    rev=0,
                    created=m["created_ns"] / 1e9,
                    source=m["sample_ns"] / 1e9,
                    action=m["action"],
                )
            ),
            time.monotonic(),
        )
        accepted = time.monotonic_ns()
        crash("after_accept")
        timer_due = accepted + int(m.get("receiver_timer", 0.005) * 1e9)
        delay = (timer_due - time.monotonic_ns()) / 1e9
        if delay > 0:
            time.sleep(delay)
        authorized = time.monotonic_ns()
        data = dict(
            socket_received_ns=socket_received,
            received_ns=received,
            before_receive_ns=before_receive,
            accepted_ns=accepted,
            timer_due_ns=timer_due,
            authorization_ns=authorized,
            adapter_send_ns=None,
            ack_received_ns=None,
            mock_output_ns=None,
            pid=os.getpid(),
            receipt_status=status,
            ack_lost=False,
        )

        def emit(command):
            data["adapter_send_ns"] = time.monotonic_ns()
            request = dict(
                kind="output", stream=stream, id=command["id"], drop_ack=m.get("drop_ack", False)
            )
            try:
                ack = rpc(actuator, request, timeout=m.get("adapter_timeout", 0.15))
                data["ack_received_ns"] = time.monotonic_ns()
                verify_ack(ack, stream, command["id"])
                data["mock_output_ns"] = ack["output_ns"]
            except socket.timeout:
                data["ack_lost"] = True
                raise

        try:
            r.step(authorized / 1e9, emit, crash)
        except socket.timeout:
            pass  # The durable reservation remains blocked; no reset or retry.
        data.update(
            status=r.state["status"],
            blocked=r.state["blocked"],
            completed_ns=time.monotonic_ns(),
            journal_timings=journal.timings,
        )
        journal.close()
        sock.sendto(pack(data), address)


def supervise(root, mock_host):
    root.mkdir(parents=True, exist_ok=True)
    while True:
        before = time.monotonic_ns()
        child = subprocess.Popen(
            [
                sys.executable,
                __file__,
                "--role",
                "receiver",
                "--root",
                str(root),
                "--mock-host",
                mock_host,
            ]
        )
        code = child.wait()
        with (root / "restarts.jsonl").open("a") as f:
            f.write(
                json.dumps(
                    dict(pid=child.pid, start_ns=before, exit_ns=time.monotonic_ns(), code=code)
                )
                + "\n"
            )
        if code != -signal.SIGKILL:
            raise RuntimeError(f"Receiver exited unexpectedly: {code}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["mock", "receiver", "supervisor"], required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--mock-host", default="execution-mock")
    args = parser.parse_args()
    if args.role == "mock":
        mock(args.root)
    elif args.role == "receiver":
        receiver(args.root, args.mock_host)
    else:
        supervise(args.root, args.mock_host)
