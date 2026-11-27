from datetime import datetime, timezone

import pytest

from intiligence_mcp.storage.freshness import FreshnessStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def _store(tmp_path):
    database = tmp_path / "freshness.sqlite3"
    source = SourceRegistry(database).add("https://example.org/report")
    return FreshnessStore(database), source


def test_new_source_is_unknown_and_due(tmp_path):
    store, source = _store(tmp_path)
    state = store.ensure(source.source_id)
    assert state.state == "unknown"
    assert store.due(10)[0].source_id == source.source_id


def test_verified_source_stores_http_validators(tmp_path):
    store, source = _store(tmp_path)
    store.ensure(source.source_id, "github")
    state = store.mark_verified(
        source.source_id,
        raw_sha256="a" * 64,
        http_status=200,
        etag='"release-12"',
        last_modified="Mon, 23 Nov 2026 10:00:00 GMT",
    )
    assert state.state == "fresh"
    assert state.last_raw_sha256 == "a" * 64
    assert store.conditional_headers(source.source_id) == {
        "If-None-Match": '"release-12"'
    }


def test_304_revalidation_advances_verified_time_without_replacing_hash(tmp_path):
    store, source = _store(tmp_path)
    store.mark_verified(source.source_id, raw_sha256="b" * 64, http_status=200)
    previous = store.get(source.source_id)
    current = store.mark_verified(
        source.source_id, raw_sha256=None, http_status=304, not_modified=True
    )
    assert current.last_raw_sha256 == "b" * 64
    assert current.last_verified_at >= previous.last_verified_at
    assert current.state == "fresh"


def test_failed_revalidation_never_marks_old_data_fresh(tmp_path):
    store, source = _store(tmp_path)
    store.mark_verified(source.source_id, raw_sha256="c" * 64, http_status=200)
    failed = store.mark_failure(source.source_id, error_code="provider_timeout")
    assert failed.state == "stale"
    assert failed.consecutive_failures == 1
    assert failed.last_raw_sha256 == "c" * 64


def test_invalid_limits_and_policy_are_rejected(tmp_path):
    store, source = _store(tmp_path)
    with pytest.raises(ValueError):
        store.ensure(source.source_id, "unknown-policy")
    with pytest.raises(ValueError):
        store.due(0)
    with pytest.raises(ValueError):
        store.due(True)


def test_change_interval_is_recorded_on_second_content_change(tmp_path):
    store, source = _store(tmp_path)
    store.mark_verified(source.source_id, raw_sha256="1" * 64, http_status=200)
    store.mark_verified(source.source_id, raw_sha256="2" * 64, http_status=200)
    state = store.get(source.source_id)
    assert state.last_raw_sha256 == "2" * 64
    assert state.last_changed_at is not None
    assert state.change_interval_seconds is not None
    assert state.change_interval_seconds > 0



def test_full_200_response_clears_missing_http_validators(tmp_path):
    store, source = _store(tmp_path)
    store.mark_verified(
        source.source_id,
        raw_sha256="d" * 64,
        http_status=200,
        etag='"old"',
        last_modified="Sun, 22 Nov 2026 10:00:00 GMT",
    )
    current = store.mark_verified(
        source.source_id,
        raw_sha256="e" * 64,
        http_status=200,
        etag=None,
        last_modified=None,
    )
    assert current.etag is None
    assert current.last_modified is None
    assert store.conditional_headers(source.source_id) == {}


def test_due_can_exclude_optional_onion_sources(tmp_path):
    database = tmp_path / "freshness.sqlite3"
    registry = SourceRegistry(database)
    web_source = registry.add("https://example.org/report")
    onion_source = registry.add(f"https://{'a' * 56}.onion/report")
    store = FreshnessStore(database)
    store.ensure(web_source.source_id, "web")
    store.ensure(onion_source.source_id, "onion")

    due = store.due(10, exclude_policy_names=("onion",))
    assert web_source.source_id in {item.source_id for item in due}
    assert onion_source.source_id not in {item.source_id for item in due}


def test_due_rejects_invalid_exclusion_policy(tmp_path):
    store, _source = _store(tmp_path)
    with pytest.raises(ValueError):
        store.due(10, exclude_policy_names=["onion"])
    with pytest.raises(ValueError):
        store.due(10, exclude_policy_names=("not-a-policy",))
