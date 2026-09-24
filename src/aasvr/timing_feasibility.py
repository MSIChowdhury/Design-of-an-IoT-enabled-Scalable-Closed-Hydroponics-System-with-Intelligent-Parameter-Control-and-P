"""Component ablations and action-timer feasibility with fixed packet polling.

Only output wakeups change between schedulers. Sensing and packet intake remain
on the existing 16-second clock; no future measurement enters the scheduler.
"""

from __future__ import annotations

import heapq
import json

import numpy as np

from aasvr.delivery_challenge import Challenge, Transport
from aasvr.recovery_contract import Contract, Journal, RecoveryReceiver
from aasvr.reliable_events import Delivery, EventReceiver, EventSender
from aasvr.telemetry import Controller, direction, pack


class AblationReceiver(RecoveryReceiver):
    def __init__(self, journal, now, contract, recovery=True):
        self.use_recovery = recovery
        super().__init__(journal, now, contract)
        if not recovery:
            self.ready = True
            self.state["recovery_floor"] = -1e30
            self.journal.save(self.state)

    def tick(self, now, clock_valid=True):
        if self.use_recovery:
            super().tick(now, clock_valid)
        else:
            self._clock(now, clock_valid)


def variants(cfg):
    return [
        dict(stage=stage, bound=bound, scheduler=scheduler, variant=f"{stage}_b{bound}_{scheduler}")
        for stage in cfg["stages"]
        for bound in (cfg["clock_bounds"] if stage in ("clock", "recovery") else [0])
        for scheduler in cfg["schedulers"]
    ]


def interval(created, source, arrival, next_allowed, bound, dispatch, expiry=64, freshness=120):
    """Receiver-clock admissible interval conditional on the current output history."""
    earliest = max(arrival, created + bound, next_allowed + bound)
    latest = min(created + expiry, source + freshness) - bound - dispatch
    return float(earliest), float(latest)


def receiver_window(receiver, now, bound, dispatch):
    m = receiver.pending
    if m is None:
        return None
    if isinstance(receiver, RecoveryReceiver):
        if receiver.state["blocked"] or not receiver.ready or receiver.state["status"] != "pending":
            return None
        next_allowed = receiver.state["next_allowed"]
    else:
        next_allowed = receiver.next_allowed
    return interval(m["created"], m["source"], now, next_allowed, bound, dispatch)


class InjectedCrash(Exception):
    pass


