# ADR 0001 — Start with a Modular Monolith

- **Status:** Accepted as initial direction
- **Date:** 2026-11-21

## Context

The initial deployment budget is approximately 2 vCPU and 6 GB RAM. Early microservices add network, deployment, and observability complexity before independent scaling needs are known.

## Decision

Build explicit domain modules in one deployable application. Isolate browser automation and document parsing as bounded on-demand workers where process isolation is required. Extract services only when profiling or independent security/scaling needs justify it.

## Consequences

- Lower initial operational overhead.
- Module boundaries and interfaces must be enforced in code.
- Later service extraction remains possible.
- Worker isolation is still required for untrusted or resource-intensive tasks.
