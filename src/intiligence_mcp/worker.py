"""Standalone local scheduler for conditional source revalidation."""

from __future__ import annotations

import argparse
import asyncio
import logging

from intiligence_mcp.config import settings
from intiligence_mcp.research.refresh import RefreshService
from intiligence_mcp.storage.challenges import AccessChallengeStore
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.freshness import FreshnessStore
from intiligence_mcp.storage.source_registry import SourceRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("intiligence.refresh")


async def _run_once(service: RefreshService) -> None:
    result = await service.refresh_due(settings.refresh_worker_batch_size)
    outcomes: dict[str, int] = {}
    for item in result["results"]:
        status = str(item.get("status", "unknown"))
        outcomes[status] = outcomes.get(status, 0) + 1
    logger.info("refresh cycle completed: checked=%d outcomes=%s", result["checked"], outcomes)


async def _run_forever(service: RefreshService) -> None:
    while True:
        try:
            await _run_once(service)
        except Exception as exc:  # keep worker alive; exception details may contain URLs
            logger.error("refresh cycle failed: %s", type(exc).__name__)
        await asyncio.sleep(settings.refresh_worker_interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Intiligence conditional refresh worker")
    parser.add_argument("--once", action="store_true", help="run one refresh batch and exit")
    args = parser.parse_args()

    sources = SourceRegistry(settings.source_registry_path)
    evidence = EvidenceStore(settings.source_registry_path)
    freshness = FreshnessStore(settings.source_registry_path)
    challenges = AccessChallengeStore(settings.source_registry_path)
    service = RefreshService(sources, evidence, freshness, challenges)
    try:
        if args.once:
            asyncio.run(_run_once(service))
        else:
            asyncio.run(_run_forever(service))
    except KeyboardInterrupt:
        logger.info("refresh worker stopped by operator")


if __name__ == "__main__":
    main()
