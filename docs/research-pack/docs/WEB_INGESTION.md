# Web Ingestion Pipeline

Official API → bounded HTTP fetch → static extraction → browser only when necessary.

## Components
- HTTPX: bounded static fetch.
- Trafilatura/Readability: main-content extraction.
- Scrapy/Crawlee: large structured crawls.
- Playwright: JS-rendered pages in isolated workers.
- Crawl4AI: optional higher-level extraction adapter.
- Firecrawl: optional external service; AGPL-3.0 legal review before embedding/distribution.
- Katana: authorized asset/endpoint discovery only.

## Required controls
SSRF and DNS-rebinding protection; validate every redirect and resolved IP; block loopback/private/link-local/metadata targets; host allowlists; content-type and byte caps; timeout; max pages/depth; robots/terms/license checks; cancellation; provenance.

## Prohibited
No CAPTCHA bypass, paywall bypass, proxy rotation to evade bans or rate limits, credential/session theft, or unauthorized crawling.

## Evidence
Persist capture time, source URL, response status, content hash, parser version, exact heading/page/table locator and extraction quality flags.