import hashlib
import sqlite3

import pytest

from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def test_capture_records_each_fetch_but_deduplicates_raw_blob(tmp_path):
    database = tmp_path / "research.sqlite3"
    source = SourceRegistry(database).add("https://example.org/report")
    store = EvidenceStore(database)

    first = store.capture(
        source.source_id,
        b"<html>raw</html>",
        "alpha evidence omega",
        media_type="text/html; charset=utf-8",
        http_status=200,
        final_url="https://example.org/report",
        response_headers={
            "Content-Type": "text/html",
            "ETag": '"abc"',
            "Set-Cookie": "must-not-be-stored",
        },
        redirect_chain=[
            {
                "status": 302,
                "from": "https://example.org/",
                "to": "https://example.org/report",
            }
        ],
    )
    second = store.capture(
        source.source_id,
        b"<html>raw</html>",
        "alpha evidence omega",
        media_type="text/html",
        http_status=200,
        final_url="https://example.org/report",
    )

    assert first.artifact_id != second.artifact_id
    assert first.representation_id != second.representation_id
    assert first.evidence_id == second.evidence_id
    assert first.raw_sha256 == hashlib.sha256(b"<html>raw</html>").hexdigest()
    assert first.response_headers == {
        "content-type": "text/html",
        "etag": '"abc"',
    }
    assert store.get_artifact_content(first.artifact_id) == b"<html>raw</html>"
    assert store.get_capture(first.artifact_id) == first
    assert store.get_capture(second.artifact_id) == second


def test_capsule_preserves_exact_excerpt_and_artifact_locator(tmp_path):
    database = tmp_path / "research.sqlite3"
    source = SourceRegistry(database).add("https://example.org/report")
    store = EvidenceStore(database)
    capture = store.capture(
        source.source_id,
        b"<p>alpha evidence omega</p>",
        "alpha evidence omega",
        media_type="text/html",
        http_status=200,
        final_url="https://example.org/report",
    )

    capsule = store.create_capsule(
        capture.evidence_id,
        6,
        14,
        locator={"heading": "Findings", "paragraph": 2},
    )

    assert capsule.excerpt == "evidence"
    assert capsule.artifact_id == capture.artifact_id
    assert capsule.excerpt_sha256 == hashlib.sha256(b"evidence").hexdigest()
    assert capsule.locator == {"heading": "Findings", "paragraph": 2}
    assert store.get_capsule(capsule.capsule_id) == capsule


@pytest.mark.parametrize(
    "start,end",
    [(-1, 2), (4, 3), (0, 100), (True, 2), (0, False)],
)
def test_capsule_rejects_invalid_offsets(tmp_path, start, end):
    database = tmp_path / "research.sqlite3"
    source = SourceRegistry(database).add("https://example.org/report")
    store = EvidenceStore(database)
    capture = store.capture(
        source.source_id,
        b"body",
        "short text",
        media_type="text/plain",
        http_status=200,
        final_url="https://example.org/report",
    )
    with pytest.raises(ValueError):
        store.create_capsule(capture.evidence_id, start, end)


def test_capsule_update_is_rejected(tmp_path):
    database = tmp_path / "research.sqlite3"
    source = SourceRegistry(database).add("https://example.org/report")
    store = EvidenceStore(database)
    capture = store.capture(
        source.source_id,
        b"body",
        "short text",
        media_type="text/plain",
        http_status=200,
        final_url="https://example.org/report",
    )
    capsule = store.create_capsule(capture.evidence_id, 0, 5)

    with sqlite3.connect(database) as db, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        db.execute(
            "UPDATE evidence_capsules SET excerpt='changed' WHERE capsule_id=?",
            (capsule.capsule_id,),
        )


def test_capsule_requires_an_artifact_backed_representation(tmp_path):
    database = tmp_path / "research.sqlite3"
    source = SourceRegistry(database).add("https://example.org/report")
    store = EvidenceStore(database)
    evidence = store.save(source.source_id, "legacy text without raw capture")

    with pytest.raises(ValueError, match="captured artifact"):
        store.create_capsule(evidence.evidence_id, 0, 6)
