# Runtime Implementation Status

## Implemented in this branch

- Python 3.12–3.14 package foundation and editable installation (`pip install -e . --no-deps` verified on Python 3.13).
- MCP server entry point: `intiligence_mcp.server`.
- MCP tools: `research_fetch`, `research_check_robots`, `research_register_source`, `research_get_evidence`, `research_get_capture`, `research_create_evidence_capsule`, `research_get_evidence_capsule`, `research_extract_indicators`, `research_find_indicator`, `research_inspect_github_repository`, `research_inspect_domain`, `research_create_claim`, `research_link_claim_evidence`, `research_review_claim`, and `research_get_claim_review_history`.
- Bounded HTTP acquisition: manual redirect handling, per-hop URL checks, response byte cap, request timeout, environment proxy inheritance disabled, and aiohttp DNS resolver pinning (validated numeric addresses are the addresses handed to the connector).
- URL policy: HTTP(S)-only, embedded-credential rejection, domain allow/deny lists (including denied subdomains), and DNS/IP checks.
- Per-host request pacing: process-local by default, with optional Redis-backed cross-process pacing using an atomic Lua reservation script and Redis server time. Redis failures fail closed when the shared backend is configured.
- SQLite source registry with canonical URL deduplication, stable SHA-256 source IDs, host index, first-seen timestamp, and WAL mode.
- Evidence store with source foreign keys, content SHA-256, deterministic evidence IDs, and content-addressed raw blobs. Every fetch can create a distinct artifact/capture record even when the underlying raw blob and extracted evidence are deduplicated.
- Extractor-versioned representations retain the artifact/evidence link. Immutable excerpt capsules store exact character offsets, a structured locator, and an excerpt SHA-256; reads verify raw, extracted and capsule hashes.
- Evidence-linked passive IOC index for IPv4, IPv6, domains, CVEs, and SHA-256; deterministic indicator IDs, deduplication across evidence records, and lookup by indicator.
- Passive domain intelligence tool backed by DNS-over-HTTPS, IANA RDAP DNS bootstrap (RFC 9224 longest-match selection), and bounded crt.sh Certificate Transparency results. RDAP contact/vCard/entity data is removed before evidence persistence; DNS TXT and EDNS Client Subnet are not queried. CT provider errors remain visible; a live `python.org` check succeeded for DNS and RDAP while crt.sh returned HTTP 502.
- Claim ledger supports supports/contradicts/qualifies evidence relations, reviewer/rationale attribution, append-only review and evidence-link event history, and evidence gates for supported/contradicted states.
- HTTP acquisition returns redirect provenance and allowlisted response metadata. A caller-supplied policy callback is checked for every redirect destination; research_fetch applies robots policy on each hop.
- MCP tools expose bounded evidence pagination, immutable capsule retrieval, capture metadata, and tool annotations. Retrieved page content is explicitly labelled untrusted.
- GitHub Actions CI and Dependabot configuration added; CI uses read-only token permissions and SHA-pinned actions.
- Public GitHub repository inventory using the existing bounded acquisition path; metadata and recursive tree responses are preserved as evidence, with MCP manifest/skills/hooks/build-file classification. No repository code is downloaded or executed.
- Trafilatura 2.3.1 source vendored at pinned commit `65eac050b7a2961bac9aefdfb7514121dd7382ba` under `src/intiligence_mcp/_vendor/trafilatura`, with Apache-2.0 license and provenance retained.
- Extraction adapter calling the vendored source.
- CAPTCHA/access-challenge detection and explicit human-review escalation. No automatic challenge bypass is implemented.
- `.gitignore` excludes Python bytecode, local env/secrets, caches, build artifacts, and local SQLite data.
- Unit tests cover URL policy, challenge detection/escalation, extraction, source registry persistence/deduplication, and evidence integrity/deduplication.

## Current worktree verification (2026-11-23)

