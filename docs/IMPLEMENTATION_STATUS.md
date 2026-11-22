# Runtime Implementation Status

## Implemented in this branch

- Python 3.12–3.14 package foundation and editable installation (`pip install -e . --no-deps` verified on Python 3.13).
- MCP server entry point: `intiligence_mcp.server`.
- MCP tools: `research_fetch`, `research_check_robots`, `research_register_source`, `research_get_evidence`, `research_create_claim`, and `research_review_claim`.
- Bounded HTTP acquisition: manual redirect handling, per-hop URL checks, response byte cap, request timeout, environment proxy inheritance disabled, and aiohttp DNS resolver pinning (validated numeric addresses are the addresses handed to the connector).
- URL policy: HTTP(S)-only, embedded-credential rejection, domain allow/deny lists (including denied subdomains), and DNS/IP checks.
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
- `py -3.13 -m pytest -q`: 56 passed
- `py -3.13 -m ruff check src/intiligence_mcp tests`: passed
- `py -3.13 -m mypy src/intiligence_mcp`: passed
- `docker compose -f compose.yaml config --quiet`: passed (static configuration validation only; Docker daemon unavailable)
- DNS resolver unit tests reject mixed public/private DNS answers and metadata addresses; an HTTP connector integration test confirms aiohttp connects to the numeric address returned by the configured resolver.
- Editable package wheel built and installed successfully; `pip check` reports no broken requirements.
- Crawl4AI shallow checkout inspected at commit `67a717723f6413eeb5a5b14569aef8308f888adc`; upstream declares Apache-2.0 and has 86 Python/source files in its package tree.

## Known limitations — not production-ready yet

1. The application HTTP and robots.txt paths use `PinnedPublicResolver`: aiohttp connects to the exact numeric addresses returned by the resolver after public-IP validation, retaining the original hostname for Host/TLS verification. The resolver rejects the entire answer set if any address is non-public (unless `INTILIGENCE_ALLOW_PRIVATE_NETWORKS=true` is explicitly configured). A Docker reference profile now adds an isolated app network, required Squid proxy routing, and destination CIDR deny rules. The Docker daemon was unavailable during implementation, so image builds, runtime behavior, and live Squid ACL enforcement have not been verified. Production still requires host/cloud egress firewall policy and staging validation.
2. Browser automation is not enabled. Playwright must run in an isolated worker/container with enforced network egress policy; application-level URL validation alone cannot constrain browser subresource requests.
3. Per-host pacing is process-local. Multi-worker deployments require a shared/distributed limiter.
4. Source-domain authorization workflow, immutable evidence capsules, PostgreSQL migrations, tenant authentication, reviewer attribution, and durable job orchestration remain to be implemented.
5. CAPTCHA solver provider integrations are not active. Any future solver must be gated to explicitly authorized domains and operator-approved test workflows.
6. Crawl4AI has been cloned and metadata-inspected but is not vendored. Its overlapping browser/crawling stack, large dependency surface, and stealth/anti-bot related functionality require file-level review before selecting safe modules.
7. Docling, Playwright source, search engines, CTI platforms, and workflow engines remain separate candidates; no claim is made that their code has been copied or approved.

## Next implementation sequence

1. Validate the Docker egress profile with a running Docker daemon and live Squid ACL tests, then enforce matching host/cloud egress firewall rules in staging; application-level HTTP/robots DNS pinning is implemented.
2. Add shared/distributed per-domain pacing and robots cache for multi-worker deployments.
3. Add an isolated Playwright browser worker with DNS/egress, download, subresource, and filesystem controls.
4. Add immutable evidence capsules, reviewer attribution, PostgreSQL migrations, tenant authentication, and durable job orchestration.
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
- Local verification: 56 tests passed; Ruff, mypy, pip check, and git diff checks passed.
- Docker CLI and Compose are installed. `docker compose -f compose.yaml config --quiet` passed, but the Docker Desktop Linux engine was unavailable. Therefore image builds, Squid startup, and live ACL/egress tests could not be verified. No container or VPS deployment was performed.
- Deployment instructions and explicit remaining gates are documented in `deploy/EGRESS_SECURITY.md`.
