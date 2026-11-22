import asyncio
import socket

import pytest

from intiligence_mcp.security.dns_resolver import PinnedPublicResolver


class FakeLoop:
    def __init__(self, records):
        self.records = records

    async def getaddrinfo(self, *args, **kwargs):
        return self.records


def record(address, family=socket.AF_INET):
    sockaddr = (address, 443) if family == socket.AF_INET else (address, 443, 0, 0)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


def test_resolver_returns_the_checked_numeric_addresses(monkeypatch):
    loop = FakeLoop([record("1.1.1.1"), record("8.8.8.8")])
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    result = asyncio.run(PinnedPublicResolver().resolve("example.org", 443, socket.AF_UNSPEC))

    assert [item["host"] for item in result] == ["1.1.1.1", "8.8.8.8"]
    assert all(item["hostname"] == "example.org" for item in result)


def test_resolver_rejects_mixed_public_and_private_dns_answers(monkeypatch):
    loop = FakeLoop([record("1.1.1.1"), record("127.0.0.1")])
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    with pytest.raises(OSError, match="non-public"):
        asyncio.run(PinnedPublicResolver().resolve("rebind.example", 443, socket.AF_UNSPEC))


def test_resolver_rejects_metadata_ip(monkeypatch):
    loop = FakeLoop([record("169.254.169.254")])
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    with pytest.raises(OSError, match="non-public"):
        asyncio.run(PinnedPublicResolver().resolve("metadata.example", 80, socket.AF_UNSPEC))


def test_private_addresses_require_explicit_opt_in(monkeypatch):
    loop = FakeLoop([record("10.0.0.8")])
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    result = asyncio.run(
        PinnedPublicResolver(allow_private=True).resolve("internal.example", 443, socket.AF_UNSPEC)
    )

    assert result[0]["host"] == "10.0.0.8"
