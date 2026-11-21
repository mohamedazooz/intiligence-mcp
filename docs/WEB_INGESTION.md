# Web Ingestion and Scraping Pipeline

**Status:** Proposed operational design.

## Scope

The pipeline discovers, acquires, extracts, normalizes, and records permitted web content. Search, crawling, and extraction are separate responsibilities implemented behind provider adapters.

## Pipeline stages

1. **Request classification:** identify intent, domains, source types, freshness needs, and access constraints.
2. **Discovery:** obtain candidate URLs from approved search providers or known source registries; record query, provider, and discovery time.
3. **Policy gate:** evaluate host rules, robots/access policy, terms, license, privacy, and task authorization.
4. **Acquisition:** use a bounded HTTP client or approved browser worker; apply per-host concurrency, request budgets, timeouts, size limits, and redirect validation.
5. **Artifact preservation:** store raw response or stable reference, capture timestamp, status, media type, and content hash where possible.
6. **Extraction:** parse supported formats through isolated adapters.
7. **Normalization:** normalize encoding and structure while preserving headings, tables, links, and source locators.
8. **Evidence generation:** create excerpt-level evidence capsules linked to the artifact.
9. **Quality checks:** detect empty extraction, duplicate content, truncation, boilerplate, encoding errors, and stale captures.
10. **Claim update:** attach evidence to claims; never promote generated summaries directly to verified knowledge.

## Provider adapter contract

Each adapter declares supported operations and source types; authentication requirements and secret references; rate limits, concurrency, timeout, and response-size bounds; output schema and provenance fields; error taxonomy and retryability; license and operational constraints; and health checks. An adapter must not silently strip source locators or provenance.

## Responsible acquisition rules

- Respect licenses, terms, privacy, robots/access policies, and applicable law.
- Never bypass authentication, paywalls, CAPTCHAs, rate limits, or technical access controls.
- Do not rotate identities or proxies to evade restrictions.
- Restrict crawling to authorized scope and avoid destructive or intrusive requests.
- Validate redirects and resolved IP addresses to mitigate SSRF; block loopback, link-local, private, and metadata endpoints by default.
- Treat page content as hostile input; never execute embedded instructions as agent policy.
- Avoid downloading executable content unless explicitly required and safely isolated.

## Reliability controls

Use explicit timeouts, bounded concurrency, per-host budgets, exponential backoff with jitter for retryable errors, circuit breakers where needed, maximum response sizes, and cancellation propagation. Do not retry policy denials or permanent client errors.

## Extraction quality

Record parser and version. Preserve page number, heading path, table coordinates, URL fragment, or other stable locator. Report extraction failures rather than inventing missing content. Mark OCR-derived text and retain quality metadata where available.

## Observability

Log request identifiers, provider, host, duration, byte count, outcome, and retry count. Do not log credentials, private documents, or sensitive query payloads. Track success rate, latency, extraction yield, duplicate rate, and policy denials.
