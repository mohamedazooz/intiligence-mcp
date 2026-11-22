"""Small durable source registry with canonical URL deduplication and provenance fields."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    url: str
    host: str
    title: str | None
    first_seen_at: str


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Only absolute HTTP(S) source URLs are accepted")
    if parts.username or parts.password:
        raise ValueError("Source URL must not contain embedded credentials")
    host = parts.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    port = parts.port
    netloc = host if port is None or (scheme, port) in {("http", 80), ("https", 443)} else f"{host}:{port}"
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


class SourceRegistry:
    def __init__(self, database_path: str | Path) -> None:
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                host TEXT NOT NULL,
                title TEXT,
                first_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_sources_host ON sources(host)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def add(self, url: str, title: str | None = None) -> SourceRecord:
        canonical = canonicalize_url(url)
        host = urlsplit(canonical).hostname or ""
        source_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO sources(source_id,url,host,title) VALUES(?,?,?,?)", (source_id, canonical, host, title))
            row = db.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        if row is None:
            raise RuntimeError("Source registry write did not persist")
        return SourceRecord(row["source_id"], row["url"], row["host"], row["title"], row["first_seen_at"])

    def get(self, source_id: str) -> SourceRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        if row is None:
            return None
        return SourceRecord(row["source_id"], row["url"], row["host"], row["title"], row["first_seen_at"])
