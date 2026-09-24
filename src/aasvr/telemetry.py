"""Causal telemetry replay with a common controller and receiver contracts.

Communication is simulated. Payload lengths are serialized bytes; no energy or
physical-control outcome is inferred from the historical measurements.
"""

from __future__ import annotations

import heapq
import json
from dataclasses import dataclass

import numpy as np


@dataclass
class Controller:
    persistence: float = 32
    cooldown: float = 600
    direction: int = 0
    since: float = 0
    next_allowed: float = -1e30

    def step(self, now: float, direction: int) -> int:
        if direction != self.direction:
            self.direction = direction
            self.since = now
        if direction and now - self.since >= self.persistence and now >= self.next_allowed:
            self.next_allowed = now + self.cooldown
            return direction
        return 0


def direction(value, low, high):
    if not np.isfinite(value):
        return 0
    return 1 if value < low else -1 if value > high else 0


@dataclass(frozen=True)
class Link:
    name: str
    loss: float = 0
    delay: float = 0
    jitter: float = 0
    duplicate: float = 0
    burst_period: float = 0
    burst_duration: float = 0


class Receiver:
    """Latest source sequence wins; event identity, expiry and lockout are separate.

    Snapshot state can synchronize the virtual controller but cannot shorten
    the output actuator's outstanding cooldown. Events carry creation times.
    """

    def __init__(self, low, high, freshness=120.0, event_ttl=64.0):
        self.low, self.high = low, high
        self.freshness, self.event_ttl = freshness, event_ttl
        self.controller = Controller()
        self.latest_sequence = -1
        self.source_time = -1e30
        self.value = np.nan
        self.output_next_allowed = -1e30
        self.last_now = -1e30
        self.event_ids = set()
        self.pending = None
        self.stats = dict(
            duplicate_or_reordered=0, expired=0, duplicate_event=0, lockout_veto=0, stale_ticks=0
        )

    def receive(self, payload, now):
        m = json.loads(payload)
        if now < self.last_now:
            raise ValueError("Receiver clock must be monotonic")
        self.last_now = now
        kind = m["kind"]
        expiry = self.freshness
        if now - m["time"] > expiry:
            self.stats["expired"] += 1
            return 0
        if m["seq"] <= self.latest_sequence:
            self.stats["duplicate_or_reordered"] += 1
            return 0
        self.latest_sequence = m["seq"]
        if kind != "event":
            self.source_time = m["time"]
            self.value = float(m["value"])
        if kind == "snapshot":
            self.controller.direction = m["direction"]
            self.controller.since = m["since"]
            self.controller.next_allowed = m["next_allowed"]
        if kind in ("event", "snapshot") and m.get("action", 0):
            event_id = m["event_id"]
            if event_id in self.event_ids:
                self.stats["duplicate_event"] += 1
                return 0
            self.event_ids.add(event_id)
            if now - m["event_time"] > self.event_ttl:
                self.stats["expired"] += 1
                return 0
            return self.emit(
                m["action"],
                now,
                expires=m["event_time"] + self.event_ttl,
                source_time=m["time"],
                event_only=kind == "event",
            )
        return 0

    def emit(self, action, now, *, expires=None, source_time=None, event_only=False):
        if now < self.output_next_allowed:
            self.stats["lockout_veto"] += 1
            self.pending = (
                action,
                now + self.event_ttl if expires is None else expires,
                self.source_time if source_time is None else source_time,
                event_only,
            )
            return 0
        self.pending = None
        self.output_next_allowed = now + self.controller.cooldown
        return action

    def step(self, now, events_only=False):
        if now < self.last_now:
            raise ValueError("Receiver clock must be monotonic")
        self.last_now = now
        fresh = now - self.source_time <= self.freshness
        if not fresh and not events_only:
            self.stats["stale_ticks"] += 1
        d = direction(self.value, self.low, self.high) if fresh else 0
        action = 0 if events_only else self.controller.step(now, d)
        if self.pending is not None:
            pending_action, expires, source_time, event_only = self.pending
            valid = (
                now <= expires
                and now - source_time <= self.freshness
                and (event_only or d == pending_action)
            )
            if not valid:
                self.pending = None
            elif now >= self.output_next_allowed:
                return self.emit(pending_action, now)
        return self.emit(action, now) if action else 0


def pack(message):
    return json.dumps(message, separators=(",", ":"), allow_nan=False).encode()


