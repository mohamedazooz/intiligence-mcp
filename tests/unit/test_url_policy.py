import socket

import pytest

from intiligence_mcp.security.url_policy import URLPolicyError, validate_url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/a",
        "http://127.0.0.1/",
        "http://localhost/",
        "http://169.254.169.254/latest/meta-data",
        "http://user:pass@example.com/",
    ],
)
def test_rejects_unsafe_urls(url):
    with pytest.raises(URLPolicyError):
        validate_url(url)


def test_allowlist_rejects_other_hosts():
    with pytest.raises(URLPolicyError):
        validate_url("https://example.com", allowlist={"example.org"})


def test_allowlist_accepts_exact_host(monkeypatch):
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("1.1.1.1", 443))])
    assert validate_url("https://example.org", allowlist={"example.org"}) == "example.org"


def test_denylist_rejects_subdomains():
    with pytest.raises(URLPolicyError, match="denied"):
        validate_url("https://sub.example.org", denylist={"example.org"})


def test_temporary_dns_failure_can_be_delegated_to_required_proxy(monkeypatch):
    def temporary_failure(*_args, **_kwargs):
        raise socket.gaierror(socket.EAI_AGAIN, "Temporary failure in name resolution")

    monkeypatch.setattr("socket.getaddrinfo", temporary_failure)
    assert validate_url(
        "https://example.org/resource",
        allow_temporary_dns_failure=True,
    ) == "example.org"


def test_nxdomain_still_fails_closed_even_with_proxy_dns_fallback(monkeypatch):
    def name_not_found(*_args, **_kwargs):
        raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")

    monkeypatch.setattr("socket.getaddrinfo", name_not_found)
    with pytest.raises(URLPolicyError, match="DNS resolution failed"):
        validate_url("https://does-not-exist.invalid", allow_temporary_dns_failure=True)


def test_private_ip_literal_still_fails_closed_with_proxy_dns_fallback():
    with pytest.raises(URLPolicyError, match="non-public"):
        validate_url("http://169.254.169.254/", allow_temporary_dns_failure=True)
