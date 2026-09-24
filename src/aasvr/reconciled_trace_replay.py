"""Isolated extension of the frozen trace replay: bounded reconciliation hook only."""

from __future__ import annotations
import heapq
import json
import numpy as np
from aasvr.measured_trace_replay import (
    validate_trace,
    ingress_delay,
    effect_delay,
    MissingOutputAcknowledgment,
)
from aasvr.recovery_contract import Contract, Journal
from aasvr.reliable_events import Delivery, EventReceiver, EventSender
from aasvr.telemetry import Controller, direction, pack
from aasvr.timing_feasibility import AblationReceiver, interval, receiver_window
from aasvr.reconciliation import Reconciler, uncertain_command, command_digest


class ReplayReconciliation:
    """Independent mock-effect observer; reply latency/outages are declared assumptions."""

    def __init__(self, receiver, condition="available"):
        self.receiver = receiver
        self.reconciler = Reconciler(receiver, "replay", "shared_mock_clock")
        self.condition = condition
        self.pending = []
        self.counters = dict(
            reconciliation_queries=0,
            reconciliation_bytes=0,
            reconciled=0,
            recovery_seconds_sum=0.0,
            recovery_seconds_max=0.0,
            unresolved=0,
        )

    def tick(self, now, outputs):
        for due, proof in list(self.pending):
            if due <= now:
                self.pending.remove((due, proof))
                if self.reconciler.apply(proof, now):
                    seconds = now - self.receiver.state["reconciliation"]["started"]
                    self.counters["reconciled"] += 1
                    self.counters["recovery_seconds_sum"] += seconds
                    self.counters["recovery_seconds_max"] = max(
                        self.counters["recovery_seconds_max"], seconds
                    )
        request = self.reconciler.request(now)
        if request is not None:
            self.counters["reconciliation_queries"] += 1
            self.counters["reconciliation_bytes"] += len(pack(request)) + 28
            command = uncertain_command(self.receiver)
            output = next(
                (
                    o
                    for o in reversed(outputs)
                    if o["event_id"] == request["id"] and o["time"] <= now
                ),
                None,
            )
            progress = self.receiver.state["reconciliation"]
            if self.condition == "unavailable" or (
                self.condition == "delayed_32" and now - progress["started"] < 32
            ):
                pass  # No response: absence is not negative execution evidence.
            else:
                proof = dict(
                    stream="replay",
                    id=request["id"],
                    digest=command_digest(command),
                    clock_domain="shared_mock_clock",
                    status="completed" if output else "not_found",
                    output_time=output["time"] if output else None,
                    fenced=False,
                )
                if self.condition == "wrong_id":
                    proof["id"] = -999
                if self.condition == "contradictory":
                    proof["fenced"] = True
                self.counters["reconciliation_bytes"] += len(pack(proof)) + 28
                self.pending.append((now + 16, proof))
        self.counters["unresolved"] = int(self.receiver.state["blocked"])


