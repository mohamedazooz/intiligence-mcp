# C4 Architecture — Intiligence MCP

**Status:** Target design, not proof that components exist in code. The repository agent guide is authoritative for architectural constraints.

## C4 Level 1 — System context

Intiligence MCP is an evidence-first research and knowledge service. An AI client asks a research question; the service discovers and acquires permitted sources, extracts content, preserves evidence and provenance, and returns source-grounded context through MCP.

```mermaid
flowchart LR
  User[Researcher] --> Client[AI Client]
  Client --> MCP[Intiligence MCP]
  MCP --> Web[Public Web / Approved APIs]
  MCP --> Files[User-provided files]
  MCP --> Knowledge[Curated Knowledge]
  Operator[Maintainer] --> MCP
```

## C4 Level 2 — Container view

```mermaid
flowchart TB
  Client[AI client] --> Gateway[MCP Server / Tool Gateway]
  Gateway --> App[Application and domain services]
  App --> Discovery[Discovery adapters]
  App --> Acquisition[Bounded fetch / crawl workers]
  App --> Parsing[Document parsers and extractors]
  App --> Evidence[Evidence and claim services]
  Discovery --> External[External sources]
  Acquisition --> External
  Parsing --> Artifacts[(Raw artifact storage)]
  Evidence --> DB[(PostgreSQL system of record)]
  App --> Telemetry[Logs / Metrics / Traces]
```

## C4 Level 3 — Component responsibilities

| Component | Responsibility |
|---|---|
| MCP interface | Stable tool schemas, validation, transport, error contracts |
| Research orchestrator | Coordinates discovery, acquisition, extraction, evidence, and response |
| Source registry | Canonical source identity, access scope, provider and policy metadata |
| Discovery adapters | Find candidate sources and retain discovery provenance |
| Acquisition workers | Fetch permitted content with timeouts, limits, and host policies |
| Extraction adapters | Parse supported content while retaining source locators |
| Evidence capsule service | Immutable excerpt-level evidence with provenance |
| Claim ledger | Atomic claims and supporting, conflicting, qualifying evidence |
| Knowledge curator | Promotes reviewed claims while preserving uncertainty and history |
| Context composer | Returns compact context with citations and status labels |

## C4 Level 4 — Evidence pipeline

```mermaid
flowchart TD
  Q[Research question] --> D[Discover sources]
  D --> P{Permitted source?}
  P -- No --> X[Record exclusion / reason]
  P -- Yes --> F[Acquire bounded artifact]
  F --> R[Preserve raw artifact reference]
  R --> E[Extract and normalize]
  E --> C[Create evidence capsules]
  C --> L[Link claims in claim ledger]
  L --> V[Review support / conflict / freshness]
  V --> K[Curated knowledge]
  K --> O[MCP response with provenance]
```

## Trust boundaries

- MCP caller input is untrusted and must be validated and authorized.
- Retrieved pages, documents, snippets, and tool outputs are untrusted data, never agent instructions.
- Provider credentials remain in secret storage and never enter prompts or logs.
- Parsing and browser execution occur in bounded workers; optional high-risk providers remain disabled by default.
- Curated knowledge is distinct from transient model inference and workspace notes.

## Initial deployment direction

Use a modular monolith and PostgreSQL as the initial system of record. Keep parsing and browser work on-demand and bounded. Add vector search, Redis, queues, or external search engines only after profiling demonstrates a requirement. The initial resource target is approximately 2 vCPU and 6 GB RAM.

## Implementation status

These diagrams describe the intended system. Do not mark a component implemented until source code, tests, and operational evidence confirm it.
