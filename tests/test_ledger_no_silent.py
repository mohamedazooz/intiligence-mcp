import asyncio
from omnipulse.ledger import CoverageLedger


def test_ledger_records():
    l = CoverageLedger("m1")
    l.record("searxng", "OK", 10, 5)
    l.record("crawl4ai", "TIMEOUT", 18000, 0, "timeout")
    entries = l.to_list()
    assert len(entries) == 2
    assert entries[1]["status"] == "TIMEOUT"
    assert entries[1]["reason"] == "timeout"
