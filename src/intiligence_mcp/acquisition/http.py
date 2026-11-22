"""Bounded HTTP acquisition using DNS-pinned connections and manual redirects."""

from __future__ import annotations

import socket
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


class AcquisitionError(RuntimeError):
    pass


async def fetch_response(
    url: str, *, max_redirects: int | None = None
) -> tuple[int, str, str]:
    """Return status, decoded body, and final URL without following implicit redirects."""
    current = url
    redirect_limit = settings.max_redirects if max_redirects is None else max_redirects
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml",
    }
    if settings.require_egress_proxy and not settings.egress_proxy_url.strip():
        raise AcquisitionError("Egress proxy is required but not configured; outbound request denied")

    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    # When proxying, the connector resolves only the proxy endpoint. The proxy
    # independently enforces destination-IP ACLs; the target URL is still
    # resolved and checked by validate_url before every request/redirect hop.
    resolver = PinnedPublicResolver(
        allow_private=settings.allow_private_networks or bool(settings.egress_proxy_url.strip())
    )
    connector = aiohttp.TCPConnector(
        resolver=resolver,
        use_dns_cache=True,
        ttl_dns_cache=60,
        family=socket.AF_UNSPEC,
    )

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
                        current = urljoin(current, location)
                        continue

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.content.iter_chunked(64 * 1024):
                        total += len(chunk)
                        if total > settings.max_response_bytes:
                            raise AcquisitionError(
                                "Response exceeded configured size limit"
                            )
                        chunks.append(chunk)
                    body = b"".join(chunks).decode(
                        response.charset or "utf-8", errors="replace"
                    )
                    return response.status, body, str(response.url)
            except AcquisitionError:
                raise
            except (aiohttp.ClientError, TimeoutError) as exc:
                raise AcquisitionError(
                    f"HTTP acquisition failed: {type(exc).__name__}"
                ) from exc
    raise AcquisitionError("Unable to fetch URL")


async def fetch_url(url: str) -> tuple[str, str]:
    status, body, final_url = await fetch_response(url)
    if status < 200 or status >= 300:
        raise AcquisitionError(f"HTTP acquisition returned status {status}")
    return body, final_url
