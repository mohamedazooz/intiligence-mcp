# Operations and Deployment

**Status:** Proposed runbook baseline. Confirm actual commands and configuration against implementation before use.

## Initial deployment profile

The agent guide sets an initial target of approximately **2 vCPU and 6 GB RAM**. Start with a single modular application and PostgreSQL. Do not deploy multiple heavyweight databases, browser fleets, and orchestration systems simultaneously.

## Deployment principles

- Keep configuration external to source code.
- Use separate development, staging, and production environments.
- Run as a non-root user with least privilege.
- Expose only required ports; terminate TLS at a maintained ingress/reverse proxy.
- Use health/readiness checks.
- Bound CPU, memory, file descriptors, request duration, and worker concurrency.
- Keep browser and document parsing workers on demand.
- Pin dependencies and images; scan and update on a controlled cadence.

## Configuration contract

| Variable | Default | Purpose | Notes |
|---|---|---|---|
| `INTILIGENCE_EGRESS_PROXY_URL` | empty | HTTP(S) proxy origin for outbound acquisition | Optional outside the isolated Compose profile; credentials, paths, query strings, and fragments are rejected. |
| `INTILIGENCE_REQUIRE_EGRESS_PROXY` | `false` | Fail closed if no egress proxy is configured | Set to `true` in the isolated Compose profile. |
| `INTILIGENCE_ALLOW_PRIVATE_NETWORKS` | `false` | Permit private target addresses | Keep `false` for public research acquisition; never enable in the reference egress profile. |

Never commit real credentials. See [isolated egress profile](../deploy/EGRESS_SECURITY.md) for the reference network topology and remaining deployment gates.

## Observability

Track request count, latency, errors, cancellation; provider latency/throttling/retries; acquisition bytes and host budgets; extraction success/yield/failure; evidence and claim counts by status; database health and storage growth; worker resource use and queue depth if applicable. Use correlation IDs across MCP request, provider operation, artifact, evidence, and claim. Redact sensitive data.

## Backup and recovery

Back up PostgreSQL on a documented schedule. Test restore, not just backup creation. Define retention for raw artifacts separately from database backups. Record recovery point and recovery time objectives before production. Ensure deletion propagates to derived indexes and caches where required.

## Release checklist

- Tests and static checks pass.
- Database migrations are reviewed and reversible where feasible.
- Dependency and license review is complete.
- Secrets and configuration are validated.
- Backup/restore path is tested.
- Health checks and alerts are configured.
- Rollback procedure is documented.
- Release notes identify changes and known limitations.

## Operational commands

The repository now includes a Dockerfile and Compose reference profile. Validate its rendered configuration with `docker compose -f compose.yaml config --quiet`, then follow [EGRESS_SECURITY.md](../deploy/EGRESS_SECURITY.md) for build/run commands. The profile has not been deployed to a live Docker daemon or VPS; do not treat it as production-validated.
