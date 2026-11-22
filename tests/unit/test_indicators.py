from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.indicators import IndicatorStore, extract_indicators
from intiligence_mcp.storage.source_registry import SourceRegistry


def test_extracts_validated_indicators_and_ignores_invalid_ipv4_and_emails():
    text = (
        "Known hosts: 8.8.8.8 and 999.999.1.1; "
        "IPv6 2001:4860:4860::8888; domain example.com; "
        "CVE-2024-12345; SHA256 "
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; "
        "contact analyst@example.com"
    )

    indicators = set(extract_indicators(text))

    assert ("ipv4", "8.8.8.8") in indicators
    assert not any(value == "999.999.1.1" for _, value in indicators)
    assert ("ipv6", "2001:4860:4860::8888") in indicators
    assert ("domain", "example.com") in indicators
    assert ("cve", "CVE-2024-12345") in indicators
    assert (
        "sha256",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    ) in indicators
    assert not any("analyst@example.com" in value for _, value in indicators)


def test_indicator_records_are_deduplicated_and_linked_to_evidence(tmp_path):
    database = tmp_path / "research.sqlite3"
    sources = SourceRegistry(database)
    evidence_store = EvidenceStore(database)
    indicators = IndicatorStore(database)

    source = sources.add("https://example.org/report")
    first = evidence_store.save(
        source.source_id,
        "Observed 8.8.8.8, CVE-2024-12345, and 2001:4860:4860::8888",
    )
    second = evidence_store.save(source.source_id, "Repeated observation: 8.8.8.8")

    first_records = indicators.add_many(first.evidence_id, extract_indicators(first.content))
    second_records = indicators.add_many(second.evidence_id, extract_indicators(second.content))

    assert len(first_records) == 3
    assert len(second_records) == 1
    first_ipv4 = next(item for item in first_records if item.kind == "ipv4")
    assert first_ipv4.indicator_id == second_records[0].indicator_id

    matches = indicators.find("8.8.8.8", "ipv4")
    assert len(matches) == 1
    assert matches[0]["evidence_count"] == 2
    assert set(matches[0]["evidence_ids"]) == {first.evidence_id, second.evidence_id}

    ipv6_matches = indicators.find("2001:4860:4860:0:0:0:0:8888")
    assert len(ipv6_matches) == 1
    assert ipv6_matches[0]["kind"] == "ipv6"


def test_indicator_store_rejects_unknown_evidence(tmp_path):
    database = tmp_path / "research.sqlite3"
    SourceRegistry(database)
    EvidenceStore(database)
    indicators = IndicatorStore(database)

    try:
        indicators.add_many("missing-evidence", [("ipv4", "8.8.8.8")])
    except ValueError as exc:
        assert "Unknown evidence_id" in str(exc)
    else:
        raise AssertionError("unknown evidence must not be indexed")
