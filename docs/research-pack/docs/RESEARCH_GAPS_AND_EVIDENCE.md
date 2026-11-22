# Research Gaps and Evidence Register

## Confirmed from supplied review scope

| Finding | Basis | Status |
|---|---|---|
| Target Intiligence repository is documentation-first/bootstrap | Inspected GitHub main tree; no application package in reviewed tree | Verified at inspected ref; recheck |
| OmniMCP control plane is in separate MULTI-AGENTS-OPS repository | Supplied local audit and inspected snapshot | Verified in supplied scope |
| MCP bearer authentication pending in inspected OmniMCP snapshot | Implementation status and MCP boundary review | P0; revalidate branch |
| Worker uses host subprocess plus rlimits; no enforced container/gVisor sandbox | Worker/security source audit | P0 for untrusted jobs |
| Some MCP paths pass owner_id=None | Inspected MCP call paths | Verify all tools and reachable data |
| Alembic migrations deferred | Dependency/implementation status | P1 before production schema evolution |
| HF storage adapter buffers entire object | Storage source inspection | P1; stream or cap |
| Local StealthScraper exposes scrape_page and check_ip_stealth | Local README/MCP server inspection | Static review only |
| StealthScraper accepts arbitrary URLs and proxy/anti-bot options | Local source/docs inspection | Unsafe for direct production integration |
| Supplied scraping note contains 22 unique GitHub URLs | Research note analysis | Not exhaustive of historical conversation |

## Not yet verified
- Full source audit of all 22 URLs.
- Current OmniMCP branch after audited commit.
- Full transitive dependency/license inventory.
- Runtime and resource benchmarks for each candidate.
- Docling OCR/model licensing.
- IntelOwl analyzer-by-analyzer license and egress.
- ProjectDiscovery license per selected tool.
- Target VPS capacity, storage, throughput and cost.
- Final MCP SDK language/version and client compatibility.

A README or metadata lookup is discovery evidence, not source audit. Every new finding must record URL, immutable commit/release, inspected files, date, method, confidence and limitations.
