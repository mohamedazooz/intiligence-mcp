import pytest

from intiligence_mcp.acquisition.http import AcquisitionError
from intiligence_mcp.acquisition.onion import fetch_onion_response, validate_onion_target
from intiligence_mcp.config import settings


def _v3_host(char: str = "a") -> str:
    return char * 56 + ".onion"


def test_onion_target_requires_explicit_v3_allowlist(monkeypatch):
    host = _v3_host()
    monkeypatch.setattr(settings, "onion_source_allowlist", host)
    assert validate_onion_target(f"http://{host}/") == host

    monkeypatch.setattr(settings, "onion_source_allowlist", "")
    with pytest.raises(ValueError, match="ALLOWLIST"):
        validate_onion_target(f"http://{host}/")


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/",
        f"http://{_v3_host()}@example.org/",
        f"http://user:pass@{_v3_host()}/",
        f"http://{_v3_host()}:8080/",
        f"http://{_v3_host()}/#fragment",
        f"http://{'a' * 55}.onion/",
        f"http://{'a' * 57}.onion/",
    ],
)
def test_onion_target_rejects_non_onion_and_unsafe_urls(url, monkeypatch):
    monkeypatch.setattr(settings, "onion_source_allowlist", _v3_host())
    with pytest.raises(ValueError):
        validate_onion_target(url)


@pytest.mark.asyncio
async def test_onion_collection_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "enable_onion_osint", False)
    with pytest.raises(AcquisitionError, match="disabled"):
        await fetch_onion_response(f"http://{_v3_host()}/")


@pytest.mark.asyncio
async def test_onion_rejects_unbounded_or_unapproved_conditional_headers(monkeypatch):
    monkeypatch.setattr(settings, "enable_onion_osint", True)
    monkeypatch.setattr(settings, "onion_source_allowlist", _v3_host())
    monkeypatch.setattr(settings, "tor_socks_url", "socks5://localhost:9050")
    with pytest.raises(ValueError, match="cache validators"):
        await fetch_onion_response(
            f"http://{_v3_host()}/",
            conditional_headers={"Authorization": "secret"},
        )
