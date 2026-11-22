# Release Acceptance Gates

## A. Repository hygiene
Canonical docs index current; no secrets/private data/generated binaries; lint/format/link checks pass; third-party sources have provenance and notices.

## B. Security
MCP auth and scopes enforced; tenant isolation passes; SSRF/redirect/DNS/egress tests pass; parser/browser/analyzer workers isolated; P0 defects closed.

## C. Evidence quality
Raw artifact or stable reference preserved; source/time/hash/extractor recorded; exact locators retained; conflict/staleness visible; model inference cannot mark claim supported.

## D. Reliability
Timeout/cancel/retry/idempotency tested; provider failure does not corrupt evidence; migrations and restore pass; backpressure and resource caps work.

## E. Release operations
SBOM, license and vulnerability reports attached; staging smoke passes; metrics/alerts/runbooks ready; canary and rollback rehearsed; operator approves rollout.
