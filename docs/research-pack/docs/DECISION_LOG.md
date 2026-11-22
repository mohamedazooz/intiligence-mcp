# Engineering Decision Log

| ID | Decision | Rationale | Revisit trigger |
|---|---|---|---|
| DEC-001 | Retain existing OmniMCP control plane | Avoid duplicate worker/job/workspace/storage lifecycle | Control plane becomes unmaintainable or unsafe |
| DEC-002 | Intiligence is modular research/evidence layer | Clear ownership and low operational complexity | Measured scale/team boundary |
| DEC-003 | PostgreSQL is initial source of truth | Transactions and fewer moving parts | Benchmark proves unmet requirement |
| DEC-004 | HTTPX + Trafilatura is static baseline | Bounded and replaceable acquisition path | Corpus benchmark fails |
| DEC-005 | Playwright isolated and on-demand | Dynamic pages add cost and attack surface | Required coverage needs it |
| DEC-006 | Docling is first parser PoC | Broad document/layout candidate | Accuracy/resource test fails |
| DEC-007 | Qdrant/OpenSearch/Redis/Temporal deferred | Avoid premature infrastructure | Measured need and ADR |
| DEC-008 | OpenCTI/MISP separate services | Preserve models, licenses and operations | Reviewed requirement changes topology |
| DEC-009 | No stealth/access-control evasion | Safety and legal boundary | No exception |
| DEC-010 | No wholesale upstream copying | License, supply-chain and maintenance control | Small attributed file reuse approved |