def replay(times, source, values, low, high, trace, variant, cfg, phase=0, reconciliation=None):
    """Repeat paired measured rows over source ticks; not a deployment trace."""
    validate_trace(trace)
    alarm = None
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
    journal = Journal() if durable else None

    def new_receiver(now):
        return (
            AblationReceiver(journal, now, contract, recovery)
            if durable
            else EventReceiver(delivery)
        )

    receiver = new_receiver(0)
    recovery_driver = reconciliation(receiver) if reconciliation is not None else None
    sender, controller = EventSender(delivery), Controller()
    queue, serial, outputs, ledger = [], 0, [], {}
    ref, dirs = np.zeros(len(times), int), np.zeros(len(times), int)
    last_output, seen = -1e30, set()
    counters = dict(
        bytes=0,
        heartbeat_bytes=0,
        repeated_outputs=0,
        expired_outputs=0,
        cooldown_violations=0,
        outputs=0,
        missing_output_acks=0,
        restarts=0,
    )

    def transmit(payload, now, i, heartbeat=False):
        nonlocal serial
        counters["bytes"] += len(payload) + 28
        counters["heartbeat_bytes"] += int(heartbeat) * (len(payload) + 28)
        observation = trace[(i + phase) % len(trace)]
        lag = ingress_delay(observation, durable)
        if lag is not None:
            serial += 1
            heapq.heappush(queue, (now + lag, serial, payload, (i + phase) % len(trace)))

    def deliver(now):
        while queue and queue[0][0] <= now:
            _, _, payload, trace_index = heapq.heappop(queue)
            m = json.loads(payload)
            if m["kind"] == "heartbeat":
                receiver.receive(payload, now)
                continue
            event_id = m["id"]
            entry = ledger[event_id]
            first_command = m["kind"] == "command" and not np.isfinite(entry["first_arrival"])
            if first_command:
                entry["first_arrival"] = now
                entry["trace_index"] = trace_index
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
        nonlocal last_output
        pending = receiver.pending
        observation = trace[ledger[pending["id"]]["trace_index"]] if pending else None

        def emitted(m):
            nonlocal last_output
            output_time = now + effect_delay(observation, durable)
            outputs.append(dict(time=float(output_time), action=m["action"], event_id=m["id"]))
            counters["outputs"] += 1
            counters["repeated_outputs"] += int(m["id"] in seen)
            counters["expired_outputs"] += int(
                output_time > m["created"] + 64 or output_time - m["source"] > 120
            )
            counters["cooldown_violations"] += int(output_time - last_output < 600 - 1e-9)
            seen.add(m["id"])
            last_output = output_time
            ledger[m["id"]]["output_time"] = output_time
            if observation.get("ack_lost", False):
                counters["missing_output_acks"] += 1
                if durable:
                    raise MissingOutputAcknowledgment()

        if durable:
            try:
                receiver.step(now, emitted)
            except MissingOutputAcknowledgment:
                pass  # Retain durable reserved/blocked state; no automatic reset.
        else:
            action = receiver.step(now)
            if action:
                emitted(pending)
        if pending is not None:
            status = receiver.state["status"] if durable else receiver.status
            ledger[pending["id"]]["terminal"] = status

    for i, now in enumerate(times):
        if alarm is not None and alarm[0] < now:
            wake, event_id = alarm
            alarm = None
            if receiver.pending is not None and receiver.pending["id"] == event_id:
                execute(wake)
        if durable:
            prior = receiver.pending
            receiver.tick(now)
            if prior is not None and receiver.pending is None:
                ledger[prior["id"]]["terminal"] = receiver.state["status"]
        if recovery_driver is not None:
            recovery_driver.tick(now, outputs)
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
        # Source/cancellation intake wins ties. A planned wake is retained until
        # executed or invalidated; scheduling adds observed lateness exactly once.
        if alarm is not None and alarm[0] <= now:
            wake, event_id = alarm
            alarm = None
            if receiver.pending is not None and receiver.pending["id"] == event_id:
                execute(wake)
        if alarm is not None and (receiver.pending is None or receiver.pending["id"] != alarm[1]):
            alarm = None
        if alarm is None and receiver.pending is not None:
            window = receiver_window(receiver, now, bound, dispatch)
            if window is not None:
                earliest, latest = window
                planned = now if scheduler == "poll" else earliest
                observation = trace[ledger[receiver.pending["id"]]["trace_index"]]
                wake = planned + observation["timer_lateness_s"]
                if planned <= latest:
                    if wake == now:
                        execute(now)
                    else:
                        alarm = (wake, receiver.pending["id"])
    if recovery_driver is not None:
        recovery_driver.counters["unresolved"] = int(receiver.state["blocked"])
        counters.update(recovery_driver.counters)
    counters["unresolved"] = int(durable and receiver.state["blocked"])
    if journal:
        journal.close()
    return dict(reference=ref, directions=dirs, outputs=outputs, ledger=ledger, counters=counters)