def replay(times, source, values, low, high, scenario, variant, cfg, seed):
    stage, bound, scheduler = variant["stage"], variant["bound"], variant["scheduler"]
    durable = stage != "current"
    recovery = stage == "recovery"
    dispatch = cfg["dispatch_bound"] if stage in ("clock", "recovery") else 0
    contract = Contract(
        clock_bound=bound,
        dispatch_bound=dispatch,
        expiry=cfg["expiry"],
        freshness=cfg["freshness"],
        cooldown=cfg["cooldown"],
        heartbeat_timeout=cfg["heartbeat_timeout"],
    )
    delivery = Delivery(
        retry_seconds=cfg["retry_seconds"], max_attempts=cfg["max_attempts"], acknowledgments=False
    )
    challenge = Challenge(
        **{
            k: v
            for k, v in scenario.items()
            if k not in ("restart_phase", "crash_after_output_seconds")
        }
    )
    transport = Transport(challenge, len(times), seed)
    journal = Journal() if durable else None

    def new_receiver(now):
        return (
            AblationReceiver(journal, now, contract, recovery)
            if durable
            else EventReceiver(delivery)
        )

    receiver = new_receiver(0)
    sender, controller = EventSender(delivery), Controller()
    queue, serial, outputs, ledger = [], 0, [], {}
    ref, dirs = np.zeros(len(times), int), np.zeros(len(times), int)
    next_restart = (
        challenge.restart_period + scenario.get("restart_phase", 0)
        if challenge.restart_period
        else np.inf
    )
    crash_at = scenario.get("crash_after_output_seconds", np.inf)
    crashed, last_output, seen = False, -1e30, set()
    counters = dict(
        bytes=0,
        heartbeat_bytes=0,
        repeated_outputs=0,
        expired_outputs=0,
        cooldown_violations=0,
        outputs=0,
        restarts=0,
    )

    def transmit(payload, now, i, heartbeat=False):
        nonlocal serial
        counters["bytes"] += len(payload) + 28
        counters["heartbeat_bytes"] += int(heartbeat) * (len(payload) + 28)
        lag = transport.lag(now, i, 0)
        if lag is not None:
            serial += 1
            heapq.heappush(queue, (now + lag, serial, payload))

    def track_pending(reason):
        m = receiver.pending
        if m is not None and m["id"] in ledger:
            ledger[m["id"]]["terminal"] = reason

    def restart(now):
        nonlocal receiver
        track_pending("restart_abandoned")
        receiver = new_receiver(now)
        counters["restarts"] += 1

    def deliver(now):
        while queue and queue[0][0] <= now:
            _, _, payload = heapq.heappop(queue)
            m = json.loads(payload)
            if m["kind"] == "heartbeat":
                receiver.receive(payload, now)
                continue
            event_id = m["id"]
            entry = ledger[event_id]
            first_command = m["kind"] == "command" and not np.isfinite(entry["first_arrival"])
            if first_command:
                entry["first_arrival"] = now
                next_allowed = receiver.state["next_allowed"] if durable else receiver.next_allowed
                earliest, latest = interval(
                    m["created"], m["source"], now, next_allowed, bound, dispatch
                )
                entry.update(
                    earliest=earliest,
                    latest=latest,
                    next_allowed=next_allowed,
                    timing_feasible=earliest <= latest,
                    poll_tick_exists=np.ceil(earliest / 16) * 16 <= latest,
                )
                if durable:
                    entry["was_blocked"] = receiver.state["blocked"]
                    entry["not_ready"] = not receiver.ready
                    entry["before_barrier"] = (
                        min(m["created"], m["source"]) <= receiver.state["recovery_floor"]
                    )
            prior_id = receiver.state["event_id"] if durable else receiver.event_id
            receiver.receive(payload, now)
            if first_command and durable:
                entry["before_barrier"] = (
                    min(m["created"], m["source"]) <= receiver.state["recovery_floor"]
                )
            status = receiver.state["status"] if durable else receiver.status
            if durable and receiver.state["blocked"]:
                status = "uncertain_block"
            if m["kind"] == "cancel":
                if status != "emitted" and status != "executed":
                    entry["terminal"] = "cancelled"
            elif event_id >= prior_id:
                # A duplicate receipt must not overwrite a prior terminal explanation.
                entry["terminal"] = status

    def execute(now):
        nonlocal receiver, crashed, last_output
        pending = receiver.pending

        def emitted(m):
            nonlocal last_output
            outputs.append(dict(time=float(now), action=m["action"], event_id=m["id"]))
            counters["outputs"] += 1
            counters["repeated_outputs"] += int(m["id"] in seen)
            counters["expired_outputs"] += int(now > m["created"] + 64 or now - m["source"] > 120)
            counters["cooldown_violations"] += int(now - last_output < 600)
            seen.add(m["id"])
            last_output = now
            ledger[m["id"]]["output_time"] = now

        if durable:

            def hook(point):
                if point == "after_output" and now >= crash_at and not crashed:
                    raise InjectedCrash()

            try:
                receiver.step(now, emitted, hook)
            except InjectedCrash:
                crashed = True
                restart(now)
        else:
            action = receiver.step(now)
            if action:
                emitted(pending)
                if now >= crash_at and not crashed:
                    crashed = True
                    restart(now)
        if pending is not None:
            status = receiver.state["status"] if durable else receiver.status
            ledger[pending["id"]]["terminal"] = status

    for i, now in enumerate(times):
        if scheduler == "deadline" and i:
            # At source-tick ties, packet intake/cancellation happens before output.
            window = receiver_window(receiver, times[i - 1], bound, dispatch)
            if window is not None:
                earliest, latest = window
                if times[i - 1] < earliest < now and earliest <= latest:
                    execute(earliest)
        if now >= next_restart:
            restart(now)
            next_restart += challenge.restart_period
        if durable:
            prior = receiver.pending
            receiver.tick(now)
            if prior is not None and receiver.pending is None:
                ledger[prior["id"]]["terminal"] = receiver.state["status"]
        deliver(now)
        fresh = now - source[i] <= 120 and np.isfinite(values[i])
        d = direction(values[i], low, high) if fresh else 0
        action = controller.step(now, d)
        ref[i], dirs[i] = action, d
        if action:
            ledger[i] = dict(
                event_id=i,
                created=float(now),
                source=float(source[i]),
                action=int(action),
                first_arrival=np.nan,
                earliest=np.nan,
                latest=np.nan,
                next_allowed=np.nan,
                timing_feasible=False,
                poll_tick_exists=False,
                was_blocked=False,
                not_ready=False,
                before_barrier=False,
                output_time=np.nan,
                terminal="not_received",
            )
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
        deliver(now)
        execute(now)
    if journal:
        journal.close()
    return dict(reference=ref, directions=dirs, outputs=outputs, ledger=ledger, counters=counters)


