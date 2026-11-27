# Best-Practice Research and Applied Decisions

**Reviewed:** 2026-11-23  
**Scope:** Current local worktree branch feat/passive-osint-intel-v2  
**Purpose:** Record the standards and upstream practices used for the current implementation. A cited standard or project is a design reference, not a claim of certification or full protocol conformance.

## Applied design decisions

### Evidence and provenance

The evidence pipeline now distinguishes:

1. **Source** — the canonical external URL or identifier.
2. **Artifact/capture** — one acquisition event, with its own ID and timestamp.
3. **Raw blob** — content-addressed bytes deduplicated by SHA-256.
4. **Representation** — extracted/normalized content tied to an artifact and a named/versioned extractor.
5. **Evidence capsule** — an immutable, hashed excerpt with offsets and a structured locator.
6. **Claim** — a proposition with typed evidence relationships (supports, contradicts, qualifies).
7. **Review event** — an attributed transition with reviewer and rationale.

This is aligned conceptually with W3C PROV's Entity/Activity/Agent model: capture and extraction are activities, source/artifact/representation are entities, and reviewer identity is an agent. The current SQLite model is a practical first step, not a full PROV-O implementation.

An artifact capture is separate from evidence-text deduplication. Repeated retrieval of identical bytes therefore creates distinct capture records while retaining one content-addressed blob. The capture stores the decompressed HTTP entity bytes returned by aiohttp, not a packet-level or compressed wire image.

### Claims and review integrity

- Claims may exist as unreviewed hypotheses without evidence.
- A supported status requires at least one supports relationship.
- A contradicted status requires at least one contradicts relationship.
- Every review event requires a reviewer identifier and a rationale.
- Review history and evidence-link events reject UPDATE operations at the database layer.
- A local INTILIGENCE_REVIEWER_ID is attribution only. It is not authentication, multi-user identity proof, or an authorization boundary. A remote multi-tenant service still needs authenticated principals and server-enforced permissions.

### Safe acquisition

- Redirects are handled manually, with URL/DNS validation on each hop.
- A source policy callback runs on the initial URL and every redirect destination. The research_fetch path uses it to evaluate robots.txt for each origin.
- Output is bounded and paginated rather than returning an arbitrarily large evidence record in one MCP response.
- Retrieved content is labelled as untrusted source data. This is a context signal for the client, not a substitute for prompt-injection isolation.
- Tool annotations describe intended read/write and open-world behavior. MCP annotations are client hints, not access-control enforcement.

### Passive domain intelligence

The new research_inspect_domain tool collects only passive observations:

- DNS A, AAAA, CNAME, MX, NS and CAA through Google's HTTPS JSON DoH API. TXT is omitted to avoid collecting arbitrary TXT payloads such as email/security policy strings. EDNS Client Subnet is not sent.
- RDAP authority discovery through the IANA DNS bootstrap registry. Selection uses RFC 9224 label-wise longest suffix matching; the implementation prefers HTTPS bootstrap endpoints.
- RDAP data is privacy-minimized before persistence. Entity/vCard, email, phone, address, remarks, notices and public-ID fields are not retained.
- Certificate Transparency search is bounded and results are restricted to names equal to or beneath the queried domain. CT presence is a discovery lead, not proof of ownership or current control.

No active port scanning, brute force, authentication attempts, or access-control bypass is performed by this tool.

## Upstream standards and projects consulted

