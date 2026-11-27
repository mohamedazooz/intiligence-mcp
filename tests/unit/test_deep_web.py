import json

import pytest

from intiligence_mcp.acquisition.http import FetchResult
from intiligence_mcp.research import deep_web


def _result(url: str, payload: dict) -> FetchResult:
    body = json.dumps(payload).encode()
    return FetchResult(
        status=200,
        body=body,
        text=body.decode(),
        final_url=url,
        media_type="application/json",
        response_headers={"content-type": "application/json"},
        redirect_chain=(),
    )


@pytest.mark.asyncio
async def test_deep_web_queries_crossref_and_europe_pmc(monkeypatch):
    calls = []

    async def fake_fetch(url, **_kwargs):
        calls.append(url)
        if "api.crossref.org" in url:
            return _result(
                url,
                {
                    "message": {
                        "items": [
                            {
                                "DOI": "10.5555/example.1",
                                "title": ["Evidence-led research"],
                                "published": {"date-parts": [[2026, 11, 20]]},
                                "author": [{"given": "Ada", "family": "Lovelace"}],
                                "container-title": ["Journal of Tests"],
                                "type": "journal-article",
                            }
                        ]
                    }
                },
            )
        if "europepmc" in url:
            return _result(
                url,
                {
                    "resultList": {
                        "result": [
                            {
                                "pmcid": "PMC123456",
                                "title": "Public research metadata",
                                "firstPublicationDate": "2026-10-01",
                                "authorString": "A. Researcher",
                                "isOpenAccess": "Y",
                                "abstractText": "A public abstract.",
                            }
                        ]
                    }
                },
            )
        raise AssertionError(url)

    monkeypatch.setattr(deep_web, "fetch_response_details", fake_fetch)
    result = await deep_web.search_deep_web("evidence integrity", 5)

    assert result["status"] == "ok"
    assert result["result_count"] == 2
    assert {item["provider"] for item in result["results"]} == {"crossref", "europe_pmc"}
    assert any(item["record_id"] == "10.5555/example.1" for item in result["results"])
    assert any(item["url"] == "https://europepmc.org/articles/PMC123456" for item in result["results"])
    assert len(calls) == 2
    assert result["results_are_untrusted_discovery_hints"] is True


@pytest.mark.asyncio
async def test_deep_web_provider_failure_is_partial_not_fabricated(monkeypatch):
    from intiligence_mcp.acquisition.http import AcquisitionError

    async def failing_fetch(_query, _limit):
        raise AcquisitionError("provider unreachable")

    async def crossref_empty(_query, _limit):
        return []

    monkeypatch.setattr(deep_web, "_crossref", crossref_empty)
    monkeypatch.setattr(deep_web, "_europe_pmc", failing_fetch)
    result = await deep_web.search_deep_web("test query", 3)

    assert result["status"] == "providers_unavailable_or_no_results"
    assert result["result_count"] == 0
    assert result["provider_status"]["europe_pmc"]["status"] == "AcquisitionError"


@pytest.mark.asyncio
async def test_deep_web_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        await deep_web.search_deep_web(" ", 5)
    with pytest.raises(ValueError):
        await deep_web.search_deep_web("ok", 11)
