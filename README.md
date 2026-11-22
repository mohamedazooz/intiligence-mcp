# Intiligence MCP — Research & Integration Foundation

This is an evidence-led research and architecture pack for building Intiligence MCP on top of the existing OmniMCP control plane.

## Inspected inputs
- GitHub repository: https://github.com/mohamedazooz/MULTI-AGENTS-OPS, branch `vibe/omnimcp-foundation-5d6ade`.
- Uploaded ZIP: 82 entries including backend, worker, tests, 15 docs and 5 ADRs.
- Uploaded scraping research note: 30,983 characters and 22 unique GitHub URLs.
- Target repository: https://github.com/mohamedazooz/intiligence-mcp; inspected main tree is documentation-only.
- Local laptop project: `D:\StealthScraper_Engine` (README, SDK, MCP server, live test script).

## Core recommendation
Keep OmniMCP as the Control Plane. Intiligence owns search, acquisition, source provenance, evidence, claims and curated knowledge. Reuse OmniMCP's agent/worker/job/workspace/storage primitives rather than cloning them.

## P0 blockers discovered
1. OmniMCP implementation status says MCP bearer authentication is pending. Do not expose MCP to untrusted clients until transport auth and per-tool authorization are implemented and tested.
2. Worker currently runs host subprocesses with resource limits. Docker/OCI/gVisor isolation is not implemented in the supplied snapshot. Do not treat this as a secure sandbox for untrusted code.
3. Owner scoping of MCP operations must be verified; inspected tools call domain functions with `owner_id=None` in some paths.
4. Alembic migrations are deferred; add migration discipline before production schema changes.
5. Hugging Face storage adapter buffers whole objects in memory; add streaming or strict object-size caps.

## Contents
- `docs/`: audit, architecture, search, deep-web, web ingestion, OSINT/CTI, document intelligence, evidence, security, licensing, operations and roadmap.
- `catalog/`: integration candidates grouped by capability.
- `security/`: dark-web policy and secure adapter requirements.
- `roadmap/`: phased delivery plan.

## Evidence labels
Verified in source / Documented upstream / Candidate / Adopt / Defer / Reject / Not tested.

No candidate is considered installed merely because it appears in this pack.