import hashlib

import pytest

from intiligence_mcp.research import facade
from intiligence_mcp.research.facade import ResearchFacade
from intiligence_mcp.research.search import SearchResult
from intiligence_mcp.research.refresh import RefreshService
from intiligence_mcp.storage.challenges import AccessChallengeStore
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.freshness import FreshnessStore
from intiligence_mcp.storage.source_registry import SourceRegistry


@pytest.mark.asyncio
async def test_research_facade_compiles_intent_into_compact_verified_packet(tmp_path, monkeypatch):
    database = tmp_path / "facade.sqlite3"
    sources = SourceRegistry(database)
    evidence = EvidenceStore(database)
    freshness = FreshnessStore(database)
    challenges = AccessChallengeStore(database)
    refresh = RefreshService(sources, evidence, freshness, challenges)
    service = ResearchFacade(sources, evidence, freshness, refresh)

    async def fake_web_search(_query, limit):
        return _search_results()[:limit]

    monkeypatch.setattr(facade, "search_web", fake_web_search)

    async def fake_specialist(_query, limit):
        return {
            "status": "ok",
            "result_count": 1,
            "results": [{"provider": "crossref", "record_id": "10.5555/a"}][:limit],
        }

    monkeypatch.setattr(facade, "search_deep_web", fake_specialist)
    refresh_calls = []

    async def fake_refresh(source_id, *, force=False):
        refresh_calls.append((source_id, force))
        raw = b"<html><body>Fresh verified content.</body></html>"
        capture = evidence.capture(
            source_id,
            raw,
            "Fresh verified content.",
            media_type="text/html",
            http_status=200,
            final_url=sources.get(source_id).url,
            extractor_name="test",
            extractor_version="1",
        )
        freshness.mark_verified(
            source_id,
            raw_sha256=hashlib.sha256(raw).hexdigest(),
            http_status=200,
        )
        return {"status": "updated", "capture": {"artifact_id": capture.artifact_id}}

    monkeypatch.setattr(refresh, "refresh_source", fake_refresh)

    result = await service.research("  current   evidence  ", max_sources=1)

    assert result["status"] == "ok"
    assert result["intent"] == "current evidence"
    assert result["acquisition"]["evidence_count"] == 1
    assert result["evidence"][0]["excerpt"] == "Fresh verified content."
    assert result["evidence"][0]["freshness"] == "fresh"
    assert result["specialist_discovery"]["result_count"] == 1
    assert refresh_calls[0][1] is True


@pytest.mark.asyncio
async def test_balanced_research_reuses_fresh_evidence(tmp_path, monkeypatch):
    database = tmp_path / "facade-cache.sqlite3"
    sources = SourceRegistry(database)
    evidence = EvidenceStore(database)
    freshness = FreshnessStore(database)
    challenges = AccessChallengeStore(database)
    refresh = RefreshService(sources, evidence, freshness, challenges)
    service = ResearchFacade(sources, evidence, freshness, refresh)

    async def fake_web_search(_query, _limit):
        return _search_results()

    monkeypatch.setattr(facade, "search_web", fake_web_search)

    async def no_specialist(_query, _limit):
        return {"status": "not_requested", "result_count": 0, "results": []}

    monkeypatch.setattr(facade, "search_deep_web", no_specialist)

    async def fake_refresh(source_id, *, force=False):
        raw = b"<html><body>Cached text.</body></html>"
        evidence.capture(
            source_id,
            raw,
            "Cached text.",
            media_type="text/html",
            http_status=200,
            final_url=sources.get(source_id).url,
            extractor_name="test",
            extractor_version="1",
        )
        freshness.mark_verified(source_id, raw_sha256=hashlib.sha256(raw).hexdigest(), http_status=200)
        return {"status": "updated"}

    calls = 0

    async def counted_refresh(source_id, *, force=False):
        nonlocal calls
        calls += 1
        return await fake_refresh(source_id, force=force)

    monkeypatch.setattr(refresh, "refresh_source", counted_refresh)

    await service.research("example topic", max_sources=1)
    second = await service.research("example topic", max_sources=1)

    assert calls == 1
    assert second["evidence"][0]["acquisition_status"] == "reused_fresh_evidence"


def _search_results():
    return [
        SearchResult(
            title="Example Research",
            url="https://example.org/research",
            snippet="A search snippet.",
            engine="test",
            published_at="2026-11-20",
        )
    ]
