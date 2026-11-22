"""Bounded HTTP acquisition with redirect-by-redirect URL validation."""

from urllib.parse import urljoin

import httpx

from intiligence_mcp.acquisition.rate_limit import HostRateLimiter
from intiligence_mcp.config import settings
from intiligence_mcp.security.url_policy import validate_url

_host_limiter = HostRateLimiter(settings.min_host_interval_seconds)


class AcquisitionError(RuntimeError):
    pass


async def fetch_url(url: str) -> tuple[str, str]:
    current = url
    headers = {"User-Agent": settings.user_agent, "Accept": "text/html,application/xhtml+xml"}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(settings.request_timeout_seconds),
        follow_redirects=False,
        headers=headers,
        trust_env=False,
    ) as client:
        for hop in range(settings.max_redirects + 1):
            host = validate_url(
                current,
                allow_private=settings.allow_private_networks,
                allowlist=settings.domains(settings.domain_allowlist),
                denylist=settings.domains(settings.domain_denylist),
            )
            await _host_limiter.wait(host)
            try:
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        if hop >= settings.max_redirects:
                            raise AcquisitionError("Redirect limit exceeded")
                        location = response.headers.get("location")
                        if not location:
                            raise AcquisitionError("Redirect missing Location header")
                        current = urljoin(current, location)
                        continue
                    response.raise_for_status()
                    chunks, total = [], 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > settings.max_response_bytes:
                            raise AcquisitionError("Response exceeded configured size limit")
                        chunks.append(chunk)
                    return b"".join(chunks).decode(
                        response.encoding or "utf-8", errors="replace"
                    ), str(response.url)
            except httpx.HTTPError as exc:
                raise AcquisitionError(f"HTTP acquisition failed: {type(exc).__name__}") from exc
    raise AcquisitionError("Unable to fetch URL")
