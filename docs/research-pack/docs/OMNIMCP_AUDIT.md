# OmniMCP Source Audit

Repository: https://github.com/mohamedazooz/MULTI-AGENTS-OPS
Reviewed ref: `vibe/omnimcp-foundation-5d6ade`
Inputs: GitHub recursive tree + README + MCP server + security.py + jobs.py + storage.py + pyproject + Compose + implementation status + dependency matrix + uploaded ZIP.

## Verified structure
- FastAPI control plane in `backend/omnimcp`.
- Worker package in `worker/omnimcp_worker`.
- Tests in backend/tests and worker/tests.
- Existing docs include API, architecture, dependency matrix, implementation status, deployment, MCP integration, scheduler, storage, security, threat model, testing, operations and ADRs.
- CI workflow under .github/workflows.

## Existing capabilities documented/implemented
- Argon2 password hashing, JWT, RBAC admin/operator/user.
- Agent and worker registries; hashed API keys/tokens.
- Worker heartbeat/capability reporting and pull-based execution.
- Resource-aware job scheduler with retry, timeout, cancellation and idempotency.
- Workspace containment and archive hardening.
- Local storage plus GCS/HF adapters.
- MCP Streamable HTTP server with 12 typed tools.
- JSON logs, metrics and audit redaction.

## Findings
### P0 — MCP authentication
The implementation status explicitly says MCP bearer-token enforcement is pending. Implement auth at the MCP boundary, bind principal and tenant from verified credentials, enforce per-tool scopes and test expiry/revocation/unauthorized calls.

### P0 — Execution isolation
The executor uses host subprocesses and rlimits. Docker/OCI/gVisor is listed as not implemented. Block untrusted jobs until an enforced sandbox provider exists.

### P1 — Owner/tenant scope
Inspect MCP methods that pass `owner_id=None`; ensure job/workspace/artifact access is always scoped to the authenticated principal and tenant.

### P1 — Rate limiting
The inspected security primitive uses in-memory process-local state. It will not coordinate across replicas or survive restarts; use shared backend or edge enforcement.

### P1 — Migrations
Alembic is deferred and create_all is used. Add migrations before production schema evolution.

### P1 — Storage
HF adapter uses `b"".join(...)` and can buffer a large file. Stream or cap size. GCS/HF live credentials/integration tests were not available in the supplied snapshot.

### P1 — Compose
The supplied compose file mounts a named volume at `/app`; validate that it does not mask application files and separate DB data from code paths.

### P2 — Cross-platform
POSIX rlimits are not portable; Windows/macOS worker execution needs native CI.

## Test validation
The ZIP claims 51 backend + 10 worker tests and clean Ruff. Independent rerun in this environment: 1 passed, 50 collection errors because dependency `mcp` is missing. This is not a passing run.

## Decision
Retain OmniMCP as control plane; fix P0 blockers before external MCP exposure or untrusted execution.