"""Conservative robots.txt enforcement with a bounded in-memory cache."""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from intiligence_mcp.acquisition.http import AcquisitionError, fetch_response
from intiligence_mcp.config import settings


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
            try:
                status, body, _final_url = await fetch_response(
                    robots_url, max_redirects=0
                )
            except AcquisitionError as exc:
                raise RobotsPolicyError(
                    "robots.txt unavailable; acquisition denied"
                ) from exc
            if status in (404, 410):
                self._cache[origin] = (time.monotonic() + self._ttl, None, True)
                return True
            if status != 200:
                raise RobotsPolicyError(
                    f"robots.txt returned {status}; acquisition denied"
                )
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(body.splitlines())
            self._cache[origin] = (time.monotonic() + self._ttl, parser, False)
            return parser.can_fetch(settings.user_agent, url)


robots_policy = RobotsPolicy()
