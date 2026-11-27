"""Allowlisted, text-only Tor onion acquisition. Disabled unless explicitly enabled."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

import aiohttp

from intiligence_mcp.config import settings
from intiligence_mcp.acquisition.http import AcquisitionError, FetchResult


def validate_onion_target(url: str) -> str:
    """Accept only a v3 onion hostname explicitly approved by the operator."""
    if len(url) > 2048:
        raise ValueError("Onion URL exceeds the 2048 character limit")
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Malformed onion URL") from exc
    if parsed.scheme not in {"http", "https"} or not host.endswith(".onion"):
        raise ValueError("Only HTTP(S) v3 onion URLs are permitted")
    label = host[:-6]
    if len(label) != 56 or any(char not in "abcdefghijklmnopqrstuvwxyz234567" for char in label):
        raise ValueError("Only 56-character v3 onion hostnames are permitted")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError("Onion URL must not contain credentials or fragments")
    if port not in {None, 80, 443}:
        raise ValueError("Only onion service ports 80 and 443 are permitted")
    approved = settings.onion_hosts()
    if not approved or host not in approved:
        raise ValueError("Onion hostname is not in INTILIGENCE_ONION_SOURCE_ALLOWLIST")
    return host


async def fetch_onion_response(
    url: str, *, conditional_headers: dict[str, str] | None = None
) -> FetchResult:
    """Fetch one approved onion page through SOCKS with remote hostname resolution.

    No redirects, cookies, JavaScript, form submissions, credentials, downloads,
    or arbitrary ports are permitted. This adapter never performs CAPTCHA solving.
    """
    if not settings.enable_onion_osint:
        raise AcquisitionError("Tor/onion collection is disabled")
    host = validate_onion_target(url)
    proxy = urlsplit(settings.tor_socks_url)
    if proxy.scheme != "socks5" or not proxy.hostname or not proxy.port:
        raise AcquisitionError("A valid operator-configured SOCKS5 Tor proxy is required")

    timeout = aiohttp.ClientTimeout(total=min(settings.request_timeout_seconds, 30))
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,text/plain,application/json",
    }
    for key, value in (conditional_headers or {}).items():
        if (
            key not in {"If-None-Match", "If-Modified-Since"}
            or not isinstance(value, str)
            or len(value) > 1024
        ):
            raise ValueError("Only bounded HTTP cache validators are accepted")
        headers[key] = value

    try:
        from aiohttp_socks import ProxyConnector, ProxyType
    except ImportError as exc:
        raise AcquisitionError(
            "Tor support is optional; install the 'tor' extra to enable onion collection"
        ) from exc

    # rdns=True is essential: the .onion name must be resolved by Tor, not local DNS.
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=proxy.hostname,
        port=proxy.port,
        rdns=True,
    )
    try:
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            trust_env=False,
            cookie_jar=aiohttp.DummyCookieJar(),
            auto_decompress=True,
        ) as client:
            async with client.get(url, allow_redirects=False) as response:
                media_type = response.headers.get("Content-Type")
                safe_headers = {
                    key.lower(): value
                    for key, value in response.headers.items()
                    if key.lower()
                    in {"content-type", "content-length", "etag", "last-modified", "date", "cache-control"}
                }
                if response.status in {301, 302, 303, 307, 308}:
                    return FetchResult(
                        response.status, b"", "", str(response.url), media_type,
                        safe_headers, (),
                    )
                if response.status == 304:
                    return FetchResult(
                        response.status, b"", "", str(response.url), media_type,
                        safe_headers, (),
                    )
                if response.status < 200 or response.status >= 300:
                    return FetchResult(
                        response.status, b"", "", str(response.url), media_type,
                        safe_headers, (),
                    )
                allowed_types = {
                    "text/html", "application/xhtml+xml", "text/plain",
                    "application/json", "application/ld+json",
                }
                if response.content_type not in allowed_types:
                    raise AcquisitionError("Onion response media type is not allowed")
                if (
                    response.content_length is not None
                    and response.content_length > settings.max_onion_response_bytes
                ):
                    raise AcquisitionError("Onion response exceeded the configured size limit")
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.content.iter_chunked(32 * 1024):
                    total += len(chunk)
                    if total > settings.max_onion_response_bytes:
                        raise AcquisitionError("Onion response exceeded the configured size limit")
                    chunks.append(chunk)
                body = b"".join(chunks)
                charset = response.charset or "utf-8"
                text = body.decode(charset, errors="replace")
                return FetchResult(
                    response.status, body, text, str(response.url),
                    media_type, safe_headers, (),
                )
    except AcquisitionError:
        raise
    except (aiohttp.ClientError, TimeoutError, UnicodeError, OSError) as exc:
        raise AcquisitionError(f"Tor onion acquisition failed: {type(exc).__name__}") from exc
