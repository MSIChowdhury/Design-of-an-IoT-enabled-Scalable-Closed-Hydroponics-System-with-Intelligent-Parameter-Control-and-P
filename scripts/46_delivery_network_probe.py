"""Two-container UDP execution with an application-level impairment relay.

Historical time is accelerated 1000x. UDP delivery and process scheduling are
real; configured delay/loss are introduced by the client-side relay. This is
not a kernel netem, radio, physical-actuator, or latency guarantee experiment.
"""

from __future__ import annotations

import argparse
import heapq
import json
import resource
import socket
import time
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_yaml
from aasvr.delivery_challenge import Transport, delivery_for, scenarios
from aasvr.reliable_events import EventReceiver, EventSender
from aasvr.telemetry import Controller, direction, pack, score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/delivery_challenge"


def connect_ready(host):
    for attempt in range(50):
        try:
            return socket.create_connection((host, 9511), timeout=30)
        except ConnectionRefusedError:
            if attempt == 49:
                raise
            time.sleep(0.1)


def server():
    control = socket.socket()
    control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    control.bind(("0.0.0.0", 9511))
    control.listen()
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", 9512))
    udp.setblocking(False)
    print("UDP receiver ready", flush=True)
    while True:
        connection, _ = control.accept()
        with connection, connection.makefile("rwb") as stream:
            request = json.loads(stream.readline())
            if request.get("stop"):
                return
            cfg, policy = request["cfg"], request["policy"]
            delivery = delivery_for(policy, cfg)
            receivers = {s: EventReceiver(delivery) for s in request["streams"]}
            start, scale, n, tick = (request[k] for k in ("start", "scale", "n", "tick"))
            # Drain any residual datagrams before the trial starts.
            try:
                while True:
                    udp.recvfrom(65535)
            except BlockingIOError:
                pass
            stream.write(b'{"ready":true}\n')
            stream.flush()
            pending, records, timings, lateness = [], [], [], []
            received_bytes = ack_bytes = 0
            index = 0
            while index < n:
                try:
                    while True:
                        payload, address = udp.recvfrom(65535)
                        pending.append((payload, address))
                        received_bytes += len(payload) + 28
                except BlockingIOError:
                    pass
                current = time.monotonic()
                due = start + index * tick * scale
                if current < due:
                    time.sleep(min(0.0005, due - current))
                    continue
                # Receiver tick is offset by half a source tick to avoid an arbitrary
                # send/receive race on exactly simultaneous source/receiver clocks.
                now = index * tick + tick / 2
                lateness.append(max(0, (current - due) * 1000))
                for payload, address in pending:
                    before = time.perf_counter_ns()
                    m = json.loads(payload)
                    s = m["stream"]
                    ack = receivers[s].receive(payload, now)
                    timings.append((time.perf_counter_ns() - before) / 1000)
                    if delivery.acknowledgments:
                        ack = pack({**json.loads(ack), "stream": s})
                        udp.sendto(ack, address)
                        ack_bytes += len(ack) + 28
                pending.clear()
                for s, receiver in receivers.items():
                    action = receiver.step(now)
                    if action:
                        records.append(
                            dict(
                                stream=s,
                                index=index,
                                logical_time=now,
                                action=action,
                                event_id=receiver.event_id,
                            )
                        )
                index += 1
            response = dict(
                records=records,
                received_bytes=received_bytes,
                ack_bytes=ack_bytes,
                processing_median_us=float(np.median(timings)) if timings else 0,
                processing_p99_us=float(np.quantile(timings, 0.99)) if timings else 0,
                tick_lateness_p99_ms=float(np.quantile(lateness, 0.99)),
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                receiver_stats={s: r.stats for s, r in receivers.items()},
            )
            stream.write(json.dumps(response).encode() + b"\n")
            stream.flush()


