"""Public deep-web research adapters for scholarly and specialist databases.

These connectors query publicly accessible metadata APIs. They do not attempt to
authenticate to private portals, retrieve restricted full text, or bypass access
controls. Returned records are discovery leads until their linked sources are
independently fetched and captured as evidence.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlencode

from intiligence_mcp.acquisition.http import AcquisitionError, fetch_response_details
from intiligence_mcp.policy.robots import robots_policy


class DeepWebProviderError(RuntimeError):
    """A public data provider returned an invalid or unavailable response."""


async def _json_get(url: str) -> dict[str, Any]:
    response = await fetch_response_details(
        url,
        accept="application/json",
        policy_check=robots_policy.can_fetch,
    )
    if response.status != 200:
        raise DeepWebProviderError(f"HTTP {response.status}")
    try:
        payload = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise DeepWebProviderError("invalid_json") from exc
    if not isinstance(payload, dict):
        raise DeepWebProviderError("invalid_response_shape")
    return payload


def _first_text(value: Any, maximum: int = 500) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    return value.strip()[:maximum] if isinstance(value, str) else ""


def _crossref_date(item: dict[str, Any]) -> str | None:
    for key in ("published-print", "published-online", "published", "created"):
        value = item.get(key)
        if not isinstance(value, dict):
            continue
        parts = value.get("date-parts")
        if not isinstance(parts, list) or not parts or not isinstance(parts[0], list):
            continue
        numbers = parts[0]
        if not numbers or not all(isinstance(part, int) for part in numbers):
            continue
        return "-".join(f"{part:02d}" if index else str(part) for index, part in enumerate(numbers))
    return None


async def _crossref(query: str, limit: int) -> list[dict[str, Any]]:
    params = urlencode(
        {
            "query.bibliographic": query,
            "rows": str(limit),
            "select": "DOI,title,published,published-print,published-online,created,URL,author,type,container-title",
        }
    )
    payload = await _json_get(f"https://api.crossref.org/works?{params}")
    message = payload.get("message")
    items = message.get("items") if isinstance(message, dict) else None
    if not isinstance(items, list):
        raise DeepWebProviderError("missing_results")
    results: list[dict[str, Any]] = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        doi = item.get("DOI")
        if not isinstance(doi, str) or not doi.strip():
            continue
        authors = item.get("author")
        author_names = []
        if isinstance(authors, list):
            for author in authors[:3]:
                if isinstance(author, dict):
                    name = " ".join(
                        part for part in (author.get("given"), author.get("family")) if isinstance(part, str)
                    ).strip()
                    if name:
                        author_names.append(name[:120])
        results.append(
            {
                "provider": "crossref",
                "record_id": doi[:256],
                "title": _first_text(item.get("title")),
                "url": f"https://doi.org/{doi}",
                "published_at": _crossref_date(item),
                "authors": author_names,
                "journal": _first_text(item.get("container-title"), 200),
                "work_type": str(item.get("type", ""))[:80],
                "abstract": "",
                "is_open_access": None,
                "content_is_untrusted": True,
            }
        )
    return results


async def _europe_pmc(query: str, limit: int) -> list[dict[str, Any]]:
    params = urlencode(
        {
            "query": query,
            "format": "json",
            "pageSize": str(limit),
            "resultType": "core",
        }
    )
    payload = await _json_get(
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}"
    )
    result_list = payload.get("resultList")
    items = result_list.get("result") if isinstance(result_list, dict) else None
    if not isinstance(items, list):
        raise DeepWebProviderError("missing_results")
    results: list[dict[str, Any]] = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        pmid = item.get("pmid")
        pmcid = item.get("pmcid")
        doi = item.get("doi")
        if isinstance(pmcid, str) and pmcid:
            link = f"https://europepmc.org/articles/{pmcid}"
        elif isinstance(pmid, str) and pmid:
            link = f"https://europepmc.org/article/MED/{pmid}"
        elif isinstance(doi, str) and doi:
            link = f"https://doi.org/{doi}"
        else:
            continue
        record_id = str(pmcid or pmid or doi)[:256]
        abstract = item.get("abstractText")
        results.append(
            {
                "provider": "europe_pmc",
                "record_id": record_id,
                "title": _first_text(item.get("title")),
                "url": link,
                "published_at": str(item.get("firstPublicationDate", ""))[:32] or None,
                "authors": [str(item.get("authorString", ""))[:300]]
                if item.get("authorString")
                else [],
                "journal": str(item.get("journalTitle", ""))[:200],
                "work_type": str(item.get("pubType", ""))[:80],
                "abstract": abstract[:1200] if isinstance(abstract, str) else "",
                "is_open_access": str(item.get("isOpenAccess", "")).lower() == "y",
                "content_is_untrusted": True,
            }
        )
    return results


async def search_deep_web(query: str, limit: int = 8) -> dict[str, Any]:
    """Search public scholarly databases outside ordinary web-index coverage."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    normalized = " ".join(query.split())
    if not normalized or len(normalized) > 500:
        raise ValueError("query must contain 1–500 non-whitespace characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")

    providers = (
        ("crossref", _crossref),
        ("europe_pmc", _europe_pmc),
    )

    async def run_provider(name: str, callback: Any) -> tuple[str, list[dict[str, Any]], str]:
        try:
            return name, await callback(normalized, limit), "ok"
        except (AcquisitionError, DeepWebProviderError, TimeoutError, ValueError) as exc:
            return name, [], type(exc).__name__

    outcomes = await asyncio.gather(
        *(run_provider(name, callback) for name, callback in providers)
    )
    results: list[dict[str, Any]] = []
    provider_status: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for name, items, status in outcomes:
        provider_status[name] = {"status": status, "count": len(items)}
        for item in items:
            key = str(item.get("record_id", "")).casefold()
            if key and key not in seen:
                seen.add(key)
                results.append(item)

    return {
        "status": "ok" if results else "providers_unavailable_or_no_results",
        "provider_status": provider_status,
        "result_count": len(results),
        "results": results,
        "results_are_untrusted_discovery_hints": True,
        "notice": (
            "Public database metadata only. Records are not verified evidence until the "
            "linked public source is fetched and captured. No private portal or paywall is bypassed."
        ),
    }
