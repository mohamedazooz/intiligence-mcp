"""Append-only evidence storage with content-addressed identifiers."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    source_id: str
    content_sha256: str
    content: str
    captured_at: str


class EvidenceStore:
    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(source_id),
                content_sha256 TEXT NOT NULL,
                content TEXT NOT NULL,
                captured_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                UNIQUE(source_id, content_sha256)
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source_id, captured_at)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def save(self, source_id: str, content: str) -> EvidenceRecord:
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        evidence_id = hashlib.sha256(f"{source_id}:{digest}".encode()).hexdigest()
        with self._connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO evidence(evidence_id,source_id,content_sha256,content) VALUES(?,?,?,?)",
                (evidence_id, source_id, digest, content),
            )
            row = db.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone()
        if row is None:
            raise RuntimeError("Evidence write did not persist")
        return EvidenceRecord(row["evidence_id"], row["source_id"], row["content_sha256"], row["content"], row["captured_at"])

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone()
        if row is None:
            return None
        return EvidenceRecord(row["evidence_id"], row["source_id"], row["content_sha256"], row["content"], row["captured_at"])
