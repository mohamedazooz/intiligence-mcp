"""Adapter for the internally vendored Trafilatura source."""

from intiligence_mcp._vendor import trafilatura


def extract_main_text(html: str, url: str | None = None) -> str:
    result = trafilatura.extract(
        html,
        url=url,
        output_format="txt",
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    return result or ""
