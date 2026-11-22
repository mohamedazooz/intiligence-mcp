# Master Roadmap — Intiligence MCP

Planning baseline: 2026-11-22. Proposed sequence; update implementation state only from code, CI and deployment evidence.

## Phase 0 — Repository foundation
Confirm target repo/runtime/clients; define package boundaries, coding/test conventions and CI; maintain canonical docs index, SBOM and upstream manifest. Exit: clean checkout builds and CI green.

## Phase 1 — Control-plane security (blocking)
Enforce MCP auth and per-tool scopes; derive tenant from verified principal; prove owner/tenant scoping; block untrusted execution until sandbox exists; add migrations, storage streaming/caps, audit and redaction. Exit: all P0 security tests pass.

## Phase 2 — Evidence core
Implement Source, DiscoveryRun, Acquisition, Artifact, Representation, Locator, EvidenceCapsule, Claim and ClaimEvidence; migrations, retention and deletion. Exit: provenance and contradiction invariants pass.

## Phase 3 — Safe acquisition
Implement SSRF-safe HTTPX, per-host budgets, redirect/DNS validation, artifact hashing and Trafilatura adapter. Evaluate SearXNG optionally. Exit: SSRF and resource tests pass.

## Phase 4 — Document intelligence
Docling parser PoC, page/table locators, warnings, OCR/model license review and hostile-file corpus. Exit: accuracy/resource thresholds pass.

## Phase 5 — Dynamic acquisition
Isolated Playwright worker; compare Crawl4AI against baseline; deny egress by default; test session isolation, cancellation and cleanup. Exit: sandbox tests pass.

## Phase 6 — MCP research workflow
Versioned tools for discovery, acquisition, parsing, evidence, claim proposals and reports; client contract tests. Exit: traceable end-to-end report.

## Phase 7 — CTI and OSINT
STIX/TAXII; separate OpenCTI/MISP connectors; IntelOwl only with analyzer isolation; preserve TLP/confidence/source handling. Exit: sharing and authorization tests pass.

## Phase 8 — Retrieval and scale
Benchmark PostgreSQL first; Qdrant/OpenSearch/Redis/Temporal only with measured need and ADR. Exit: proven quality/cost/latency improvement.

## Phase 9 — Production readiness
Observability, SLOs, runbooks, SBOM, license/security scan, restore drill, load test, canary and rollback. Exit: release gates approved.
