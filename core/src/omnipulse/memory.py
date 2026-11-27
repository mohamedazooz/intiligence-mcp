import aiosqlite
import json
import hashlib
from datetime import datetime, timedelta
from .config import settings

DB_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    mode TEXT NOT NULL,
    depth TEXT NOT NULL,
    status TEXT NOT NULL,
    summary_json TEXT,
    token_estimate INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_value TEXT NOT NULL,
    metadata_json TEXT,
    content_hash TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, canonical_value)
);
CREATE TABLE IF NOT EXISTS edges (
    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    evidence_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS coverage_receipts (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    adapter_name TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INTEGER DEFAULT 0,
    items_found INTEGER DEFAULT 0,
    detail_note TEXT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS watch_targets (
    watch_id TEXT PRIMARY KEY,
    target_value TEXT NOT NULL,
    watch_type TEXT NOT NULL,
    cadence_hours INTEGER NOT NULL DEFAULT 24,
    last_hash TEXT,
    selector_state TEXT,
    is_active INTEGER DEFAULT 1,
    last_checked_at DATETIME,
    next_check_at DATETIME
);
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    entity_id UNINDEXED,
    entity_type,
    canonical_value,
    metadata_json
);
"""


class Memory:
    def __init__(self, path: str | None = None):
        self.path = path or settings.sqlite_path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(DB_SCHEMA)
            await db.commit()

    async def record_mission(self, mission_id, goal, mode, depth, status="running", summary=None, tokens=0):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO missions (mission_id,goal,mode,depth,status,summary_json,token_estimate,expires_at) VALUES (?,?,?,?,?,?,?,?)",
                (mission_id, goal, mode, depth, status, json.dumps(summary) if summary else None, tokens, (datetime.utcnow() + timedelta(days=7)).isoformat()),
            )
            await db.commit()

    async def record_coverage(self, mission_id, adapter, status, latency_ms=0, items=0, note=""):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO coverage_receipts (mission_id,adapter_name,status,latency_ms,items_found,detail_note) VALUES (?,?,?,?,?,?)",
                (mission_id, adapter, status, latency_ms, items, note),
            )
            await db.commit()

    async def upsert_entity(self, entity_id, entity_type, canonical_value, metadata=None, content_hash=None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO entities (entity_id,entity_type,canonical_value,metadata_json,content_hash)
                   VALUES (?,?,?,?,?) ON CONFLICT(entity_type,canonical_value) DO UPDATE SET
                   last_seen=CURRENT_TIMESTAMP, metadata_json=excluded.metadata_json, content_hash=excluded.content_hash""",
                (entity_id, entity_type, canonical_value, json.dumps(metadata) if metadata else None, content_hash),
            )
            await db.commit()

    @staticmethod
    def hash_content(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()
