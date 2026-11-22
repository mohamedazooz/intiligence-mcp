"""Per-host pacing with local and optional Redis-backed coordination."""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import time
from collections import defaultdict
from typing import Any

REDIS_PACING_SCRIPT = """
local clock = redis.call('TIME')
local now_ms = tonumber(clock[1]) * 1000 + math.floor(tonumber(clock[2]) / 1000)
local interval_ms = tonumber(ARGV[1])
local minimum_ttl_ms = tonumber(ARGV[2])
local grace_ms = tonumber(ARGV[3])
local next_ms = tonumber(redis.call('GET', KEYS[1]) or '0')
local slot_ms = math.max(now_ms, next_ms)
local expiry_ms = math.max(minimum_ttl_ms, slot_ms + interval_ms - now_ms + grace_ms)
redis.call('SET', KEYS[1], slot_ms + interval_ms, 'PX', expiry_ms)
return math.max(0, slot_ms - now_ms)
"""


class HostRateLimiter:
    """Process-local limiter for single-process development deployments."""

    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        self._interval = min_interval_seconds
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._last_request: dict[str, float] = {}

    async def wait(self, host: str) -> None:
        key = host.lower().rstrip(".")
        async with self._locks[key]:
            now = time.monotonic()
            delay = self._interval - (now - self._last_request.get(key, 0.0))
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_request[key] = time.monotonic()


class RedisHostRateLimiter:
    """Atomic cross-process pacing using Redis TIME and a Lua reservation script."""

    def __init__(
        self,
        redis_client: Any,
        min_interval_seconds: float = 1.0,
        *,
        key_prefix: str = "intiligence:host-pacing",
    ) -> None:
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        self._client = redis_client
        self._interval_ms = max(1, round(min_interval_seconds * 1000)) if min_interval_seconds > 0 else 0
        self._key_prefix = key_prefix.rstrip(":")

    async def wait(self, host: str) -> None:
        if self._interval_ms <= 0:
            return
        normalized = host.lower().rstrip(".")
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        wait_ms = await self._client.eval(
            REDIS_PACING_SCRIPT,
            1,
            f"{self._key_prefix}:{digest}",
            self._interval_ms,
            60_000,
            60_000,
        )
        delay_ms = int(wait_ms or 0)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)


def create_host_rate_limiter(
    min_interval_seconds: float,
    *,
    redis_url: str = "",
    require_shared: bool = False,
) -> HostRateLimiter | RedisHostRateLimiter:
    """Build the configured limiter; Redis failures never silently fall back locally."""
    if redis_url.strip():
        try:
            redis_asyncio = importlib.import_module("redis.asyncio")
        except ImportError as exc:
            raise RuntimeError(
                "Redis rate limiting is configured but the 'distributed' extra is not installed"
            ) from exc
        redis_client = redis_asyncio.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        return RedisHostRateLimiter(redis_client, min_interval_seconds)
    if require_shared:
        raise RuntimeError(
            "Shared rate limiting is required but INTILIGENCE_REDIS_URL is not configured"
        )
    return HostRateLimiter(min_interval_seconds)