- Runtime tested locally: Python 3.13. The full `pytest -q` suite passed: **120 passed, 1 optional urllib3/PySocks warning**.
- Ruff formatting and lint passed; mypy passed across 24 source files; `pip check` reported no broken requirements; `git diff --check` passed.
- A temporary isolated environment built and installed the application package successfully. `pip-audit 2.10.1 --strict` reported no known vulnerabilities in the resolved third-party runtime dependency snapshot.
- MCP STDIO integration smoke test initialized the server and enumerated all 15 registered tools. The test used a temporary SQLite database and left no smoke-test scripts behind.
- Live passive OSINT smoke test for `python.org`: six DNS query types and the IANA-selected `.org` RDAP endpoint succeeded. `crt.sh` returned HTTP 502; the adapter surfaced `provider_http_502` without fabricating CT results. Overall: 7/8 provider operations succeeded in this single run.
- Python 3.12 is installed locally but its project/test dependencies are not installed; Python 3.14 is not installed. Neither version has been locally verified in this worktree. Both remain in the GitHub Actions matrix.
- No commit, push, release or deployment was performed. Project-local SQLite data was not used by smoke tests.

## Earlier recorded Docker/integration verification

- Python: 3.13
- Python 3.13 in Docker: `pytest tests/unit -q`: 88 passed (one optional PySocks dependency warning).
- Ruff: passed with `EXE002` ignored for Windows bind-mount executable-mode artifacts.
- mypy: passed (23 source files).
- Docker images built; Compose configuration and Squid configuration parsing passed.
- Local Docker integration verified Squid public HTTP/HTTPS, private/metadata/loopback/IPv6/IPv4-mapped destination denials, direct-egress denial from the app network, Redis-backed pacing, shared robots-cache reuse, and MCP stdio initialization/tool invocation. The GitHub repository inventory was exercised through the live egress proxy and MCP stdio; both GitHub API responses were stored with source/evidence IDs.
- DNS resolver unit tests reject mixed public/private DNS answers and metadata addresses; an HTTP connector integration test confirms aiohttp connects to the numeric address returned by the configured resolver.
- Editable package wheel built and installed successfully; `pip check` reports no broken requirements.
- Crawl4AI shallow checkout inspected at commit `67a717723f6413eeb5a5b14569aef8308f888adc`; upstream declares Apache-2.0 and has 86 Python/source files in its package tree.

## Known limitations — not production-ready yet

1. The application HTTP and robots.txt paths use `PinnedPublicResolver` and per-hop URL validation. The local Docker profile routes through Squid and has been tested against public destinations and representative private, metadata, loopback, IPv6, mapped-IPv6, and Docker gateway destinations. Mixed DNS answers, DNS rebinding, redirects to private destinations under live staging conditions, host-gateway routes beyond the tested gateway, and production host/cloud egress firewall policy still require validation.
2. Browser automation is not enabled. Playwright must run in an isolated worker/container with enforced network egress policy; application-level URL validation alone cannot constrain browser subresource requests.
3. Redis-backed shared host pacing and shared robots-policy caching are implemented and enabled in the Compose profile. Both were exercised against local Redis 7.4.12, including shared cache reuse. Production Redis TLS/authentication, failover, persistence, lock contention under load, and backup/restore still require staging validation.
4. Source-domain authorization workflow, PostgreSQL migrations, tenant authentication/authorization, authenticated reviewer principals, and durable job orchestration remain to be implemented. Local reviewer ID configuration is attribution only, not authentication.
5. CAPTCHA detection and human-review escalation are implemented. Automatic CAPTCHA solving or technical access-control bypass is out of scope under the repository's responsible-acquisition policy.
6. Crawl4AI has been cloned and metadata-inspected but is not vendored. Its overlapping browser/crawling stack, large dependency surface, and stealth/anti-bot related functionality require file-level review before selecting safe modules.
7. Docling, Playwright source, search engines, CTI platforms, and workflow engines remain separate candidates; no claim is made that their code has been copied or approved.

## Next implementation sequence

