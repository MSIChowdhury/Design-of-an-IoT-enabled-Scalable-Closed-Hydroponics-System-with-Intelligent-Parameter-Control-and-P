"""Bounded-lifetime command delivery with idempotence and cancellation revisions.

ACK means receipt/disposition, not measured actuator execution. No cancellation
can undo an action already emitted. Clocks and monotonic event IDs are assumed.
"""

from __future__ import annotations

import heapq
import json
from dataclasses import dataclass

import numpy as np

from aasvr.telemetry import Controller, Link, direction, pack


@dataclass(frozen=True)
class Delivery:
    retry_seconds: float = 16
    max_attempts: int = 3
    cancellation: bool = True
    acknowledgments: bool = True
    expiry_seconds: float = 64
    freshness_seconds: float = 120


class EventReceiver:
    """One monotonic high-water ID and revision prevent replay without a growing log."""

    def __init__(self, delivery=Delivery(), cooldown=600.0):
        self.delivery = delivery
        self.cooldown = cooldown
        self.event_id = -1
        self.revision = -1
        self.status = "empty"
        self.pending = None
        self.next_allowed = -1e30
        self.last_now = -1e30
        self.stats = dict(
            duplicates=0,
            reordered=0,
            expired=0,
            cancelled=0,
            late_cancellations=0,
            executed=0,
            deferred=0,
        )

    def receive(self, payload, now):
        self._clock(now)
        m = json.loads(payload)
        event_id, revision = m["id"], m["rev"]
        if event_id < self.event_id:
            self.stats["reordered"] += 1
            status = "superseded"
        elif event_id == self.event_id and revision <= self.revision:
            self.stats["duplicates"] += 1
            status = self.status
        else:
            same = event_id == self.event_id
            already_executed = same and self.status == "executed"
            self.event_id, self.revision = event_id, revision
            self.pending = None
            if m["kind"] == "cancel":
                if already_executed:
                    self.stats["late_cancellations"] += 1
                    self.status = "executed"
                else:
                    self.stats["cancelled"] += 1
                    self.status = "cancelled"
            elif m["kind"] != "command" or revision != 0 or m["action"] not in (-1, 1):
                raise ValueError("Invalid command envelope")
            elif (
                m["created"] > now
                or m["source"] > m["created"]
                or now > m["created"] + self.delivery.expiry_seconds
                or now - m["source"] > self.delivery.freshness_seconds
            ):
                self.stats["expired"] += 1
                self.status = "expired"
            else:
                self.pending = m
                self.status = "pending"
                self.stats["deferred"] += int(now < self.next_allowed)
            status = self.status
        return pack(dict(kind="ack", id=event_id, rev=revision, status=status))

    def step(self, now):
        self._clock(now)
        if self.pending is None:
            return 0
        m = self.pending
        if (
            now > m["created"] + self.delivery.expiry_seconds
            or now - m["source"] > self.delivery.freshness_seconds
        ):
            self.pending = None
            self.status = "expired"
            self.stats["expired"] += 1
            return 0
        if now < self.next_allowed:
            return 0
        self.pending = None
        self.status = "executed"
        self.next_allowed = now + self.cooldown
        self.stats["executed"] += 1
        return m["action"]

    def _clock(self, now):
        if now < self.last_now:
            raise ValueError("Clock must be monotonic")
        self.last_now = now


