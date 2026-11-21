# Evidence Model and Claim Ledger

**Status:** Proposed domain contract.

## Design goals

1. Every externally verifiable claim returned as fact should link to evidence.
2. Preserve the source and exact location from which evidence was extracted.
3. Keep raw artifacts, extracted representations, evidence, claims, and curated knowledge as separate lifecycle layers.
4. Preserve disagreement, staleness, and uncertainty instead of forcing a single answer.
5. Never allow generated text to verify itself.

## Lifecycle layers

| Layer | Meaning | Mutability |
|---|---|---|
| Raw artifact | Captured source bytes or durable reference | Immutable after capture; a new capture creates a new version |
| Extracted representation | Normalized text, tables, metadata, and structural locators | Rebuildable; versioned by extractor |
| Evidence capsule | Exact excerpt or structured fact with source locator and provenance | Immutable; supersede with a new capsule |
| Claim ledger | Atomic proposition and evidence relationships | Versioned; review state may change |
| Curated knowledge | Reviewed, reusable synthesis with uncertainty and lineage | Versioned and auditable |
| Workspace/inference | Temporary model notes and hypotheses | Not verified knowledge |

## Proposed record contracts

### Source

- `source_id`: stable internal identifier.
- `canonical_uri`: normalized URL or external identifier.
- `source_type`: web page, API record, uploaded file, dataset, or declared type.
- `publisher` and `title`: when known.
- `access_scope`: public, user-provided, private-authorized, or restricted.
- `first_seen_at`, `last_seen_at`: timestamps.
- `policy_snapshot`: acquisition restrictions and relevant license/terms metadata.

### Artifact

- `artifact_id`, `source_id`, `captured_at`.
- `content_hash`: cryptographic digest where available.
- `media_type`, `byte_size`, `storage_ref`.
- `fetch_method`, response/provider status.
- `retention_class` and `redaction_state`.

### Evidence capsule

- `evidence_id`, `artifact_id`.
- `locator`: URL fragment, page number, paragraph/table/cell, JSONPath, timestamp, or byte range.
- `exact_excerpt` or structured payload.
- `extractor_name`, `extractor_version`, `extracted_at`.
- `language`, `content_hash`, `quality_notes`.

### Claim

- `claim_id`, `claim_text`, normalized subject/predicate/object when appropriate.
- `status`: supported, conflicting, stale, unverified, rejected, or needs_review.
- `created_at`, `reviewed_at`, `reviewer`, and `valid_time` if applicable.
- Evidence relationships: supports, contradicts, qualifies, supersedes.

## Invariants

- Evidence must reference an artifact and a usable locator.
- A claim cannot be `supported` without at least one supporting evidence record.
- Contradictory evidence must remain queryable and visible.
- Freshness is domain-specific; do not apply one universal expiry period.
- A summary is not a substitute for the underlying excerpt and locator.
- Model confidence is not source reliability.
- Curated knowledge must retain lineage to claims and evidence.

## Response contract

Distinguish **verified from source**, **conflicting**, **stale**, **unverified**, and **inference**. Label each clearly. A research response should never imply that inference has the same status as direct evidence.

## Privacy and retention

Do not ingest private or sensitive material beyond user authorization and task scope. Apply redaction and retention rules before indexing or sharing. Hashes and metadata can themselves be sensitive; protect them accordingly.
