from intiligence_mcp.storage.source_registry import SourceRegistry, canonicalize_url


def test_canonicalize_url_removes_fragment_and_default_port():
    assert canonicalize_url("HTTPS://Example.org:443/a#section") == "https://example.org/a"


def test_registry_is_durable_and_deduplicates(tmp_path):
    path = tmp_path / "sources.sqlite3"
    first = SourceRegistry(path).add("https://example.org/a#one", "Example")
    second = SourceRegistry(path).add("https://example.org/a#two", "Other title")
    assert first.source_id == second.source_id
    assert SourceRegistry(path).get(first.source_id) == first
    assert first.title == "Example"


def test_rejects_credentialed_or_non_http_urls():
    for value in ("file:///etc/passwd", "https://user:pass@example.org"):
        try:
            canonicalize_url(value)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe URL was accepted")
