# Dark-Web and Tor Policy — Defensive Only

## Allowed scope
- Ingest vetted CTI feeds and vendor reports.
- Search public advisories and reputable reporting on ransomware, malware campaigns and vulnerabilities.
- Store defensive indicators and reports with source provenance and analyst confidence.
- Use OpenCTI, MISP or IntelOwl through documented APIs after legal, license and security review.
- Use approved monitoring providers under contract.

## Prohibited
- Illicit-market purchases or vendor interaction.
- Acquiring stolen credentials, private personal records, malware or contraband.
- Doxxing, stalking, extortion, credential validation or accessing victims' accounts.
- Bypassing access controls, CAPTCHAs, bans or rate limits.
- Autonomous Tor crawling or bulk downloading unknown binaries.
- Publishing unverified allegations or leaked personal data.

## Tor access
No onion/Tor crawler is enabled by default. Any future approved monitoring use case requires legal/security review, isolated egress-controlled worker, vetted destination allowlist, no downloads by default, no active interactions, malware quarantine, metadata minimization and human review.

## Data handling
Treat dark-web content as highly sensitive and potentially unlawful to possess. Store minimal metadata, redact personal data, apply short retention and require analyst approval before export.

## Escalation
For imminent harm or active compromise, preserve minimal evidence and follow incident/legal response. Do not autonomously contact criminal actors.