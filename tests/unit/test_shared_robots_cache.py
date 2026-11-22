import pytest

from intiligence_mcp.policy import robots
from intiligence_mcp.policy.robots import RobotsPolicy, RobotsPolicyError


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.released = []

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, *, nx=False, ex=None):
        if nx and key in self.values:
            return None
        self.values[key] = value
        return True

    async def eval(self, script, key_count, key, token):
        assert key_count == 1
        assert "redis.call('DEL'" in script
        if self.values.get(key) == token:
            del self.values[key]
            self.released.append(key)
            return 1
        return 0


@pytest.mark.asyncio
async def test_shared_robots_cache_fetches_once_and_shares_policy(monkeypatch):
    redis = FakeRedis()
    policy = RobotsPolicy(ttl_seconds=120, redis_client=redis)
    calls = []

    async def fake_fetch(url, *, max_redirects=None):
        calls.append((url, max_redirects))
        return 200, "User-agent: *\nDisallow: /private\n", url

    monkeypatch.setattr(robots, "fetch_response", fake_fetch)

    assert await policy.can_fetch("https://Example.org/public") is True
    assert await policy.can_fetch("https://example.org/private/data") is False
    assert await policy.can_fetch("https://example.org/public/again") is True
    assert calls == [("https://example.org/robots.txt", 0)]
    assert len(redis.released) == 1
    assert any(key.startswith("intiligence:robots:cache:") for key in redis.values)


@pytest.mark.asyncio
async def test_shared_robots_cache_allows_404_and_410(monkeypatch):
    for status in (404, 410):
        redis = FakeRedis()
        policy = RobotsPolicy(redis_client=redis)

        async def fake_fetch(url, *, max_redirects=None, response_status=status):
            return response_status, "", url

        monkeypatch.setattr(robots, "fetch_response", fake_fetch)
        assert await policy.can_fetch("https://missing.example/path") is True


@pytest.mark.asyncio
async def test_shared_robots_cache_fails_closed_when_redis_unavailable():
    class BrokenRedis:
        async def get(self, _key):
            raise ConnectionError("redis unavailable")

    policy = RobotsPolicy(redis_client=BrokenRedis())
    with pytest.raises(RobotsPolicyError, match="shared robots cache unavailable"):
        await policy.can_fetch("https://example.org/path")


def test_shared_robots_cache_required_without_url_fails_startup():
    with pytest.raises(RuntimeError, match="INTILIGENCE_REDIS_URL"):
        RobotsPolicy(require_shared=True)


@pytest.mark.asyncio
async def test_shared_robots_waiter_reads_other_workers_cached_policy(monkeypatch):
    import hashlib
    import json

    redis = FakeRedis()
    origin = "https://example.org"
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()
    lock_key = f"intiligence:robots:lock:{digest}"
    cache_key = f"intiligence:robots:cache:{digest}"
    redis.values[lock_key] = "another-worker-token"
    policy = RobotsPolicy(redis_client=redis)

    async def other_worker_finishes(_delay):
        redis.values[cache_key] = json.dumps(
            {"status": 200, "body": "User-agent: *" + chr(10) + "Disallow: /private" + chr(10)}
        )

    monkeypatch.setattr(robots.asyncio, "sleep", other_worker_finishes)
    assert await policy.can_fetch("https://example.org/private/report") is False
    assert lock_key not in redis.released
