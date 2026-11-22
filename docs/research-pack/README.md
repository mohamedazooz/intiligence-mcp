# Intiligence MCP — Research and Engineering Pack

This pack is an evidence-led architecture, source-audit and implementation planning baseline for Intiligence MCP.

## Project boundary

Target repository: https://github.com/mohamedazooz/intiligence-mcp

Existing control plane: https://github.com/mohamedazooz/MULTI-AGENTS-OPS

The target repository is currently documentation-first in the inspected main tree. The existing OmniMCP control plane remains a separate repository. Intiligence owns source discovery/acquisition, evidence, claims, research workflows and cited reports. Do not duplicate the control plane.

## Inspected inputs

- Existing control-plane audit: FastAPI API, worker package, tests, storage and MCP surface.
- Supplied research note: 22 unique GitHub URLs; discovery inventory is not a complete source audit.
- Local D-drive StealthScraper_Engine: README and MCP server reviewed statically; no live bypass testing performed.
- Target repository: main branch and documentation tree inspected.
- Research pack imported to the target branch separately from the canonical project docs.

## P0 blockers carried forward

1. MCP bearer authentication was pending in the inspected control-plane snapshot.
2. Worker execution used host subprocesses and resource limits without an enforced container/gVisor sandbox.
3. Owner/tenant scoping needed verification; some inspected MCP paths passed owner_id=None.
4. Alembic migrations were deferred.
5. HF storage adapter buffered complete objects in memory.
6. Arbitrary URL/proxy/anti-bot behavior in StealthScraper must not be connected directly to production. Reuse only compliant extraction concepts after SSRF, policy and isolation controls.

Revalidate all findings against the current control-plane branch before implementation.

## Core architecture direction

- Retain OmniMCP as control plane.
- Modular monolith for Intiligence domain services.
- PostgreSQL as initial system of record.
- HTTPX + Trafilatura as static acquisition baseline.
- Docling as first document-parser proof of concept.
- Playwright as isolated on-demand browser worker.
- Crawl4AI as a comparative candidate, not an automatic second crawler.
- SearXNG as optional separate search service.
- OpenCTI and MISP as separate CTI services via API/STIX/TAXII.
- Qdrant, OpenSearch, Redis, Temporal and Firecracker deferred until measured need.

## Code reuse policy

Prefer dependencies, APIs and adapters. Fork or copy source only after exact commit, file-level license, NOTICE, security and dependency review. Preserve provenance and produce an SBOM. No wholesale copy of upstream repositories into the product core.

## Contents

- catalog/: upstream portfolio and reuse decisions.
- docs/: architecture, integration, data model, MCP contracts, security, testing, deployment and research.
- roadmap/: master phases, backlog and acceptance gates.
- security/: threat model and safe acquisition policy.
- UPSTREAM_SOURCE_MANIFEST.md: 22-repository audit register.

## Status labels

Verified in source; Documented upstream; Candidate; Adopt; Defer; Reject; Not tested. A proposed design is not proof of implementation.