1. Complete staging egress validation: mixed DNS answers, DNS rebinding, redirect-to-private behavior, host-gateway variants, and matching host/cloud firewall rules.
2. Stress-test Redis pacing and shared robots caching under contention, TTL expiry, Redis restart/failover, and persistence recovery.
3. Extend passive domain intelligence with an approved historical-web adapter and passive IP intelligence after provider terms, privacy and rate limits are reviewed.
4. Add passive IP threat-intelligence enrichment with strict public-IP validation, provider disclosure, and bounded evidence capture.
5. Add an isolated Playwright browser worker with DNS/egress, download, subresource, and filesystem controls.
6. Add PostgreSQL migrations, authenticated reviewer principals, tenant isolation, durable research jobs and a tested backup/restore path.
7. Add Docling as a separately isolated document/OCR pipeline; benchmark against the existing parser.
8. Complete file-level Crawl4AI review and selectively vendor only independently useful, safe, license-compatible modules.
9. Review remaining upstream candidates against actual product requirements; do not bulk-copy whole repositories with incompatible licenses or irrelevant services.


## Follow-up policy slice (2026-11-22)

- Added `policy/robots.py`: conservative robots.txt enforcement, 15-minute in-memory cache, per-origin async lock, redirects not followed, and fail-closed behavior for transport errors and non-200/non-404/non-410 responses.
- `research_fetch` now validates the target URL, checks robots.txt, and returns `blocked_by_robots_txt` when disallowed.
- Added MCP tool `research_check_robots` for explicit policy inspection.
- Added unit coverage for allow/disallow rules and cache behavior.
- Latest validation after this slice: 19 tests passed; Ruff clean; `git diff --check` clean.

### Policy caveats

- Robots rules are crawler coordination policy, not authorization or access control. Domain allow/deny policy and operator authorization still apply independently.
- The robots cache is process-local and resets on restart. A multi-worker deployment needs a shared cache.
- At the time of this initial robots-policy slice, DNS rebinding was not yet closed. The later DNS-pinned acquisition slice below supersedes that limitation; production network egress controls are now specified in the isolated egress deployment slice, but live deployment validation remains outstanding.


## Claim ledger slice (2026-11-22)

- Added SQLite `claims` and `claim_evidence` tables with foreign-key enforcement.
- Claim statements are normalized and assigned deterministic SHA-256 IDs.
- Evidence references must point to existing evidence records; duplicate links are idempotent.
- Review states are constrained to `unreviewed`, `supported`, `contradicted`, `inconclusive`, and `rejected`.
- Added MCP tools `research_create_claim` and `research_review_claim`.
- Latest local validation: 22 tests passed; Ruff clean; `git diff --check` clean.

The ledger is an initial structured claim register, not automated fact verification. Status transitions currently accept the allowed target states without enforcing a reviewer identity or approval workflow; production authorization/audit attribution remains required.

## DNS-pinned acquisition slice (2026-11-22)

- Replaced the acquisition transport with aiohttp and added `PinnedPublicResolver`, which validates every resolved address and returns the checked numeric addresses directly to the TCP connector. The original hostname remains the URL authority for HTTP Host and TLS certificate/SNI validation.
- The resolver rejects the entire DNS answer set if any answer is private, loopback, link-local, multicast, reserved, or otherwise non-global. Private-network access is possible only through the explicit `INTILIGENCE_ALLOW_PRIVATE_NETWORKS=true` opt-in.
- Redirects remain manual and each hop is independently URL-validated. Response byte caps, total timeout, per-host pacing, decompression, and `trust_env=False` remain enforced.
- Robots.txt now uses the same pinned transport and fails closed on redirects, transport errors, and unexpected statuses.
- Added resolver tests for public answers, mixed public/private rebinding answers, metadata IP rejection, explicit private opt-in, and a local HTTP integration test proving the connector uses the resolver-returned IP.
- Local verification on Python 3.13: 28 tests passed; Ruff and mypy passed; `pip check` and `git diff --check` passed.
- Defense in depth still requires network egress controls for browser workers and any network clients added outside this transport.

## Isolated egress deployment slice (2026-11-22)

