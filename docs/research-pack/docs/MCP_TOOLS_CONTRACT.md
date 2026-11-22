# MCP Tool Surface — Proposed Contract

Proposed API only. Do not claim tools exist until implemented and contract-tested.

## Rules
- Small task-oriented tools with typed JSON schemas.
- Tenant/principal identity comes from verified middleware, never caller-supplied owner IDs.
- Return stable IDs, provenance, warnings and bounded content.
- Enforce pagination, result caps, deadlines, cancellation and scopes.
- Never expose arbitrary shell, unrestricted filesystem, unrestricted browser, raw credentials or unrestricted URL fetch.
- Retrieved content is explicitly marked untrusted.

## Candidate tools

| Tool | Purpose | Required scope |
|---|---|---|
| research.search_sources | Discover candidate sources | research:discover |
| research.acquire_source | Acquire permitted source | research:acquire |
| research.parse_artifact | Parse stored artifact | research:parse |
| research.get_evidence | Retrieve evidence capsules | evidence:read |
| research.create_claim_proposal | Create unverified claim | claims:propose |
| research.link_claim_evidence | Link supporting/conflicting evidence | claims:review |
| research.get_claim | Read claim and evidence graph | claims:read |
| research.compile_report | Compile cited report | reports:write |
| research.get_report | Read report and references | reports:read |
| research.provider_health | Provider health | providers:read |
| research.list_sources | List authorized sources | sources:read |

Error envelope: stable code, safe message, retryable flag, request ID and optional sanitized details. Never return stack traces, secrets, internal IPs or raw paths.

Every list/search tool has bounded page size and opaque cursor. Enforce query length, output size, acquisition bytes and wall-clock deadlines. Version schemas and maintain compatibility tests for supported MCP clients.
