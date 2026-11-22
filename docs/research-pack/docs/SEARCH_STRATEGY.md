# Search and Deep-Web Strategy

## Provider priority
1. Official APIs and primary-source portals.
2. Licensed search APIs.
3. SearXNG metasearch with selected engines and per-engine policy.
4. Domain-specific sources: scholarly metadata, government datasets, CVE/NVD and CTI feeds.
5. Historical archives where their terms allow use.

## Deep web
Means non-indexed but legitimately accessible data: user-authorized enterprise portals, licensed databases, academic resources and internal documents. It does not mean bypassing logins, paywalls or access restrictions.

## Normalized result
Store provider, query ID, URL, title, snippet, rank, discovery time, source type, license/access policy and raw provider reference. Search snippets are discovery hints, not evidence.

## Ranking
Relevance, source authority, primary-source status, freshness, corroboration and extraction quality. Popularity is not truth.

## Controls
Provider budgets, pagination, timeout, retries, rate limits, deduplication and visible unavailable/denied states.