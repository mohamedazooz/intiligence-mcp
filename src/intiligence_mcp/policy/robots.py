"""Conservative robots.txt enforcement with a bounded in-memory cache."""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

from intiligence_mcp.config import settings
from intiligence_mcp.security.url_policy import validate_url


class RobotsPolicyError(RuntimeError):
    """Raised when robots policy cannot be safely established."""


class RobotsPolicy:
    def __init__(self, ttl_seconds: float = 900.0) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, RobotFileParser | None, bool]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def can_fetch(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        now = time.monotonic()
        cached = self._cache.get(origin)
        if cached and cached[0] > now:
            parser, allow_all = cached[1], cached[2]
            return allow_all if parser is None else parser.can_fetch(settings.user_agent, url)
        lock = self._locks.setdefault(origin, asyncio.Lock())
        async with lock:
            cached = self._cache.get(origin)
            if cached and cached[0] > time.monotonic():
                parser, allow_all = cached[1], cached[2]
                return allow_all if parser is None else parser.can_fetch(settings.user_agent, url)
            robots_url = origin + "/robots.txt"
            validate_url(
                robots_url,
                allow_private=settings.allow_private_networks,
                allowlist=settings.domains(settings.domain_allowlist),
                denylist=settings.domains(settings.domain_denylist),
            )
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(min(settings.request_timeout_seconds, 10.0)),
                    follow_redirects=False,
                    trust_env=False,
                    headers={"User-Agent": settings.user_agent},
                ) as client:
                    response = await client.get(robots_url)
            except httpx.HTTPError as exc:
                raise RobotsPolicyError("robots.txt unavailable; acquisition denied") from exc
            if response.status_code in (404, 410):
                self._cache[origin] = (time.monotonic() + self._ttl, None, True)
                return True
            if response.status_code != 200:
                raise RobotsPolicyError(f"robots.txt returned {response.status_code}; acquisition denied")
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())
            self._cache[origin] = (time.monotonic() + self._ttl, parser, False)
            return parser.can_fetch(settings.user_agent, url)


robots_policy = RobotsPolicy()
