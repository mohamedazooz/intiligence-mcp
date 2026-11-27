from intiligence_mcp.acquisition.http import FetchResult
from intiligence_mcp.config import settings
from intiligence_mcp.research import refresh
from intiligence_mcp.research.refresh import RefreshService
from intiligence_mcp.storage.challenges import AccessChallengeStore
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.freshness import FreshnessStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def _service(tmp_path):
    database = tmp_path / "refresh-onion.sqlite3"
    sources = SourceRegistry(database)
    evidence = EvidenceStore(database)
    freshness = FreshnessStore(database)
    challenges = AccessChallengeStore(database)
    service = RefreshService(sources, evidence, freshness, challenges)
    source = sources.add(f"https://{'a' * 56}.onion/report")
    freshness.ensure(source.source_id, "onion")
    return service, source, freshness


async def test_onion_revalidation_uses_tor_adapter_and_http_validators(tmp_path, monkeypatch):
    service, source, freshness = _service(tmp_path)
    freshness.mark_verified(
        source.source_id,
        raw_sha256="f" * 64,
        http_status=200,
        etag='"onion-v1"',
    )
    monkeypatch.setattr(settings, "enable_onion_osint", True)
    calls = []

    async def fake_onion(url, *, conditional_headers=None):
        calls.append((url, conditional_headers))
        return FetchResult(304, b"", "", url, None, {"etag": '"onion-v1"'}, ())

    async def forbidden_clearnet(*_args, **_kwargs):
        raise AssertionError("onion source must never use the clearnet HTTP adapter")

    monkeypatch.setattr(refresh, "fetch_onion_response", fake_onion)
    monkeypatch.setattr(refresh, "fetch_response_details", forbidden_clearnet)

    result = await service.refresh_source(source.source_id, force=True)

    assert result["status"] == "not_modified"
    assert calls == [(source.url, {"If-None-Match": '"onion-v1"'})]
    assert freshness.get(source.source_id).state == "fresh"


async def test_due_refresh_skips_onion_when_tor_is_disabled(tmp_path, monkeypatch):
    service, source, _freshness = _service(tmp_path)
    monkeypatch.setattr(settings, "enable_onion_osint", False)

    async def forbidden_fetch(*_args, **_kwargs):
        raise AssertionError("disabled onion sources must not be fetched")

    monkeypatch.setattr(refresh, "fetch_onion_response", forbidden_fetch)
    monkeypatch.setattr(refresh, "fetch_response_details", forbidden_fetch)

    result = await service.refresh_due(10)

    assert result["checked"] == 0
    assert result["results"] == []
    assert source.source_id
