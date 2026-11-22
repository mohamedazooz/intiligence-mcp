# Observability and Service Objectives

Use structured JSON logs with request, research-run, acquisition and worker IDs. Never log secrets, authorization headers, full private documents or sensitive query payloads by default. Keep audit events separate from debug logs. Avoid high-cardinality metric labels such as full URLs or user IDs.

Core metrics:
- MCP request latency/error/auth denial.
- Research run success, failure, cancellation and duration.
- Search provider latency, quota errors and result counts.
- Acquisition policy outcomes and error categories.
- Extraction success, empty output, truncation and parser timeout.
- Evidence provenance completeness and citation coverage.
- Queue age, retries, worker utilization and sandbox failures.
- Database latency/connections/locks/migration state.
- Object-store errors, artifact bytes and deletion backlog.

Provisional targets, not promises:
- Internal MCP read calls p95 below 1 second under an agreed baseline.
- No P0 auth, tenant, SSRF or sandbox defect at release.
- Every published claim has evidence or is explicitly marked inference/unverified.
- Every artifact/evidence record has tenant and retention metadata.
- Restore test succeeds within agreed recovery objective.

Finalize SLOs only after load testing the actual deployment.