def score_and_explain(times, result, warmup=600, tail=192, deadline=64):
    """Independent continuous-time same-episode matching; diagnostic reasons are separate."""
    episodes = np.cumsum(np.r_[True, result["directions"][1:] != result["directions"][:-1]])
    outputs = result["outputs"]
    output_times = np.array([o["time"] for o in outputs])
    used = set()
    rows = []
    lo, hi = warmup, times[-1] - tail
    for i in np.flatnonzero(result["reference"]):
        if not lo <= times[i] <= hi:
            continue
        row = result["ledger"][int(i)].copy()
        left = np.searchsorted(output_times, times[i], side="left")
        right = np.searchsorted(output_times, times[i] + deadline, side="right")
        candidates = []
        for j in range(left, right):
            output = outputs[j]
            episode = episodes[np.searchsorted(times, output["time"], side="right") - 1]
            if (
                j not in used
                and output["action"] == result["reference"][i]
                and episode == episodes[i]
            ):
                candidates.append(j)
        matched = bool(candidates)
        if matched:
            used.add(candidates[0])
        row["matched"] = matched
        if matched:
            reason = "matched"
        elif row["was_blocked"] or row["terminal"] in ("uncertain", "uncertain_block"):
            reason = "unresolved_execution"
        elif not np.isfinite(row["first_arrival"]):
            reason = "no_delivery"
        elif row["before_barrier"]:
            reason = "recovery_barrier"
        elif row["not_ready"]:
            reason = "missing_fresh_heartbeat"
        elif np.isfinite(row["output_time"]):
            reason = "output_after_episode_or_deadline"
        elif row["terminal"] in (
            "cancelled",
            "abandoned_on_disconnect",
            "abandoned_on_restart",
            "restart_abandoned",
        ):
            reason = row["terminal"]
        elif row["timing_feasible"] and not row["poll_tick_exists"]:
            reason = "polling_missed_feasible_interval"
        elif not row["timing_feasible"]:
            raw_expiry = min(row["created"] + 64, row["source"] + 120)
            if row["first_arrival"] > raw_expiry:
                reason = "expired_before_arrival"
            elif row["first_arrival"] > row["latest"]:
                reason = "clock_or_dispatch_margin_on_arrival"
            elif row["next_allowed"] >= row["created"]:
                reason = "cooldown_no_interval"
            else:
                reason = "clock_window_empty"
        else:
            reason = "other_terminal_" + row["terminal"]
        row["reason"] = reason
        rows.append(row)
    undesirable = 0
    for o in outputs:
        if lo <= o["time"] <= hi:
            d = result["directions"][np.searchsorted(times, o["time"], side="right") - 1]
            undesirable += int(d == 0 or d != o["action"])
    return rows, undesirable
