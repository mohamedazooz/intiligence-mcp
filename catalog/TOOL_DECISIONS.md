# Tool Integration Decisions

| Candidate | Responsibility | Decision |
|---|---|---|
| OmniMCP | Agent/worker/job/workspace/storage control plane | Retain; fix P0s |
| Agentgateway | MCP/A2A L7 gateway | Defer until gateway gaps measured |
| OpenHands | Coding-agent runtime | Candidate; isolated runtime adapter only |
| LiteLLM | Model routing/spend controls | Optional adapter |
| Crawl4AI | Dynamic web crawling/extraction | Optional; compare with baseline |
| Docling | PDF/Office parsing | First parser PoC |
| SearXNG | Self-hosted metasearch | Optional search provider |
| HTTPX + Trafilatura | Static web fetch/extraction | Baseline adopt |
| Playwright | JS-rendered pages | Isolated worker only |
| Firecrawl | Crawl/extract service | Optional; AGPL review |
| Qdrant | Vector retrieval | Optional derived index |
| OpenSearch | Lexical search/analytics | Defer pending benchmark |
| OpenCTI | CTI knowledge graph | Separate service later |
| MISP | Threat sharing | Separate service; AGPL review |
| IntelOwl | Analyzer orchestration | Candidate; isolate analyzers |
| ProjectDiscovery | Authorized recon | Passive-first; allowlisted active scans only |
| gVisor | OCI sandbox | Optional worker capability |
| Firecracker | MicroVM isolation | Later dedicated worker pool |
| LangGraph | Stateful agent workflows | Selective use |
| Temporal | Durable workflows | Defer; existing job engine first |
| n8n | Workflow automation | Optional; license/use terms review |
| Telegram AI Agent | Telegram UX/session patterns | Extract UX only; no direct shell bridge |

Never install all candidates together. One provider per responsibility; add alternatives only behind adapters after tests.