| Reference | What it informs | Applied boundary |
|---|---|---|
| [MCP Python SDK — Tools](https://github.com/modelcontextprotocol/python-sdk) | Tool registration, schemas and tool annotations | Annotate tools, but enforce policy in application code |
| [MCP Python SDK — Lifespan](https://github.com/modelcontextprotocol/python-sdk) | Lifecycle management for shared resources | Use lifespan-managed clients/pools when persistent HTTP/DB resources are introduced |
| [MCP Security Best Practices (2026-07-28 revision)](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/2026-07-28/tutorials/security/security_best_practices.mdx) and [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html) | SSRF, DNS rebinding, redirect validation, least privilege, schema integrity, sandboxing and auditability | Validate every redirect, pin DNS, keep tools scoped, and do not treat annotations or tool descriptions as authorization |
| [MCP Authorization Security Considerations (2026-07-28)](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/security-considerations.mdx) | Token audience binding, issuer validation, secure token storage and HTTPS requirements | No remote Streamable HTTP is exposed; authenticate and authorize every request before adding it |
| [W3C PROV-O](https://www.w3.org/TR/prov-o/) | Provenance relationships between entities, activities and agents | Model capture, extraction and human review as distinct provenance events |
| [RFC 9224](https://www.rfc-editor.org/rfc/rfc9224.html) and [IANA RDAP DNS Bootstrap Registry](https://www.iana.org/assignments/rdap-dns) | Authoritative RDAP discovery and longest-match lookup | Discover the RDAP server by the queried domain's suffix; do not hardcode one registrar |
| [Google Public DNS JSON API](https://developers.google.com/speed/public-dns/docs/doh/json) | HTTPS DNS queries and JSON response fields | Use /resolve; interpret DNS Status separately from HTTP status |
| [RFC 9162](https://www.rfc-editor.org/rfc/rfc9162.html) | Certificate Transparency v2 and append-only Merkle logs | Treat CT results as logged certificate observations, not ownership proof |
| [OWASP Amass Open Asset Model — Assets](https://owasp-amass.github.io/docs/open_asset_model/assets/) | Typed asset identity, source provenance and confidence | Future graph records should carry first/last seen, source and confidence |
| [OWASP Amass Open Asset Model — Relations](https://owasp-amass.github.io/docs/open_asset_model/relations/) | Typed, directional, time-aware relationships | Future entity links should be explicit and evidence-backed rather than inferred from string coincidence |
| [Ruff](https://docs.astral.sh/ruff/) and [pytest](https://docs.pytest.org/en/stable/) | Fast linting/formatting and deterministic regression tests | Run on every CI matrix entry |
| [actions/checkout](https://github.com/actions/checkout) and [actions/setup-python](https://github.com/actions/setup-python) | Current GitHub Actions runtime and checkout hardening | Pin reviewed action commits; disable persisted checkout credentials; grant read-only token permissions |

## MCP SDK compatibility policy

As reviewed on 2026-11-23, the official Python SDK has a stable 2.x line (v2.0.0 was released on 2026-07-28; v2.3.0 is listed in the official release history). SDK v1 is in maintenance mode. This project deliberately keeps `mcp>=1.12,<2` because its current server implementation targets the v1 API. Do not widen that dependency range as a routine version bump.

A dedicated v2 migration must verify, in a separate change set:

- Server API and import migration (including the `FastMCP` to `MCPServer` transition).
- Wire compatibility with the 2026-07-28 protocol revision and supported legacy MCP clients.
- STDIO lifecycle, tool discovery, structured outputs, annotations and cancellation behavior.
- Any transport/authentication boundary before enabling remote Streamable HTTP.

The current v1 pin is a compatibility constraint, not a claim that v1 is the newest SDK. Track security fixes and plan an explicit v2 migration rather than silently crossing the major-version boundary.

## CI and supply-chain decisions

- GitHub Actions are pinned to full commit SHAs for the reviewed releases, rather than mutable major-version tags.
- GITHUB_TOKEN permissions are read-only (contents: read).
- Checkout credentials are not persisted (persist-credentials: false).
- CI tests Python 3.12, 3.13 and 3.14, matching requires-python.
- CI runs Ruff lint/format, mypy, unit tests and pip check.
- A separate `pip-audit --strict` job snapshots resolved third-party runtime dependencies with `pip freeze --exclude-editable` before installing the audit tool, then audits that snapshot. This avoids treating the local, non-PyPI application package as a third-party release while including transitive runtime dependencies.
- On 2026-11-23, `pip-audit 2.10.1 --strict` reported **no known vulnerabilities** in the resolved third-party runtime dependency snapshot. This is a point-in-time advisory check, not a guarantee that application code is vulnerability-free.
- Dependabot checks both Python packages and GitHub Actions weekly.

## Live smoke-test snapshot (2026-11-23)

A live, read-only inspection of `python.org` was run with a temporary SQLite database outside the project data directory:

- **DNS:** 6/6 query types returned valid provider responses (A, AAAA, CNAME, MX, NS and CAA). Empty CNAME/CAA answer sets are valid DNS results, not transport failures.
- **RDAP:** succeeded through the IANA-selected `.org` server, `https://rdap.publicinterestregistry.org/rdap/`.
- **Certificate Transparency:** `crt.sh` returned HTTP 502. The provider error was preserved as `provider_http_502`; no CT names were inferred or fabricated.
- **Overall:** 7/8 provider operations succeeded. This is one point-in-time smoke test, not a reliability or coverage guarantee.

A possible hosted CT alternative, ctlogs.dev, documents anonymous access at 100 requests per UTC day per address and free API keys for testing/non-commercial use; commercial API use requires a paid plan. It also documents a 90-day certificate window on its lower plans. It is therefore recorded as an optional provider candidate, not silently wired into this product without a licensing decision, credential/configuration policy and adapter tests. The current CT source remains isolated behind its provider adapter.

## Known limits after this implementation slice

- SQLite remains the current store. There are no PostgreSQL migrations, multi-tenant isolation, authenticated reviewer principals or durable research jobs.
- Raw response bytes are currently stored in the same SQLite database as research metadata. This is adequate for a bounded local prototype, not a long-term artifact store. Define retention, access control, encryption, size quotas and deletion propagation before production.
- Evidence capsules have a character-range locator by default. DOM selectors, PDF page/paragraph locations, table coordinates, and JSONPath need format-specific extractors before those locators can be claimed as implemented.
- Evidence and review tables reject UPDATE, but privileged operators with direct SQLite write access can still alter or delete the database. Tamper-evident external audit anchoring and immutable/WORM storage are not implemented.
- The INTILIGENCE_REVIEWER_ID environment variable identifies a configured local operator; it does not authenticate the caller. Do not expose these review tools over an unauthenticated shared server.
- crt.sh is an external search provider, not an RFC-defined API contract. Keep it behind the adapter and monitor provider response/rate-limit changes.
- The provider implementations are covered by mocked deterministic tests. One live `python.org` smoke test passed all six DNS query types and the IANA-selected RDAP path, while `crt.sh` returned HTTP 502. Additional domains, repeat-run behavior and VPS/staging egress validation are still required.
- The local Python 3.13 run emits an optional urllib3 SOCKS warning because PySocks is not installed. The current proxy configuration accepts HTTP(S) proxies only; do not add PySocks unless SOCKS proxy support is deliberately introduced and tested.
