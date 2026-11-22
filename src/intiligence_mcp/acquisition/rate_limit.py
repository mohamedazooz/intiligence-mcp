"""Process-local per-host request pacing; use a distributed limiter in multi-worker deployments."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict


class HostRateLimiter:
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
