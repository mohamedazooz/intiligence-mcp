# Runtime Implementation Status

## Implemented in this branch

- Python 3.12–3.14 package foundation and editable installation (`pip install -e . --no-deps` verified on Python 3.13).
- MCP server entry point: `intiligence_mcp.server`.
- MCP tools: `research_fetch`, `research_register_source`, and `research_get_evidence`.
- Bounded HTTP acquisition: manual redirect handling, per-hop URL checks, response byte cap, request timeout, and environment proxy inheritance disabled.
- URL policy: HTTP(S)-only, embedded-credential rejection, domain allow/deny lists, and DNS/IP checks.
- Process-local per-host request pacing, configurable with `INTILIGENCE_MIN_HOST_INTERVAL_SECONDS`.
- SQLite source registry with canonical URL deduplication, stable SHA-256 source IDs, host index, first-seen timestamp, and WAL mode.
- Append-only-through-API evidence store with source foreign keys, content SHA-256, deterministic evidence IDs, capture timestamps, and deduplication.
- Trafilatura 2.3.1 source vendored at pinned commit `65eac050b7a2961bac9aefdfb7514121dd7382ba` under `src/intiligence_mcp/_vendor/trafilatura`, with Apache-2.0 license and provenance retained.
- Extraction adapter calling the vendored source.
- CAPTCHA/access-challenge detection and explicit human-review escalation. No automatic challenge bypass is implemented.
- `.gitignore` excludes Python bytecode, local env/secrets, caches, build artifacts, and local SQLite data.
- Unit tests cover URL policy, challenge detection/escalation, extraction, source registry persistence/deduplication, and evidence integrity/deduplication.

## Latest local verification

- Python: 3.13
- `pytest -q`: 17 passed
- `ruff check src/intiligence_mcp tests`: passed
- Editable package wheel built and installed successfully; `pip check` reports no broken requirements.
- Crawl4AI shallow checkout inspected at commit `67a717723f6413eeb5a5b14569aef8308f888adc`; upstream declares Apache-2.0 and has 86 Python/source files in its package tree.

## Known limitations — not production-ready yet

1. DNS is validated before each HTTP request, but the HTTP transport performs its own DNS resolution. A hostile DNS rebinding race is not fully eliminated. Production deployment must use a pinned-IP transport or an egress proxy/firewall that blocks private, loopback, link-local, and metadata networks.
2. Browser automation is not enabled. Playwright must run in an isolated worker/container with enforced network egress policy; application-level URL validation alone cannot constrain browser subresource requests.
3. Per-host pacing is process-local. Multi-worker deployments require a shared/distributed limiter.
4. Robots.txt policy, source-domain authorization workflow, immutable evidence capsules, claim ledger, PostgreSQL migrations, tenant authentication, and durable job orchestration remain to be implemented.
5. CAPTCHA solver provider integrations are not active. Any future solver must be gated to explicitly authorized domains and operator-approved test workflows.
6. Crawl4AI has been cloned and metadata-inspected but is not vendored. Its overlapping browser/crawling stack, large dependency surface, and stealth/anti-bot related functionality require file-level review before selecting safe modules.
7. Docling, Playwright source, search engines, CTI platforms, and workflow engines remain separate candidates; no claim is made that their code has been copied or approved.

## Next implementation sequence

1. Implement DNS pinning or enforceable network egress proxy/firewall and close the rebinding gap.
2. Add robots policy and durable per-domain policy/rate controls.
3. Add isolated Playwright browser worker with download, subresource, and filesystem controls.
4. Add evidence capsules, content hashes, immutable provenance, claim ledger, and PostgreSQL persistence.
5. Add Docling as a separately isolated document/OCR pipeline; benchmark against the existing parser.
6. Complete file-level Crawl4AI review and selectively vendor only independently useful, safe, license-compatible modules.
7. Review remaining upstream candidates against actual product requirements; do not bulk-copy whole repositories with incompatible licenses or irrelevant services.


## Follow-up policy slice (2026-11-22)

- Added `policy/robots.py`: conservative robots.txt enforcement, 15-minute in-memory cache, per-origin async lock, redirects not followed, and fail-closed behavior for transport errors and non-200/non-404/non-410 responses.
- `research_fetch` now validates the target URL, checks robots.txt, and returns `blocked_by_robots_txt` when disallowed.
- Added MCP tool `research_check_robots` for explicit policy inspection.
- Added unit coverage for allow/disallow rules and cache behavior.
- Latest validation after this slice: 19 tests passed; Ruff clean; `git diff --check` clean.

### Policy caveats

- Robots rules are crawler coordination policy, not authorization or access control. Domain allow/deny policy and operator authorization still apply independently.
- The robots cache is process-local and resets on restart. A multi-worker deployment needs a shared cache.
- This slice does not close DNS rebinding. HTTP transport DNS pinning or network egress enforcement remains a production blocker.
