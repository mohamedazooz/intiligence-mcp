# Integration Blueprints

Status: target design. A component is not implemented until code, tests and deployment evidence exist.

## 1. Existing OmniMCP control plane

Keep the existing MULTI-AGENTS-OPS repository as control plane. Intiligence owns research-domain behavior, not a duplicate scheduler.

OmniMCP responsibilities: agent and worker registry, job lifecycle/retry/cancel/timeout/idempotency, workspace lifecycle, storage adapters and operator audit.

Intiligence responsibilities: source registry, discovery/acquisition, parsing, evidence capsules, claim ledger, research orchestration and report compilation.

Inspected snapshot blockers: MCP bearer authentication pending; worker uses host subprocesses plus resource limits but no enforced OCI/gVisor sandbox; some MCP paths pass owner_id=None; Alembic migrations deferred; HF storage buffers full objects. Revalidate current branch and close P0s before untrusted exposure.

## 2. Search provider

Internal contract: search(query, filters, freshness, cursor) returns a bounded page of candidates. Persist query, provider/version, timestamp, URL, rank and provider metadata. Search results are candidates, not verified evidence. SearXNG is optional and must remain a separate service unless AGPL obligations are reviewed.

## 3. Static acquisition

Baseline: HTTPX plus URL policy plus Trafilatura. Validate scheme, host, DNS, IP ranges and every redirect. Block loopback, private, link-local, multicast, reserved and cloud metadata addresses. Bind validation to the actual connection destination to mitigate DNS rebinding. Enforce response/decompression bytes, redirects, timeouts, concurrency and per-host budgets. Record policy decision, final URL, timestamp, hash, status and extraction version.

## 4. Dynamic browser acquisition

Playwright is an isolated on-demand worker, not the default fetch path. Crawl4AI may be benchmarked as a higher-level adapter. Per-job browser contexts, ephemeral scratch, no host profile, deny-by-default egress, host allowlists, download caps, CPU/RAM/time/page limits, cancellation and cleanup are mandatory. Retrieved page content is untrusted data, never instructions.

## 5. Document intelligence

Docling is the first parser PoC. Run in a bounded parser worker with network disabled by default. Preserve page/table/heading locators, parser version and warnings. Test scanned PDFs, OCR, malformed files, embedded content, large tables and timeouts. Review model/OCR licenses separately.

## 6. Evidence and claims

Raw artifacts -> extracted representations -> evidence capsules -> atomic claims -> reviewed knowledge. Claims may be proposed, supported, contradicted, qualified, stale, unverified or rejected. LLM output is a proposal only; it cannot self-certify.

## 7. CTI integrations

OpenCTI and MISP remain separate systems with separate credentials, access controls and data-sharing markings. Integrate via documented APIs and STIX/TAXII. IntelOwl analyzers require separate isolation, allowlists and egress controls. Preserve TLP, source reliability, confidence, validity and redistribution restrictions.

## 8. Vector retrieval

PostgreSQL remains authoritative. Qdrant, if adopted, is a rebuildable derived index keyed to canonical IDs and embedding version. Updates/deletions must propagate. Benchmark recall, precision, tenant filters and stale-index behavior first.
