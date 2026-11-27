import json

import pytest

from intiligence_mcp.research.github import (
    GitHubResearchError,
    inspect_public_repository,
    normalize_repository,
)
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def test_normalize_repository_accepts_slug_and_https_github_url():
    assert normalize_repository("owner/repo") == "owner/repo"
    assert normalize_repository("https://github.com/owner/repo.git") == "owner/repo"


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/owner/repo",
        "https://github.com.evil.test/owner/repo",
        "https://example.com/owner/repo",
        "https://github.com:invalid/owner/repo",
        "owner/repo/extra",
        "../repo",
    ],
)
def test_normalize_repository_rejects_untrusted_or_ambiguous_input(value):
    with pytest.raises(GitHubResearchError):
        normalize_repository(value)


@pytest.mark.asyncio
async def test_public_repository_inventory_is_bounded_and_evidence_linked(tmp_path):
    database = tmp_path / "research.sqlite3"
    source_registry = SourceRegistry(database)
    evidence_store = EvidenceStore(database)
    calls = []

    async def fake_fetch(url: str):
        calls.append(url)
        if url.endswith("/repos/owner/repo"):
            body = {
                "private": False,
                "default_branch": "main",
                "description": "A sample MCP repository",
                "language": "Python",
                "stargazers_count": 12,
                "archived": False,
                "license": {"spdx_id": "MIT"},
            }
        else:
            body = {
                "truncated": False,
                "tree": [
                    {"type": "blob", "path": ".mcp.json"},
                    {"type": "blob", "path": ".claude/skills/research/SKILL.md"},
                    {"type": "blob", "path": ".claude/settings.json"},
                    {"type": "blob", "path": "pyproject.toml"},
                    {"type": "tree", "path": "src"},
                ],
            }
        return 200, json.dumps(body), url

    result = await inspect_public_repository(
        "owner/repo",
        source_registry,
        evidence_store,
        fetcher=fake_fetch,
    )

    assert result["status"] == "ok"
    assert result["repository"] == "owner/repo"
    assert result["license_spdx"] == "MIT"
    assert result["file_count"] == 4
    assert result["inventory"]["mcp_manifests"] == [".mcp.json"]
    assert result["inventory"]["skills"] == [".claude/skills/research/SKILL.md"]
    assert result["inventory"]["hooks"] == [".claude/settings.json"]
    assert result["inventory"]["build_manifests"] == ["pyproject.toml"]
    assert len(calls) == 2
    for artifact in result["provenance"].values():
        assert evidence_store.get(artifact["evidence_id"]) is not None
        assert evidence_store.get_capture(artifact["artifact_id"]) is not None
