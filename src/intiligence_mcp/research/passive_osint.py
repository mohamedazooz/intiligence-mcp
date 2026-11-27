"""Passive domain intelligence adapters with provenance and privacy minimization."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import re
import sqlite3
from typing import Any
from urllib.parse import quote, urlencode, urljoin

from intiligence_mcp.acquisition.http import FetchResult, fetch_response_details
from intiligence_mcp.storage.evidence import EvidenceStore
from intiligence_mcp.storage.source_registry import SourceRegistry

DNS_TYPES: tuple[tuple[str, int], ...] = (
    ("A", 1),
    ("AAAA", 28),
    ("CNAME", 5),
    ("MX", 15),
    ("NS", 2),
    ("CAA", 257),
)
RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
DNS_JSON_URL = "https://dns.google/resolve"
CT_SEARCH_URL = "https://crt.sh/"
_MAX_DNS_RECORDS = 100
_MAX_CT_ROWS = 100
_MAX_CT_NAMES = 500
_DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class PassiveOSINTError(ValueError):
    """Invalid domain or unusable passive-intelligence provider response."""


def normalize_domain(value: str) -> str:
    """Return a normalized public DNS name; reject IPs, wildcards and local names."""
    if not isinstance(value, str):
        raise TypeError("domain must be text")
    candidate = value.strip().rstrip(".")
    if not candidate or len(candidate) > 253 or "*" in candidate:
        raise PassiveOSINTError("A fully-qualified domain name is required")
    try:
        ipaddress.ip_address(candidate.strip("[]"))
    except ValueError:
        pass
    else:
        raise PassiveOSINTError("IP literals are not accepted by domain inspection")
    try:
        ascii_name = candidate.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise PassiveOSINTError("Domain is not valid IDNA") from exc
    labels = ascii_name.split(".")
    if len(labels) < 2 or len(ascii_name) > 253:
        raise PassiveOSINTError("A public multi-label domain name is required")
    if any(len(label) > 63 or not _DOMAIN_LABEL.fullmatch(label) for label in labels):
        raise PassiveOSINTError("Domain contains an invalid DNS label")
    if labels[-1] in {"localhost", "local", "internal", "test", "invalid", "example"}:
        raise PassiveOSINTError("Local, reserved, and example domains are not queried")
    return ascii_name


def find_rdap_base(domain: str, bootstrap: dict[str, Any]) -> str | None:
    """Apply RFC 9224 label-wise longest-match selection to IANA bootstrap data."""
    services = bootstrap.get("services")
    if not isinstance(services, list):
        raise PassiveOSINTError("IANA RDAP bootstrap has no valid services array")
    labels = domain.lower().rstrip(".").split(".")
    candidates: list[tuple[int, str]] = []
    for service in services:
        if not isinstance(service, list) or len(service) != 2:
            continue
        suffixes, urls = service
        if not isinstance(suffixes, list) or not isinstance(urls, list):
            continue
        for suffix in suffixes:
            if not isinstance(suffix, str):
                continue
            suffix_labels = suffix.lower().rstrip(".").split(".")
            if len(suffix_labels) <= len(labels) and labels[-len(suffix_labels) :] == suffix_labels:
                for base in urls:
                    if isinstance(base, str) and base.startswith("https://"):
                        candidates.append((len(suffix_labels), base))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def sanitize_rdap_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop registrant/entity contact data and retain only technical registration facts."""
    output: dict[str, Any] = {}
    for key in ("objectClassName", "handle", "ldhName", "unicodeName"):
        value = payload.get(key)
        if isinstance(value, str):
            output[key] = value[:512]
    status = payload.get("status")
    if isinstance(status, list):
        output["status"] = [item[:128] for item in status if isinstance(item, str)][:50]
    events = payload.get("events")
    if isinstance(events, list):
        safe_events = []
        for event in events[:50]:
            if not isinstance(event, dict):
                continue
            action = event.get("eventAction")
            date = event.get("eventDate")
            if isinstance(action, str) and isinstance(date, str):
                safe_events.append({"eventAction": action[:128], "eventDate": date[:64]})
        output["events"] = safe_events
    nameservers = payload.get("nameservers")
    if isinstance(nameservers, list):
        output["nameservers"] = [
            {
                key: value[:253]
                for key in ("ldhName", "unicodeName")
                if isinstance(value := item.get(key), str)
            }
            for item in nameservers[:100]
            if isinstance(item, dict)
        ]
    output["privacy"] = {
        "contact_entities_retained": False,
        "vcard_contact_fields_retained": False,
        "redaction": "RDAP entity/contact/vCard/remarks/notices/publicIds omitted",
    }
    return output


