"""Durable, fail-closed software output reservation with bounded clock uncertainty.

Not physical exactly-once execution. A reserved output with an unknown outcome
blocks further output until independent reconciliation (not implemented here).
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Contract:
    clock_bound: float = 16
    dispatch_bound: float = 1
    expiry: float = 64
    freshness: float = 120
    cooldown: float = 600
    heartbeat_timeout: float = 96


class Journal:
    """Single-writer SQLite journal; disk mode uses FULL synchronous durability.

    Replay uses :memory: with the same transactions, retaining this object across
    receiver restarts. Abrupt-process tests reopen a real disk-backed journal.
    """

    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, body TEXT NOT NULL)"
        )
        self.db.commit()
        self.writes = 0

    def read(self):
        row = self.db.execute("SELECT body FROM state WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None

    def save(self, state):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO state VALUES (1, ?)", (json.dumps(state),))
        self.writes += 1

    def close(self):
        self.db.close()


class RecoveryReceiver:
    def __init__(self, journal, now, contract=Contract()):
        if not math.isfinite(now) or any(
            v < 0 or not math.isfinite(v) for v in asdict(contract).values()
        ):
            raise ValueError("Finite clock and nonnegative finite contract parameters required")
        self.journal, self.contract = journal, contract
        self.last_now = now
        self.last_heard = now
        self.last_source = -1e30
        self.ready = False
        self.awaiting_contact = False
        self.stats = dict(
            clock_rejects=0,
            recovery_rejects=0,
            duplicate_rejects=0,
            expired_rejects=0,
            recoveries=0,
            outputs=0,
        )
        self.state = journal.read() or dict(
            version=1,
            contract=asdict(contract),
            event_id=-1,
            revision=-1,
            status="empty",
            pending=None,
            next_allowed=-1e30,
            recovery_floor=-1e30,
            blocked=False,
        )
        if self.state["contract"] != asdict(contract):
            raise ValueError("Journal contract mismatch: explicit migration required")
        if self.state["status"] == "reserved":
            self.state["uncertain_command"] = self.state["pending"]
            self.state["status"] = "uncertain"
            self.state["blocked"] = True
        elif self.state["status"] == "pending":
            self.state["status"] = "abandoned_on_restart"
        self.state["pending"] = None
        self.state["recovery_floor"] = max(self.state["recovery_floor"], now + contract.clock_bound)
        journal.save(self.state)

    def _clock(self, now, clock_valid=True):
        if not clock_valid or not math.isfinite(now) or now < self.last_now:
            self.state["blocked"] = True
            self.state["clock_invalid"] = True
            self.journal.save(self.state)
            self.stats["clock_rejects"] += 1
            return False
        self.last_now = now
        return True

    def tick(self, now, clock_valid=True):
        if not self._clock(now, clock_valid):
            return
        if self.ready and now - self.last_heard > self.contract.heartbeat_timeout:
            self.ready = False
            self.awaiting_contact = True
            self.state["recovery_floor"] = max(
                self.state["recovery_floor"], now + self.contract.clock_bound
            )
            if self.state["status"] == "pending":
                self.state["status"] = "abandoned_on_disconnect"
                self.state["pending"] = None
            self.journal.save(self.state)

    def receive(self, payload, now, clock_valid=True):
        self.tick(now, clock_valid)
        if self.state["blocked"]:
            return "blocked"
        m = json.loads(payload)
        c = self.contract
        hi = now + c.clock_bound
        if self.awaiting_contact:
            # First contact can itself be delayed old evidence. Establish a new
            # barrier and require subsequently generated evidence/commands.
            self.state["recovery_floor"] = max(self.state["recovery_floor"], hi)
            self.journal.save(self.state)
            self.awaiting_contact = False
        if m["kind"] == "heartbeat":
            source, created = m["source"], m["created"]
            if (
                math.isfinite(source)
                and math.isfinite(created)
                and source <= created <= hi
                and source > self.state["recovery_floor"]
                and hi - source <= c.freshness
                and source > self.last_source
            ):
                self.last_source, self.last_heard = source, now
                self.stats["recoveries"] += int(not self.ready)
                self.ready = True
            return "ready" if self.ready else "recovering"
        event_id, revision = m["id"], m["rev"]
        if event_id < self.state["event_id"] or (
            event_id == self.state["event_id"] and revision <= self.state["revision"]
        ):
            self.stats["duplicate_rejects"] += 1
            return "duplicate"
        same_emitted = event_id == self.state["event_id"] and self.state["status"] == "emitted"
        if m["kind"] == "cancel":
            self.state.update(
                event_id=event_id,
                revision=revision,
                pending=None,
                status="emitted" if same_emitted else "cancelled",
            )
            self.journal.save(self.state)
            return self.state["status"]
        if (
            m["kind"] != "command"
            or revision != 0
            or m["action"] not in (-1, 1)
            or not all(math.isfinite(m[k]) for k in ("created", "source"))
            or m["source"] > m["created"]
        ):
            raise ValueError("Invalid command")
        status = "pending"
        if not self.ready or min(m["created"], m["source"]) <= self.state["recovery_floor"]:
            status = "recovery_reject"
            self.stats["recovery_rejects"] += 1
        elif hi + c.dispatch_bound > min(m["created"] + c.expiry, m["source"] + c.freshness):
            status = "expired"
            self.stats["expired_rejects"] += 1
        elif m["created"] > hi:
            status = "future_reject"
            self.stats["clock_rejects"] += 1
        self.state.update(
            event_id=event_id,
            revision=revision,
            status=status,
            pending=m if status == "pending" else None,
        )
        self.journal.save(self.state)
        return status

    @property
    def pending(self):
        return self.state["pending"]

    def step(self, now, emit, hook=lambda stage: None, clock_valid=True):
        self.tick(now, clock_valid)
        if self.state["blocked"] or not self.ready or self.state["status"] != "pending":
            return 0
        m, c = self.pending, self.contract
        lo, hi = now - c.clock_bound, now + c.clock_bound
        if hi + c.dispatch_bound > min(m["created"] + c.expiry, m["source"] + c.freshness):
            self.state.update(status="expired", pending=None)
            self.journal.save(self.state)
            self.stats["expired_rejects"] += 1
            return 0
        if lo < max(m["created"], self.state["next_allowed"]):
            return 0
        # Reserve durably BEFORE calling the output adapter. On any uncertain exit,
        # this reservation prevents another output; it is not evidence of execution.
        self.state.update(
            status="reserved", blocked=True, next_allowed=hi + c.dispatch_bound + c.cooldown
        )
        self.journal.save(self.state)
        hook("after_reserve")
        emit(m)
        hook("after_output")
        completed = dict(self.state, status="emitted", blocked=False, pending=None)
        self.journal.save(completed)
        self.state = completed
        self.stats["outputs"] += 1
        hook("after_commit")
        return m["action"]
