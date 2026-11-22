# Roadmap — Research to Production

## Phase 0 — Inventory
Freeze repository refs, complete historical repo list, source/license ledger and ownership boundaries.

## Phase 1 — P0 Security
MCP bearer auth and tool scopes; tenant/owner binding; worker Docker/OCI isolation; SSRF defenses; Alembic migrations. Block untrusted host subprocess jobs until sandbox enforced.

## Phase 2 — Evidence/Search
PostgreSQL source/artifact/evidence/claim schema; HTTPX + Trafilatura; search provider interface; citations and conflict handling.

## Phase 3 — Documents/Dynamic Web
Docling parser worker; Playwright/Crawl4AI only for approved JS sites; Arabic/English and RTL quality benchmark.

## Phase 4 — Agent/Model Integrations
LiteLLM optional adapter; LangGraph selectively; OmniMCP job delegation; approval gates; Telegram UX through API only.

## Phase 5 — Defensive CTI
Passive enrichment; OpenCTI/MISP/IntelOwl separate services; ProjectDiscovery active tools only under explicit allowlists.

## Phase 6 — Production
Backup/restore, telemetry, rate budgets, tenant isolation, load/security tests, canary rollout, incident runbooks and provider kill switches.

## DoD
Pinned commit/version, license approval, threat review, tests, owner, metrics, fallback and rollback for every integration.