def replay(
    times,
    source_times,
    values,
    low,
    high,
    policy,
    setting,
    link,
    seed=0,
    *,
    delta=1.0,
    freshness=120.0,
    event_ttl=64.0,
):
    """Sender sees only currently available source values; no future access.

    Fixed 16-second controller ticks. Source age is never refreshed by retransmission.
    Link randomness is keyed to tick, not conditional on policy sending a packet.
    The candidate synchronizes timer state on band changes and heartbeat.
    """
    n = len(times)
    rng = np.random.default_rng(seed)
    random = rng.random((n, 3))
    ref = Controller()
    receiver = Receiver(low, high, freshness, event_ttl)
    last_sent_time, last_source, last_value, last_direction = -1e30, -1e30, np.nan, None
    queue, sent, wire_bytes, sequence, delivered, lost = [], 0, 0, 0, 0, 0
    ref_actions, actions, ref_directions = np.zeros(n, int), np.zeros(n, int), np.zeros(n, int)
    for i, now in enumerate(times):
        value = values[i]
        fresh = now - source_times[i] <= freshness and np.isfinite(value)
        d = direction(value, low, high) if fresh else 0
        action = ref.step(now, d)
        ref_actions[i], ref_directions[i] = action, d
        new_sample = source_times[i] != last_source
        last_source = source_times[i]
        heartbeat = now - last_sent_time >= setting
        crossing = last_direction is None or d != last_direction
        if policy == "full":
            send = new_sample
        elif policy == "periodic":
            send = heartbeat
        elif policy == "delta":
            send = heartbeat or not np.isfinite(last_value) or abs(value - last_value) >= delta
        elif policy in ("threshold", "stateful"):
            send = crossing or heartbeat
        elif policy == "edge_events":
            send = bool(action)
        else:
            raise ValueError(policy)
        # Do not invent measurements inside gaps. Receiver ages the last report.
        if send and fresh:
            sequence += 1
            kind = (
                "event"
                if policy == "edge_events"
                else "snapshot"
                if policy == "stateful"
                else "sample"
            )
            message = dict(kind=kind, seq=sequence, time=float(source_times[i]))
            if kind != "event":
                message["value"] = float(value)
            if kind in ("event", "snapshot"):
                message.update(action=int(action), event_id=i, event_time=float(now))
            if kind == "snapshot":
                message.update(
                    direction=d, since=float(ref.since), next_allowed=float(ref.next_allowed)
                )
            payload = pack(message)
            sent += 1
            # Explicit IPv4+UDP model, not measured link-layer traffic.
            wire_bytes += len(payload) + 28
            last_sent_time, last_value, last_direction = now, value, d
            burst = link.burst_period > 0 and now % link.burst_period < link.burst_duration
            if random[i, 0] < link.loss or burst:
                lost += 1
            else:
                arrival = now + link.delay + link.jitter * random[i, 1]
                heapq.heappush(queue, (arrival, sequence, 0, payload))
                if random[i, 2] < link.duplicate:
                    heapq.heappush(queue, (arrival + 32, sequence, 1, payload))
                    wire_bytes += len(payload) + 28
        while queue and queue[0][0] <= now:
            _, _, _, payload = heapq.heappop(queue)
            delivered += 1
            received_action = receiver.receive(payload, now)
            if received_action:
                actions[i] = received_action
        tick_action = receiver.step(now, policy == "edge_events")
        if tick_action:
            actions[i] = tick_action
    return dict(
        reference=ref_actions,
        actions=actions,
        directions=ref_directions,
        sent=sent,
        wire_bytes=wire_bytes,
        delivered=delivered,
        lost=lost,
        contracts=receiver.stats,
    )


def score(times, reference, actions, directions, deadline=64.0, warmup=600.0, tail=192.0):
    """Match actions once, in direction and episode, after the reference event."""
    times = np.asarray(times)
    mask = (times >= warmup) & (times <= times[-1] - tail)
    episodes = np.cumsum(np.r_[True, directions[1:] != directions[:-1]])
    refs_all = np.flatnonzero(reference)
    refs = refs_all[mask[refs_all]]
    used, matched, delays = set(), [], []
    action_indices = np.flatnonzero(actions)
    action_times = times[action_indices]
    for i in refs:
        left = np.searchsorted(action_times, times[i])
        right = np.searchsorted(action_times, times[i] + deadline, side="right")
        candidates = action_indices[left:right]
        candidates = candidates[
            (actions[candidates] == reference[i]) & (episodes[candidates] == episodes[i])
        ]
        hit = next((int(j) for j in candidates if j not in used), None)
        if hit is not None:
            used.add(hit)
            matched.append(i)
            delays.append(times[hit] - times[i])
    wrong = (actions != 0) & (directions != 0) & (actions != directions) & mask
    unnecessary = (actions != 0) & (directions == 0) & mask
    # Cluster counters belong to the reference event's day for matches/delays.
    matched_mask = np.zeros(len(times), int)
    delay_values = np.zeros(len(times))
    for i, delay in zip(matched, delays):
        matched_mask[i], delay_values[i] = 1, delay
    return dict(
        opportunities=int(len(refs)),
        matched=len(matched),
        authorizations=int(((actions != 0) & mask).sum()),
        wrong_direction=int(wrong.sum()),
        unnecessary=int(unnecessary.sum()),
        exact_disagreement=int(((actions != reference) & mask).sum()),
        ticks=int(mask.sum()),
        delay_sum=float(sum(delays)),
        reference_mask=(reference != 0) & mask,
        matched_mask=matched_mask,
        wrong_mask=wrong,
        unnecessary_mask=unnecessary,
        delay_values=delay_values,
    )
