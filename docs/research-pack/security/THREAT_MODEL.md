# Threat Model

## Assets
Provider credentials; user queries and private files; raw artifacts and evidence; claims/reports/curated knowledge; worker runtime and temporary files; CTI markings; audit logs and backups.

## Adversaries
Malicious pages/documents/archives; prompt injection; compromised MCP clients; malicious tenants; compromised workers; dependency supply-chain attackers; poisoned CTI feeds; operator misconfiguration.

## Attack paths
1. User URL -> redirect or DNS rebinding -> internal service (SSRF).
2. Retrieved content -> prompt injection -> model/tool misuse.
3. Malformed PDF/archive -> parser exploit or resource exhaustion.
4. MCP request -> missing auth/scope -> cross-tenant access.
5. Job payload -> host subprocess -> host filesystem/network.
6. Provider error/log -> credential disclosure.
7. CTI feed -> false indicator/attribution -> harmful decision.
8. Upstream update -> supply-chain compromise.

## Controls
Deny by default; authenticate every MCP call; authorize every operation; derive tenant from verified principal; treat external content as untrusted; isolate browser/parser/analyzers; keep secrets out of model context; preserve uncertainty and handling restrictions; fail closed if policy/sandbox unavailable.

Every accepted residual risk needs severity, owner, mitigation, expiry and release impact. P0 residual risk blocks production exposure.
