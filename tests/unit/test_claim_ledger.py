import sqlite3

import pytest

from intiligence_mcp.storage.claims import ClaimLedger
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def test_claim_links_evidence_and_tracks_review_state(tmp_path):
    db = tmp_path / "research.sqlite3"
    source = SourceRegistry(db).add("https://example.org/article")
    evidence = EvidenceStore(db).save(source.source_id, "Evidence text")
    ledger = ClaimLedger(db)
    claim = ledger.create("The article reports a new policy.", (evidence.evidence_id,))
    assert claim.status == "unreviewed"
    assert claim.evidence_ids == (evidence.evidence_id,)
    reviewed = ledger.set_status(
        claim.claim_id,
        "supported",
        reviewer_id="analyst-1",
        rationale="The linked excerpt directly supports the proposition.",
    )
    assert reviewed is not None and reviewed.status == "supported"
    history = ledger.get_review_history(claim.claim_id)
    assert len(history) == 1
    assert history[0].reviewer_id == "analyst-1"
    assert history[0].previous_status == "unreviewed"


def test_claim_rejects_unknown_evidence_and_invalid_status(tmp_path):
    db = tmp_path / "research.sqlite3"
    SourceRegistry(db)
    EvidenceStore(db)
    ledger = ClaimLedger(db)
    with pytest.raises(sqlite3.IntegrityError):
        ledger.create("Claim with missing evidence", ("missing",))
    with pytest.raises(ValueError):
        ledger.set_status(
            "not-real",
            "maybe",
            reviewer_id="analyst",
            rationale="Invalid test status.",
        )


def test_claim_statement_is_required_and_normalized(tmp_path):
    ledger = ClaimLedger(tmp_path / "claims.sqlite3")
    with pytest.raises(ValueError):
        ledger.create("  \n ")
    claim = ledger.create("  A   normalized claim  ")
    assert claim.statement == "A normalized claim"


def test_supported_claim_requires_supporting_evidence(tmp_path):
    ledger = ClaimLedger(tmp_path / "claims.sqlite3")
    claim = ledger.create("Claim without evidence")

    with pytest.raises(ValueError, match="supporting evidence"):
        ledger.set_status(
            claim.claim_id,
            "supported",
            reviewer_id="analyst",
            rationale="Attempt to approve without evidence.",
        )


def test_contradicted_claim_requires_a_contradicting_link(tmp_path):
    db = tmp_path / "research.sqlite3"
    source = SourceRegistry(db).add("https://example.org/article")
    evidence = EvidenceStore(db).save(source.source_id, "Conflicting evidence")
    ledger = ClaimLedger(db)
    claim = ledger.create("The article reports a new policy.")

    with pytest.raises(ValueError, match="contradicting evidence"):
        ledger.set_status(
            claim.claim_id,
            "contradicted",
            reviewer_id="analyst",
            rationale="No contradiction link exists yet.",
        )

    linked = ledger.link_evidence(
        claim.claim_id,
        evidence.evidence_id,
        "contradicts",
        "The source explicitly disputes the proposition.",
        "analyst",
    )
    assert linked.evidence_links[0][1] == "contradicts"
    reviewed = ledger.set_status(
        claim.claim_id,
        "contradicted",
        reviewer_id="analyst",
        rationale="Contradicting excerpt was reviewed.",
    )
    assert reviewed is not None and reviewed.status == "contradicted"


def test_review_requires_reviewer_and_rationale(tmp_path):
    ledger = ClaimLedger(tmp_path / "claims.sqlite3")
    claim = ledger.create("An unreviewed proposition")

    with pytest.raises(ValueError, match="reviewer_id"):
        ledger.set_status(
            claim.claim_id,
            "inconclusive",
            reviewer_id=" ",
            rationale="Insufficient evidence.",
        )
    with pytest.raises(ValueError, match="rationale"):
        ledger.set_status(
            claim.claim_id,
            "inconclusive",
            reviewer_id="analyst",
            rationale=" ",
        )


def test_legacy_claim_evidence_schema_is_migrated(tmp_path):
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE sources(source_id TEXT PRIMARY KEY);
            CREATE TABLE evidence(
                evidence_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(source_id)
            );
            CREATE TABLE claims(
                claim_id TEXT PRIMARY KEY,
                statement TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE claim_evidence(
                claim_id TEXT NOT NULL REFERENCES claims(claim_id),
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                PRIMARY KEY(claim_id, evidence_id)
            );
            """
        )

    ledger = ClaimLedger(db_path)
    with sqlite3.connect(db_path) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(claim_evidence)")}
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"relation", "rationale", "linked_at"} <= columns
    assert "claim_evidence_events" in tables
    assert ledger is not None


def test_claim_review_history_rejects_mutation(tmp_path):
    db = tmp_path / "research.sqlite3"
    source = SourceRegistry(db).add("https://example.org/article")
    evidence = EvidenceStore(db).save(source.source_id, "Supporting evidence")
    ledger = ClaimLedger(db)
    claim = ledger.create("A reviewable claim", (evidence.evidence_id,))
    ledger.set_status(
        claim.claim_id,
        "supported",
        reviewer_id="analyst",
        rationale="Evidence supports the claim.",
    )
    review = ledger.get_review_history(claim.claim_id)[0]

    with (
        sqlite3.connect(db) as connection,
        pytest.raises(sqlite3.IntegrityError, match="append-only"),
    ):
        connection.execute(
            "UPDATE claim_reviews SET rationale='edited' WHERE review_id=?",
            (review.review_id,),
        )
