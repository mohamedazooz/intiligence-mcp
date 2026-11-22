# Intelligence MCP v2 Archive — Senior Engineering Review & Integration Plan

## Intake

- Archive: `intelligence-mcp-v2-full.zip`
- SHA-256: `2de56e201566cea5f1c3fba47a6fa62c012c1c2a870043677baebe0ca7de0fcc`
- Contents: 27 files, including 11 Python modules/scripts, a second MCP gateway, Docker Compose stack, Tor/I2P, SearXNG, Byparr, Neo4j, hooks, skills, and setup scripts.
- Review method: source inspection, Python AST parsing of every archived Python file, and comparison with the existing Intiligence MCP architecture and operating rules.
- The archive contains no test directory or automated test suite. Its README/CATALOG claims are not treated as proof of implemented or verified behavior.

## Architectural decision

Do not deploy or merge this archive wholesale. The existing repository is an evidence-first modular monolith with SSRF-safe acquisition, robots enforcement, source/evidence registries, and a claim ledger. The archive introduces a second FastMCP server, a second SQLite data model, optional Neo4j, and a separate Compose network. Running both stacks would duplicate acquisition, provenance, storage, configuration, and operational controls.

Port capabilities into the existing package behind its existing acquisition and evidence interfaces. Keep optional/high-risk providers disabled by default. Preserve a single system of record and avoid introducing Neo4j until measured query or scale requirements justify it.

## Findings — prioritized

| Priority | Finding | Impact | Required treatment |
|---|---|---|---|
| Critical | Several archive modules create their own `httpx.AsyncClient` and access external services directly. | Bypasses this project's URL policy, DNS pinning, mandatory egress proxy, host pacing, robots policy, and response-size limits. | Route every outbound request through a controlled adapter; reject direct network clients in feature modules. |
| Critical | CAPTCHA solver integrations and Byparr/Camoufox escalation are designed to solve or bypass anti-bot challenges. | Conflicts with the repository rule not to bypass CAPTCHAs or technical access controls. | Do not port, configure, or enable these capabilities. Retain detection-only reporting and stop/escalate to an authorized human workflow. |
| Critical | Tor/I2P fetch functions accept broad URL inputs and follow redirects; all archive services share one bridge network. | Insufficient destination policy and service isolation; a compromised worker could reach unrelated internal services. | Do not deploy this topology. Any future Tor/I2P worker must be separately isolated, destination constrained, non-default, and explicitly authorized. |
| Critical | Compose contains default fallback passwords and placeholder SearXNG secret values. | Running Compose without setup can retain known credentials. | Remove insecure defaults; fail startup when required secrets are absent; use secret files or a supported secret manager. |
| Important | Username pivot and breach/infostealer lookup collect or correlate personal identifiers and exposure data. | Privacy, lawful-basis, data-minimization, retention, and false-positive concerns. | Keep disabled pending case-scoped authorization, minimization, retention controls, audit actor, and disclosure policy. |
| Important | Domain/IP OSINT functions do not consistently validate inputs and call third-party APIs directly. | Invalid targets, privacy leakage, unbounded outbound requests, and inconsistent provenance. | Validate domain/IP syntax, use approved providers only, route HTTP through controlled acquisition, and persist provider response evidence. |
| Important | GitHub harvester has useful bounded depth/repository counts, but no explicit API response-size cap, retry/backoff policy, or dedicated tests. | Rate-limit failures and reliability issues during recursive traversal. | Port as a read-only public-repository cataloger with strict request budgets, bounded response sizes, and provenance. |
| Important | Neo4j errors are silently swallowed while SQLite is treated as successful. | SQLite/Neo4j divergence can be hidden; reported backend state can overstate consistency. | Keep SQLite authoritative; make graph mirroring observable and retryable, or remove Neo4j until consistency semantics are designed. |
| Important | Graph traversal and list limits are not consistently clamped; Mermaid export includes source-controlled labels/keys. | Resource exhaustion and diagram injection/format corruption. | Clamp every limit, escape Mermaid text and edge labels, and add adversarial tests. |
| Important | Sanitizer flags selected prompt-injection patterns but redacts only matching substrings. | It is a detector, not a reliable prompt-injection defense or safe HTML sanitizer. | Preserve raw evidence separately; label content untrusted; emit detection signals, never claim sanitization makes instructions safe. |
| Important | Dependencies use broad/unpinned ranges and container images use `latest`. | Reproducibility and supply-chain risk. | Pin tested versions/digests, add license/SBOM review, image scanning, and CI. |
| Nice to have | Hooks are Claude-specific and hardcode service ports/tool names. | Not portable across MCP clients or deployment environments. | Keep agent hooks optional and configuration-driven; core security controls must live in the server, not hooks. |

