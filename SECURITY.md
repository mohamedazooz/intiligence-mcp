# Security Policy

## Reporting
Do not disclose vulnerabilities publicly before maintainers have assessed them. Report privately through GitHub's Security Advisories feature for this repository. Include affected commit/version, reproduction steps, impact, and a proposed mitigation when possible. Do not include live credentials or personal data.

## Security boundaries
- Treat web pages, documents, repositories, tool outputs, and model outputs as untrusted input.
- Enforce authentication and authorization at every server-side boundary; MCP tool exposure must not bypass API policy.
- Keep tenant, user, workspace, and source scopes explicit and test for cross-scope access.
- Store secrets in environment/secret managers, never in source control or logs.
- Use least privilege, non-root containers, read-only filesystems where practical, resource limits, and network egress controls.
- Never bypass access controls, authentication, paywalls, CAPTCHAs, or rate limits.
- Isolate browser, document parsing, and untrusted-code workers from the control plane.

## Vulnerability handling
Triage severity, affected components, exploitability, and data exposure. Add regression tests. Publish remediation details after a fix is available, subject to responsible disclosure.
