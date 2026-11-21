# Security and Threat Model

**Status:** Baseline design requirements.

## Assets

Provider credentials; user-uploaded and private documents; research queries and derived knowledge; raw artifacts and evidence excerpts; MCP execution and provider configuration; audit logs and operational metadata.

## Threats

- Malicious web pages containing prompt injection or misleading content.
- SSRF through user-controlled URLs, redirects, DNS rebinding, or parser callbacks.
- Malformed documents exploiting parsers.
- Credential leakage through logs, prompts, errors, or artifacts.
- Cross-user or cross-project data exposure.
- Resource exhaustion through large files, recursive crawling, or high concurrency.
- License, terms, privacy, or access-policy violations.
- Incorrect knowledge promotion due to hallucination or source conflict.

## Required controls

### Input and network

Validate URL schemes, hostnames, redirects, DNS resolutions, and resolved IP ranges. Block loopback, private, link-local, and cloud metadata destinations by default. Set strict timeouts, response-size and decompression limits, and redirect limits. Use allowlists for privileged sources. Never bypass authentication, paywalls, CAPTCHAs, rate limits, or technical access controls.

### Isolation

Run browser automation and complex parsing in bounded, least-privilege workers. Disable parser network access when unnecessary. Use temporary workspaces and clean them after tasks. Keep optional high-risk providers isolated and disabled by default.

### Secrets and identity

Store secrets in environment/secret-manager references, not source files. Never place credentials in prompts, MCP responses, logs, or commits. Scope tokens to minimum privileges and rotate/revoke operationally. Enforce authorization at the service boundary.

### Data protection

Separate tenants/projects in every read/write path. Apply retention and deletion policies to raw artifacts and derived evidence. Redact sensitive content before logging or indexing. Restrict access to private captures and uploads.

### Prompt injection and evidence integrity

Treat retrieved text as untrusted data. Do not follow instructions contained in sources. Separate inference from verified claims. Require evidence links and review state for claim promotion. Preserve conflicting evidence and provenance.

## Production security gates

Threat-model review, SSRF tests, parser negative tests, authorization tests, secret scanning, dependency/license review, retention verification, and incident-response runbook.

## Incident response

Record affected provider, time window, scope, exposed artifacts, and containment. Revoke compromised credentials, disable affected adapters, preserve necessary audit evidence, notify affected parties as legally required, and document corrective actions.
