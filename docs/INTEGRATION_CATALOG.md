# Integration Catalog

**Status:** Candidate architecture. No provider is approved for production merely by appearing in this list.

## Principles

- Keep providers behind narrow adapters and stable internal contracts.
- Prefer official APIs and permitted access paths over browser automation.
- Evaluate maintenance, security posture, license, data handling, operational footprint, and reproducibility before adoption.
- Pin versions and record the evaluated commit/release.
- Optional heavyweight or high-risk providers remain disabled by default.

## Capability map

| Capability | Candidate approach | Decision gate |
|---|---|---|
| MCP transport | Official MCP SDK for the selected language | Confirm runtime and protocol compatibility |
| Search/discovery | Approved search APIs; optional self-hosted metasearch | Coverage, terms, rate limits, attribution |
| Static acquisition | Bounded HTTP client | SSRF controls, robots/terms, size limits |
| Dynamic pages | Isolated browser worker, on demand | Sandbox, resource budget, site policy |
| HTML extraction | Readability/structured parser adapters | Locator preservation and extraction quality |
| IOC extraction/index | Evidence-linked SQLite indicator store | Strict parsing, deterministic IDs, evidence references, privacy minimization |
| Public repository inventory | GitHub REST API via bounded acquisition | API rate limits, response caps, source/evidence provenance; never execute repository code |
| PDF/office parsing | Docling or equivalent adapter | Accuracy, formats, runtime footprint, license |
| Primary data store | PostgreSQL | Initial system of record per agent guide |
| Vector retrieval | Optional Qdrant or PostgreSQL extension | Benchmark before adding another database |
| Cache/queue | Optional Redis or managed queue | Add only for measured needs |
| Observability | Structured logs, metrics, traces | Data minimization and deployment cost |

## Candidate evaluation checklist

- Is the repository active and security-maintained?
- Is its license compatible with intended use and distribution?
- Can it run within the initial 2 vCPU / 6 GB RAM budget?
- Does it support bounded execution and cancellation?
- Can it preserve source identity, exact locators, and provenance?
- Are authentication and secrets handled safely?
- Can it be replaced without changing domain contracts?
- What is the fallback if unavailable?

## Decision record

Every adopted provider needs an ADR recording requirements, alternatives, license/security review, benchmarks, operational ownership, failure mode, version/commit, and revisit trigger.

## Current status

The public GitHub repository inventory is implemented through the existing bounded acquisition path and was smoke-tested through the local Squid egress proxy and MCP stdio. Repository metadata and tree responses are persisted as source/evidence records. The IOC index is implemented in SQLite and links indicators to existing evidence. No other third-party OSINT provider from the supplied v2 archive is approved or enabled.
