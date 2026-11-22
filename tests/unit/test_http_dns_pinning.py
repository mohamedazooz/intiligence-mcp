import asyncio
import socket

import pytest
from aiohttp.abc import AbstractResolver

from intiligence_mcp.acquisition import http
from intiligence_mcp.config import settings


class LoopbackResolver(AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_INET):
        return [
            {
                "hostname": host,
                "host": "127.0.0.1",
                "port": port,
                "family": socket.AF_INET,
                "proto": socket.IPPROTO_TCP,
                "flags": 0,
            }
        ]

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_http_connector_uses_resolver_returned_ip(monkeypatch):
    async def handler(reader, writer):
        while await reader.readline() not in (b"\r\n", b""):
            pass
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async def no_wait(_host):
        return None

    monkeypatch.setattr(http, "PinnedPublicResolver", lambda **_kwargs: LoopbackResolver())
    monkeypatch.setattr(http, "validate_url", lambda _url, **_kwargs: "rebind.test")
    monkeypatch.setattr(http._host_limiter, "wait", no_wait)
    monkeypatch.setattr(settings, "allow_private_networks", True)

    try:
        body, final_url = await http.fetch_url(f"http://rebind.test:{port}/proof")
        assert body == "ok"
        assert final_url == f"http://rebind.test:{port}/proof"
    finally:
        server.close()
        await server.wait_closed()
