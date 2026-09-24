"""Timestamp/clock and durable mock-output instrumentation; no physical actuation."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import time

from aasvr.recovery_contract import Journal


def clock_metadata():
    boot = open("/proc/sys/kernel/random/boot_id").read().strip()
    namespace = os.readlink("/proc/self/ns/time")
    offsets = open("/proc/self/timens_offsets").read()
    return dict(
        clock_domain=hashlib.sha256((boot + "|" + offsets).encode()).hexdigest(),
        time_namespace=namespace,
        boot_hash=hashlib.sha256(boot.encode()).hexdigest(),
        time_offsets=offsets,
        monotonic_resolution=time.get_clock_info("monotonic").resolution,
        realtime_adjustable=time.get_clock_info("time").adjustable,
        cpu_affinity=sorted(os.sched_getaffinity(0)),
        hostname=socket.gethostname(),
        pid=os.getpid(),
        monotonic_ns=time.monotonic_ns(),
        wall_ns=time.time_ns(),
    )


def clock_exchange(t0, t1, t2, t3):
    """Remote-minus-local interval given nonnegative transit times (no symmetry claim)."""
    if t3 < t0 or t2 < t1:
        raise ValueError("Clock stepped backwards during exchange")
    lower, upper = t2 - t3, t1 - t0
    if lower > upper:
        raise ValueError("Inconsistent exchange timestamps")
    return dict(
        offset_low_ns=lower,
        offset_high_ns=upper,
        midpoint_ns=(lower + upper) / 2,
        network_rtt_ns=(t3 - t0) - (t2 - t1),
    )


class TimedJournal(Journal):
    def __init__(self, path):
        self.timings = []
        super().__init__(path)

    def save(self, state):
        before = time.monotonic_ns()
        super().save(state)
        self.timings.append(
            dict(status=state["status"], start_ns=before, end_ns=time.monotonic_ns())
        )


def verify_ack(ack, stream, event_id):
    if (ack.get("stream"), ack.get("id"), ack.get("status")) != (stream, event_id, "recorded"):
        raise ValueError("Acknowledgment does not confirm the requested mock output")


def pack(message):
    return json.dumps(message, separators=(",", ":")).encode()


def rpc(address, message, timeout=1):
    # A fresh socket isolates delayed replies after timeout from later requests.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(pack(message), address)
        payload, _ = sock.recvfrom(65535)
        return json.loads(payload)