class EventSender:
    def __init__(self, delivery=Delivery()):
        self.delivery = delivery
        self.command = None
        self.message = None
        self.acked = False
        self.attempts = 0
        self.last_send = -1e30
        self.stats = dict(commands=0, cancellations=0, retries=0, acknowledgments=0, stale_acks=0)

    def observe(self, now, source_time, direction_now, action, event_id):
        if action:
            self.command = dict(
                kind="command",
                id=int(event_id),
                rev=0,
                created=float(now),
                source=float(source_time),
                action=int(action),
            )
            self._replace(self.command.copy())
            self.stats["commands"] += 1
        elif (
            self.command is not None
            and self.delivery.cancellation
            and now <= self.command["created"] + self.delivery.expiry_seconds
            and self.message["rev"] == 0
            and direction_now != self.command["action"]
        ):
            self._replace(dict(kind="cancel", id=self.command["id"], rev=1))
            self.stats["cancellations"] += 1

    def _replace(self, message):
        self.message = message
        self.acked = False
        self.attempts = 0
        self.last_send = -1e30

    def acknowledge(self, payload):
        ack = json.loads(payload)
        if self.message is not None and (ack["id"], ack["rev"]) == (
            self.message["id"],
            self.message["rev"],
        ):
            self.acked = True
            self.stats["acknowledgments"] += 1
        else:
            self.stats["stale_acks"] += 1

    def send(self, now):
        if self.command is None:
            return None
        if now > self.command["created"] + self.delivery.expiry_seconds:
            return None
        if (
            self.delivery.acknowledgments and self.acked
        ) or self.attempts >= self.delivery.max_attempts:
            return None
        if now - self.last_send < self.delivery.retry_seconds:
            return None
        self.stats["retries"] += int(self.attempts > 0)
        self.attempts += 1
        self.last_send = now
        return pack(self.message)


def replay_reliable(
    times, source_times, values, low, high, link: Link, delivery=Delivery(), seed=0
):
    n = len(times)
    forward = np.random.default_rng(seed).random((n, 3))
    reverse = np.random.default_rng(seed + 104729).random((n, 3))
    sender, receiver, controller = EventSender(delivery), EventReceiver(delivery), Controller()
    queue = []
    serial = 0
    counters = dict(
        forward_messages=0,
        ack_messages=0,
        forward_bytes=0,
        ack_bytes=0,
        command_packets=0,
        cancel_packets=0,
        lost_forward=0,
        lost_ack=0,
    )
    references, actions, directions = np.zeros(n, int), np.zeros(n, int), np.zeros(n, int)

    def transmit(payload, now, index, channel):
        nonlocal serial
        serial += 1
        label = "forward" if channel == 0 else "ack"
        counters[label + "_messages"] += 1
        counters[label + "_bytes"] += len(payload) + 28
        if channel == 0:
            kind = json.loads(payload)["kind"]
            counters["cancel_packets" if kind == "cancel" else "command_packets"] += 1
        draw = (forward if channel == 0 else reverse)[index]
        burst = link.burst_period > 0 and now % link.burst_period < link.burst_duration
        if draw[0] < link.loss or burst:
            counters["lost_" + label] += 1
            return
        arrival = now + link.delay + link.jitter * draw[1]
        heapq.heappush(queue, (arrival, serial, channel, payload))
        if draw[2] < link.duplicate:
            counters[label + "_bytes"] += len(payload) + 28
            serial += 1
            heapq.heappush(queue, (arrival + 32, serial, channel, payload))

    def drain(now, index):
        # Commands/cancellations due on the same control tick are all processed
        # before an output is emitted. An already-emitted action is never undone.
        while queue and queue[0][0] <= now:
            _, _, channel, payload = heapq.heappop(queue)
            if channel == 0:
                ack = receiver.receive(payload, now)
                if delivery.acknowledgments:
                    transmit(ack, now, index, 1)
            else:
                sender.acknowledge(payload)

    for i, now in enumerate(times):
        drain(now, i)
        fresh = now - source_times[i] <= delivery.freshness_seconds and np.isfinite(values[i])
        d = direction(values[i], low, high) if fresh else 0
        action = controller.step(now, d)
        references[i], directions[i] = action, d
        sender.observe(now, source_times[i], d, action, i)
        payload = sender.send(now)
        if payload is not None:
            transmit(payload, now, i, 0)
        drain(now, i)
        actions[i] = receiver.step(now)
    return dict(
        reference=references,
        actions=actions,
        directions=directions,
        **counters,
        **{"receiver_" + k: v for k, v in receiver.stats.items()},
        **{"sender_" + k: v for k, v in sender.stats.items()},
    )
