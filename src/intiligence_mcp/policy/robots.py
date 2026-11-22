"""Conservative robots.txt enforcement with local or Redis-shared caching."""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import secrets
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from intiligence_mcp.acquisition.http import AcquisitionError, fetch_response
from intiligence_mcp.config import settings


class RobotsPolicyError(RuntimeError):
    """Raised when robots policy cannot be safely established."""


RELEASE_LOCK_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


class RobotsPolicy:
    def __init__(
        self,
        ttl_seconds: float = 900.0,
        *,
        redis_client: Any | None = None,
        redis_url: str = "",
        require_shared: bool = False,
    ) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, RobotFileParser | None, bool]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._redis = redis_client
        if redis_url.strip():
            try:
                redis_asyncio = importlib.import_module("redis.asyncio")
            except ImportError as exc:
                raise RuntimeError(
                    "Shared robots caching is configured but the 'distributed' extra is not installed"
                ) from exc
            self._redis = redis_asyncio.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        elif require_shared:
            raise RuntimeError(
                "Shared robots caching is required but INTILIGENCE_REDIS_URL is not configured"
            )

    @staticmethod
    def _origin(url: str) -> str:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), "", "", ""))

    @staticmethod
    def _decision(
        record: str, robots_url: str
    ) -> tuple[RobotFileParser | None, bool]:
        try:
            payload = json.loads(record)
            status = int(payload["status"])
            body = str(payload.get("body", ""))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise RobotsPolicyError("shared robots cache record is invalid; acquisition denied") from exc
        if status in (404, 410):
            return None, True
        if status != 200:
            raise RobotsPolicyError(
                f"robots.txt returned {status}; acquisition denied"
            )
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(body.splitlines())
        return parser, False

    def _allowed(
        self, url: str, parser: RobotFileParser | None, allow_all: bool
    ) -> bool:
        return allow_all if parser is None else parser.can_fetch(settings.user_agent, url)

    async def _fetch_policy(self, robots_url: str) -> tuple[int, str]:
        try:
            status, body, _final_url = await fetch_response(robots_url, max_redirects=0)
        except AcquisitionError as exc:
            raise RobotsPolicyError("robots.txt unavailable; acquisition denied") from exc
        if status not in (200, 404, 410):
            raise RobotsPolicyError(f"robots.txt returned {status}; acquisition denied")
        return status, body

    async def _can_fetch_shared(self, url: str, origin: str, robots_url: str) -> bool:
        assert self._redis is not None
        digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()
        cache_key = f"intiligence:robots:cache:{digest}"
        lock_key = f"intiligence:robots:lock:{digest}"
        cached = await self._redis.get(cache_key)
        if cached is not None:
            parser, allow_all = self._decision(cached, robots_url)
            return self._allowed(url, parser, allow_all)

        token = secrets.token_hex(16)
        lock_ttl = max(30, int(settings.request_timeout_seconds) + 10)
        deadline = time.monotonic() + lock_ttl
        acquired = False
        while not acquired:
            cached = await self._redis.get(cache_key)
            if cached is not None:
                parser, allow_all = self._decision(cached, robots_url)
                return self._allowed(url, parser, allow_all)
            acquired = bool(await self._redis.set(lock_key, token, nx=True, ex=lock_ttl))
            if acquired:
                break
            if time.monotonic() >= deadline:
                raise RobotsPolicyError(
                    "timed out waiting for shared robots policy; acquisition denied"
                )
            await asyncio.sleep(0.1)

        try:
            cached = await self._redis.get(cache_key)
            if cached is not None:
                parser, allow_all = self._decision(cached, robots_url)
                return self._allowed(url, parser, allow_all)
            status, body = await self._fetch_policy(robots_url)
            record = json.dumps({"status": status, "body": body}, separators=(",", ":"))
            await self._redis.set(cache_key, record, ex=max(1, int(self._ttl)))
            parser, allow_all = self._decision(record, robots_url)
            return self._allowed(url, parser, allow_all)
        finally:
            await self._redis.eval(RELEASE_LOCK_SCRIPT, 1, lock_key, token)

    async def can_fetch(self, url: str) -> bool:
        origin = self._origin(url)
        robots_url = origin + "/robots.txt"
        if self._redis is not None:
            try:
                return await self._can_fetch_shared(url, origin, robots_url)
            except RobotsPolicyError:
                raise
            except Exception as exc:
                raise RobotsPolicyError(
                    "shared robots cache unavailable; acquisition denied"
                ) from exc

        now = time.monotonic()
        cached = self._cache.get(origin)
        if cached and cached[0] > now:
            parser, allow_all = cached[1], cached[2]
            return self._allowed(url, parser, allow_all)
        lock = self._locks.setdefault(origin, asyncio.Lock())
        async with lock:
            cached = self._cache.get(origin)
            if cached and cached[0] > time.monotonic():
                parser, allow_all = cached[1], cached[2]
                return self._allowed(url, parser, allow_all)
            status, body = await self._fetch_policy(robots_url)
            if status in (404, 410):
                self._cache[origin] = (time.monotonic() + self._ttl, None, True)
                return True
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(body.splitlines())
            self._cache[origin] = (time.monotonic() + self._ttl, parser, False)
            return self._allowed(url, parser, False)


robots_policy = RobotsPolicy(
    redis_url=settings.redis_url,
    require_shared=settings.require_shared_robots_cache,
)
