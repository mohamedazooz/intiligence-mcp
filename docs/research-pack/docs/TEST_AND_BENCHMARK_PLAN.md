# Test and Benchmark Plan

## Test pyramid

Unit tests: URL policy, DNS/IP/redirect checks, hashing/deduplication, extraction locators, claim invariants, tenant helpers, retry/timeout/cancellation/idempotency.

Contract tests: search adapter schemas, HTTP/parser output, MCP schemas/error envelopes, OmniMCP job lifecycle, OpenCTI/MISP APIs when enabled.

Integration tests: PostgreSQL migrations from empty and previous schema, object storage hash verification, end-to-end discovery-to-report fixture, two-tenant isolation, deletion propagation, provider outage behavior.

Security tests: SSRF over IPv4/IPv6, private and metadata ranges, redirects, DNS rebinding, archive traversal, decompression bombs, malformed PDFs, prompt injection, secret canaries, auth expiry/revocation, worker escape, unexpected egress, crawl budgets.

## Benchmarks

| Component | Metrics |
|---|---|
| Search | Recall@k, precision@k, latency, quota errors |
| Static extraction | Clean-text ratio, locator coverage, success rate, p95 latency |
| Browser extraction | Page-class success, resource use, timeout and cleanup rate |
| Document parsing | Page/table fidelity, OCR accuracy, RAM/CPU |
| Evidence | Locator correctness, hash integrity, provenance completeness |
| Retrieval | Recall/precision, stale-index rate, tenant filter correctness |
| Research report | Citation coverage, unsupported-claim rate, conflict recall, cost |
| Operations | Throughput, queue age, error budget, recovery and restore time |

Build a legally reusable fixture corpus: static and JS HTML, redirects, language variants, PDFs with tables, scanned PDFs, DOCX/XLSX, malformed documents, duplicates and prompt-injection samples. Record expected text and exact locators.

Release gates: P0 security tests pass; tenant isolation proven; migrations and restore pass; no unreviewed critical/high vulnerability; every report claim is cited or marked inference/unverified; benchmarks meet agreed VPS thresholds.
