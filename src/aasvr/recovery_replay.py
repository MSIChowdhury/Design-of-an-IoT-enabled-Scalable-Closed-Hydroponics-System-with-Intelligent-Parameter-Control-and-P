"""Comparison harness with observer-only structural checks and counted heartbeats."""

import heapq

import numpy as np

from aasvr.delivery_challenge import Challenge, Transport
from aasvr.recovery_contract import Contract, Journal, RecoveryReceiver
from aasvr.reliable_events import Delivery, EventReceiver, EventSender
from aasvr.telemetry import Controller, direction, pack


def run(times, source, values, low, high, scenario, policy, cfg, seed):
    extra = {"restart_phase", "in_contract"}
    challenge = Challenge(**{k: v for k, v in scenario.items() if k not in extra})
    contract = Contract(**{k: cfg[k] for k in Contract.__dataclass_fields__})
    delivery = Delivery(
        retry_seconds=cfg["retry_seconds"],
        max_attempts=cfg["max_attempts"],
        cancellation=policy != "plain_repetition",
        acknowledgments=False,
    )
    recovery = policy == "recovery_v2"
    journal = Journal() if recovery else None
    receiver = (
        RecoveryReceiver(journal, challenge.offset, contract)
        if recovery
        else EventReceiver(delivery)
    )
    controller, sender = Controller(), EventSender(delivery)
    transport = Transport(challenge, len(times), seed)
    queue, serial = [], 0
    next_restart = (
        (scenario.get("restart_phase", 0) + challenge.restart_period)
        if challenge.restart_period
        else np.inf
    )
    actions, reference, directions = (np.zeros(len(times), int) for _ in range(3))
    seen, last_output = set(), -1e30
    counts = dict(
        bytes=0,
        heartbeat_bytes=0,
        packets=0,
        dropped=0,
        repeated_outputs=0,
        expired_outputs=0,
        cooldown_violations=0,
        stale_recovery_outputs=0,
        restarts=0,
        not_ready_ticks=0,
        blocked_ticks=0,
        journal_writes=0,
    )

    def transmit(payload, now, i, heartbeat=False):
        nonlocal serial
        counts["bytes"] += len(payload) + 28
        counts["heartbeat_bytes"] += (len(payload) + 28) * int(heartbeat)
        counts["packets"] += 1
        lag = transport.lag(now, i, 0)
        if lag is None:
            counts["dropped"] += 1
        else:
            serial += 1
            heapq.heappush(queue, (now + lag, serial, payload))

    def drain(now):
        while queue and queue[0][0] <= now:
            _, _, payload = heapq.heappop(queue)
            receiver.receive(payload, now + challenge.offset)

    for i, now in enumerate(times):
        if now >= next_restart:
            receiver = (
                RecoveryReceiver(journal, now + challenge.offset, contract)
                if recovery
                else EventReceiver(delivery)
            )
            counts["restarts"] += 1
            next_restart += challenge.restart_period
        if recovery:
            receiver.tick(now + challenge.offset)
        drain(now)
        fresh = now - source[i] <= delivery.freshness_seconds and np.isfinite(values[i])
        d = direction(values[i], low, high) if fresh else 0
        action = controller.step(now, d)
        reference[i], directions[i] = action, d
        if recovery and now % cfg["heartbeat_seconds"] == 0 and fresh:
            transmit(
                pack(dict(kind="heartbeat", created=float(now), source=float(source[i]))),
                now,
                i,
                True,
            )
        sender.observe(now, source[i], d, action, i)
        payload = sender.send(now)
        if payload is not None:
            transmit(payload, now, i)
        drain(now)
        pending = receiver.pending
        if recovery:
            emitted = []
            receiver.step(now + challenge.offset, lambda m: emitted.append(m.copy()))
            actions[i] = emitted[0]["action"] if emitted else 0
            counts["not_ready_ticks"] += int(not receiver.ready)
            counts["blocked_ticks"] += int(receiver.state["blocked"])
        else:
            actions[i] = receiver.step(now + challenge.offset)
        if actions[i]:
            counts["repeated_outputs"] += int(pending["id"] in seen)
            counts["expired_outputs"] += int(
                now > pending["created"] + delivery.expiry_seconds
                or now - pending["source"] > delivery.freshness_seconds
            )
            counts["cooldown_violations"] += int(now - last_output < 600)
            if recovery:
                counts["stale_recovery_outputs"] += int(
                    min(pending["created"], pending["source"]) <= receiver.state["recovery_floor"]
                )
            seen.add(pending["id"])
            last_output = now
    if journal:
        counts["journal_writes"] = journal.writes
        journal.close()
    return dict(reference=reference, actions=actions, directions=directions, **counts)
