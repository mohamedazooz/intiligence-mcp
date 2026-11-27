import json
from urllib.parse import parse_qs, urlsplit

import pytest

from intiligence_mcp.acquisition.http import FetchResult
from intiligence_mcp.research.passive_osint import (
    PassiveOSINTError,
    PassiveOSINTService,
    find_rdap_base,
    normalize_domain,
    parse_ct_results,
    sanitize_rdap_payload,
)
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry


def _fetch_result(url: str, payload, media_type="application/json") -> FetchResult:
    body = json.dumps(payload).encode()
    return FetchResult(
        status=200,
        body=body,
        text=body.decode(),
        final_url=url,
        media_type=media_type,
        response_headers={"content-type": media_type},
        redirect_chain=(),
    )


@pytest.mark.parametrize(
    "value",
    [
        "127.0.0.1",
        "https://example.org",
        "*.example.org",
        "localhost",
        "host.internal",
        "bad..example.org",
        "-bad.example.org",
        "bad-.example.org",
    ],
)
def test_normalize_domain_rejects_non_domains_and_invalid_names(value):
    with pytest.raises((PassiveOSINTError, TypeError)):
        normalize_domain(value)


def test_normalize_domain_accepts_idna_and_trailing_dot():
    assert normalize_domain("BÜCHER.de.") == "xn--bcher-kva.de"


def test_rdap_bootstrap_uses_label_wise_longest_suffix_match():
    bootstrap = {
        "services": [
            [["uk"], ["https://rdap.uk/"]],
            [["co.uk"], ["https://rdap.co.uk/"]],
            [["com"], ["https://rdap.com/"]],
        ]
    }
    assert find_rdap_base("host.example.co.uk", bootstrap) == "https://rdap.co.uk/"
    assert find_rdap_base("example.com", bootstrap) == "https://rdap.com/"


def test_rdap_bootstrap_ignores_http_only_endpoints():
    bootstrap = {"services": [[["com"], ["http://rdap.example/"]]]}
    assert find_rdap_base("example.com", bootstrap) is None


def test_rdap_sanitizer_removes_contact_and_personal_fields():
    result = sanitize_rdap_payload(
        {
            "objectClassName": "domain",
            "ldhName": "example.org",
            "status": ["active"],
            "events": [{"eventAction": "registration", "eventDate": "2025-01-01"}],
            "nameservers": [{"ldhName": "ns1.example.org"}],
            "entities": [
                {
                    "roles": ["registrant"],
                    "vcardArray": ["vcard", [["email", {}, "text", "person@example.org"]]],
                }
            ],
            "remarks": [{"description": ["contact person@example.org"]}],
            "notices": [{"title": "Personal contact"}],
        }
    )
    serialized = json.dumps(result)
    assert result["ldhName"] == "example.org"
    assert result["events"][0]["eventAction"] == "registration"
    assert "entities" not in result
    assert "remarks" not in result
    assert "notices" not in result
    assert "person@example.org" not in serialized
    assert result["privacy"]["contact_entities_retained"] is False


def test_ct_parser_keeps_only_names_in_requested_domain():
    result = parse_ct_results(
        [
            {
                "id": 11,
                "issuer_name": "Test CA",
                "not_before": "2025-01-01",
                "not_after": "2026-01-01",
                "name_value": "www.acme.org\n*.api.acme.org\nexample.net\nnotacme.org",
            },
            {
                "id": 12,
                "issuer_name": "Another CA",
                "name_value": "acme.org\nadmin.acme.org\nwww.acme.org",
            },
        ],
        "acme.org",
    )
    assert result["names"] == [
        "acme.org",
        "admin.acme.org",
        "api.acme.org",
        "www.acme.org",
    ]
    assert result["matching_certificate_count"] == 2
    assert "www.acme.org" in result["certificates"][0]["matching_names"]
    assert "www.acme.org" in result["certificates"][1]["matching_names"]
    assert "does not prove current control or ownership" in result["interpretation"]


