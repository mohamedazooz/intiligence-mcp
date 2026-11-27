"""Evidence-linked IOC extraction and lookup.

Only passive indicators are extracted. Email addresses, credentials, and wallet
identifiers are intentionally excluded to avoid turning evidence parsing into
personal-data harvesting.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

_IPV4_CANDIDATE = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
_IPV6_CANDIDATE = re.compile(
    r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])"
)
_DOMAIN_CANDIDATE = re.compile(
    r"(?<![A-Za-z0-9._@-])"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}"
    r"(?![A-Za-z0-9.-])"
)
_CVE_CANDIDATE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
_SHA256_CANDIDATE = re.compile(r"\b[a-fA-F0-9]{64}\b")


@dataclass(frozen=True, slots=True)
class Indicator:
    indicator_id: str
    kind: str
    value: str
    normalized_value: str


class IndicatorStore:
    """SQLite indicator index with explicit evidence provenance."""

    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS indicators (
                    indicator_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    normalized_value TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    UNIQUE(kind, normalized_value)
                );
                CREATE TABLE IF NOT EXISTS indicator_evidence (
                    indicator_id TEXT NOT NULL REFERENCES indicators(indicator_id),
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    first_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    PRIMARY KEY(indicator_id, evidence_id)
                );
                CREATE INDEX IF NOT EXISTS idx_indicator_evidence_evidence
                    ON indicator_evidence(evidence_id);
                CREATE INDEX IF NOT EXISTS idx_indicators_normalized
                    ON indicators(normalized_value);
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
    def _normalize(kind: str, value: str) -> str:
        if kind in {"ipv4", "ipv6"}:
            return ipaddress.ip_address(value).compressed.lower()
        if kind == "domain":
            return value.rstrip(".").encode("idna").decode("ascii").lower()
        return value.lower() if kind == "sha256" else value.upper()

    def add_many(self, evidence_id: str, values: list[tuple[str, str]]) -> list[Indicator]:
        records: list[Indicator] = []
        with self._connect() as db:
            exists = db.execute(
                "SELECT 1 FROM evidence WHERE evidence_id=?", (evidence_id,)
            ).fetchone()
            if exists is None:
                raise ValueError(f"Unknown evidence_id: {evidence_id}")

            for kind, value in values:
                normalized = self._normalize(kind, value)
                indicator_id = hashlib.sha256(f"{kind}:{normalized}".encode()).hexdigest()
                db.execute(
                    """
                    INSERT OR IGNORE INTO indicators
                        (indicator_id, kind, value, normalized_value)
                    VALUES (?, ?, ?, ?)
                    """,
                    (indicator_id, kind, value, normalized),
                )
                db.execute(
                    """
                    INSERT OR IGNORE INTO indicator_evidence(indicator_id, evidence_id)
                    VALUES (?, ?)
                    """,
                    (indicator_id, evidence_id),
                )
                row = db.execute(
                    "SELECT indicator_id, kind, value, normalized_value "
                    "FROM indicators WHERE indicator_id=?",
                    (indicator_id,),
                ).fetchone()
                if row is not None:
                    records.append(
                        Indicator(
                            row["indicator_id"],
                            row["kind"],
                            row["value"],
                            row["normalized_value"],
                        )
                    )
        return records

    @staticmethod
    def _normalize_query(value: str) -> str:
        candidate = value.strip()
        try:
            return ipaddress.ip_address(candidate).compressed.lower()
        except ValueError:
            pass
        if _CVE_CANDIDATE.fullmatch(candidate):
            return candidate.upper()
        if _SHA256_CANDIDATE.fullmatch(candidate):
            return candidate.lower()
        if _DOMAIN_CANDIDATE.fullmatch(candidate):
            try:
                return candidate.rstrip(".").encode("idna").decode("ascii").lower()
            except UnicodeError:
                return candidate.lower()
        return candidate.lower()

    def find(self, value: str, kind: str | None = None) -> list[dict]:
        normalized_value = self._normalize(kind, value) if kind else self._normalize_query(value)
        query = """
            SELECT i.indicator_id, i.kind, i.value, i.normalized_value,
                   GROUP_CONCAT(ie.evidence_id) AS evidence_ids,
                   COUNT(ie.evidence_id) AS evidence_count
            FROM indicators i
            LEFT JOIN indicator_evidence ie ON ie.indicator_id=i.indicator_id
            WHERE LOWER(i.normalized_value)=LOWER(?)
        """
        params: list[str] = [normalized_value]
        if kind:
            query += " AND i.kind=?"
            params.append(kind)
        query += " GROUP BY i.indicator_id ORDER BY i.kind"
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [
            {
                "indicator_id": row["indicator_id"],
                "kind": row["kind"],
                "value": row["value"],
                "normalized_value": row["normalized_value"],
                "evidence_ids": (row["evidence_ids"] or "").split(",")
                if row["evidence_ids"]
                else [],
                "evidence_count": row["evidence_count"],
            }
            for row in rows
        ]


def extract_indicators(text: str, *, max_per_kind: int = 100) -> list[tuple[str, str]]:
    """Extract validated, deduplicated network and threat indicators from text."""
    if max_per_kind < 1:
        raise ValueError("max_per_kind must be positive")

    found: dict[tuple[str, str], None] = {}

    def add(kind: str, raw: str) -> None:
        try:
            normalized = IndicatorStore._normalize(kind, raw)
        except (ValueError, UnicodeError):
            return
        found[(kind, normalized)] = None

    for raw in _IPV4_CANDIDATE.findall(text):
        try:
            parsed = ipaddress.ip_address(raw)
            if parsed.version == 4:
                add("ipv4", parsed.compressed)
        except ValueError:
            continue

    for raw in _IPV6_CANDIDATE.findall(text):
        try:
            parsed = ipaddress.ip_address(raw)
            if parsed.version == 6:
                add("ipv6", parsed.compressed)
        except ValueError:
            continue

    for raw in _DOMAIN_CANDIDATE.findall(text):
        candidate = raw.rstrip(".")
        try:
            ascii_name = candidate.encode("idna").decode("ascii").lower()
        except UnicodeError:
            continue
        labels = ascii_name.split(".")
        if (
            len(ascii_name) <= 253
            and all(1 <= len(label) <= 63 for label in labels)
            and not all(label.isdigit() for label in labels)
        ):
            add("domain", ascii_name)

    for raw in _CVE_CANDIDATE.findall(text):
        add("cve", raw)
    for raw in _SHA256_CANDIDATE.findall(text):
        add("sha256", raw)

    counts: dict[str, int] = {}
    output: list[tuple[str, str]] = []
    for kind, normalized in sorted(found):
        if counts.get(kind, 0) >= max_per_kind:
            continue
        counts[kind] = counts.get(kind, 0) + 1
        output.append((kind, normalized))
    return output
