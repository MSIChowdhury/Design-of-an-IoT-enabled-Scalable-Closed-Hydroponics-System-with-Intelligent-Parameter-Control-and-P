"""Bounded, event-specific recovery from a durable uncertain-output reservation.

Evidence is trusted only on the configured local mock channel/clock domain.
No authentication or physical exactly-once guarantee is provided here.
"""

from __future__ import annotations

import hashlib
import json
import math


def command_digest(command):
    body = {k: command[k] for k in ("id", "action", "created", "source")}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def uncertain_command(receiver):
    state = receiver.state
    if not state["blocked"] or state.get("clock_invalid"):
        return None
    if state["status"] == "reserved":
        return state["pending"]
    if state["status"] == "uncertain":
        return state.get("uncertain_command")
    return None


class Reconciler:
    def __init__(self, receiver, stream, clock_domain, interval=16.0, max_attempts=4, horizon=64.0):
        if interval <= 0 or max_attempts <= 0 or horizon <= 0:
            raise ValueError("Positive retry limits required")
        self.receiver, self.stream, self.clock_domain = receiver, stream, clock_domain
        self.interval, self.max_attempts, self.horizon = interval, max_attempts, horizon
        bound_stream = receiver.state.get("execution_stream")
        if bound_stream is not None and bound_stream != stream:
            raise ValueError("Journal belongs to another execution stream")
        # The durable-only ablation clears startup recovery barriers. Preserve
        # this extension's committed evidence barrier across its reopen as well.
        resolved = receiver.state.get("reconciliation", {}).get("resolved")
        if resolved is not None:
            receiver.state["recovery_floor"] = max(
                receiver.state["recovery_floor"], resolved + receiver.contract.clock_bound
            )
        receiver.state["execution_stream"] = stream
        receiver.journal.save(receiver.state)

    def request(self, now):
        r = self.receiver
        if not r._clock(now):
            return None
        command = uncertain_command(r)
        if command is None:
            return None
        digest = command_digest(command)
        progress = r.state.get("reconciliation")
        if progress is None or progress["digest"] != digest:
            progress = dict(
                digest=digest, attempts=0, started=now, next_query=now, reason="pending"
            )
        if (
            progress["attempts"] >= self.max_attempts
            or now - progress["started"] > self.horizon
            or now < progress["next_query"]
        ):
            return None
        progress = dict(progress, attempts=progress["attempts"] + 1, next_query=now + self.interval)
        r.state["reconciliation"] = progress
        r.journal.save(r.state)  # Attempt budget survives crashes; never reset by lookup.
        return dict(kind="lookup", stream=self.stream, id=command["id"], digest=digest)

    def apply(self, evidence, now, hook=lambda stage: None):
        r = self.receiver
        if not r._clock(now):
            return False
        m = uncertain_command(r)
        progress = r.state.get("reconciliation")
        if m is None or progress is None or progress["attempts"] == 0:
            return False
        if progress["digest"] != command_digest(m):
            return False  # A different event's query budget cannot authorize this evidence.
        reason = "unresolved"
        valid = isinstance(evidence, dict)
        if valid:
            valid = (
                evidence.get("stream"),
                evidence.get("id"),
                evidence.get("digest"),
                evidence.get("clock_domain"),
            ) == (self.stream, m["id"], command_digest(m), self.clock_domain)
        if not valid:
            reason = "identity_or_domain_mismatch"
        elif now - progress["started"] > self.horizon:
            valid, reason = False, "late_evidence"
        elif evidence.get("status") == "completed":
            stamp = evidence.get("output_time")
            valid = (
                isinstance(stamp, (int, float))
                and math.isfinite(stamp)
                and m["created"] <= stamp <= now
                and stamp
                <= min(m["created"] + r.contract.expiry, m["source"] + r.contract.freshness)
                and evidence.get("fenced") is False
            )
            reason = "completed" if valid else "contradictory_or_invalid_completion"
        elif evidence.get("status") == "cancelled":
            valid = evidence.get("fenced") is True and evidence.get("output_time") is None
            reason = "cancelled" if valid else "contradictory_cancellation"
        else:
            valid, reason = False, "nonterminal_or_unavailable"
        if not valid:
            r.state["reconciliation"] = dict(progress, reason=reason)
            r.journal.save(r.state)
            return False
        completed = dict(
            r.state,
            blocked=False,
            pending=None,
            status="emitted" if reason == "completed" else "cancelled",
            recovery_floor=max(r.state["recovery_floor"], now + r.contract.clock_bound),
            reconciliation=dict(progress, reason=reason, resolved=now),
            reconciliation_evidence=evidence.copy(),
        )
        completed.pop("uncertain_command", None)
        if reason == "completed":
            # Never shorten a previously reserved cooldown. All times here share
            # the verified mock clock domain; no unknown cross-device conversion.
            completed["next_allowed"] = max(
                completed["next_allowed"], evidence["output_time"] + r.contract.cooldown
            )
        hook("before_reconcile_commit")
        r.journal.save(completed)
        hook("after_reconcile_commit")
        r.state = completed
        if r.use_recovery:
            r.ready = False  # Require a new heartbeat/source after the evidence barrier.
        return True
