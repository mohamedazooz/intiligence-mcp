from intiligence_mcp.extraction.trafilatura_adapter import extract_main_text


def test_extracts_article_text():
    html = """<html><body><article><h1>Test article</h1><p>This is a sufficiently long paragraph containing useful article text.</p><p>Another paragraph with additional context for extraction testing.</p></article></body></html>"""
    assert "Test article" in extract_main_text(html, "https://example.org/a")