## Capability disposition

### Integrated in this branch

- Evidence-linked passive IOC extraction and lookup.
- Indicator records are content-independent, deterministic identifiers linked to existing evidence IDs.
- Supported indicator types: IPv4, IPv6, domain, CVE, and SHA-256.
- Email addresses, credentials, and wallet identifiers are intentionally excluded from extraction to reduce personal-data and account-identifier collection.
- MCP tools:
  - `research_extract_indicators(evidence_id)`
  - `research_find_indicator(value, kind?)`
  - `research_inspect_github_repository(repo_or_url)` — bounded public metadata/tree inventory; stores both API responses as evidence and never executes repository code.

### Approved for subsequent implementation

1. Passive domain intelligence: DNS, RDAP, certificate-transparency metadata, and historical URL references. Validate input domains; use the existing acquisition path for HTTP; persist provider responses as source/evidence records; do not probe discovered hosts.
2. Passive IP threat-intelligence enrichment: strict IP parsing, approved public intelligence APIs, explicit third-party disclosure, bounded responses, and evidence provenance. No port scanning or exploit validation.
3. IOC correlation and graph queries over the existing SQLite evidence store. Keep the claim ledger authoritative and distinguish observations from conclusions.
4. Prompt-injection indicators as metadata attached to evidence. Preserve original evidence and never treat regex redaction as a security boundary.
5. Optional SearXNG connector after endpoint allowlisting, response bounds, robots/terms review, and safe-query presets. Do not add leak/config-secret harvesting presets.

### Not approved for integration

- CAPTCHA solving through CapSolver, 2Captcha, CapMonster, OCR solvers, or Byparr.
- Cloudflare, WAF, bot-detection, fingerprint, or rate-limit bypass.
- Stealth scraping or residential-proxy evasion.
- Automated collection of personal usernames, email breach records, or infostealer credentials without a separate approved privacy/legal workflow.
- Broad darknet crawling/search or Tor circuit rotation in the main application container.
- SpiderFoot, Crawl4AI, Neo4j, and additional heavyweight services in the default Compose profile. These require separate resource, license, threat, and operational assessments.

## Implementation record

### Evidence-linked IOC index

Files:
- `src/intiligence_mcp/storage/indicators.py`
- `src/intiligence_mcp/server.py`
- `tests/unit/test_indicators.py`

Design:
- SQLite is the authoritative indicator index.
- Every indicator must reference an existing evidence record; unknown evidence IDs are rejected.
- Duplicate indicators are deduplicated while retaining links to multiple evidence records.
- Indicator IDs are deterministic SHA-256 identifiers over normalized type/value.
- IPv4/IPv6 candidates are validated with Python's `ipaddress` module.
- No automatic outbound lookup occurs during extraction.

## Verification status

- All archived Python files passed AST parsing; this is syntax validation only, not runtime validation.
- Existing project test suite plus new IOC and GitHub inventory tests: 88 passed (one optional PySocks warning).
- Final Ruff check passed (with the Windows bind-mount `EXE002` artifact excluded); mypy passed on 23 source files.
- Live GitHub API smoke test through the local Squid egress proxy and MCP stdio succeeded for the project's public repository; metadata and tree responses were stored with source/evidence IDs.
- No archive service, Tor/I2P route, Neo4j, Byparr, or third-party OSINT provider was started as part of this review.
- No archive code was executed as a service.

## Acceptance gates for future features

- [ ] Feature uses existing `fetch_response` / approved acquisition adapters; no direct ungoverned HTTP clients.
- [ ] URL, domain, IP, redirect, DNS, robots, and egress policy are enforced server-side.
- [ ] Inputs, output bytes, response count, concurrency, retries, and timeouts are bounded.
- [ ] Every externally sourced result has source ID, provider, captured timestamp, content hash, and evidence ID.
- [ ] PII and secrets are minimized, redacted from logs, and subject to retention controls.
- [ ] Tests cover invalid inputs, private/metadata targets, redirects, provider failures, limits, and provenance.
- [ ] License, dependency, image digest, and operational impact are reviewed.
- [ ] Optional services are disabled by default and isolated from the core application.
