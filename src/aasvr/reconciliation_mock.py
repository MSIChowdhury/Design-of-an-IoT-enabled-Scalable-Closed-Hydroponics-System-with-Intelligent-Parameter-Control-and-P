"""Independent transactional mock ledger with terminal cancellation fencing.

The SQLite completed transition IS the mock effect. This does not solve the
physical effect/database atomicity problem for real pumps.
"""

from __future__ import annotations

import json
import sqlite3

from aasvr.reconciliation import command_digest


class MockLedger:
    def __init__(self, path, domain):
        self.domain = domain
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS commands (stream TEXT, id INTEGER, digest TEXT, body TEXT, due REAL, status TEXT, output_time REAL, PRIMARY KEY(stream,id))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS effects (stream TEXT, id INTEGER, stamp REAL, PRIMARY KEY(stream,id))"
        )
        self.db.commit()

    def submit(self, stream, command, due):
        digest = command_digest(command)
        with self.db:
            row = self.db.execute(
                "SELECT digest FROM commands WHERE stream=? AND id=?", (stream, command["id"])
            ).fetchone()
            if row and row[0] != digest:
                raise ValueError("Event ID reused with different command")
            self.db.execute(
                "INSERT OR IGNORE INTO commands VALUES (?,?,?,?,?,?,NULL)",
                (stream, command["id"], digest, json.dumps(command), due, "pending"),
            )

    def advance(self, now):
        # Serialized writer; cancellation and effect creation cannot both win.
        with self.db:
            for stream, event_id, body in self.db.execute(
                "SELECT stream,id,body FROM commands WHERE status='pending' AND due<=?", (now,)
            ).fetchall():
                m = json.loads(body)
                if now > min(m["created"] + 64, m["source"] + 120):
                    self.db.execute(
                        "UPDATE commands SET status='cancelled' WHERE stream=? AND id=?",
                        (stream, event_id),
                    )
                    continue
                self.db.execute("INSERT INTO effects VALUES (?,?,?)", (stream, event_id, now))
                self.db.execute(
                    "UPDATE commands SET status='completed',output_time=? WHERE stream=? AND id=?",
                    (now, stream, event_id),
                )

    def cancel(self, stream, command):
        # Install an immutable tombstone even if the old request has not arrived.
        self.submit(stream, command, float("inf"))
        with self.db:
            self.db.execute(
                "UPDATE commands SET status='cancelled' WHERE stream=? AND id=? AND status='pending'",
                (stream, command["id"]),
            )
        return self.lookup(stream, command["id"])

    def lookup(self, stream, event_id):
        row = self.db.execute(
            "SELECT digest,status,output_time FROM commands WHERE stream=? AND id=?",
            (stream, event_id),
        ).fetchone()
        return dict(
            stream=stream,
            id=event_id,
            digest=row[0] if row else None,
            status=row[1] if row else "not_found",
            output_time=row[2] if row else None,
            fenced=bool(row and row[1] == "cancelled"),
            clock_domain=self.domain,
        )

    def effect_count(self, stream, event_id):
        return self.db.execute(
            "SELECT COUNT(*) FROM effects WHERE stream=? AND id=?", (stream, event_id)
        ).fetchone()[0]

    def close(self):
        self.db.close()
