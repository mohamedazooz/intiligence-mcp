# Deployment and Operations Blueprint

Status: target topology; exact VPS sizing requires measurement.

Initial topology: existing OmniMCP API/control plane; Intiligence research/MCP module; PostgreSQL; object storage; bounded acquisition/parser workers; optional separate search provider; TLS reverse proxy and network policy; structured logs/metrics.

Do not add Redis, Qdrant, OpenSearch, Temporal or a separate broker until measured requirements justify them.

Environment separation: development, staging and production use separate credentials, databases, buckets and provider quotas. Secrets never enter source, prompts or logs.

Worker rules: separate worker identity; no Docker socket exposed to app code; per-job scratch and cleanup; deny-by-default egress; CPU/RAM/file/page/concurrency/time limits; fail closed if sandbox/policy unavailable. Containerization alone is not proof of isolation.

Database: versioned migrations; no implicit create-all in production; encrypted backups; tested restore; connection/query limits; tenant-scoped indexes; retention-aware deletion.

Release: clean build; lint/type/unit/integration/security/contract tests; SBOM and license report; image/dependency scan; staging smoke; telemetry/backup verification; operator approval; canary and rollback.

Runbooks required: provider outage, quota exhaustion, credential leak, SSRF alert, worker compromise, cross-tenant exposure, evidence corruption, object-store loss, migration failure, CTI poisoning.