def parse_ct_results(payload: Any, domain: str) -> dict[str, Any]:
    """Keep certificate metadata and DNS names scoped to the requested domain."""
    if not isinstance(payload, list):
        raise PassiveOSINTError("Certificate Transparency response must be a JSON array")
    names: set[str] = set()
    certificates: list[dict[str, str]] = []

    def add_name(raw: str) -> str | None:
        name = raw.strip().lower().rstrip(".").removeprefix("*.")
        try:
            normalized = name.encode("idna").decode("ascii")
        except UnicodeError:
            return None
        if (
            len(normalized) > 253
            or not all(_DOMAIN_LABEL.fullmatch(label) for label in normalized.split("."))
            or not (normalized == domain or normalized.endswith("." + domain))
        ):
            return None
        if normalized not in names and len(names) >= _MAX_CT_NAMES:
            return None
        names.add(normalized)
        return normalized

    for row in payload[:_MAX_CT_ROWS]:
        if not isinstance(row, dict):
            continue
        row_names: set[str] = set()
        for field in ("name_value", "common_name"):
            value = row.get(field)
            if isinstance(value, str):
                for candidate in value.splitlines():
                    normalized_name = add_name(candidate)
                    if normalized_name is not None:
                        row_names.add(normalized_name)
        if row_names:
            certificate: dict[str, str] = {}
            for key in ("id", "issuer_name", "not_before", "not_after"):
                value = row.get(key)
                if isinstance(value, (str, int)):
                    certificate[key] = str(value)[:512]
            certificate["matching_names"] = ", ".join(sorted(row_names)[:20])
            certificates.append(certificate)

    return {
        "status": "ok",
        "entries_considered": min(len(payload), _MAX_CT_ROWS),
        "matching_certificate_count": len(certificates),
        "names": sorted(names),
        "certificates": certificates[:_MAX_CT_ROWS],
        "interpretation": (
            "A CT entry shows a name appeared in a logged certificate; "
            "it does not prove current control or ownership of that name."
        ),
    }


