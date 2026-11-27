"""Minimal durable queue for access challenges; it never stores challenge solutions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class AccessChallengeStore:
    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS access_challenges (
                    challenge_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    artifact_id TEXT,
                    category TEXT NOT NULL,
                    markers_json TEXT NOT NULL,
                    detected_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    status TEXT NOT NULL DEFAULT 'requires_human_review'
                        CHECK(status='requires_human_review')
                )"""
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_challenges_detected ON access_challenges(detected_at)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(
        self, source_id: str, artifact_id: str, category: str, markers: tuple[str, ...]
    ) -> str:
        if category not in {"captcha", "bot_challenge", "authentication", "paywall", "rate_limit"}:
            raise ValueError("Unsupported access challenge category")
        challenge_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute(
                """INSERT INTO access_challenges
                   (challenge_id,source_id,artifact_id,category,markers_json)
                   VALUES(?,?,?,?,?)""",
                (challenge_id, source_id, artifact_id, category,
                 json.dumps(list(markers), separators=(",", ":"))),
            )
        return challenge_id

    def list_pending(self, limit: int = 20) -> list[dict[str, Any]]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._connect() as db:
            rows = db.execute(
                """SELECT c.challenge_id,c.source_id,s.url,c.artifact_id,c.category,
                          c.markers_json,c.detected_at,c.status
                   FROM access_challenges c JOIN sources s ON s.source_id=c.source_id
                   ORDER BY c.detected_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            {
                "challenge_id": row["challenge_id"],
                "source_id": row["source_id"],
                "url": row["url"],
                "artifact_id": row["artifact_id"],
                "category": row["category"],
                "markers": json.loads(row["markers_json"]),
                "detected_at": row["detected_at"],
                "status": row["status"],
                "action": "stop_and_review_manually; automated solving is disabled",
            }
            for row in rows
        ]
