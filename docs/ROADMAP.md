# Product and Engineering Roadmap

**Status:** Proposed sequence; prioritize from verified requirements and measured risk.

## Phase 0 — Repository foundation

Confirm project scope, supported MCP clients, runtime language, and deployment target. Establish package/build/test conventions and CI. Define domain terminology and API error conventions. **Acceptance:** reproducible local setup, baseline CI, reviewed agent rules.

## Phase 1 — Evidence core

Implement source, artifact, evidence capsule, claim, and provenance contracts. Add PostgreSQL migrations and repository layer. Enforce claim/evidence invariants. **Acceptance:** deterministic tests prove provenance retention and prevent unsupported claims from being marked supported.

## Phase 2 — Ingestion foundation

Implement approved discovery and bounded HTTP acquisition adapters. Add artifact hashing, deduplication, and extraction metadata. Add HTML and one document parser adapter. **Acceptance:** fixtures preserve exact source locators; SSRF, size, timeout, and policy-denial tests pass.

## Phase 3 — Research orchestration

Implement orchestration, source selection, cancellation, and retry policy. Add claim extraction as a proposal, never automatic verification. Handle conflicting, stale, and insufficient evidence explicitly. **Acceptance:** an end-to-end fixture produces a traceable report with citations and visible uncertainty.

## Phase 4 — MCP surface

Expose stable MCP tools with versioned input/output schemas. Add authentication/authorization appropriate to deployment. Add contract tests and client compatibility checks. **Acceptance:** supported clients call documented tools and receive provenance-preserving responses.

## Phase 5 — Knowledge retrieval

Add curated knowledge lifecycle and review workflow. Benchmark PostgreSQL retrieval before considering vector infrastructure. Add optional vector search only when measurements justify it. **Acceptance:** curated records retain evidence lineage and tenant-isolation tests pass.

## Phase 6 — Production hardening

Add telemetry, dashboards, alerts, backup/restore, and incident runbooks. Complete security, privacy, and license reviews. Load-test against the target VPS profile and define capacity thresholds. **Acceptance:** restore drill, security gates, operational ownership, and release checklist completed.

## Prioritization

Prioritize correctness, provenance, safe acquisition, and stable contracts before provider breadth or advanced autonomy. Do not add infrastructure without a measured requirement and documented decision.


## Detailed delivery plan

The phase-level engineering plan and acceptance evidence are maintained in [research-pack/roadmap/MASTER_ROADMAP.md](research-pack/roadmap/MASTER_ROADMAP.md), [IMPLEMENTATION_BACKLOG.md](research-pack/roadmap/IMPLEMENTATION_BACKLOG.md) and [ACCEPTANCE_GATES.md](research-pack/roadmap/ACCEPTANCE_GATES.md). These are proposed work items, not claims of completed implementation.
