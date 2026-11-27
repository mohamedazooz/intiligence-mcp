"""Temporal freshness metadata and adaptive revalidation scheduling."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    name: str
    base_ttl_seconds: int
    min_ttl_seconds: int
    max_ttl_seconds: int
    max_stale_seconds: int

POLICIES: dict[str, FreshnessPolicy] = {
    "web": FreshnessPolicy("web", 86_400, 900, 2_592_000, 7_776_000),
    "news": FreshnessPolicy("news", 900, 300, 7_200, 86_400),
    "github": FreshnessPolicy("github", 3_600, 300, 86_400, 604_800),
    "dns": FreshnessPolicy("dns", 3_600, 60, 86_400, 604_800),
    "rdap": FreshnessPolicy("rdap", 86_400, 3_600, 604_800, 2_592_000),
    "ct": FreshnessPolicy("ct", 21_600, 900, 172_800, 1_209_600),
    "onion": FreshnessPolicy("onion", 86_400, 3_600, 604_800, 2_592_000),
}

@dataclass(frozen=True, slots=True)
class FreshnessRecord:
    source_id: str
    policy_name: str
    last_verified_at: str | None
    next_refresh_at: str | None
    state: str
    etag: str | None
    last_modified: str | None
    last_raw_sha256: str | None
    last_http_status: int | None
    consecutive_failures: int
    unchanged_checks: int
    last_changed_at: str | None
    change_interval_seconds: float | None

@dataclass(frozen=True, slots=True)
class DueSource:
    source_id: str
    url: str
    policy_name: str
    state: str

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def _parse(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

class FreshnessStore:
    """Stores freshness state separately from immutable evidence snapshots."""

    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_freshness (
                    source_id TEXT PRIMARY KEY REFERENCES sources(source_id),
                    policy_name TEXT NOT NULL DEFAULT 'web',
                    last_verified_at TEXT,
                    next_refresh_at TEXT,
                    state TEXT NOT NULL DEFAULT 'unknown'
                        CHECK(state IN ('unknown','fresh','stale','expired')),
                    etag TEXT,
                    last_modified TEXT,
                    last_raw_sha256 TEXT,
                    last_http_status INTEGER,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    unchanged_checks INTEGER NOT NULL DEFAULT 0,
                    last_changed_at TEXT,
                    change_interval_seconds REAL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_freshness_due
                    ON source_freshness(state, next_refresh_at);
                CREATE TABLE IF NOT EXISTS freshness_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    checked_at TEXT NOT NULL,
                    outcome TEXT NOT NULL CHECK(outcome IN
                        ('changed','unchanged','not_modified','failed','challenge')),
                    http_status INTEGER,
                    raw_sha256 TEXT,
                    error_code TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_freshness_events_source
                    ON freshness_events(source_id, checked_at);
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
    def _record(row: sqlite3.Row) -> FreshnessRecord:
        return FreshnessRecord(
            source_id=row["source_id"],
            policy_name=row["policy_name"],
            last_verified_at=row["last_verified_at"],
            next_refresh_at=row["next_refresh_at"],
            state=row["state"],
            etag=row["etag"],
            last_modified=row["last_modified"],
            last_raw_sha256=row["last_raw_sha256"],
            last_http_status=row["last_http_status"],
            consecutive_failures=row["consecutive_failures"],
            unchanged_checks=row["unchanged_checks"],
            last_changed_at=row["last_changed_at"],
            change_interval_seconds=row["change_interval_seconds"],
        )

    def ensure(self, source_id: str, policy_name: str = "web") -> FreshnessRecord:
        if policy_name not in POLICIES:
            raise ValueError(f"Unknown freshness policy: {policy_name}")
        now = _stamp(_now())
        with self._connect() as db:
            db.execute(
                """INSERT OR IGNORE INTO source_freshness
                   (source_id,policy_name,next_refresh_at,state,updated_at)
                   VALUES(?,?,?,'unknown',?)""",
                (source_id, policy_name, now, now),
            )
            row = db.execute(
                "SELECT * FROM source_freshness WHERE source_id=?", (source_id,)
            ).fetchone()
        if row is None:
            raise RuntimeError("Freshness record was not created")
        return self._record(row)

    def get(self, source_id: str) -> FreshnessRecord | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM source_freshness WHERE source_id=?", (source_id,)
            ).fetchone()
        if row is None:
            return None
        record = self._record(row)
        if record.last_verified_at is None:
            return record
        policy = POLICIES.get(record.policy_name, POLICIES["web"])
        verified = _parse(record.last_verified_at)
        next_refresh = _parse(record.next_refresh_at)
        age = (_now() - verified).total_seconds() if verified else 0
        state = record.state
        if age > policy.max_stale_seconds:
            state = "expired"
        elif next_refresh is not None and _now() >= next_refresh and state == "fresh":
            state = "stale"
        if state == record.state:
            return record
        values = record.__dict__ if hasattr(record, "__dict__") else None
        del values
        return FreshnessRecord(
            record.source_id, record.policy_name, record.last_verified_at,
            record.next_refresh_at, state, record.etag, record.last_modified,
            record.last_raw_sha256, record.last_http_status,
            record.consecutive_failures, record.unchanged_checks,
            record.last_changed_at, record.change_interval_seconds,
        )

    def conditional_headers(self, source_id: str) -> dict[str, str]:
        record = self.get(source_id)
        if record is None:
            return {}
        headers: dict[str, str] = {}
        if record.etag:
            headers["If-None-Match"] = record.etag
        elif record.last_modified:
            headers["If-Modified-Since"] = record.last_modified
        return headers

    @staticmethod
    def _next_ttl(record: FreshnessRecord, policy: FreshnessPolicy) -> int:
        ttl = float(policy.base_ttl_seconds)
        if record.change_interval_seconds and record.change_interval_seconds > 0:
            ttl = min(ttl, record.change_interval_seconds / 3.0)
        if record.unchanged_checks >= 3:
            ttl = min(policy.max_ttl_seconds, ttl * min(4.0, 1.0 + record.unchanged_checks / 3.0))
        return int(max(policy.min_ttl_seconds, min(policy.max_ttl_seconds, ttl)))

    def mark_verified(
        self, source_id: str, *, raw_sha256: str | None, http_status: int,
        etag: str | None = None, last_modified: str | None = None,
        not_modified: bool = False,
    ) -> FreshnessRecord:
        previous = self.ensure(source_id)
        now_dt = _now()
        now = _stamp(now_dt)
        policy = POLICIES[previous.policy_name]
        changed = (
            not not_modified
            and raw_sha256 is not None
            and previous.last_raw_sha256 != raw_sha256
        )
        interval = previous.change_interval_seconds
        last_changed_at = previous.last_changed_at
        if changed:
            old_change = _parse(last_changed_at)
            if old_change is not None:
                sample = max(1.0, (now_dt - old_change).total_seconds())
                interval = sample if interval is None else (0.7 * interval + 0.3 * sample)
            last_changed_at = now
        unchanged = 0 if changed else previous.unchanged_checks + 1
        updated = FreshnessRecord(
            previous.source_id, previous.policy_name, now, None, "fresh",
            (
                (etag or previous.etag) if not_modified else etag
            ),
            (
                (last_modified or previous.last_modified)
                if not_modified
                else last_modified
            ),
            raw_sha256 if raw_sha256 is not None else previous.last_raw_sha256,
            http_status, 0, unchanged, last_changed_at, interval,
        )
        ttl = self._next_ttl(updated, policy)
        next_refresh = _stamp(now_dt + timedelta(seconds=ttl))
        outcome = "not_modified" if not_modified else ("changed" if changed else "unchanged")
        with self._connect() as db:
            db.execute(
                """UPDATE source_freshness SET last_verified_at=?,next_refresh_at=?,
                   state='fresh',etag=?,last_modified=?,last_raw_sha256=?,
                   last_http_status=?,consecutive_failures=0,unchanged_checks=?,
                   last_changed_at=?,change_interval_seconds=?,updated_at=?
                   WHERE source_id=?""",
                (now, next_refresh, updated.etag, updated.last_modified,
                 updated.last_raw_sha256, http_status, unchanged, last_changed_at,
                 interval, now, source_id),
            )
            db.execute(
                """INSERT INTO freshness_events
                   (source_id,checked_at,outcome,http_status,raw_sha256)
                   VALUES(?,?,?,?,?)""",
                (source_id, now, outcome, http_status, updated.last_raw_sha256),
            )
        return self.get(source_id)  # type: ignore[return-value]

    def mark_failure(self, source_id: str, *, error_code: str, http_status: int | None = None) -> FreshnessRecord:
        previous = self.ensure(source_id)
        now_dt = _now()
        now = _stamp(now_dt)
        failures = previous.consecutive_failures + 1
        backoff = min(3_600, 30 * (2 ** min(failures - 1, 7)))
        policy = POLICIES[previous.policy_name]
        verified = _parse(previous.last_verified_at)
        age = (now_dt - verified).total_seconds() if verified else float("inf")
        state = "unknown" if verified is None else (
            "expired" if age > policy.max_stale_seconds else "stale"
        )
        with self._connect() as db:
            db.execute(
                """UPDATE source_freshness SET state=?,last_http_status=?,
                   consecutive_failures=?,next_refresh_at=?,updated_at=?
                   WHERE source_id=?""",
                (state, http_status, failures,
                 _stamp(now_dt + timedelta(seconds=backoff)), now, source_id),
            )
            db.execute(
                """INSERT INTO freshness_events
                   (source_id,checked_at,outcome,http_status,error_code)
                   VALUES(?,?,'failed',?,?)""",
                (source_id, now, http_status, error_code[:120]),
            )
        return self.get(source_id)  # type: ignore[return-value]

    def due(
        self,
        limit: int = 20,
        *,
        exclude_policy_names: tuple[str, ...] = (),
    ) -> list[DueSource]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if not isinstance(exclude_policy_names, tuple) or any(
            name not in POLICIES for name in exclude_policy_names
        ):
            raise ValueError("exclude_policy_names must be a tuple of known policy names")
        now = _stamp(_now())
        exclusions = ""
        params: tuple[object, ...] = (now, limit)
        if exclude_policy_names:
            placeholders = ",".join("?" for _ in exclude_policy_names)
            exclusions = f" AND COALESCE(f.policy_name,'web') NOT IN ({placeholders})"
            params = (now, *exclude_policy_names, limit)
        with self._connect() as db:
            rows = db.execute(
                """SELECT s.source_id,s.url,COALESCE(f.policy_name,'web') policy_name,
                          COALESCE(f.state,'unknown') state
                   FROM sources s LEFT JOIN source_freshness f ON f.source_id=s.source_id
                   WHERE (f.next_refresh_at IS NULL OR f.next_refresh_at<=?)"""
                + exclusions
                + " ORDER BY COALESCE(f.next_refresh_at,'') ASC LIMIT ?",
                params,
            ).fetchall()
        return [DueSource(row["source_id"], row["url"], row["policy_name"], row["state"]) for row in rows]
