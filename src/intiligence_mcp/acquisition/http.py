"""Bounded HTTP acquisition with DNS pinning, redirect checks, and provenance capture."""

from __future__ import annotations

import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import urljoin

import aiohttp

from intiligence_mcp.acquisition.rate_limit import create_host_rate_limiter
from intiligence_mcp.config import settings
from intiligence_mcp.security.dns_resolver import PinnedPublicResolver
from intiligence_mcp.security.url_policy import validate_url

_host_limiter = create_host_rate_limiter(
    settings.min_host_interval_seconds,
    redis_url=settings.redis_url,
    require_shared=settings.require_shared_rate_limiter,
)

PolicyCheck = Callable[[str], Awaitable[bool]]
_SAFE_RESPONSE_HEADERS = {
    "content-type",
    "content-length",
    "content-encoding",
    "etag",
    "last-modified",
    "date",
    "cache-control",
}


@dataclass(frozen=True, slots=True)
class FetchResult:
    """A bounded HTTP result; body contains decompressed entity bytes."""

    status: int
    body: bytes
    text: str
    final_url: str
    media_type: str | None
    response_headers: dict[str, str]
    redirect_chain: tuple[dict[str, str | int], ...]


class AcquisitionError(RuntimeError):
    """An acquisition failed or violated a configured safety bound."""


class AcquisitionPolicyDenied(AcquisitionError):
    """A policy check denied this URL before its response was requested."""

    def __init__(self, url: str) -> None:
        super().__init__("Acquisition denied by source policy")
        self.url = url


async def fetch_response_details(
    url: str,
    *,
    max_redirects: int | None = None,
    accept: str | None = None,
    policy_check: PolicyCheck | None = None,
    conditional_headers: dict[str, str] | None = None,
) -> FetchResult:
    """Fetch one page and preserve safe response metadata and redirect provenance.

    If policy_check is supplied, it is called for the initial URL and every
    redirect target before the request is made. Robots.txt retrieval itself
    uses the compatibility wrapper without a policy callback to avoid recursion.
    """
    current = url
    redirect_limit = settings.max_redirects if max_redirects is None else max_redirects
    if redirect_limit < 0:
        raise ValueError("max_redirects must be non-negative")
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": accept or "text/html,application/xhtml+xml",
    }
    allowed_conditionals = {"If-None-Match", "If-Modified-Since"}
    for key, value in (conditional_headers or {}).items():
        if key not in allowed_conditionals or not isinstance(value, str) or len(value) > 1024:
            raise ValueError("Only bounded HTTP cache validators are accepted")
        headers[key] = value
    if settings.require_egress_proxy and not settings.egress_proxy_url.strip():
        raise AcquisitionError(
            "Egress proxy is required but not configured; outbound request denied"
        )

    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    resolver = PinnedPublicResolver(
        allow_private=settings.allow_private_networks or bool(settings.egress_proxy_url.strip())
    )
    connector = aiohttp.TCPConnector(
        resolver=resolver,
        use_dns_cache=True,
        ttl_dns_cache=60,
        family=socket.AF_UNSPEC,
    )
    redirect_chain: list[dict[str, str | int]] = []

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers,
        trust_env=False,
        auto_decompress=True,
    ) as client:
        for hop in range(redirect_limit + 1):
            host = validate_url(
                current,
                allow_private=settings.allow_private_networks,
                allowlist=settings.domains(settings.domain_allowlist),
                denylist=settings.domains(settings.domain_denylist),
                allow_temporary_dns_failure=(
                    settings.require_egress_proxy and bool(settings.egress_proxy_url.strip())
                ),
            )
            if policy_check is not None and not await policy_check(current):
                raise AcquisitionPolicyDenied(current)

            try:
                await _host_limiter.wait(host)
            except Exception as exc:
                raise AcquisitionError("Host pacing unavailable; acquisition denied") from exc

            try:
                async with client.get(
                    current,
                    allow_redirects=False,
                    proxy=settings.egress_proxy_url.strip() or None,
                ) as response:
                    if response.status in {301, 302, 303, 307, 308}:
                        if hop >= redirect_limit:
                            raise AcquisitionError("Redirect limit exceeded")
                        location = response.headers.get("Location")
                        if not location:
                            raise AcquisitionError("Redirect missing Location header")
                        next_url = urljoin(current, location)
                        redirect_chain.append(
                            {"status": response.status, "from": current, "to": next_url}
                        )
                        current = next_url
                        continue

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.content.iter_chunked(64 * 1024):
                        total += len(chunk)
                        if total > settings.max_response_bytes:
                            raise AcquisitionError("Response exceeded configured size limit")
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    charset = response.charset or "utf-8"
                    text = body.decode(charset, errors="replace")
                    response_headers = {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower() in _SAFE_RESPONSE_HEADERS
                    }
                    return FetchResult(
                        status=response.status,
                        body=body,
                        text=text,
                        final_url=str(response.url),
                        media_type=response.headers.get("Content-Type"),
                        response_headers=response_headers,
                        redirect_chain=tuple(redirect_chain),
                    )
            except (AcquisitionError, AcquisitionPolicyDenied):
                raise
            except (aiohttp.ClientError, TimeoutError, UnicodeError) as exc:
                raise AcquisitionError(f"HTTP acquisition failed: {type(exc).__name__}") from exc

    raise AcquisitionError("Unable to fetch URL")


async def fetch_response(
    url: str, *, max_redirects: int | None = None, accept: str | None = None
) -> tuple[int, str, str]:
    """Backward-compatible tuple interface used by policy and provider adapters."""
    result = await fetch_response_details(url, max_redirects=max_redirects, accept=accept)
    return result.status, result.text, result.final_url


async def fetch_url(url: str) -> tuple[str, str]:
    result = await fetch_response_details(url)
    if result.status < 200 or result.status >= 300:
        raise AcquisitionError(f"HTTP acquisition returned status {result.status}")
    return result.text, result.final_url
