"""Evidence-linked claim ledger with explicit review states."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

CLAIM_STATUSES = {"unreviewed", "supported", "contradicted", "inconclusive", "rejected"}


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    claim_id: str
    statement: str
    status: str
    evidence_ids: tuple[str, ...]
    created_at: str


class ClaimLedger:
    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                statement TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('unreviewed','supported','contradicted','inconclusive','rejected')),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS claim_evidence (
                claim_id TEXT NOT NULL REFERENCES claims(claim_id),
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                PRIMARY KEY(claim_id, evidence_id)
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def create(self, statement: str, evidence_ids: tuple[str, ...] = ()) -> ClaimRecord:
        clean = " ".join(statement.split())
        if not clean:
            raise ValueError("Claim statement must not be empty")
        claim_id = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO claims(claim_id,statement,status) VALUES(?,?,'unreviewed')", (claim_id, clean))
            for evidence_id in evidence_ids:
                db.execute("INSERT OR IGNORE INTO claim_evidence(claim_id,evidence_id) VALUES(?,?)", (claim_id, evidence_id))
        record = self.get(claim_id)
        if record is None:
            raise RuntimeError("Claim write did not persist")
        return record

    def set_status(self, claim_id: str, status: str) -> ClaimRecord | None:
        if status not in CLAIM_STATUSES:
            raise ValueError("Invalid claim status")
        with self._connect() as db:
            db.execute("UPDATE claims SET status=? WHERE claim_id=?", (status, claim_id))
        return self.get(claim_id)

    def get(self, claim_id: str) -> ClaimRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            if row is None:
                return None
            evidence = db.execute("SELECT evidence_id FROM claim_evidence WHERE claim_id=? ORDER BY evidence_id", (claim_id,)).fetchall()
        return ClaimRecord(row["claim_id"], row["statement"], row["status"], tuple(item["evidence_id"] for item in evidence), row["created_at"])
