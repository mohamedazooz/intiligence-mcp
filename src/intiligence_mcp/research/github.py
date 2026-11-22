"""Bounded, read-only inventory of public GitHub repositories."""
from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from urllib.parse import quote, urlsplit

from intiligence_mcp.acquisition.http import fetch_response
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry

FetchResponse = Callable[[str], Awaitable[tuple[int, str, str]]]


async def _fetch_github_api(url: str) -> tuple[int, str, str]:
    return await fetch_response(url, accept="application/vnd.github+json")


_REPO_SLUG = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")


class GitHubResearchError(ValueError):
    """Raised when a public repository cannot be safely inspected."""


def normalize_repository(value: str) -> str:
    candidate = value.strip()
    if candidate.startswith(("https://", "http://")):
        parts = urlsplit(candidate)
        if parts.scheme != "https" or parts.hostname not in {"github.com", "www.github.com"}:
            raise GitHubResearchError("Only HTTPS github.com repository URLs are accepted")
        try:
            port = parts.port
        except ValueError as exc:
            raise GitHubResearchError("Repository URL contains an invalid port") from exc
        if parts.username or parts.password or port not in (None, 443):
            raise GitHubResearchError("Repository URL contains unsupported authority details")
        segments = [segment for segment in parts.path.split("/") if segment]
        if len(segments) != 2:
            raise GitHubResearchError("Expected a GitHub URL in owner/repository form")
        candidate = "/".join(segments)
    candidate = candidate.removesuffix(".git")
    if not _REPO_SLUG.fullmatch(candidate):
        raise GitHubResearchError("Expected a public GitHub repository as owner/repository")
    owner, repository = candidate.split("/", 1)
    if owner in {".", ".."} or repository in {".", ".."}:
        raise GitHubResearchError("Invalid repository path")
    return f"{owner}/{repository}"


async def _fetch_json_evidence(
    url: str,
    title: str,
    source_registry: SourceRegistry,
    evidence_store: EvidenceStore,
    fetcher: FetchResponse,
) -> tuple[dict, dict]:
    status, body, final_url = await fetcher(url)
    if status != 200:
        raise GitHubResearchError(f"GitHub API returned HTTP {status}")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GitHubResearchError("GitHub API returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise GitHubResearchError("GitHub API response must be a JSON object")
    source = source_registry.add(final_url, title)
    evidence = evidence_store.save(source.source_id, body)
    return payload, {
        "source_id": source.source_id,
        "evidence_id": evidence.evidence_id,
        "content_sha256": evidence.content_sha256,
        "captured_at": evidence.captured_at,
    }


async def inspect_public_repository(
    repo_or_url: str,
    source_registry: SourceRegistry,
    evidence_store: EvidenceStore,
    *,
    fetcher: FetchResponse = _fetch_github_api,
) -> dict:
    """Inspect repository metadata and one bounded recursive tree; never downloads or executes code."""
    slug = normalize_repository(repo_or_url)
    encoded_slug = quote(slug, safe="/")
    metadata_url = f"https://api.github.com/repos/{encoded_slug}"
    metadata, metadata_evidence = await _fetch_json_evidence(
        metadata_url,
        f"GitHub repository metadata: {slug}",
        source_registry,
        evidence_store,
        fetcher,
    )

    if metadata.get("private") is True:
        raise GitHubResearchError("Private repositories are not inspected by this public-only tool")
    default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise GitHubResearchError("GitHub repository metadata omitted default_branch")

    tree_url = (
        f"https://api.github.com/repos/{encoded_slug}/git/trees/"
        f"{quote(default_branch, safe='')}?recursive=1"
    )
    tree_payload, tree_evidence = await _fetch_json_evidence(
        tree_url,
        f"GitHub repository tree: {slug}",
        source_registry,
        evidence_store,
        fetcher,
    )
    raw_tree = tree_payload.get("tree", [])
    if not isinstance(raw_tree, list):
        raise GitHubResearchError("GitHub tree response has an invalid tree field")

    paths = [
        item["path"]
        for item in raw_tree[:20_000]
        if isinstance(item, dict)
        and item.get("type") == "blob"
        and isinstance(item.get("path"), str)
    ]

    mcp_files = sorted(
        path for path in paths
        if path.lower().endswith((".mcp.json", "/mcp.json"))
        or path.lower() == "mcp.json"
    )[:100]
    skill_files = sorted(
        path for path in paths
        if path.lower().endswith("skill.md")
        or "/.claude/skills/" in f"/{path.lower()}/"
    )[:100]
    hook_files = sorted(
        path for path in paths
        if path.lower().endswith((".claude/settings.json",))
        or "/hooks/" in f"/{path.lower()}/"
    )[:100]
    build_files = sorted(
        path for path in paths
        if path.rsplit("/", 1)[-1].lower() in {
            "pyproject.toml", "package.json", "requirements.txt",
            "dockerfile", "compose.yaml", "compose.yml", "docker-compose.yml",
        }
    )[:100]

    license_info = metadata.get("license")
    license_spdx = (
        license_info.get("spdx_id")
        if isinstance(license_info, dict)
        else None
    )

    return {
        "status": "ok",
        "repository": slug,
        "description": metadata.get("description") or "",
        "default_branch": default_branch,
        "language": metadata.get("language"),
        "stars": metadata.get("stargazers_count", 0),
        "archived": bool(metadata.get("archived", False)),
        "license_spdx": license_spdx,
        "file_count": len(paths),
        "tree_truncated": bool(tree_payload.get("truncated")) or len(raw_tree) > 20_000,
        "inventory": {
            "mcp_manifests": mcp_files,
            "skills": skill_files,
            "hooks": hook_files,
            "build_manifests": build_files,
        },
        "provenance": {
            "metadata": metadata_evidence,
            "tree": tree_evidence,
        },
        "execution_performed": False,
        "recursive_repo_following": False,
    }
