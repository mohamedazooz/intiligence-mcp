# Agent Operating Guide

## Mission
Build Intelligence MCP as an evidence-first research and knowledge platform exposed through the Model Context Protocol (MCP). The system should help AI clients retrieve traceable evidence, maintain durable research knowledge, and compile compact, source-grounded context.

## Non-negotiable principles
- Evidence before conclusions. Every externally verifiable claim must link to one or more evidence records.
- Preserve provenance: source, canonical URL or identifier, capture time, content hash when available, exact locator, extraction method, and access scope.
- Never let an LLM-generated statement certify itself as verified.
- Distinguish supported, conflicting, stale, and unverified claims. Keep model inference separate from curated knowledge.
- Never silently discard contradictory evidence or uncertainty.
- Respect licenses, terms, privacy, robots/access policies, and applicable law. Never bypass authentication, paywalls, CAPTCHAs, rate limits, or technical access controls.
- Do not expose secrets, tokens, credentials, private user data, or sensitive source material in logs or generated context.

## Architecture direction
- Start as a modular monolith with explicit module boundaries; do not introduce microservices without measured need.
- Keep the evidence pipeline conceptually layered: Raw Artifacts -> Extracted Representations -> Evidence Capsules -> Claim Ledger -> Curated Knowledge.
- Keep inference/workspace outputs separate from verified knowledge.
- Treat PostgreSQL as the initial system of record. Add vector search, Redis, distributed queues, or external search engines only when a measured requirement justifies their operational cost.
- Prefer bounded, on-demand workers for browser automation and document parsing.
- Keep optional high-risk or resource-heavy providers isolated and disabled by default.

## Engineering rules
- Inspect the existing repository before changing architecture or dependencies.
- Prefer small, reviewable changes and deterministic interfaces.
- Add tests for behavior, failure paths, permissions, and provenance invariants.
- Validate and normalize all external input; use timeouts, bounded concurrency, retries with backoff, and explicit resource limits.
- Pin or constrain dependencies and document license obligations.
- Never commit generated secrets, local state, caches, downloaded corpora, or user data.
- Update documentation when contracts, configuration, data models, or operational behavior change.

## Agent workflow
1. State the task, assumptions, risks, and acceptance criteria.
2. Inspect relevant code and docs before proposing changes.
3. Implement the smallest complete change.
4. Run relevant tests and static checks; report what was and was not run.
5. Review the diff for security, licensing, data-loss, and backward-compatibility risks.
6. Summarize changed files, validation evidence, limitations, and follow-up work.

## Resource budget
The initial deployment target is a small VPS (approximately 2 vCPU and 6 GB RAM). Avoid enabling multiple heavyweight databases, browser fleets, and orchestration services simultaneously. Measure memory, CPU, storage, and latency before expanding the stack.

## Definition of done
A change is done only when its behavior is documented, tests or a justified validation method exist, security and provenance implications are reviewed, and unresolved risks are explicitly recorded.
