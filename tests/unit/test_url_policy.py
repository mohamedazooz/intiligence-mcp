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