def client(host):
    cfg = load_yaml(ROOT / "configs/experiments/delivery_challenge.yaml")
    data = json.loads((OUT / "probe_input.json").read_text())
    tick, streams = data["tick"], data["streams"]
    n = len(next(iter(streams.values()))["values"])
    scale = cfg["probe"]["seconds_per_logical_second"]
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", 0))
    udp.setblocking(False)
    address = (socket.gethostbyname(host), 9512)
    reports, details = [], []
    for scenario in scenarios(cfg):
        if scenario.name not in cfg["probe"]["scenarios"]:
            continue
        for policy in cfg["policies"]:
            try:
                while True:
                    udp.recvfrom(65535)
            except BlockingIOError:
                pass
            delivery = delivery_for(policy, cfg)
            senders = {s: EventSender(delivery) for s in streams}
            controllers = {s: Controller() for s in streams}
            transport = Transport(scenario, n + 2, cfg["seed"] + cfg["probe"]["seed"])
            references = {s: np.zeros(n, int) for s in streams}
            directions = {s: np.zeros(n, int) for s in streams}
            queue, serial, index = [], 0, 0
            offered_bytes = sent_bytes = dropped = reverse_offered_bytes = 0
            started = time.monotonic() + 0.25
            before_cpu = time.process_time()
            with connect_ready(host) as control:
                stream = control.makefile("rwb")
                request = dict(
                    cfg=cfg,
                    policy=policy,
                    streams=list(streams),
                    start=started + tick / 2 * scale,
                    scale=scale,
                    n=n,
                    tick=tick,
                )
                stream.write(json.dumps(request).encode() + b"\n")
                stream.flush()
                assert json.loads(stream.readline())["ready"]
                while time.monotonic() < started + (n * tick) * scale:
                    current = time.monotonic()
                    elapsed = max(0, (current - started) / scale)
                    try:
                        while True:
                            payload, _ = udp.recvfrom(65535)
                            reverse_offered_bytes += len(payload) + 28
                            j = min(n - 1, max(0, int(elapsed / tick)))
                            lag = transport.lag(elapsed, j, 1)
                            if lag is not None:
                                serial += 1
                                heapq.heappush(queue, (current + lag * scale, serial, 1, payload))
                            else:
                                dropped += 1
                    except BlockingIOError:
                        pass
                    while queue and queue[0][0] <= current:
                        _, _, channel, payload = heapq.heappop(queue)
                        if channel:
                            senders[json.loads(payload)["stream"]].acknowledge(payload)
                        else:
                            udp.sendto(payload, address)
                            sent_bytes += len(payload) + 28
                    while index < n and current >= started + index * tick * scale:
                        now = index * tick
                        for s, values in streams.items():
                            value, source = values["values"][index], values["source"][index]
                            d = (
                                direction(value, values["low"], values["high"])
                                if now - source <= 120
                                else 0
                            )
                            action = controllers[s].step(now, d)
                            references[s][index], directions[s][index] = action, d
                            senders[s].observe(now, source, d, action, index)
                            payload = senders[s].send(now)
                            if payload is not None:
                                payload = pack({**json.loads(payload), "stream": s})
                                offered_bytes += len(payload) + 28
                                lag = transport.lag(now, index, 0)
                                if lag is None:
                                    dropped += 1
                                else:
                                    serial += 1
                                    heapq.heappush(
                                        queue, (current + lag * scale, serial, 0, payload)
                                    )
                        index += 1
                    time.sleep(0.0003)
                result = json.loads(stream.readline())
                stream.close()
            total = dict(opportunities=0, matched=0, unnecessary=0, wrong_direction=0)
            # Half-tick receiver offset is represented explicitly on an 8-second grid.
            times = np.arange(2 * n) * tick / 2
            for s in streams:
                refs = np.zeros(2 * n, int)
                refs[::2] = references[s]
                acts = np.zeros(2 * n, int)
                dirs = np.repeat(directions[s], 2)
                for record in result["records"]:
                    if record["stream"] == s:
                        acts[2 * record["index"] + 1] = record["action"]
                scored = score(times, refs, acts, dirs, 64, 600, 192)
                for k in total:
                    total[k] += scored[k]
            summary = dict(
                scenario=scenario.name,
                policy=policy,
                **total,
                coverage=total["matched"] / total["opportunities"]
                if total["opportunities"]
                else None,
                undesirable_fraction=(total["unnecessary"] + total["wrong_direction"])
                / total["opportunities"]
                if total["opportunities"]
                else None,
                offered_forward_bytes=offered_bytes,
                sent_udp_bytes=sent_bytes,
                reverse_offered_bytes=reverse_offered_bytes,
                relay_dropped=dropped,
                client_cpu_seconds=time.process_time() - before_cpu,
                client_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                **{k: v for k, v in result.items() if k not in ("records", "receiver_stats")},
            )
            reports.append(summary)
            details.append(dict(scenario=scenario.name, policy=policy, **result))
            print(f"UDP {scenario.name}/{policy}: {total}", flush=True)
    pd.DataFrame(reports).to_csv(OUT / "network_probe.csv", index=False)
    (OUT / "network_probe_details.json").write_text(json.dumps(details, indent=2))
    (OUT / "network_probe_environment.json").write_text(
        json.dumps(
            dict(
                uname=list(__import__("os").uname()),
                scale=scale,
                sensors=len(streams),
                receiver_tick_offset_seconds=tick / 2,
                impairment="application-level delayed/lossy UDP relay",
                transport="separate Docker containers on bridge network",
                python=__import__("sys").version,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--host", default="delivery-challenge-receiver")
    args = parser.parse_args()
    server() if args.server else client(args.host)
