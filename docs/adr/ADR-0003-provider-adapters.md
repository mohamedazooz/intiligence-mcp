# ADR 0003 — Integrate Providers Through Adapters

- **Status:** Accepted as design direction
- **Date:** 2026-11-21

## Context

Search, crawling, parsing, and storage providers evolve independently and have different licenses, limits, and operational costs.

## Decision

Define narrow provider interfaces. Keep provider-specific schemas, credentials, retries, and error mapping inside adapters. Domain services consume normalized contracts and must not depend on provider-specific details.

## Consequences

- Providers can be evaluated and replaced independently.
- Adapter contracts preserve provenance and cancellation.
- Each adoption requires license, security, resource, and maintenance review.
- Avoid integrating multiple providers for one capability before benchmarking.
