# Security Review Matrix

| ID | Threat | Required control | Verification | Priority |
|---|---|---|---|---|
| SEC-001 | Unauthenticated MCP access | Auth at transport boundary; per-tool scopes | Unauthorized, expired, revoked token tests | P0 |
| SEC-002 | Cross-tenant data exposure | Mandatory tenant scope on every query/artifact | Two-tenant negative tests | P0 |
| SEC-003 | Host command execution | No untrusted shell; enforced isolated runner | Escape and host-file tests | P0 |
| SEC-004 | SSRF | Scheme/host/DNS/IP/redirect validation and egress firewall | IPv4/IPv6/private/metadata/redirect tests | P0 |
| SEC-005 | Prompt injection | Retrieved text treated as untrusted data | Poisoned HTML/PDF corpus | P0 |
| SEC-006 | Parser exploit/resource exhaustion | Isolated parser, no network, strict size/time/memory caps | Malformed and decompression-bomb fixtures | P0 |
| SEC-007 | Secret leakage | Secret references, redaction, no secrets in prompts | Canary/log scan | P0 |
| SEC-008 | Unbounded crawling | Per-host budgets, page/depth caps, cancellation | Load/cancel tests | P1 |
| SEC-009 | Archive traversal | Safe extraction and temporary workspace | ZIP-slip fixtures | P1 |
| SEC-010 | Retention violation | Retention/deletion workflow and backup expiry | Deletion verification | P1 |
| SEC-011 | Dependency compromise | Lockfiles, SBOM, pinned versions, scans | CI supply-chain checks | P1 |
| SEC-012 | Unauthorized active recon | Explicit authorization and target allowlist | Reject out-of-scope target | P0 |
| SEC-013 | Browser session leakage | Ephemeral isolated contexts | Cross-job session test | P1 |
| SEC-014 | Stale/conflicting claims | Visible freshness/conflict states | Contradiction fixtures | P1 |
| SEC-015 | Unsafe analyzer | Isolated worker and egress allowlist | Analyzer escape/network tests | P1 |

Trust boundaries: MCP client/gateway; gateway/application; application/provider; external content/parser; worker/host; evidence/LLM context; CTI integration/external sharing.

Any open P0 blocks external production exposure. Resource limits alone are not a sandbox.
