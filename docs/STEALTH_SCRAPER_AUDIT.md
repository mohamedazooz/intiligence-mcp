# StealthScraper_Engine — Local D: Drive Review

## Files inspected
- README.md
- mcp_server.py
- test_scraper.py
- SDK source was requested but its remote read had not completed at the time of this review.

## Observed MCP tools
- `scrape_page(url, format, country, sticky, session_id, wait_selector, proxy)`
- `check_ip_stealth(country, proxy)`

The server constructs one global SDK instance from environment variables and exposes scrape operations through FastMCP. The README advertises Cloudflare/anti-bot bypass, residential rotating/sticky proxies, country targeting, optional Browserless and a Tor proxy example.

## Risks
1. Proxy override and per-request rotation can be used to evade site restrictions. Do not use for bypassing bans, CAPTCHAs, paywalls or rate limits.
2. The MCP tool accepts arbitrary URLs; this is an SSRF risk unless URL schemes, DNS, redirects and private IP destinations are validated.
3. The server has no visible authentication or per-tool authorization in the inspected file.
4. Global SDK lifecycle/close behavior and browser cleanup need tests.
5. The live test only targets a public Playwright documentation URL; it does not establish reliability, compliance or safety.
6. No dependency manifest or license was visible in the inspected directory listing.

## Decision
Do not connect this server directly to production Intiligence as a stealth/anti-detection provider. Reuse only compliant extraction and browser automation concepts after removing evasion features, adding strict allowlists, SSRF controls, per-host budgets, auth, cancellation and provenance.

## Validation status
Static review only. No live scrape, proxy, Tor or Cloudflare bypass test was executed.