- Added a non-root application Dockerfile and a Compose topology with an internal-only app network (`172.30.0.0/24`) and a separate Squid proxy attached to both the internal and egress networks.
- The MCP container has no direct external route, runs read-only with dropped capabilities, no-new-privileges, bounded PIDs/CPU/memory, and a persistent data volume.
- The proxy is not published on a host port, allows only the application subnet and web ports, and denies special-use IPv4/IPv6 destination ranges including loopback, RFC1918, link-local, CGNAT, metadata/link-local ranges, documentation, multicast, and reserved ranges.
- Added `INTILIGENCE_EGRESS_PROXY_URL` and `INTILIGENCE_REQUIRE_EGRESS_PROXY`. Required-proxy mode fails closed when no proxy URL is configured. HTTP and robots requests pass the configured proxy explicitly; environment proxy variables remain ignored.
- Added tests for required-proxy fail-closed behavior, proxy-origin URL validation (scheme, credentials, path, port normalization), and an HTTP proxy integration test proving requests use the configured proxy endpoint.
- Added static CIDR-policy tests covering 20 representative special-use IPv4/IPv6 destinations and three representative public addresses; the tests parse the Squid ACL source directly.
- Local verification for the egress-only slice: 56 tests passed; Ruff, mypy, pip check, and git diff checks passed.
- Docker CLI and Compose are installed. `docker compose -f compose.yaml config --quiet` passed, but the Docker Desktop Linux engine was unavailable. Therefore image builds, Squid startup, and live ACL/egress tests could not be verified. No container or VPS deployment was performed.
- Deployment instructions and explicit remaining gates are documented in `deploy/EGRESS_SECURITY.md`.

## Redis shared host-pacing slice (2026-11-22)

- Added an optional `distributed` dependency extra containing redis-py; the container image installs this extra.
- Added `RedisHostRateLimiter` using a single atomic Lua reservation script. The script uses Redis `TIME` (not client clocks), stores each normalized host under a SHA-256 key, reserves serialized request slots, and sets a TTL long enough to cover queued reservations.
- Added `INTILIGENCE_REDIS_URL` and `INTILIGENCE_REQUIRE_SHARED_RATE_LIMIT`. Required mode fails during server initialization if the URL is missing; configured Redis failures fail acquisition closed and never silently fall back to process-local pacing.
- Added a Redis service on a dedicated internal-only network in Compose. Only the MCP service joins that network; Redis has no published port and is not connected to the egress proxy network.
- Added unit tests for Lua invocation arguments, normalized/hashed host keys, wait scheduling, Redis URL validation, required-backend startup, and fail-closed behavior on Redis outage.
- Python 3.13 verification after this slice: 66 tests passed; Ruff, mypy, pip check, Compose static validation, and `git diff --check` passed.
- No live Redis server or Docker engine was available; Redis protocol/runtime behavior and container networking still require staging verification.
- Added a shared Redis robots cache keyed by normalized origin, with a bounded distributed lock to avoid duplicate concurrent robots.txt fetches across workers.
- Cache entries preserve the robots status/body and use the configured TTL. 404/410 are shared as allow-all; other unexpected statuses and Redis failures fail closed.
- Added `INTILIGENCE_REQUIRE_SHARED_ROBOTS_CACHE`; required mode fails during server initialization if Redis is not configured. Redis cache errors do not fall back to process-local policy.
- Added tests for cross-call cache reuse, 404/410 semantics, required configuration, and fail-closed Redis outage behavior.
- Python 3.13 verification after shared robots support: 71 tests passed; Ruff, mypy, pip check, Compose static validation, and `git diff --check` passed.
- No live Redis server or Docker engine was available; Redis protocol/runtime behavior and distributed lock behavior still require staging verification.


## Unified research, specialist sources and optional Tor acquisition (2026-11-23)

### Implemented in the current worktree

