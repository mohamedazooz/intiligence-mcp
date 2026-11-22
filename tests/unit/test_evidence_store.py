import hashlib
import sqlite3

import pytest

from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def test_evidence_is_content_addressed_and_deduplicated(tmp_path):
    db = tmp_path / "research.sqlite3"
    source = SourceRegistry(db).add("https://example.org/report")
    store = EvidenceStore(db)
    first = store.save(source.source_id, "captured source text")
    second = store.save(source.source_id, "captured source text")
    assert first == second
    assert first.content_sha256 == hashlib.sha256(b"captured source text").hexdigest()
    assert store.get(first.evidence_id) == first


def test_evidence_cannot_reference_unknown_source(tmp_path):
    db = tmp_path / "research.sqlite3"
    SourceRegistry(db)
    store = EvidenceStore(db)
    with pytest.raises(sqlite3.IntegrityError):
        store.save("missing-source", "unlinked evidence")
