# Evidence-First Data Model

Status: logical model; schema and migrations must be validated against implementation.

| Entity | Core fields | Purpose |
|---|---|---|
| Tenant | id, name, policy_id | Isolation boundary |
| Principal | id, tenant_id, role, status | Authenticated identity |
| Source | id, canonical_uri, type, license, terms, access_policy | Source registry |
| DiscoveryRun | id, query, provider, started_at, status | Search provenance |
| SourceCandidate | id, discovery_id, url, rank, payload_hash | Candidate result |
| Acquisition | id, source_id, final_uri, captured_at, status, policy_decision | Fetch attempt |
| Artifact | id, tenant_id, storage_ref, sha256, media_type, size, retention | Immutable raw reference |
| Representation | id, artifact_id, format, parser_version, warnings | Extracted form |
| Locator | id, representation_id, page, heading, block, bbox | Exact location |
| EvidenceCapsule | id, locator_id, excerpt_hash, excerpt, captured_at | Traceable excerpt |
| Claim | id, subject, predicate, object, scope, status, confidence | Atomic assertion |
| ClaimEvidence | claim_id, evidence_id, relation, rationale | Support/conflict/qualify |
| ResearchRun | id, request, policy_snapshot, status, timing | Workflow execution |
| Report | id, research_run_id, version, content_ref | Compiled output |
| ReviewEvent | id, entity, reviewer, decision, rationale | Human review/audit |
| CredentialRef | id, tenant_id, provider, secret_ref, scopes | Reference only; never store raw secret |

Invariants:
1. Every artifact belongs to one tenant or an explicitly public shared scope.
2. Every evidence capsule resolves to source artifact and stable locator.
3. Every claim transition is auditable.
4. Supported claims require valid supporting evidence and required review.
5. Contradictory evidence is retained, not overwritten.
6. Staleness follows source-specific freshness policy.
7. Hash integrity does not prove truth or authenticity.
8. Derived indexes are rebuildable and non-authoritative.
9. Secrets never appear in DB fields, logs or model context.
10. Retention/deletion applies to artifacts, excerpts, embeddings and backups.

Claim states: proposed, supported, contradicted, qualified, stale, unverified, rejected. PostgreSQL is initial source of truth; object storage holds large immutable artifacts; vector indexes are derived.
