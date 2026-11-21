# ADR 0002 — Provenance Is a First-Class Contract

- **Status:** Accepted
- **Date:** 2026-11-21

## Context

Research answers are useful when claims can be traced to source material and exact locations. Summaries alone lose provenance and can hide contradictions.

## Decision

Separate raw artifacts, extracted representations, evidence capsules, claim ledger entries, and curated knowledge. Evidence records retain source identity, capture time, exact locator, extraction metadata, and content hash when available. Model-generated text cannot verify itself.

## Consequences

- More metadata and storage are required.
- Extraction adapters must preserve locators.
- Claim status reflects support, conflict, staleness, and uncertainty.
- Tests enforce evidence lineage and prevent unsupported promotion.
