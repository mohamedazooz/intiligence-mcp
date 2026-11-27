"""Conditional revalidation and bounded due-source refresh orchestration."""

from __future__ import annotations

import hashlib
from typing import Any

from intiligence_mcp.acquisition.captcha.detector import detect_challenge
from intiligence_mcp.acquisition.onion import fetch_onion_response
from intiligence_mcp.config import settings
from intiligence_mcp.acquisition.http import (
    AcquisitionError,
    AcquisitionPolicyDenied,
    fetch_response_details,
)
from intiligence_mcp.extraction.trafilatura_adapter import extract_main_text
from intiligence_mcp.policy.robots import robots_policy
from intiligence_mcp.storage.challenges import AccessChallengeStore
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.freshness import FreshnessStore
from intiligence_mcp.storage.source_registry import SourceRegistry


class RefreshService:
    def __init__(
        self,
        sources: SourceRegistry,
        evidence: EvidenceStore,
        freshness: FreshnessStore,
        challenges: AccessChallengeStore,
    ) -> None:
        self.sources = sources
        self.evidence = evidence
        self.freshness = freshness
        self.challenges = challenges

    async def refresh_source(self, source_id: str, *, force: bool = False) -> dict[str, Any]:
        source = self.sources.get(source_id)
        if source is None:
            return {"status": "not_found", "source_id": source_id}
        state = self.freshness.ensure(source_id)
        if not force and state.state == "fresh" and state.next_refresh_at:
            from datetime import datetime, timezone
            due_at = datetime.fromisoformat(state.next_refresh_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < due_at:
                return {
                    "status": "not_due",
                    "source_id": source_id,
                    "next_refresh_at": state.next_refresh_at,
                }

        try:
            if source.host.endswith(".onion"):
                # Onion sources must only ever use the Tor adapter. Never fall back
                # to clearnet DNS/HTTP when Tor is disabled or its proxy is absent.
                response = await fetch_onion_response(
                    source.url,
                    conditional_headers=self.freshness.conditional_headers(source_id),
                )
            else:
                response = await fetch_response_details(
                    source.url,
                    policy_check=robots_policy.can_fetch,
                    conditional_headers=self.freshness.conditional_headers(source_id),
                )
        except AcquisitionPolicyDenied:
            state = self.freshness.mark_failure(source_id, error_code="robots_denied")
            return {"status": "blocked_by_robots_txt", "source_id": source_id, "freshness": state.state}
        except (AcquisitionError, ValueError) as exc:
            error_code = (
                "onion_source_not_allowed"
                if source.host.endswith(".onion") and isinstance(exc, ValueError)
                else type(exc).__name__
            )
            state = self.freshness.mark_failure(source_id, error_code=error_code)
            return {
                "status": "refresh_failed",
                "source_id": source_id,
                "reason": error_code,
                "freshness": state.state,
            }

        if response.status == 304:
            state = self.freshness.mark_verified(
                source_id,
                raw_sha256=None,
                http_status=304,
                etag=response.response_headers.get("etag"),
                last_modified=response.response_headers.get("last-modified"),
                not_modified=True,
            )
            return {
                "status": "not_modified",
                "source_id": source_id,
                "last_verified_at": state.last_verified_at,
                "next_refresh_at": state.next_refresh_at,
                "freshness": state.state,
            }

        if response.status != 200:
            state = self.freshness.mark_failure(
                source_id, error_code="http_status", http_status=response.status
            )
            return {
                "status": "http_error",
                "source_id": source_id,
                "http_status": response.status,
                "freshness": state.state,
            }

        challenge = detect_challenge(response.text)
        if challenge.detected:
            capture = self.evidence.capture(
                source_id, response.body, "",
                media_type=response.media_type,
                http_status=response.status,
                final_url=response.final_url,
                response_headers=response.response_headers,
                redirect_chain=list(response.redirect_chain),
                extractor_name="access-challenge-detector",
                extractor_version="1",
            )
            challenge_id = self.challenges.record(
                source_id, capture.artifact_id, challenge.category, challenge.evidence
            )
            state = self.freshness.mark_failure(
                source_id, error_code="access_challenge", http_status=response.status
            )
            return {
                "status": "requires_human_review",
                "source_id": source_id,
                "challenge_id": challenge_id,
                "challenge": challenge.category,
                "freshness": state.state,
            }

        raw_sha256 = hashlib.sha256(response.body).hexdigest()
        previous = self.freshness.get(source_id)
        changed = previous is None or previous.last_raw_sha256 != raw_sha256
        capture_payload: dict[str, Any] | None = None
        if changed:
            extracted = extract_main_text(response.text, response.final_url)
            capture = self.evidence.capture(
                source_id,
                response.body,
                extracted,
                media_type=response.media_type,
                http_status=response.status,
                final_url=response.final_url,
                response_headers=response.response_headers,
                redirect_chain=list(response.redirect_chain),
                extractor_name="trafilatura",
                extractor_version="2.3.1",
            )
            capture_payload = {
                "artifact_id": capture.artifact_id,
                "evidence_id": capture.evidence_id,
                "raw_sha256": capture.raw_sha256,
                "content_sha256": capture.content_sha256,
                "captured_at": capture.captured_at,
            }

        state = self.freshness.mark_verified(
            source_id,
            raw_sha256=raw_sha256,
            http_status=response.status,
            etag=response.response_headers.get("etag"),
            last_modified=response.response_headers.get("last-modified"),
        )
        return {
            "status": "updated" if changed else "unchanged",
            "source_id": source_id,
            "content_changed": changed,
            "capture": capture_payload,
            "last_verified_at": state.last_verified_at,
            "next_refresh_at": state.next_refresh_at,
            "freshness": state.state,
        }

    async def refresh_due(self, limit: int = 10) -> dict[str, Any]:
        excluded = () if settings.enable_onion_osint else ("onion",)
        due = self.freshness.due(limit, exclude_policy_names=excluded)
        results = []
        for item in due:
            results.append(await self.refresh_source(item.source_id, force=True))
        return {
            "status": "ok",
            "checked": len(results),
            "results": results,
        }
