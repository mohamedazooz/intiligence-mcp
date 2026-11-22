import pytest
from pydantic import ValidationError

from intiligence_mcp.acquisition.http import AcquisitionError, fetch_response
from intiligence_mcp.config import Settings, settings


@pytest.mark.asyncio
async def test_required_proxy_fails_closed_when_missing(monkeypatch):
    monkeypatch.setattr(settings, "require_egress_proxy", True)
    monkeypatch.setattr(settings, "egress_proxy_url", "")

    with pytest.raises(AcquisitionError, match="Egress proxy is required"):
        await fetch_response("https://example.org/resource")


def test_proxy_url_rejects_credentials_and_non_origin_paths():
    with pytest.raises(ValidationError):
        Settings(egress_proxy_url="http://user:secret@proxy.example:3128")
    with pytest.raises(ValidationError):
        Settings(egress_proxy_url="http://proxy.example:3128/admin")


def test_proxy_url_requires_http_scheme():
    with pytest.raises(ValidationError):
        Settings(egress_proxy_url="socks5://proxy.example:1080")


def test_proxy_url_normalizes_trailing_slash():
    configured = Settings(egress_proxy_url="http://proxy.example:3128/")
    assert configured.egress_proxy_url == "http://proxy.example:3128"