- Added a compact research MCP facade. One intent drives bounded SearXNG discovery, optional specialist-database lookup, freshness-aware source refresh/reuse, and a compact evidence packet. The facade caps source acquisition at five results and excerpts at 1,600 characters per source. Search results remain untrusted until successfully fetched and captured.
- Added public deep-web metadata adapters for Crossref Works and Europe PMC. These are specialist databases/API endpoints outside ordinary search-engine indexing; they return bibliographic metadata and public abstract fields only. They do not sign in to private portals, retrieve restricted full text, or bypass paywalls.
- Added exact-URL Internet Archive Wayback CDX lookup for historical HTML capture metadata. It is a historical discovery feature, not a current-truth signal; snapshot metadata is not itself verified evidence.
- Added an optional Tor v3 onion fetch adapter with explicit operator allowlisting, remote DNS resolution through SOCKS5, bounded text/JSON media types, 1 MB default response cap, no redirects, no cookies, no scripts, no forms, no downloads, and no automated CAPTCHA solving.
- Corrected onion freshness refresh so .onion URLs can only use the Tor adapter; they are never sent to the clearnet HTTP adapter. Due-source refresh excludes onion records while Tor is disabled.
- Added Conditional Revalidation for onion sources and corrected HTTP validator replacement: a full 200 response clears obsolete ETag/Last-Modified validators if the new response omits them; a 304 retains validators when omitted.
- Added tests for specialist metadata lookup, historical archive lookup, v3 allowlisting, Tor-disabled behavior, onion-only refresh routing, due-source filtering, freshness validator clearing, and the unified research facade.
- Added a private SearXNG Compose service reachable only on the internal Docker network. Its outbound search-provider traffic is configured to use the Squid egress proxy; JSON output is enabled for the MCP adapter and Safe Search is set to 1.
- Added an optional onion Compose profile containing a Tor client gateway, not a relay or exit node. The SOCKS port is not published to the host. The MCP process has no direct external route; it can reach the Tor SOCKS service only through the internal network.
- CAPTCHA and bot challenges are detected and recorded for operator review. No solver, stealth browser, cookie replay, login automation, or challenge bypass is implemented.

### Configuration

- Copy .env.example to .env and set SEARXNG_SECRET to a random secret. The .env file is ignored by Git; do not commit it.
- The default Compose profile leaves Tor collection disabled. To use the optional gateway, build/start it explicitly with docker compose --profile onion up -d tor-gateway, then enable INTILIGENCE_ENABLE_ONION_OSINT=true for the MCP process and supply an exact, operator-approved comma-separated INTILIGENCE_ONION_SOURCE_ALLOWLIST of v3 onion hostnames.
- Install the Python optional dependency group .[tor] in local non-container environments before using onion collection.
- SearXNG, Crossref and Europe PMC receive the user query as required for search. Self-hosting SearXNG keeps the query interface under operator control but does not prevent enabled external search engines from receiving the query.

### Validation and explicit limits

- Python 3.13 unit suite: 146 passed after the initial deep-web/archive/onion/freshness slice. Additional unified-facade tests were added after that run and must be included in the final verification snapshot.
- The SearXNG and Tor services have configuration files and Compose wiring, but were not started and no live Tor/onion collection was performed in this change. Compose schema/config validation and final static/test checks are still required.
- The exact Tor v3 .onion host must be supplied by the operator; this project does not enumerate the dark web, scrape marketplaces, search stolen-data dumps, or access hidden services without a specific allowlisted target.
- A CAPTCHA event stops automated acquisition and is placed in a human-review queue. The application cannot guarantee access to a source that requires a challenge or manual authorization.
- The existing isolated Docker egress profile still needs staging validation against the exact local Docker/Squid versions for DNS rebinding, mixed DNS answers, redirects, and host-gateway paths. No network boundary should be described as an absolute guarantee.
- Browser rendering/Playwright and OCR/Docling remain disabled/deferred pending a separately isolated worker and review of browser subresource egress, downloads, file-system access, memory use, and parser attack surface.
- The MCP Python SDK remains pinned to v1 for compatibility. A v2 SDK migration is separate work and must not be performed by widening the dependency range without tests.
