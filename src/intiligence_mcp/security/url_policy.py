"""SSRF-aware URL validation; DNS results are checked on every redirect hop."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


class URLPolicyError(ValueError):
    pass


def _is_public_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return ip.is_global and not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_url(
    url: str,
    *,
    allow_private: bool = False,
    allowlist: set[str] | None = None,
    denylist: set[str] | None = None,
    allow_temporary_dns_failure: bool = False,
) -> str:
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise URLPolicyError("Only http and https URLs are permitted")
        if not parsed.hostname or parsed.username or parsed.password:
            raise URLPolicyError("URL must contain a host and no embedded credentials")
        host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
        if any(host == denied or host.endswith("." + denied) for denied in (denylist or set())):
            raise URLPolicyError("Host is denied by policy")
        if (
            allowlist
            and host not in allowlist
            and not any(host.endswith("." + d) for d in allowlist)
        ):
            raise URLPolicyError("Host is not in the configured allowlist")
        port = parsed.port
        if port is not None and not (1 <= port <= 65535):
            raise URLPolicyError("Invalid port")
    except URLPolicyError:
        raise
    except (UnicodeError, ValueError) as exc:
        raise URLPolicyError("Malformed URL") from exc
    if allow_private:
        return host
    try:
        literal = ipaddress.ip_address(host)
        addresses = {str(literal)}
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host, port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM
            )
            addresses = {str(record[4][0]).split("%", 1)[0] for record in records}
        except socket.gaierror as exc:
            if allow_temporary_dns_failure and exc.errno == socket.EAI_AGAIN:
                # In an isolated proxy-only network, the app may have no direct DNS route.
                # The mandatory egress proxy resolves the hostname and enforces destination ACLs.
                return host
            raise URLPolicyError("Host DNS resolution failed") from exc
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise URLPolicyError("Host resolves to a non-public or unsafe IP address")
    return host
