# Upstream Source Manifest

This manifest distinguishes discovery from actual source vendoring and runtime integration. Do not mark a candidate integrated without a pinned revision, license/provenance record, source inventory, tests, and review.

| ID | Repository | Current status | Review focus |
|---|---|---|---|
| UP-001 | https://github.com/mohamedazooz/MULTI-AGENTS-OPS | Discovered; separate control plane | Auth, jobs, workers, storage, MCP boundary |
| UP-002 | https://github.com/unclecode/crawl4ai | Cloned at pinned commit; Apache-2.0 metadata checked; not vendored | Browser worker, PDF path, dependency surface, stealth/anti-bot review |
| UP-003 | https://github.com/adbar/trafilatura | Vendored; adapter integrated; tests passing | Extraction, locators, dependencies, release license |
| UP-004 | https://github.com/microsoft/playwright | Dependency candidate; not yet vendored | Browser isolation, downloads, network routing |
| UP-005 | https://github.com/docling-project/docling | Discovered | PDF/Office/OCR, models, runtime bounds |
| UP-006 | https://github.com/searxng/searxng | Discovered; AGPL boundary | Search API, engine adapters |
| UP-007 | https://github.com/qdrant/qdrant | Discovered | Vector filters, tenant isolation, backup |
| UP-008 | https://github.com/OpenCTI-Platform/opencti | Discovered; Community/Enterprise boundary | STIX/TAXII, API integration |
| UP-009 | https://github.com/MISP/MISP | Discovered; AGPL boundary | Core license, API, sharing markings |
| UP-010 | https://github.com/MISP/PyMISP | Discovered | API client, BSD-2-Clause, dependencies |
| UP-011 | https://github.com/intelowlproject/IntelOwl | Discovered | Analyzer isolation, plugins, egress |
| UP-012 | https://github.com/projectdiscovery/nuclei | Discovered | Template execution, authorization, license |
| UP-013 | https://github.com/google/gvisor | Discovered | Sandbox architecture and compatibility |
| UP-014 | https://github.com/firecracker-microvm/firecracker | Discovered | MicroVM boundary, jailer, host requirements |
| UP-015 | https://github.com/BerriAI/litellm | Discovered | Model routing, secrets, budgets, license paths |
| UP-016 | https://github.com/langchain-ai/langgraph | Discovered | State persistence, checkpoints, retries |
| UP-017 | https://github.com/temporalio/temporal | Discovered | Durable workflow tradeoffs |
| UP-018 | https://github.com/n8n-io/n8n | Discovered; license review required | License restrictions and execution isolation |
| UP-019 | https://github.com/opensearch-project/OpenSearch | Discovered | Lexical search and cluster footprint |
| UP-020 | https://github.com/mendableai/firecrawl | Discovered; AGPL/hosted terms review required | Overlap with Crawl4AI and license boundary |
| UP-021 | https://github.com/agentgateway/agentgateway | Discovered | MCP/A2A gateway, auth, routing |
| UP-022 | https://github.com/All-Hands-AI/OpenHands | Discovered | Coding agent runtime and sandbox |

## Vendored source record

### UP-003 — Trafilatura
- Upstream commit: `65eac050b7a2961bac9aefdfb7514121dd7382ba`
- Upstream version: `2.3.1`
- Upstream license: Apache-2.0
- Local package: `src/intiligence_mcp/_vendor/trafilatura/`
- Adapter: `src/intiligence_mcp/extraction/trafilatura_adapter.py`
- License copy: `third_party/licenses/TRAFILATURA-LICENSE`
- Provenance: `third_party/provenance/TRAFILATURA-CITATION.cff`
- Notice: `third_party/NOTICE.md`
- Source modifications: whitespace-only trailing-space cleanup in `data/tei_corpus.dtd` and `settings.cfg`; imported under a private package namespace.
- Verification: 12 unit tests passed; Ruff checks passed for first-party code; package import resolved to the vendored path.

## Status vocabulary

- **Discovered**: candidate identified, not yet checked out.
- **Metadata checked**: repository metadata and license inspected.
- **Source inspected**: relevant source files and dependencies reviewed.
- **Vendored**: source copied at a pinned revision with license/provenance retained.
- **Executed**: local runtime or tests exercised.
- **Integrated**: used by application code and covered by tests.
- **Approved**: security, license, and operational gates reviewed.

Do not equate vendoring with production approval. Browser workers, external analyzers, and search engines require their own egress, authorization, resource, and tenancy controls.


### UP-002 — Crawl4AI (review checkout only)
- Upstream commit: `67a717723f6413eeb5a5b14569aef8308f888adc`
- Upstream license declared in `pyproject.toml`: Apache-2.0
- Package source inventory: 86 files in the checked-out `crawl4ai/` package tree.
- Checkout: `D:\\tmp\\intiligence-upstreams\\crawl4ai` (developer workstation only; not part of the application repository).
- Vendoring decision: not copied wholesale. It overlaps the browser/crawler subsystem, has a broad dependency surface, and requires file-level review of stealth/anti-bot functionality and security advisories. Selective reuse requires its own provenance and tests.
