"""MCP server exposing bounded research acquisition tools."""

from mcp.server.fastmcp import FastMCP

from intiligence_mcp.acquisition.captcha.detector import detect_challenge
from intiligence_mcp.acquisition.captcha.escalation import escalate_challenge
from intiligence_mcp.acquisition.http import fetch_url
from intiligence_mcp.config import settings
from intiligence_mcp.extraction.trafilatura_adapter import extract_main_text
from intiligence_mcp.policy.robots import robots_policy
from intiligence_mcp.security.url_policy import validate_url
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry

_source_registry = SourceRegistry(settings.source_registry_path)
_evidence_store = EvidenceStore(settings.source_registry_path)

mcp = FastMCP("Intiligence MCP")


@mcp.tool()
async def research_fetch(url: str) -> dict:
    """Fetch a public HTTP(S) page under SSRF, redirect, and response-size controls."""
    validate_url(
        url,
        allow_private=settings.allow_private_networks,
        allowlist=settings.domains(settings.domain_allowlist),
        denylist=settings.domains(settings.domain_denylist),
    )
    if not await robots_policy.can_fetch(url):
        return {"url": url, "status": "blocked_by_robots_txt"}
    html, final_url = await fetch_url(url)
    challenge = detect_challenge(html)
    if challenge.detected:
        escalation = escalate_challenge(challenge.category)
        return {
            "url": final_url,
            "status": escalation.status,
            "challenge": challenge.category,
            "evidence": list(challenge.evidence),
        }
    text = extract_main_text(html, final_url)
    source = _source_registry.add(final_url)
    evidence = _evidence_store.save(source.source_id, text)
    return {
        "url": final_url,
        "status": "ok",
        "text": text,
        "source_id": source.source_id,
        "evidence_id": evidence.evidence_id,
        "content_sha256": evidence.content_sha256,
        "captured_at": evidence.captured_at,
    }


@mcp.tool()
async def research_check_robots(url: str) -> dict:
    """Check whether robots.txt permits fetching a public HTTP(S) URL."""
    validate_url(
        url,
        allow_private=settings.allow_private_networks,
        allowlist=settings.domains(settings.domain_allowlist),
        denylist=settings.domains(settings.domain_denylist),
    )
    allowed = await robots_policy.can_fetch(url)
    return {"url": url, "allowed": allowed, "policy": "robots.txt"}


@mcp.tool()
async def research_register_source(url: str, title: str | None = None) -> dict:
    """Register a public source URL with a stable ID and first-seen timestamp."""
    validate_url(
        url,
        allow_private=settings.allow_private_networks,
        allowlist=settings.domains(settings.domain_allowlist),
        denylist=settings.domains(settings.domain_denylist),
    )
    record = _source_registry.add(url, title)
    return {
        "source_id": record.source_id,
        "url": record.url,
        "host": record.host,
        "title": record.title,
        "first_seen_at": record.first_seen_at,
    }


@mcp.tool()
async def research_get_evidence(evidence_id: str) -> dict:
    """Retrieve a previously captured evidence record by its stable ID."""
    record = _evidence_store.get(evidence_id)
    if record is None:
        return {"status": "not_found", "evidence_id": evidence_id}
    return {
        "status": "ok",
        "evidence_id": record.evidence_id,
        "source_id": record.source_id,
        "content_sha256": record.content_sha256,
        "captured_at": record.captured_at,
        "content": record.content,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
