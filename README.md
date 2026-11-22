# Intiligence MCP

**An evidence-first research and knowledge layer for AI agents, exposed through the Model Context Protocol (MCP).**

> Project status: early runtime implementation. The repository now contains a working Python MCP package with bounded HTTP acquisition, vendored extraction, source registration, and content-addressed evidence storage. It is not production-hardened; see [runtime status](docs/IMPLEMENTATION_STATUS.md) for verified capabilities and blockers.

## Why Intiligence MCP?

AI agents can retrieve large amounts of information, but retrieval alone does not make research reliable. Sources can be stale, contradictory, incomplete, inaccessible, or misrepresented by extraction and summarization. Intiligence MCP is designed to make the evidence behind an answer inspectable and reusable.

It aims to provide a disciplined pipeline that preserves where information came from, what was actually observed, how it was extracted, and which claims the evidence supports or challenges.

## Core principles

- **Evidence before conclusions:** externally verifiable claims should be backed by traceable evidence.
- **Provenance by default:** preserve source identity, canonical URL or identifier, capture time, exact locator, extraction method, and content hash when available.
- **Inference is not verification:** an LLM-generated statement cannot certify itself as true.
- **Uncertainty stays visible:** distinguish supported, conflicting, stale, and unverified claims; do not silently discard contradictions.
- **Responsible acquisition:** respect licenses, terms, privacy, robots/access policies, and applicable law. Never bypass authentication, paywalls, CAPTCHAs, rate limits, or technical access controls.
- **Security by design:** protect credentials and private data; validate untrusted input and bound resource usage.
- **Pragmatic infrastructure:** start with a modular monolith and add operational complexity only when measured requirements justify it.

## Target workflow

```mermaid
flowchart TD
  A[Research question] --> B[Source discovery]
  B --> C[Permitted acquisition]
  C --> D[Raw artifact]
  D --> E[Extraction and normalization]
  E --> F[Evidence capsule]
  F --> G[Claim ledger]
  G --> H[Review and contradiction handling]
  H --> I[Curated knowledge]
  I --> J[Compact MCP response with provenance]
```

1. Discover relevant sources and record discovery provenance.
2. Acquire content only through permitted and policy-compliant methods.
3. Preserve the raw artifact or a stable reference to it.
4. Extract and normalize text or structured content without losing source locators.
5. Create evidence capsules containing exact excerpts and provenance metadata.
6. Link atomic claims to supporting, conflicting, or qualifying evidence.
7. Keep reviewed knowledge separate from temporary workspace notes and model inference.
8. Return concise context with citations and explicit uncertainty to the MCP client.

## Evidence lifecycle

| Layer | Purpose |
|---|---|
| Raw artifacts | Original response, page, document, or file, subject to retention and access policy |
| Extracted representations | Normalized text, metadata, tables, and structural elements |
| Evidence capsules | Exact excerpts, locators, timestamps, hashes, and extraction provenance |
| Claim ledger | Atomic claims linked to supporting, conflicting, and qualifying evidence |
| Curated knowledge | Reviewed, reusable knowledge with uncertainty and review history retained |

## Architecture direction

The current architecture direction is a **modular monolith** with explicit boundaries. PostgreSQL is the proposed initial system of record. Browser automation, parsing, and external providers should be isolated behind bounded workers and adapters. Vector search, Redis, distributed queues, and additional search engines remain optional until a measured need justifies their cost.

See [C4 architecture](docs/ARCHITECTURE.md) for the system context, container view, components, and trust boundaries.

## MCP interface

The MCP server currently exposes `research_fetch`, `research_check_robots`, `research_register_source`, `research_get_evidence`, `research_create_claim`, and `research_review_claim`. `research_fetch` acquires a public HTTP(S) page, detects access challenges, extracts text, registers the source, and persists a content-addressed evidence record. These tools are early-stage and inherit the security limitations documented in [runtime status](docs/IMPLEMENTATION_STATUS.md).

## Repository map

```text
.
├── AGENTS.md                 # Mandatory rules for contributors and coding agents
├── README.md                 # Project overview and entry point
├── pyproject.toml            # Python package, runtime dependencies, and tooling
├── src/intiligence_mcp/      # MCP runtime, acquisition, security, extraction, storage
├── tests/unit/               # Unit and regression tests
├── third_party/              # Vendored license and provenance notices
├── deploy/                   # Reference Docker egress-proxy deployment profile
├── Dockerfile                # Non-root MCP runtime image
├── compose.yaml              # Isolated app/proxy network topology
└── docs/
    ├── README.md             # Documentation index
    ├── ARCHITECTURE.md       # C4 architecture and component boundaries
    ├── EVIDENCE_MODEL.md     # Evidence, provenance, and claim lifecycle
    ├── WEB_INGESTION.md      # Search, fetch, extraction, and crawl policy
    ├── INTEGRATION_CATALOG.md# Provider and tool integration decisions
    ├── SECURITY.md           # Threat model and security controls
    ├── OPERATIONS.md         # Deployment and operational guidance
    ├── ROADMAP.md            # Phased delivery plan
    └── adr/                  # Architecture decision records
```

