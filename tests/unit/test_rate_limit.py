import asyncio
import hashlib

import pytest
from pydantic import ValidationError

from intiligence_mcp.acquisition.rate_limit import (
    REDIS_PACING_SCRIPT,
    HostRateLimiter,
    RedisHostRateLimiter,
    create_host_rate_limiter,
)
from intiligence_mcp.config import Settings


class FakeRedis:
    def __init__(self, wait_ms=0):
        self.wait_ms = wait_ms
        self.calls = []

    async def eval(self, *args):
        self.calls.append(args)
        return self.wait_ms


@pytest.mark.asyncio
async def test_redis_limiter_uses_atomic_server_time_and_hashed_host(monkeypatch):
    client = FakeRedis(wait_ms=250)
    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    limiter = RedisHostRateLimiter(client, 1.25)
    await limiter.wait("Example.COM.")

    script, key_count, key, interval_ms, minimum_ttl, grace = client.calls[0]
    assert script == REDIS_PACING_SCRIPT
    assert "redis.call('TIME')" in script
    assert key_count == 1
    assert key == "intiligence:host-pacing:" + hashlib.sha256(b"example.com").hexdigest()
    assert interval_ms == 1250
    assert minimum_ttl == 60_000
    assert grace == 60_000
    assert sleeps == [0.25]


def test_local_limiter_remains_default_for_single_process():
    assert isinstance(create_host_rate_limiter(1.0), HostRateLimiter)


def test_required_shared_limiter_fails_without_redis_url():
    with pytest.raises(RuntimeError, match="INTILIGENCE_REDIS_URL"):
        create_host_rate_limiter(1.0, require_shared=True)


def test_redis_url_validation_accepts_redis_and_rediss():
    assert Settings(redis_url="redis://cache:6379/0").redis_url == "redis://cache:6379/0"
    assert Settings(redis_url="rediss://user:secret@cache.example:6380/2").redis_url.startswith("rediss://")


@pytest.mark.parametrize("url", ["http://cache:6379", "redis://", "redis://cache:6379/a", "redis://cache:6379/0?x=1"])
def test_redis_url_validation_rejects_invalid_values(url):
    with pytest.raises(ValidationError):
        Settings(redis_url=url)



def test_redis_limiter_factory_builds_client_from_configured_url(monkeypatch):
    from types import SimpleNamespace

    from intiligence_mcp.acquisition import rate_limit

    client = FakeRedis()
    captured = {}

    class FakeRedisFactory:
        @staticmethod
        def from_url(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return client

    monkeypatch.setattr(
        rate_limit.importlib,
        "import_module",
        lambda name: SimpleNamespace(Redis=FakeRedisFactory),
    )
    limiter = create_host_rate_limiter(1.0, redis_url="redis://cache:6379/0", require_shared=True)

    assert isinstance(limiter, RedisHostRateLimiter)
    assert captured["url"] == "redis://cache:6379/0"
    assert captured["kwargs"]["decode_responses"] is True


@pytest.mark.asyncio
async def test_redis_limiter_outage_fails_closed_for_acquisition(monkeypatch):
    from intiligence_mcp.acquisition import http
    from intiligence_mcp.acquisition.http import AcquisitionError

    class FailingLimiter:
        async def wait(self, _host):
            raise ConnectionError("redis unavailable")

    monkeypatch.setattr(http, "_host_limiter", FailingLimiter())
    monkeypatch.setattr(http, "validate_url", lambda _url, **_kwargs: "example.org")

    with pytest.raises(AcquisitionError, match="Host pacing unavailable"):
        await http.fetch_response("https://example.org/resource")