class PassiveOSINTService:
    """DNS, RDAP and CT collection; all successful provider results become evidence."""

    def __init__(
        self,
        source_registry: SourceRegistry,
        evidence_store: EvidenceStore,
        *,
        fetcher=fetch_response_details,
    ) -> None:
        self.source_registry = source_registry
        self.evidence_store = evidence_store
        self.fetcher = fetcher
        self._bootstrap_cache: dict[str, Any] | None = None
        self._bootstrap_lock = asyncio.Lock()

    def _persist(
        self,
        provider_url: str,
        title: str,
        payload: Any,
        *,
        response: FetchResult,
        media_type: str = "application/json",
        privacy_note: str = "provider response normalized for evidence",
    ) -> dict[str, Any]:
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        # Store the bounded normalized representation, not a possibly sensitive provider body.
        source = self.source_registry.add(response.final_url or provider_url, title)
        capture = self.evidence_store.capture(
            source.source_id,
            content.encode("utf-8"),
            content,
            media_type=media_type,
            http_status=response.status,
            final_url=response.final_url,
            response_headers=response.response_headers,
            redirect_chain=list(response.redirect_chain),
            extractor_name="passive-osint-json-normalizer",
            extractor_version="1",
        )
        return {
            "source_id": source.source_id,
            "artifact_id": capture.artifact_id,
            "evidence_id": capture.evidence_id,
            "raw_sha256": capture.raw_sha256,
            "captured_at": capture.captured_at,
            "provider_url": provider_url,
            "final_url": response.final_url,
            "http_status": response.status,
            "response_media_type": response.media_type,
            "response_redirect_count": str(len(response.redirect_chain)),
            "stored_representation": "privacy_minimized_normalized_json",
            "privacy_note": privacy_note,
        }

    @staticmethod
    def _provider_error(exc: Exception) -> str:
        """Return a bounded, credential-safe provider failure reason."""
        message = " ".join(str(exc).split())
        return message[:180] if message else type(exc).__name__

    async def _json(self, url: str, *, accept: str = "application/json") -> tuple[Any, FetchResult]:
        response = await self.fetcher(url, accept=accept)
        if response.status < 200 or response.status >= 300:
            raise PassiveOSINTError(f"provider_http_{response.status}")
        try:
            payload = json.loads(response.text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PassiveOSINTError("provider_invalid_json") from exc
        return payload, response

    async def _dns_query(self, domain: str, record_name: str, record_type: int) -> dict[str, Any]:
        url = f"{DNS_JSON_URL}?{urlencode({'name': domain, 'type': record_type})}"
        try:
            payload, response = await self._json(url, accept="application/dns-json")
            if not isinstance(payload, dict) or not isinstance(payload.get("Status"), int):
                raise PassiveOSINTError("dns_invalid_response")
            answers = payload.get("Answer")
            records = []
            if isinstance(answers, list):
                for item in answers[:_MAX_DNS_RECORDS]:
                    if not isinstance(item, dict):
                        continue
                    data = item.get("data")
                    ttl = item.get("TTL")
                    if isinstance(data, str) and isinstance(ttl, int):
                        records.append(
                            {
                                "name": str(item.get("name", ""))[:253],
                                "type": record_name,
                                "ttl": max(0, ttl),
                                "data": data[:2048],
                            }
                        )
            result = {
                "status": "ok",
                "dns_rcode": payload["Status"],
                "dnssec_validated": bool(payload.get("AD", False)),
                "records": records,
            }
            evidence = self._persist(
                url,
                f"Google Public DNS {record_name} record query for {domain}",
                result,
                response=response,
                media_type="application/vnd.intiligence.dns+json",
                privacy_note="TXT and EDNS client-subnet data are not requested",
            )
            result["provenance"] = evidence
            return result
        except (OSError, RuntimeError, sqlite3.Error, TypeError, ValueError) as exc:
            return {
                "status": "provider_error",
                "error": self._provider_error(exc),
                "records": [],
            }

    async def _get_bootstrap(self) -> dict[str, Any]:
        async with self._bootstrap_lock:
            if self._bootstrap_cache is not None:
                return self._bootstrap_cache
            payload, response = await self._json(RDAP_BOOTSTRAP_URL)
            if not isinstance(payload, dict):
                raise PassiveOSINTError("rdap_bootstrap_invalid")
            self._persist(
                RDAP_BOOTSTRAP_URL,
                "IANA RDAP DNS bootstrap registry",
                payload,
                response=response,
                media_type="application/rdap-bootstrap+json",
                privacy_note="public IANA service-discovery registry",
            )
            self._bootstrap_cache = payload
            return payload

    async def _rdap(self, domain: str) -> dict[str, Any]:
        try:
            bootstrap = await self._get_bootstrap()
            base = find_rdap_base(domain, bootstrap)
            if base is None:
                return {"status": "unsupported_tld"}
            url = urljoin(base.rstrip("/") + "/", f"domain/{quote(domain, safe='')}")
            payload, response = await self._json(
                url, accept="application/rdap+json, application/json"
            )
            if not isinstance(payload, dict):
                raise PassiveOSINTError("rdap_invalid_response")
            returned_domain = payload.get("ldhName")
            if (
                not isinstance(returned_domain, str)
                or returned_domain.rstrip(".").lower() != domain
            ):
                raise PassiveOSINTError("rdap_domain_mismatch")
            sanitized = sanitize_rdap_payload(payload)
            evidence = self._persist(
                url,
                f"Privacy-minimized RDAP registration data for {domain}",
                sanitized,
                response=response,
                media_type="application/rdap+json; profile=privacy-minimized",
                privacy_note="Contact entities, vCards, email, phone, address and remarks omitted",
            )
            return {
                "status": "ok",
                "authoritative_base": base,
                "response_media_type": response.media_type,
                "data": sanitized,
                "provenance": evidence,
            }
        except (OSError, RuntimeError, sqlite3.Error, TypeError, ValueError) as exc:
            return {"status": "provider_error", "error": self._provider_error(exc)}

    async def _ct(self, domain: str) -> dict[str, Any]:
        url = f"{CT_SEARCH_URL}?{urlencode({'q': '%.' + domain, 'output': 'json'})}"
        try:
            payload, response = await self._json(url, accept="application/json")
            result = parse_ct_results(payload, domain)
            evidence = self._persist(
                url,
                f"Certificate Transparency search for {domain}",
                result,
                response=response,
                media_type="application/vnd.intiligence.ct+json",
                privacy_note="Only matching DNS names and bounded certificate metadata retained",
            )
            result["provenance"] = evidence
            return result
        except (OSError, RuntimeError, sqlite3.Error, TypeError, ValueError) as exc:
            return {"status": "provider_error", "error": self._provider_error(exc)}

    async def inspect_domain(self, value: str) -> dict[str, Any]:
        """Collect bounded passive DNS, RDAP and CT observations for one public domain."""
        domain = normalize_domain(value)
        dns_results = await asyncio.gather(
            *(self._dns_query(domain, name, record_type) for name, record_type in DNS_TYPES)
        )
        rdap, ct = await asyncio.gather(self._rdap(domain), self._ct(domain))
        providers_ok = sum(
            item.get("status") in {"ok", "supported_tld"} for item in [*dns_results, rdap, ct]
        )
        return {
            "status": "ok" if providers_ok else "providers_unavailable",
            "domain": domain,
            "collection_mode": "passive_only",
            "providers": {
                "dns": {name: result for (name, _), result in zip(DNS_TYPES, dns_results)},
                "rdap": rdap,
                "certificate_transparency": ct,
            },
            "provider_success_count": providers_ok,
            "provider_count": len(DNS_TYPES) + 2,
            "safety_notes": [
                "No port scanning, brute force, authentication, or access-control bypass is performed.",
                "DNS observations are resolver answers and may be cached or location-dependent.",
                "Certificate Transparency names are discovery leads, not proof of ownership.",
                "RDAP contact/entity fields are excluded before storage.",
            ],
        }
