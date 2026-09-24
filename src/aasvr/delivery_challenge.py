"""Frozen challenge transport and replay; leaves the original benchmark unchanged."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from aasvr.reliable_events import Delivery, EventReceiver, EventSender
from aasvr.telemetry import Controller, direction


@dataclass(frozen=True)
class Challenge:
    name: str
    loss: float = 0
    delay: float = 0
    jitter: float = 0
    reverse_loss: float | None = None
    reverse_delay: float | None = None
    burst_duration: float = 0
    burst_phase: float = 0
    burst_period: float = 3600
    bad_seconds: float = 0
    offset: float = 0
    restart_period: float = 0


def scenarios(cfg):
    result = [
        Challenge("ideal"),
        Challenge("iid_10", loss=0.1, delay=8, jitter=24),
        Challenge("iid_20", loss=0.2, delay=8, jitter=24),
        Challenge("delay_tail", delay=8, jitter=88),
        Challenge("asymmetric", loss=0.05, delay=8, jitter=24, reverse_loss=0.5, reverse_delay=80),
    ]
    result += [
        Challenge(
            f"outage_{d}_phase_{p}",
            delay=8,
            jitter=24,
            burst_duration=d,
            burst_phase=p,
            burst_period=cfg["outage_period"],
        )
        for d in cfg["outage_durations"]
        for p in cfg["outage_phases"]
    ]
    result += [
        Challenge(f"correlated_{d}", delay=8, jitter=24, bad_seconds=d)
        for d in cfg["correlated_bad_seconds"]
    ]
    result += [
        Challenge(f"clock_{o:+d}", delay=8, jitter=24, offset=o) for o in cfg["clock_offsets"]
    ]
    result += [Challenge("restart_hourly", delay=8, jitter=24, restart_period=3600)]
    return result


def delivery_for(policy, cfg):
    return Delivery(
        retry_seconds=cfg["retry_seconds"],
        max_attempts=cfg["max_attempts"],
        cancellation=policy != "plain_repetition",
        acknowledgments=policy == "acknowledged",
        expiry_seconds=cfg["expiry_seconds"],
        freshness_seconds=cfg["freshness_seconds"],
    )


class Transport:
    """Exogenous tick-indexed impairments, paired across policies and all sensors.

    Correlated outages alternate geometric good/bad runs with mean durations
    9*bad_seconds / bad_seconds (approximately 10% stationary outage time).
    The chains start in their stationary distribution. Both channels have their
    own chain; periodic outages affect both directions simultaneously.
    """

    def __init__(self, challenge, n, seed, tick=16):
        self.challenge = challenge
        rng = np.random.default_rng(seed)
        self.draws = rng.random((2, n, 2))
        self.bad = np.zeros((2, n), bool)
        if challenge.bad_seconds:
            transitions = rng.random((2, n))
            for channel in range(2):
                state = bool(rng.random() < 0.1)
                for i in range(n):
                    self.bad[channel, i] = state
                    duration = challenge.bad_seconds * (1 if state else 9)
                    if transitions[channel, i] < min(1, tick / duration):
                        state = not state

    def lag(self, now, index, channel):
        c = self.challenge
        loss = c.reverse_loss if channel and c.reverse_loss is not None else c.loss
        delay = c.reverse_delay if channel and c.reverse_delay is not None else c.delay
        outage = (now - c.burst_phase) % c.burst_period < c.burst_duration
        draw = self.draws[channel, index]
        if outage or self.bad[channel, index] or draw[0] < loss:
            return None
        return delay + c.jitter * draw[1]


def replay(times, source, values, low, high, challenge, delivery, seed):
    transport = Transport(challenge, len(times), seed)
    sender, receiver, controller = EventSender(delivery), EventReceiver(delivery), Controller()
    queue, serial, next_restart = [], 0, challenge.restart_period or np.inf
    counts = dict(
        bytes=0,
        forward_bytes=0,
        ack_bytes=0,
        dropped=0,
        restarts=0,
        repeated_outputs=0,
        expired_outputs=0,
        cooldown_violations=0,
    )
    actions, references, directions = (np.zeros(len(times), int) for _ in range(3))
    seen, last_output = set(), -1e30  # Observer only; never used to suppress output.

    def transmit(payload, now, i, channel):
        nonlocal serial
        size = len(payload) + 28
        counts["bytes"] += size
        counts["ack_bytes" if channel else "forward_bytes"] += size
        lag = transport.lag(now, i, channel)
        if lag is None:
            counts["dropped"] += 1
        else:
            serial += 1
            heapq.heappush(queue, (now + lag, serial, channel, payload))

    def drain(now, i):
        while queue and queue[0][0] <= now:
            _, _, channel, payload = heapq.heappop(queue)
            if channel:
                sender.acknowledge(payload)
            else:
                ack = receiver.receive(payload, now + challenge.offset)
                if delivery.acknowledgments:
                    transmit(ack, now, i, 1)

    for i, now in enumerate(times):
        if now >= next_restart:
            receiver = EventReceiver(delivery)
            counts["restarts"] += 1
            next_restart += challenge.restart_period
        drain(now, i)
        fresh = now - source[i] <= delivery.freshness_seconds and np.isfinite(values[i])
        d = direction(values[i], low, high) if fresh else 0
        action = controller.step(now, d)
        directions[i], references[i] = d, action
        sender.observe(now, source[i], d, action, i)
        payload = sender.send(now)
        if payload is not None:
            transmit(payload, now, i, 0)
        drain(now, i)
        pending = receiver.pending
        actions[i] = receiver.step(now + challenge.offset)
        if actions[i]:
            counts["repeated_outputs"] += int(receiver.event_id in seen)
            counts["cooldown_violations"] += int(now - last_output < 600)
            counts["expired_outputs"] += int(
                now > pending["created"] + delivery.expiry_seconds
                or now - pending["source"] > delivery.freshness_seconds
            )
            seen.add(receiver.event_id)
            last_output = now
    return dict(reference=references, actions=actions, directions=directions, **counts)


def assumption_checks():
    """Directed counterexamples, not prevalence estimates or repaired behavior."""
    from aasvr.telemetry import pack

    d = Delivery(retry_seconds=32, max_attempts=2, acknowledgments=False)
    packet = pack(dict(kind="command", id=1, rev=0, created=0.0, source=0.0, action=1))
    receiver = EventReceiver(d)
    receiver.receive(packet, 0)
    first = receiver.step(0)
    receiver = EventReceiver(d)  # Loss of volatile high-water mark and cooldown.
    receiver.receive(packet, 32)
    second = receiver.step(32)
    receiver = EventReceiver(d)
    receiver.receive(packet, 32)  # True arrival=96, receiver clock offset=-64.
    expired = receiver.step(32)
    return {
        "restart_reexecutes_same_id": bool(first and second),
        "negative_clock_offset_can_execute_truly_expired_command": bool(expired),
        "true_arrival_seconds": 96,
        "receiver_clock_seconds": 32,
    }
