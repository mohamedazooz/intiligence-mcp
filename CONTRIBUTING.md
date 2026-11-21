# Contributing

## Workflow
1. Open or identify an issue and agree on scope before substantial changes.
2. Create a focused branch from `main`.
3. Inspect existing contracts and documentation before changing them.
4. Implement the smallest complete change and add tests for normal and failure paths.
5. Run formatting, lint, tests, and relevant security checks locally.
6. Update documentation and changelog when behavior or interfaces change.
7. Open a pull request with scope, design notes, test evidence, risks, and rollback notes.

## Pull request requirements
- No secrets, credentials, private data, generated corpora, or local state.
- Cite evidence for claims about external tools, versions, licenses, and capabilities.
- Identify proposed versus implemented functionality accurately.
- Include tests or explain why a change is documentation-only.
- Flag migrations, breaking changes, resource requirements, and security implications.
- Require review before merging; do not self-certify unverified behavior.

## Engineering conventions
Prefer typed interfaces, explicit errors, bounded concurrency, timeouts, retries with backoff, idempotency where appropriate, structured logs, and deterministic tests. Pin dependencies and record license obligations. Avoid premature microservices.