@pytest.mark.asyncio
async def test_passive_osint_inspection_persists_evidence_and_redacts_rdap(tmp_path):
    database = tmp_path / "osint.sqlite3"
    registry = SourceRegistry(database)
    evidence = EvidenceStore(database)
    calls = []

    async def fake_fetcher(url: str, *, accept=None, **_kwargs):
        calls.append(url)
        parsed = urlsplit(url)
        if parsed.hostname == "dns.google":
            query = parse_qs(parsed.query)
            record_type = query["type"][0]
            payload = {
                "Status": 0,
                "AD": record_type == "1",
                "Answer": [
                    {
                        "name": "acme.org.",
                        "type": int(record_type),
                        "TTL": 120,
                        "data": "203.0.113.8" if record_type == "1" else "ns1.acme.org.",
                    }
                ],
            }
            return _fetch_result(url, payload, "application/dns-json")
        if parsed.hostname == "data.iana.org":
            return _fetch_result(
                url,
                {"services": [[["org"], ["https://rdap.example.test/"]]]},
                "application/rdap-bootstrap+json",
            )
        if parsed.hostname == "rdap.example.test":
            return _fetch_result(
                url,
                {
                    "objectClassName": "domain",
                    "ldhName": "acme.org",
                    "status": ["active"],
                    "entities": [
                        {
                            "vcardArray": [
                                "vcard",
                                [["email", {}, "text", "private-contact@example.org"]],
                            ]
                        }
                    ],
                },
                "application/rdap+json",
            )
        if parsed.hostname == "crt.sh":
            return _fetch_result(
                url,
                [
                    {
                        "id": 42,
                        "issuer_name": "Example CA",
                        "not_before": "2025-01-01",
                        "not_after": "2026-01-01",
                        "name_value": "www.acme.org\nnotacme.org",
                    }
                ],
            )
        raise AssertionError(f"Unexpected provider URL: {url}")

    service = PassiveOSINTService(registry, evidence, fetcher=fake_fetcher)
    result = await service.inspect_domain("ACME.ORG.")

    assert result["status"] == "ok"
    assert result["domain"] == "acme.org"
    assert result["provider_success_count"] == 8
    assert len(calls) == 9  # six DNS requests, one bootstrap, RDAP, and CT
    assert result["providers"]["dns"]["A"]["records"][0]["data"] == "203.0.113.8"
    assert result["providers"]["rdap"]["data"]["ldhName"] == "acme.org"
    assert "entities" not in result["providers"]["rdap"]["data"]
    assert result["providers"]["certificate_transparency"]["names"] == ["www.acme.org"]

    for provider in (
        *result["providers"]["dns"].values(),
        result["providers"]["rdap"],
        result["providers"]["certificate_transparency"],
    ):
        provenance = provider.get("provenance")
        assert provenance
        assert provenance["http_status"] == 200
        assert provenance["final_url"] == provenance["provider_url"]
        assert provenance["stored_representation"] == "privacy_minimized_normalized_json"
        assert evidence.get(provenance["evidence_id"]) is not None
        assert evidence.get_capture(provenance["artifact_id"]) is not None

    rdap_artifact_id = result["providers"]["rdap"]["provenance"]["artifact_id"]
    stored_rdap = evidence.get_artifact_content(rdap_artifact_id)
    assert b"private-contact@example.org" not in stored_rdap


@pytest.mark.asyncio
async def test_rdap_rejects_response_for_a_different_domain(tmp_path):
    database = tmp_path / "rdap-mismatch.sqlite3"
    registry = SourceRegistry(database)
    evidence = EvidenceStore(database)

    async def fake_fetcher(url: str, *, accept=None, **_kwargs):
        host = urlsplit(url).hostname
        if host == "data.iana.org":
            return _fetch_result(
                url,
                {"services": [[["org"], ["https://rdap.example.test/"]]]},
                "application/rdap-bootstrap+json",
            )
        if host == "rdap.example.test":
            return _fetch_result(
                url,
                {"objectClassName": "domain", "ldhName": "other.org"},
                "application/rdap+json",
            )
        raise AssertionError(f"Unexpected provider URL: {url}")

    service = PassiveOSINTService(registry, evidence, fetcher=fake_fetcher)
    result = await service._rdap("acme.org")

    assert result == {"status": "provider_error", "error": "rdap_domain_mismatch"}


@pytest.mark.asyncio
async def test_provider_http_error_is_preserved_for_diagnostics(tmp_path):
    database = tmp_path / "provider-error.sqlite3"
    registry = SourceRegistry(database)
    evidence = EvidenceStore(database)

    async def failing_fetcher(url: str, *, accept=None, **_kwargs):
        body = b"Bad Gateway"
        return FetchResult(
            status=502,
            body=body,
            text=body.decode(),
            final_url=url,
            media_type="text/plain",
            response_headers={"content-type": "text/plain"},
            redirect_chain=(),
        )

    service = PassiveOSINTService(registry, evidence, fetcher=failing_fetcher)
    result = await service._ct("acme.org")

    assert result == {"status": "provider_error", "error": "provider_http_502"}