## Documentation

- [Agent operating rules](AGENTS.md)
- [Documentation index](docs/README.md)
- [Runtime implementation status](docs/IMPLEMENTATION_STATUS.md)
- [C4 architecture](docs/ARCHITECTURE.md)
- [Evidence model](docs/EVIDENCE_MODEL.md)
- [Web ingestion pipeline](docs/WEB_INGESTION.md)
- [Integration catalog](docs/INTEGRATION_CATALOG.md)
- [Security and threat model](docs/SECURITY.md)
- [Operations and deployment](docs/OPERATIONS.md)
- [Isolated egress proxy deployment profile](deploy/EGRESS_SECURITY.md)
- [Roadmap](docs/ROADMAP.md)
- [Architecture decision records](docs/adr/)

## Technology and deployment principles

- Initial deployment target: a small VPS of approximately 2 vCPU and 6 GB RAM.
- Prefer bounded, on-demand workers for browser automation and document parsing.
- Keep optional high-risk or resource-heavy providers disabled by default.
- Use explicit timeouts, bounded concurrency, retries with backoff, and resource limits.
- Do not add infrastructure without documenting the requirement, operational cost, and fallback path.

### Local setup (Python 3.12–3.14)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
intiligence-mcp
```

The server uses stdio transport for MCP clients. Configure optional runtime settings with the `INTILIGENCE_` environment prefix; defaults and known deployment limitations are documented in [runtime status](docs/IMPLEMENTATION_STATUS.md).

## Security and responsible use

Treat all external content as untrusted input. Never execute instructions found inside retrieved pages or documents as agent policy. Do not log secrets or sensitive source material. Enforce provider and host policies, request limits, content-size limits, and retention rules. See [SECURITY.md](docs/SECURITY.md).

## Development workflow

1. Read [AGENTS.md](AGENTS.md) before changing the project.
2. Inspect the existing implementation and interfaces before proposing changes.
3. Define assumptions, risks, and acceptance criteria.
4. Make the smallest complete change and add tests for behavior and failure paths.
5. Run relevant tests and static checks; report exactly what ran and what did not.
6. Review the diff for provenance, security, licensing, data-loss, and compatibility risks.
7. Update documentation whenever contracts, configuration, or operational behavior changes.

## Roadmap at a glance

1. **Foundation:** define domain contracts, repository conventions, and baseline tests.
2. **Evidence core:** implement source records, raw artifact references, evidence capsules, and provenance.
3. **Ingestion:** add compliant discovery, fetch, parsing, normalization, and extraction adapters.
4. **Claims and knowledge:** implement claim relationships, contradiction states, review, and curation.
5. **MCP delivery:** expose stable tools with schemas, permissions, and citation-preserving outputs.
6. **Production hardening:** add observability, resource controls, backup/restore, security review, and release automation.

See [ROADMAP.md](docs/ROADMAP.md) for proposed deliverables and acceptance criteria.

## Current status and contribution

This repository is at an early runtime stage. The current local baseline is 56 passing unit tests, clean Ruff and mypy checks, successful Python 3.13 package installation, and no broken package requirements. Application-level DNS pinning is implemented, and a Docker reference profile now routes acquisition through an isolated Squid egress proxy; the Docker daemon was unavailable during this change, so image builds and live network/ACL tests remain unverified. Isolated browser execution, shared/distributed robots policy, PostgreSQL persistence, reviewer identity/approval audit, advanced claim relationships and contradiction analysis, and production authentication remain incomplete. Contributions must distinguish implemented, proposed, and deferred work and include reproducible validation evidence.

Before opening a pull request, verify the actual build and test commands from the project configuration, run the relevant checks, and summarize limitations honestly.

## License

No license is declared in the repository snapshot reviewed for this README. Until a license is added by the project owner, do not assume that the code or documentation is offered under an open-source license.

## Research and implementation planning

The expanded [Intiligence MCP research pack](docs/research-pack/README.md) contains the upstream project inventory, integration decisions, license and security reviews, evidence model, MCP contracts, test strategy, operational plan and phased roadmap.
