# OSINT and Cyber Threat Intelligence

## Candidate platforms
- OpenCTI: CTI graph and analyst workflows; deploy separately after sizing and license review.
- MISP: threat sharing and IOC correlation; AGPL review required.
- IntelOwl: analyzer orchestration; isolate analyzers and samples.
- ProjectDiscovery: Subfinder, DNSX, HTTPX, Katana and Nuclei for approved asset inventory.
- Shodan, VirusTotal, OTX, GreyNoise: optional API enrichment subject to quotas, terms and data-sharing rules.
- SpiderFoot: candidate OSINT automation; review plugins and outbound data handling.

## Safe default
Passive enrichment. Active scanning only with written authorization, allowlisted targets, rate caps and audit trail. Nuclei templates must be curated and non-destructive by default.

## Confidence
Store source reliability, recency, collection method, corroboration, false-positive caveats and analyst review. An IOC is not automatically malicious or attribution evidence.