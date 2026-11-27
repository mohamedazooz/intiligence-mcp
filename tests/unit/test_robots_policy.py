from urllib.robotparser import RobotFileParser

from intiligence_mcp.policy.robots import RobotsPolicy


def test_robots_parser_respects_disallow_rules():
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /private", "Allow: /private/public"])
    assert not parser.can_fetch("IntiligenceResearchBot", "https://example.org/private/data")
    assert parser.can_fetch("IntiligenceResearchBot", "https://example.org/private/public/page")


def test_robots_cache_returns_cached_allow_all(tmp_path):
    policy = RobotsPolicy()
    policy._cache["https://example.org"] = (10**20, None, True)
    import asyncio

    assert asyncio.run(policy.can_fetch("https://example.org/a"))
