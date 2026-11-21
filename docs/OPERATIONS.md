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

Document each environment variable in an example file once implementation exists. Include purpose, required/optional status, default, secret classification, and validation rules. Never commit real credentials.

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

Actual install, build, test, migration, and start commands are omitted until implementation manifests exist. Do not guess commands.
