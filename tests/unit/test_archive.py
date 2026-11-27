import json

import pytest

from intiligence_mcp.acquisition.http import FetchResult
from intiligence_mcp.research import archive


@pytest.mark.asyncio
async def test_archive_lookup_returns_bounded_exact_url_metadata(monkeypatch):
    calls = []
    target = "https://example.org/report"

    def fake_validate(url, **_kwargs):
        calls.append(url)
        return "example.org"

    async def fake_fetch(url, **_kwargs):
        payload = [
            ["timestamp", "original", "mimetype", "statuscode", "digest", "length"],
            ["20261120120000", target, "text/html", "200", "abc123", "5000"],
        ]
        body = json.dumps(payload).encode()
        return FetchResult(200, body, body.decode(), url, "application/json", {}, ())

    monkeypatch.setattr(archive, "validate_url", fake_validate)
    monkeypatch.setattr(archive, "fetch_response_details", fake_fetch)

    result = await archive.search_web_archive(target, 5)

    assert result["status"] == "ok"
    assert result["count"] == 1
    assert result["captures"][0]["timestamp"] == "20261120120000"
    assert result["captures"][0]["snapshot_url"] == (
        "https://web.archive.org/web/20261120120000/https://example.org/report"
    )
    assert calls == [target, target]
    assert result["content_is_untrusted"] is True


@pytest.mark.asyncio
async def test_archive_rejects_invalid_limit():
    with pytest.raises(ValueError):
        await archive.search_web_archive("https://example.org", 21)
