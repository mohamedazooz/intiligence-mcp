"""Bounded SearXNG adapter; results are discovery hints, not verified evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import aiohttp

from intiligence_mcp.config import settings
from intiligence_mcp.security.url_policy import URLPolicyError, validate_url


class SearchProviderError(RuntimeError):
    """The configured search provider could not return a safe result set."""


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str | None
    published_at: str | None


def _endpoint() -> str:
    raw = settings.searxng_url.strip()
    if not raw:
        raise SearchProviderError("SearXNG is not configured")
    parsed = urlsplit(raw)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise SearchProviderError("Configured SearXNG URL is invalid")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/") + "/search", "", ""))


async def search_web(query: str, limit: int = 10) -> list[SearchResult]:
    """Search through the operator-configured SearXNG instance.

    SearXNG sends the query to the search engines enabled by its operator. The
    query is not stored by this adapter. Returned URLs are untrusted and must
    pass the normal acquisition policy again before any fetch.
    """
    query = query.strip()
    if not query or len(query) > 500:
        raise ValueError("query must contain 1–500 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= settings.max_search_results:
        raise ValueError(f"limit must be between 1 and {settings.max_search_results}")

    endpoint = _endpoint()
    timeout = aiohttp.ClientTimeout(total=settings.searxng_timeout_seconds)
    headers = {"Accept": "application/json", "User-Agent": settings.user_agent}
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers, trust_env=False) as client:
            async with client.get(
                endpoint,
                params={"q": query, "format": "json", "safesearch": "1", "pageno": "1"},
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    raise SearchProviderError(f"SearXNG returned HTTP {response.status}")
                if response.content_length is not None and response.content_length > 2_000_000:
                    raise SearchProviderError("SearXNG response exceeded the 2 MB limit")
                body = await response.content.read(2_000_001)
                if len(body) > 2_000_000:
                    raise SearchProviderError("SearXNG response exceeded the 2 MB limit")
    except SearchProviderError:
        raise
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise SearchProviderError(f"SearXNG request failed: {type(exc).__name__}") from exc

    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SearchProviderError("SearXNG returned invalid JSON") from exc
    raw_results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(raw_results, list):
        raise SearchProviderError("SearXNG response has no results array")

    accepted: list[SearchResult] = []
    seen: set[str] = set()
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        raw_url = item.get("url")
        title = item.get("title")
        if not isinstance(raw_url, str) or not isinstance(title, str) or not title.strip():
            continue
        try:
            host = validate_url(
                raw_url,
                allow_private=False,
                allowlist=settings.domains(settings.domain_allowlist),
                denylist=settings.domains(settings.domain_denylist),
                allow_temporary_dns_failure=(
                    settings.require_egress_proxy and bool(settings.egress_proxy_url.strip())
                ),
            )
        except URLPolicyError:
            continue
        if host.endswith(".onion") or raw_url in seen:
            continue
        seen.add(raw_url)
        snippet = item.get("content")
        engine = item.get("engine")
        published = item.get("publishedDate")
        accepted.append(
            SearchResult(
                title=title.strip()[:500],
                url=raw_url[:2048],
                snippet=snippet[:1200] if isinstance(snippet, str) else "",
                engine=engine[:80] if isinstance(engine, str) else None,
                published_at=published[:64] if isinstance(published, str) else None,
            )
        )
        if len(accepted) >= limit:
            break
    return accepted
