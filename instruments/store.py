"""Owner-local durable evidence. SQLite transactions and verified event chain."""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from vendor.eleven_heap_001.infinite_radio import digest
from .contract import Refuse, bounded, require


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.root / "instrument.sqlite3", timeout=10, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, body TEXT NOT NULL, sha TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, body TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0)")
        self.verify()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> dict | None:
        row = self.db.execute("SELECT body FROM state WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None

    def save(self, state: dict) -> None:
        self.db.execute("INSERT OR REPLACE INTO state VALUES(1,?)", (bounded(state).decode(),))

    def append(self, kind: str, detail: dict, state: dict) -> dict:
        row = self.db.execute("SELECT seq,sha FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq, previous = (row[0] + 1, row[1]) if row else (0, None)
        require(seq < 10000, "session event budget exceeded")
        body = {"schema": "static-os.instrument-event/v0", "seq": seq, "previous": previous,
                "kind": kind, "detail": detail, "state": state}
        encoded = bounded(body).decode()
        address = digest(body)
        self.db.execute("INSERT INTO events VALUES(?,?,?)", (seq, encoded, address))
        self.save(state)
        return {**body, "sha256": address}

    def verify(self) -> None:
        previous = None
        last = None
        consumed_ids = set()
        for seq, encoded, address in self.db.execute("SELECT seq,body,sha FROM events ORDER BY seq"):
            body = json.loads(encoded)
            require(body["seq"] == seq and body["previous"] == previous and digest(body) == address,
                    "durable session integrity failed")
            previous, last = address, body
            if body["kind"] == "RECORD_EXECUTED":
                consumed_ids.add(body["detail"]["receipt"]["request_id"])
        if last:
            require(self.load() == last["state"], "durable state disagrees with evidence")
        for id_, encoded, consumed in self.db.execute("SELECT id,body,consumed FROM requests"):
            request = json.loads(encoded)
            require(request["id"] == id_, "request identity changed")
            event = self.db.execute("SELECT body FROM events WHERE json_extract(body,'$.detail.request.id')=?", (id_,)).fetchone()
            require(event is not None and json.loads(event[0])["detail"]["request"] == request,
                    "request disagrees with durable proposal evidence")
            require(consumed in (0, 1) and bool(consumed) == (id_ in consumed_ids),
                    "request consumption disagrees with execution evidence")

    def events(self) -> list[dict]:
        return [{**json.loads(body), "sha256": address}
                for body, address in self.db.execute("SELECT body,sha FROM events ORDER BY seq")]

    def close(self) -> None:
        self.db.close()
