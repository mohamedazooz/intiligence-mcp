# Open-Source Project Portfolio

Status: candidate inventory. Listing does not mean installed, audited, or approved.

## Control plane and agents

| Project | Repository | Role | Decision |
|---|---|---|---|
| Existing OmniMCP | https://github.com/mohamedazooz/MULTI-AGENTS-OPS | Agents, workers, jobs, workspaces, storage | Retain; remediate P0 findings |
| MCP SDK | https://github.com/modelcontextprotocol | MCP protocol implementation | Select official SDK after runtime is confirmed |
| Agentgateway | https://github.com/agentgateway/agentgateway | MCP/A2A gateway and policy | Defer until gateway gaps are measured |
| OpenHands | https://github.com/All-Hands-AI/OpenHands | Optional coding-agent runtime | Candidate; isolated execution only |
| LiteLLM | https://github.com/BerriAI/litellm | Model routing, budgets, provider abstraction | Optional; inspect enterprise paths and license |

## Search, acquisition and extraction

| Project | Repository | Role | Decision |
|---|---|---|---|
| SearXNG | https://github.com/searxng/searxng | Self-hosted metasearch | Optional separate service; AGPL-3.0 review |
| HTTPX | https://github.com/encode/httpx | Bounded async HTTP client | Baseline dependency candidate |
| Trafilatura | https://github.com/adbar/trafilatura | Main text and metadata extraction | Baseline extractor; Apache-2.0 from v1.8.0, earlier releases GPLv3+ |
| Crawl4AI | https://github.com/unclecode/crawl4ai | Browser-aware crawling and extraction | Optional isolated worker; Apache-2.0 with attribution; review advisories |
| Playwright | https://github.com/microsoft/playwright | JS-rendered browser automation | Isolated on-demand worker; Apache-2.0 |
| Firecrawl | https://github.com/mendableai/firecrawl | Alternative crawl/extract engine | Optional; AGPL-3.0 review and benchmark against Crawl4AI |
| hakrawler | https://github.com/hakluke/hakrawler | Link discovery on authorized domains | Passive/allowlisted only; verify license |
| waybackpack | https://github.com/jsvine/waybackpack | Archive retrieval | Optional historical-source adapter; verify license |
| waymore | https://github.com/xnl-h4ck3r/waymore | Historical URL discovery | Optional; source terms and rate limits apply |

## Documents and retrieval

| Project | Repository | Role | Decision |
|---|---|---|---|
| Docling | https://github.com/docling-project/docling | PDF, Office, tables and layout extraction | First parser PoC; verify parser/model licenses |
| Qdrant | https://github.com/qdrant/qdrant | Vector retrieval index | Defer until PostgreSQL baseline is benchmarked |
| OpenSearch | https://github.com/opensearch-project/OpenSearch | Lexical search and analytics | Defer; operational footprint likely excessive initially |
| PostgreSQL | https://github.com/postgres/postgres | Primary system of record | Adopt as architecture baseline |

## OSINT and CTI

| Project | Repository | Role | Decision |
|---|---|---|---|
| OpenCTI | https://github.com/OpenCTI-Platform/opencti | CTI knowledge graph, STIX/TAXII | Separate service later; Community Apache-2.0, Enterprise separately licensed |
| MISP | https://github.com/MISP/MISP | Threat sharing and IOC lifecycle | Separate service/API; core AGPL-3.0 |
| PyMISP | https://github.com/MISP/PyMISP | MISP API client | Candidate; BSD-2-Clause |
| IntelOwl | https://github.com/intelowlproject/IntelOwl | Analyzer orchestration | Candidate; isolate analyzers and inspect each analyzer license |
| ProjectDiscovery | https://github.com/projectdiscovery | Authorized asset discovery/security testing | Passive-first; active scanning only with explicit authorization; licenses vary by repo |
| MISP modules | https://github.com/MISP/misp-modules | Enrichment/import/export modules | Use behind MISP boundary; AGPL-3.0 review |

## Workflow and isolation

| Project | Repository | Role | Decision |
|---|---|---|---|
| LangGraph | https://github.com/langchain-ai/langgraph | Stateful agent workflows | Selective use; MIT |
| Temporal | https://github.com/temporalio/temporal | Durable workflows | Defer; use existing job engine first; MIT server |
| n8n | https://github.com/n8n-io/n8n | External workflow automation | Optional separate service; Sustainable Use License, not OSI open source |
| gVisor | https://github.com/google/gvisor | OCI workload isolation | Sandbox PoC candidate; Apache-2.0 |
| Firecracker | https://github.com/firecracker-microvm/firecracker | MicroVM isolation | Later high-isolation worker pool; Apache-2.0 |
| containerd | https://github.com/containerd/containerd | Container runtime substrate | Evaluate with sandbox; containers alone are not a hardened boundary |

## Adoption rule

One implementation per responsibility, behind an adapter. Do not install all candidates. Verify exact tag/commit, SPDX license, notices, transitive SBOM, security advisories, runtime footprint, data handling and tests before adoption. Unknown license means no code copying. No stealth, CAPTCHA solving, ban evasion, paywall bypass or rate-limit circumvention.
