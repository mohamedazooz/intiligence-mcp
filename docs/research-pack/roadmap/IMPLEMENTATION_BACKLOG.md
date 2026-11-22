# Implementation Backlog

P0 blocks safe exposure; P1 required before production; P2 capability/quality; P3 optional.

| ID | Priority | Item | Acceptance evidence |
|---|---|---|---|
| INT-001 | P0 | MCP bearer auth and tool scopes | Auth/expiry/revocation tests |
| INT-002 | P0 | Tenant/owner scope on every MCP path | Cross-tenant negative tests |
| INT-003 | P0 | Block untrusted execution until sandbox | Fail-closed test |
| INT-004 | P0 | SSRF-safe URL policy and egress | IPv4/IPv6/DNS/redirect tests |
| INT-005 | P0 | Secret redaction | Canary/log scan |
| INT-006 | P1 | Alembic/schema migration discipline | Upgrade/restore test |
| INT-007 | P1 | Stream/cap storage transfers | Large-object memory test |
| INT-008 | P1 | Evidence/claim schema and invariants | Domain tests |
| INT-009 | P1 | Artifact hashing/deduplication | Hash fixtures |
| INT-010 | P1 | HTTPX acquisition adapter | Acquisition fixture suite |
| INT-011 | P1 | Trafilatura extractor | Locator and quality tests |
| INT-012 | P1 | Docling parser PoC | PDF/Office fixtures |
| INT-013 | P1 | MCP schema contract tests | Schema snapshots |
| INT-014 | P1 | Audit/provenance trail | Event completeness test |
| INT-015 | P2 | SearXNG search adapter | Relevance benchmark |
| INT-016 | P2 | Isolated Playwright worker | Egress/session/resource tests |
| INT-017 | P2 | Crawl4AI comparative evaluation | Benchmark report |
| INT-018 | P2 | STIX/TAXII connector | Round-trip fixture |
| INT-019 | P2 | OpenCTI connector | API contract tests |
| INT-020 | P2 | MISP connector | API/marking tests |
| INT-021 | P2 | IntelOwl analyzer adapter | Allowlist/isolation tests |
| INT-022 | P2 | PostgreSQL retrieval benchmark | Benchmark report |
| INT-023 | P3 | Qdrant derived index | Recall and deletion tests |
| INT-024 | P3 | OpenSearch evaluation | Cost/latency comparison |
| INT-025 | P3 | Temporal evaluation | ADR and failure tests |
| INT-026 | P3 | gVisor/Firecracker comparison | Threat model and benchmark |

No item is complete because it appears in documentation. Link each to PR, commit, test run and reviewer decision.
