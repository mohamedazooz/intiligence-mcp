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
    reviewed = ledger.set_status(claim.claim_id, "supported")
    assert reviewed is not None and reviewed.status == "supported"


def test_claim_rejects_unknown_evidence_and_invalid_status(tmp_path):
    db = tmp_path / "research.sqlite3"
    SourceRegistry(db)
    EvidenceStore(db)
    ledger = ClaimLedger(db)
    with pytest.raises(sqlite3.IntegrityError):
        ledger.create("Claim with missing evidence", ("missing",))
    with pytest.raises(ValueError):
        ledger.set_status("not-real", "maybe")


def test_claim_statement_is_required_and_normalized(tmp_path):
    ledger = ClaimLedger(tmp_path / "claims.sqlite3")
    with pytest.raises(ValueError):
        ledger.create("  \n ")
    claim = ledger.create("  A   normalized claim  ")
    assert claim.statement == "A normalized claim"
