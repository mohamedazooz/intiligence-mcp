# License Compatibility and Supply-Chain Review

Initial screening only. Recheck exact release, file headers, transitive dependencies, plugins, models and distribution model before adoption.

| Component | Initial license signal | Reuse posture | Required follow-up |
|---|---|---|---|
| Crawl4AI | Apache-2.0; attribution requirement noted upstream | Dependency or isolated service after security review | Pin release; preserve attribution; inspect advisories |
| Trafilatura | Apache-2.0 from v1.8.0; earlier versions GPLv3+ | Pin reviewed release >=1.8.0 | Verify tag and transitive dependencies |
| Playwright | Apache-2.0 | Package dependency | Review browser binaries/notices |
| SearXNG | AGPL-3.0 | Prefer separate service; legal review before modification | Verify network/distribution obligations |
| Firecrawl | AGPL-3.0 listing | Separate service or legal-approved use | Check edition, current license and hosted terms |
| Docling | Verify exact release and model components | Dependency after full review | Check OCR/model licenses |
| Qdrant | Apache-2.0 | Separate service/dependency | Verify client and deployment artifacts |
| OpenCTI Community | Apache-2.0; Enterprise components separate | Community API/service boundary | Inspect per-file headers and edition boundaries |
| MISP core | AGPL-3.0 | Separate service/API | Preserve terms if modifying core |
| PyMISP | BSD-2-Clause | API client candidate | Verify package and dependencies |
| IntelOwl | Verify exact revision | Separate analyzer service | Inspect analyzer-specific licenses and egress |
| ProjectDiscovery | Varies per repository | Per-tool approval | Inspect each LICENSE independently |
| LiteLLM | MIT outside enterprise paths; enterprise directory separately licensed | Optional package/service | Exclude enterprise-only code unless licensed |
| LangGraph | MIT | Optional library | Pin dependencies |
| Temporal server | MIT | Separate platform if justified | Review SDK/UI dependencies |
| n8n | Sustainable Use License | Separate product only after use-case review | Not OSI open source; review hosted/commercial restrictions |
| OpenSearch | Apache-2.0 | Deferred service | Review plugins/distribution |
| gVisor | Apache-2.0 | Sandbox runtime candidate | Review host compatibility |
| Firecracker | Apache-2.0 | MicroVM runtime candidate | Review host integration/dependencies |
| Existing OmniMCP | User-owned repository | Internal reuse after audit | Inspect package manifests and notices |

Release evidence: SPDX/CycloneDX SBOM, exact versions/commits, LICENSE/NOTICE hashes, vulnerability scan, copied-file provenance and third-party notices. Unknown license blocks copying.
