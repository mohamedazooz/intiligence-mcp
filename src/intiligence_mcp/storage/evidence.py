"""Content-addressed evidence, per-capture artifacts, and immutable excerpt capsules."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    source_id: str
    content_sha256: str
    content: str
    captured_at: str


@dataclass(frozen=True, slots=True)
class CaptureRecord:
    artifact_id: str
    source_id: str
    raw_sha256: str
    byte_size: int
    media_type: str | None
    http_status: int
    final_url: str
    response_headers: dict[str, str]
    redirect_chain: tuple[dict[str, Any], ...]
    captured_at: str
    evidence_id: str
    representation_id: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class EvidenceCapsule:
    capsule_id: str
    evidence_id: str
    representation_id: str
    artifact_id: str
    start_offset: int
    end_offset: int
    excerpt: str
    excerpt_sha256: str
    locator: dict[str, Any]
    created_at: str


class EvidenceIntegrityError(RuntimeError):
    """Stored evidence bytes no longer match their recorded SHA-256 digest."""


class EvidenceStore:
    """SQLite-backed evidence store.

    Evidence text remains content-addressed for backwards compatibility. Each
    acquisition is separately recorded as an artifact/capture, while identical
    raw bodies are stored once in artifact_blobs. Excerpts are immutable through
    this API and always resolve to a specific representation and artifact.
    """

    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    content_sha256 TEXT NOT NULL,
                    content TEXT NOT NULL,
                    captured_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    UNIQUE(source_id, content_sha256)
                );
                CREATE INDEX IF NOT EXISTS idx_evidence_source
                    ON evidence(source_id, captured_at);

                CREATE TABLE IF NOT EXISTS artifact_blobs (
                    raw_sha256 TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    byte_size INTEGER NOT NULL CHECK(byte_size >= 0),
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    raw_sha256 TEXT NOT NULL REFERENCES artifact_blobs(raw_sha256),
                    media_type TEXT,
                    http_status INTEGER NOT NULL,
                    final_url TEXT NOT NULL,
                    response_headers_json TEXT NOT NULL DEFAULT '{}',
                    redirect_chain_json TEXT NOT NULL DEFAULT '[]',
                    captured_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE INDEX IF NOT EXISTS idx_artifacts_source_capture
                    ON artifacts(source_id, captured_at);

                CREATE TABLE IF NOT EXISTS representations (
                    representation_id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    extractor_name TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    UNIQUE(artifact_id, extractor_name, extractor_version)
                );
                CREATE INDEX IF NOT EXISTS idx_representations_evidence
                    ON representations(evidence_id, created_at);

                CREATE TABLE IF NOT EXISTS evidence_capsules (
                    capsule_id TEXT PRIMARY KEY,
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    representation_id TEXT NOT NULL REFERENCES representations(representation_id),
                    start_offset INTEGER NOT NULL CHECK(start_offset >= 0),
                    end_offset INTEGER NOT NULL CHECK(end_offset > start_offset),
                    excerpt TEXT NOT NULL,
                    excerpt_sha256 TEXT NOT NULL,
                    locator_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    UNIQUE(representation_id, start_offset, end_offset, excerpt_sha256)
                );

                CREATE TRIGGER IF NOT EXISTS trg_evidence_capsules_no_update
                BEFORE UPDATE ON evidence_capsules
                BEGIN
                    SELECT RAISE(ABORT, 'evidence capsules are immutable');
                END;
                """
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

    @staticmethod
    def _evidence_id(source_id: str, content_sha256: str) -> str:
        return hashlib.sha256(f"{source_id}:{content_sha256}".encode()).hexdigest()

    def save(self, source_id: str, content: str) -> EvidenceRecord:
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        evidence_id = self._evidence_id(source_id, digest)
        with self._connect() as db:
            db.execute(
                """
                INSERT OR IGNORE INTO evidence
                    (evidence_id, source_id, content_sha256, content)
                VALUES (?, ?, ?, ?)
                """,
                (evidence_id, source_id, digest, content),
            )
            row = db.execute(
                "SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,)
            ).fetchone()
        if row is None:
            raise RuntimeError("Evidence write did not persist")
        return EvidenceRecord(
            row["evidence_id"],
            row["source_id"],
            row["content_sha256"],
            row["content"],
            row["captured_at"],
        )

    def capture(
        self,
        source_id: str,
        raw_content: bytes | str,
        extracted_content: str,
        *,
        media_type: str | None,
        http_status: int,
        final_url: str,
        response_headers: dict[str, str] | None = None,
        redirect_chain: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        extractor_name: str = "trafilatura",
        extractor_version: str = "vendored-2.3.1",
    ) -> CaptureRecord:
        """Persist a distinct capture, deduplicated raw blob, and parser representation."""
        if not 100 <= http_status <= 599:
            raise ValueError("http_status must be a valid HTTP status")
        if not final_url.strip():
            raise ValueError("final_url must not be empty")
        if not extractor_name.strip() or not extractor_version.strip():
            raise ValueError("Extractor name and version are required")

        raw_bytes = (
            raw_content.encode("utf-8") if isinstance(raw_content, str) else bytes(raw_content)
        )
        raw_digest = hashlib.sha256(raw_bytes).hexdigest()
        extracted_digest = hashlib.sha256(extracted_content.encode("utf-8")).hexdigest()
        evidence_id = self._evidence_id(source_id, extracted_digest)
        artifact_id = uuid.uuid4().hex
        representation_id = hashlib.sha256(
            f"{artifact_id}:{extractor_name}:{extractor_version}:{extracted_digest}".encode()
        ).hexdigest()

        headers = {
            str(key).lower(): str(value)
            for key, value in (response_headers or {}).items()
            if str(key).lower()
            in {
                "content-type",
                "content-length",
                "content-encoding",
                "etag",
                "last-modified",
                "date",
                "cache-control",
            }
        }
        headers_json = json.dumps(headers, sort_keys=True, separators=(",", ":"))
        redirects_json = json.dumps(list(redirect_chain), sort_keys=True, separators=(",", ":"))

        with self._connect() as db:
            db.execute(
                """
                INSERT OR IGNORE INTO evidence
                    (evidence_id, source_id, content_sha256, content)
                VALUES (?, ?, ?, ?)
                """,
                (evidence_id, source_id, extracted_digest, extracted_content),
            )
            db.execute(
                """
                INSERT OR IGNORE INTO artifact_blobs(raw_sha256, content, byte_size)
                VALUES (?, ?, ?)
                """,
                (raw_digest, sqlite3.Binary(raw_bytes), len(raw_bytes)),
            )
            db.execute(
                """
                INSERT INTO artifacts(
                    artifact_id, source_id, raw_sha256, media_type, http_status,
                    final_url, response_headers_json, redirect_chain_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    source_id,
                    raw_digest,
                    media_type,
                    http_status,
                    final_url,
                    headers_json,
                    redirects_json,
                ),
            )
            db.execute(
                """
                INSERT INTO representations(
                    representation_id, artifact_id, evidence_id, extractor_name,
                    extractor_version, content_sha256
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    representation_id,
                    artifact_id,
                    evidence_id,
                    extractor_name,
                    extractor_version,
                    extracted_digest,
                ),
            )
            row = db.execute(
                "SELECT captured_at FROM artifacts WHERE artifact_id=?", (artifact_id,)
            ).fetchone()

        if row is None:
            raise RuntimeError("Artifact capture did not persist")
        return CaptureRecord(
            artifact_id=artifact_id,
            source_id=source_id,
            raw_sha256=raw_digest,
            byte_size=len(raw_bytes),
            media_type=media_type,
            http_status=http_status,
            final_url=final_url,
            response_headers=headers,
            redirect_chain=tuple(dict(item) for item in redirect_chain),
            captured_at=row["captured_at"],
            evidence_id=evidence_id,
            representation_id=representation_id,
            content_sha256=extracted_digest,
        )

    def latest_for_source(self, source_id: str) -> EvidenceRecord | None:
        """Return the newest stored evidence representation for one source."""
        with self._connect() as db:
            row = db.execute(
                """SELECT evidence_id FROM evidence
                   WHERE source_id=? ORDER BY captured_at DESC,evidence_id DESC LIMIT 1""",
                (source_id,),
            ).fetchone()
        return self.get(row["evidence_id"]) if row is not None else None

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,)
            ).fetchone()
        if row is None:
            return None
        content = row["content"]
        actual_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if actual_digest != row["content_sha256"]:
            raise EvidenceIntegrityError("Evidence content hash verification failed")
        return EvidenceRecord(
            row["evidence_id"],
            row["source_id"],
            row["content_sha256"],
            content,
            row["captured_at"],
        )

    def get_capture(self, artifact_id: str) -> CaptureRecord | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT a.*, b.byte_size, r.representation_id, r.evidence_id,
                       r.content_sha256
                FROM artifacts a
                JOIN artifact_blobs b ON b.raw_sha256=a.raw_sha256
                JOIN representations r ON r.artifact_id=a.artifact_id
                WHERE a.artifact_id=?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            return None
        return CaptureRecord(
            artifact_id=row["artifact_id"],
            source_id=row["source_id"],
            raw_sha256=row["raw_sha256"],
            byte_size=row["byte_size"],
            media_type=row["media_type"],
            http_status=row["http_status"],
            final_url=row["final_url"],
            response_headers=json.loads(row["response_headers_json"]),
            redirect_chain=tuple(json.loads(row["redirect_chain_json"])),
            captured_at=row["captured_at"],
            evidence_id=row["evidence_id"],
            representation_id=row["representation_id"],
            content_sha256=row["content_sha256"],
        )

    def get_artifact_content(self, artifact_id: str) -> bytes | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT b.content, b.raw_sha256 FROM artifact_blobs b
                JOIN artifacts a ON a.raw_sha256=b.raw_sha256
                WHERE a.artifact_id=?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            return None
        content = bytes(row["content"])
        if hashlib.sha256(content).hexdigest() != row["raw_sha256"]:
            raise EvidenceIntegrityError("Raw artifact hash verification failed")
        return content

    def create_capsule(
        self,
        evidence_id: str,
        start_offset: int,
        end_offset: int,
        *,
        locator: dict[str, Any] | None = None,
        representation_id: str | None = None,
        max_excerpt_chars: int = 20_000,
    ) -> EvidenceCapsule:
        evidence = self.get(evidence_id)
        if evidence is None:
            raise ValueError("Unknown evidence_id")
        if (
            isinstance(start_offset, bool)
            or isinstance(end_offset, bool)
            or not isinstance(start_offset, int)
            or not isinstance(end_offset, int)
            or start_offset < 0
            or end_offset <= start_offset
            or end_offset > len(evidence.content)
        ):
            raise ValueError("Invalid evidence offsets")
        if end_offset - start_offset > max_excerpt_chars:
            raise ValueError(f"Evidence excerpt exceeds {max_excerpt_chars} characters")

        with self._connect() as db:
            if representation_id is None:
                row = db.execute(
                    """
                    SELECT representation_id FROM representations
                    WHERE evidence_id=? ORDER BY created_at DESC LIMIT 1
                    """,
                    (evidence_id,),
                ).fetchone()
                if row is None:
                    raise ValueError("Evidence has no captured artifact representation")
                representation_id = row["representation_id"]
            row = db.execute(
                """
                SELECT artifact_id FROM representations
                WHERE representation_id=? AND evidence_id=?
                """,
                (representation_id, evidence_id),
            ).fetchone()
            if row is None:
                raise ValueError("Representation does not belong to this evidence")

            excerpt = evidence.content[start_offset:end_offset]
            excerpt_digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
            locator_value = locator or {
                "kind": "character_range",
                "start": start_offset,
                "end": end_offset,
            }
            if not isinstance(locator_value, dict):
                raise TypeError("locator must be a JSON object")
            locator_json = json.dumps(
                locator_value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            if len(locator_json) > 4096:
                raise ValueError("locator metadata exceeds 4096 characters")
            capsule_id = hashlib.sha256(
                (
                    f"{representation_id}:{start_offset}:{end_offset}:"
                    f"{excerpt_digest}:{locator_json}"
                ).encode()
            ).hexdigest()
            db.execute(
                """
                INSERT OR IGNORE INTO evidence_capsules(
                    capsule_id, evidence_id, representation_id, start_offset,
                    end_offset, excerpt, excerpt_sha256, locator_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    capsule_id,
                    evidence_id,
                    representation_id,
                    start_offset,
                    end_offset,
                    excerpt,
                    excerpt_digest,
                    locator_json,
                ),
            )
            created = db.execute(
                "SELECT created_at FROM evidence_capsules WHERE capsule_id=?",
                (capsule_id,),
            ).fetchone()

        if created is None:
            raise RuntimeError("Evidence capsule did not persist")
        return EvidenceCapsule(
            capsule_id=capsule_id,
            evidence_id=evidence_id,
            representation_id=representation_id,
            artifact_id=row["artifact_id"],
            start_offset=start_offset,
            end_offset=end_offset,
            excerpt=excerpt,
            excerpt_sha256=excerpt_digest,
            locator=locator_value,
            created_at=created["created_at"],
        )

    def get_capsule(self, capsule_id: str) -> EvidenceCapsule | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT c.*, r.artifact_id FROM evidence_capsules c
                JOIN representations r ON r.representation_id=c.representation_id
                WHERE c.capsule_id=?
                """,
                (capsule_id,),
            ).fetchone()
        if row is None:
            return None
        excerpt = row["excerpt"]
        if hashlib.sha256(excerpt.encode("utf-8")).hexdigest() != row["excerpt_sha256"]:
            raise EvidenceIntegrityError("Evidence capsule hash verification failed")
        return EvidenceCapsule(
            capsule_id=row["capsule_id"],
            evidence_id=row["evidence_id"],
            representation_id=row["representation_id"],
            artifact_id=row["artifact_id"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            excerpt=row["excerpt"],
            excerpt_sha256=row["excerpt_sha256"],
            locator=json.loads(row["locator_json"]),
            created_at=row["created_at"],
        )
