"""Evidence-linked claims with typed evidence relations and append-only review history."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

CLAIM_STATUSES = {"unreviewed", "supported", "contradicted", "inconclusive", "rejected"}
EVIDENCE_RELATIONS = {"supports", "contradicts", "qualifies"}


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    claim_id: str
    statement: str
    status: str
    evidence_ids: tuple[str, ...]
    created_at: str
    evidence_links: tuple[tuple[str, str, str | None], ...] = ()


@dataclass(frozen=True, slots=True)
class ClaimReviewRecord:
    review_id: str
    claim_id: str
    previous_status: str
    new_status: str
    reviewer_id: str
    rationale: str
    created_at: str


class ClaimLedger:
    """SQLite claim register.

    A claim may be proposed without evidence, but it cannot be marked supported
    or contradicted until evidence with the corresponding relation is linked.
    Every review transition requires an attributed reviewer and rationale.
    """

    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    statement TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN (
                        'unreviewed','supported','contradicted','inconclusive','rejected'
                    )),
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS claim_evidence (
                    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    relation TEXT NOT NULL DEFAULT 'supports'
                        CHECK(relation IN ('supports','contradicts','qualifies')),
                    rationale TEXT,
                    linked_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    PRIMARY KEY(claim_id, evidence_id)
                )
                """
            )
            self._migrate_claim_evidence(db)
            db.executescript(
                """
                CREATE INDEX IF NOT EXISTS idx_claim_evidence_evidence
                    ON claim_evidence(evidence_id);
                CREATE INDEX IF NOT EXISTS idx_claim_evidence_relation
                    ON claim_evidence(claim_id, relation);

                CREATE TABLE IF NOT EXISTS claim_reviews (
                    review_id TEXT PRIMARY KEY,
                    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
                    previous_status TEXT NOT NULL,
                    new_status TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE INDEX IF NOT EXISTS idx_claim_reviews_claim
                    ON claim_reviews(claim_id, created_at);

                CREATE TABLE IF NOT EXISTS claim_evidence_events (
                    event_id TEXT PRIMARY KEY,
                    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    previous_relation TEXT,
                    new_relation TEXT NOT NULL
                        CHECK(new_relation IN ('supports','contradicts','qualifies')),
                    actor_id TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE INDEX IF NOT EXISTS idx_claim_evidence_events_claim
                    ON claim_evidence_events(claim_id, created_at);

                CREATE TRIGGER IF NOT EXISTS trg_claim_evidence_events_no_update
                BEFORE UPDATE ON claim_evidence_events
                BEGIN
                    SELECT RAISE(ABORT, 'claim evidence history is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS trg_claim_reviews_no_update
                BEFORE UPDATE ON claim_reviews
                BEGIN
                    SELECT RAISE(ABORT, 'claim review history is append-only');
                END;
                """
            )

    @staticmethod
    def _migrate_claim_evidence(db: sqlite3.Connection) -> None:
        columns = {row["name"] for row in db.execute("PRAGMA table_info(claim_evidence)")}
        if "relation" not in columns:
            db.execute(
                """
                ALTER TABLE claim_evidence
                ADD COLUMN relation TEXT NOT NULL DEFAULT 'supports'
                CHECK(relation IN ('supports','contradicts','qualifies'))
                """
            )
        if "rationale" not in columns:
            db.execute("ALTER TABLE claim_evidence ADD COLUMN rationale TEXT")
        if "linked_at" not in columns:
            # SQLite ALTER TABLE requires a constant default for an added column.
            db.execute("ALTER TABLE claim_evidence ADD COLUMN linked_at TEXT")

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

    def create(self, statement: str, evidence_ids: tuple[str, ...] = ()) -> ClaimRecord:
        if not isinstance(statement, str):
            raise TypeError("Claim statement must be text")
        clean = " ".join(statement.split())
        if not clean:
            raise ValueError("Claim statement must not be empty")
        if len(clean) > 10_000:
            raise ValueError("Claim statement exceeds 10000 characters")

        claim_id = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        unique_evidence_ids = tuple(dict.fromkeys(evidence_ids))
        with self._connect() as db:
            db.execute(
                """
                INSERT OR IGNORE INTO claims(claim_id, statement, status)
                VALUES (?, ?, 'unreviewed')
                """,
                (claim_id, clean),
            )
            for evidence_id in unique_evidence_ids:
                db.execute(
                    """
                    INSERT OR IGNORE INTO claim_evidence(
                        claim_id, evidence_id, relation
                    ) VALUES (?, ?, 'supports')
                    """,
                    (claim_id, evidence_id),
                )

        record = self.get(claim_id)
        if record is None:
            raise RuntimeError("Claim write did not persist")
        return record

    def link_evidence(
        self,
        claim_id: str,
        evidence_id: str,
        relation: str,
        rationale: str,
        actor_id: str,
    ) -> ClaimRecord:
        if relation not in EVIDENCE_RELATIONS:
            raise ValueError("Invalid evidence relation")
        rationale_clean = " ".join(rationale.split())
        actor_clean = actor_id.strip()
        if not rationale_clean:
            raise ValueError("Evidence-link rationale is required")
        if len(rationale_clean) > 4000:
            raise ValueError("Evidence-link rationale exceeds 4000 characters")
        if not actor_clean or len(actor_clean) > 200:
            raise ValueError("A valid actor_id is required")

        with self._connect() as db:
            claim = db.execute("SELECT 1 FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            if claim is None:
                raise ValueError("Unknown claim_id")
            existing = db.execute(
                """
                SELECT relation FROM claim_evidence
                WHERE claim_id=? AND evidence_id=?
                """,
                (claim_id, evidence_id),
            ).fetchone()
            previous_relation = existing["relation"] if existing else None
            db.execute(
                """
                INSERT INTO claim_evidence(
                    claim_id, evidence_id, relation, rationale
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(claim_id, evidence_id) DO UPDATE SET
                    relation=excluded.relation,
                    rationale=excluded.rationale,
                    linked_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                """,
                (claim_id, evidence_id, relation, rationale_clean),
            )
            db.execute(
                """
                INSERT INTO claim_evidence_events(
                    event_id, claim_id, evidence_id, previous_relation,
                    new_relation, actor_id, rationale
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    claim_id,
                    evidence_id,
                    previous_relation,
                    relation,
                    actor_clean,
                    rationale_clean,
                ),
            )
        record = self.get(claim_id)
        if record is None:
            raise RuntimeError("Claim disappeared after linking evidence")
        return record

    def set_status(
        self,
        claim_id: str,
        status: str,
        *,
        reviewer_id: str,
        rationale: str,
    ) -> ClaimRecord | None:
        if status not in CLAIM_STATUSES:
            raise ValueError("Invalid claim status")
        reviewer = reviewer_id.strip()
        reason = " ".join(rationale.split())
        if not reviewer or len(reviewer) > 200:
            raise ValueError("A valid reviewer_id is required")
        if not reason:
            raise ValueError("Review rationale is required")
        if len(reason) > 4000:
            raise ValueError("Review rationale exceeds 4000 characters")

        with self._connect() as db:
            current = db.execute(
                "SELECT status FROM claims WHERE claim_id=?", (claim_id,)
            ).fetchone()
            if current is None:
                return None

            if status == "supported":
                supporting = db.execute(
                    """
                    SELECT 1 FROM claim_evidence
                    WHERE claim_id=? AND relation='supports' LIMIT 1
                    """,
                    (claim_id,),
                ).fetchone()
                if supporting is None:
                    raise ValueError(
                        "A claim requires supporting evidence before it can be supported"
                    )
            elif status == "contradicted":
                contradicting = db.execute(
                    """
                    SELECT 1 FROM claim_evidence
                    WHERE claim_id=? AND relation='contradicts' LIMIT 1
                    """,
                    (claim_id,),
                ).fetchone()
                if contradicting is None:
                    raise ValueError(
                        "A claim requires contradicting evidence before it can be contradicted"
                    )

            db.execute("UPDATE claims SET status=? WHERE claim_id=?", (status, claim_id))
            db.execute(
                """
                INSERT INTO claim_reviews(
                    review_id, claim_id, previous_status, new_status,
                    reviewer_id, rationale
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    claim_id,
                    current["status"],
                    status,
                    reviewer,
                    reason,
                ),
            )

        return self.get(claim_id)

    def get(self, claim_id: str) -> ClaimRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            if row is None:
                return None
            evidence = db.execute(
                """
                SELECT evidence_id, relation, rationale
                FROM claim_evidence WHERE claim_id=?
                ORDER BY evidence_id
                """,
                (claim_id,),
            ).fetchall()
        links = tuple(
            (item["evidence_id"], item["relation"], item["rationale"]) for item in evidence
        )
        return ClaimRecord(
            row["claim_id"],
            row["statement"],
            row["status"],
            tuple(item[0] for item in links),
            row["created_at"],
            links,
        )

    def get_review_history(self, claim_id: str) -> list[ClaimReviewRecord]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT * FROM claim_reviews
                WHERE claim_id=? ORDER BY created_at, review_id
                """,
                (claim_id,),
            ).fetchall()
        return [
            ClaimReviewRecord(
                row["review_id"],
                row["claim_id"],
                row["previous_status"],
                row["new_status"],
                row["reviewer_id"],
                row["rationale"],
                row["created_at"],
            )
            for row in rows
        ]
