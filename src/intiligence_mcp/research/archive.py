"""Bounded exact-URL lookup in public web archives."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

from intiligence_mcp.acquisition.http import AcquisitionError, fetch_response_details
from intiligence_mcp.config import settings
from intiligence_mcp.policy.robots import robots_policy
from intiligence_mcp.security.url_policy import URLPolicyError, validate_url


class ArchiveLookupError(RuntimeError):
    """A public archive index could not return a safe response."""


async def search_web_archive(url: str, limit: int = 10) -> dict[str, Any]:
    """Look up captures for one exact public HTTP(S) URL; never crawl URL patterns."""
    if not isinstance(url, str) or not url.strip() or len(url) > 2048:
        raise ValueError("url must contain 1–2048 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    try:
        validate_url(
            url,
            allow_private=False,
            allowlist=settings.domains(settings.domain_allowlist),
            denylist=settings.domains(settings.domain_denylist),
            allow_temporary_dns_failure=(
                settings.require_egress_proxy and bool(settings.egress_proxy_url.strip())
            ),
        )
    except URLPolicyError as exc:
        raise ValueError("Only permitted public HTTP(S) URLs can be queried in the archive") from exc

    params = urlencode(
        {
            "url": url,
            "matchType": "exact",
            "output": "json",
            "filter": ["statuscode:200", "mimetype:text/html"],
            "fl": "timestamp,original,mimetype,statuscode,digest,length",
            "collapse": "digest",
            "pageSize": str(limit),
        },
        doseq=True,
    )
    endpoint = f"https://web.archive.org/cdx/search/cdx?{params}"
    try:
        response = await fetch_response_details(
            endpoint,
            accept="application/json",
            policy_check=robots_policy.can_fetch,
        )
    except AcquisitionError as exc:
        raise ArchiveLookupError(type(exc).__name__) from exc
    if response.status != 200:
        raise ArchiveLookupError(f"Wayback returned HTTP {response.status}")
    try:
        payload = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ArchiveLookupError("Wayback returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise ArchiveLookupError("Wayback response shape was not an array")
    rows = payload[1:] if payload and isinstance(payload[0], list) else payload
    captures: list[dict[str, Any]] = []
    for row in rows[:limit]:
        if not isinstance(row, list) or len(row) < 6:
            continue
        timestamp, original, mime, status, digest, length = row[:6]
        if not isinstance(timestamp, str) or not timestamp.isdigit() or len(timestamp) != 14:
            continue
        if not isinstance(original, str) or len(original) > 2048:
            continue
        try:
            validate_url(
                original,
                allow_private=False,
                allowlist=settings.domains(settings.domain_allowlist),
                denylist=settings.domains(settings.domain_denylist),
                allow_temporary_dns_failure=(
                    settings.require_egress_proxy and bool(settings.egress_proxy_url.strip())
                ),
            )
        except URLPolicyError:
            continue
        captures.append(
            {
                "timestamp": timestamp,
                "original_url": original,
                "snapshot_url": f"https://web.archive.org/web/{timestamp}/{original}",
                "mime_type": str(mime)[:120],
                "status_code": str(status)[:8],
                "digest": str(digest)[:128],
                "length": str(length)[:32],
            }
        )
    return {
        "status": "ok",
        "provider": "internet_archive_wayback",
        "query_url": url,
        "count": len(captures),
        "captures": captures,
        "content_is_untrusted": True,
        "notice": (
            "Historical index metadata only. A snapshot is not proof that the archived "
            "content was accurate or that it remains current."
        ),
    }
