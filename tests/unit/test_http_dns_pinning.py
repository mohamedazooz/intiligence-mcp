import asyncio
import socket

import pytest
from aiohttp.abc import AbstractResolver

from intiligence_mcp.acquisition import http
from intiligence_mcp.config import settings
from intiligence_mcp.security.url_policy import URLPolicyError


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


@pytest.mark.asyncio
async def test_http_acquisition_routes_through_configured_proxy(monkeypatch):
    request_lines = []
    resolver_options = []

    async def proxy_handler(reader, writer):
        request_lines.append((await reader.readline()).decode().strip())
        while await reader.readline() not in (b"\r\n", b""):
            pass
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(proxy_handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async def no_wait(_host):
        return None

    def resolver_factory(**kwargs):
        resolver_options.append(kwargs)
        return LoopbackResolver()

    monkeypatch.setattr(http, "PinnedPublicResolver", resolver_factory)
    monkeypatch.setattr(http, "validate_url", lambda _url, **_kwargs: "public.test")
    monkeypatch.setattr(http._host_limiter, "wait", no_wait)
    monkeypatch.setattr(settings, "allow_private_networks", False)
    monkeypatch.setattr(settings, "require_egress_proxy", True)
    monkeypatch.setattr(settings, "egress_proxy_url", f"http://proxy.test:{port}")

    try:
        body, final_url = await http.fetch_url("http://public.test/resource")
        assert body == "ok"
        assert final_url == "http://public.test/resource"
        assert request_lines == ["GET http://public.test/resource HTTP/1.1"]
        assert resolver_options == [{"allow_private": True}]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_http_redirect_to_private_is_rejected_before_second_request(monkeypatch):
    request_lines = []

    async def redirect_handler(reader, writer):
        request_lines.append((await reader.readline()).decode().strip())
        while await reader.readline() not in (b"\r\n", b""):
            pass
        writer.write(
            b"HTTP/1.1 302 Found\r\n"
            b"Location: http://169.254.169.254/latest/meta-data/\r\n"
            b"Content-Length: 0\r\nConnection: close\r\n\r\n"
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(redirect_handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    original_validate = http.validate_url

    def validate_redirect_hop(url, **kwargs):
        if url.startswith(f"http://redirect.test:{port}/"):
            return "redirect.test"
        return original_validate(url, **kwargs)

    async def no_wait(_host):
        return None

    monkeypatch.setattr(http, "PinnedPublicResolver", lambda **_kwargs: LoopbackResolver())
    monkeypatch.setattr(http, "validate_url", validate_redirect_hop)
    monkeypatch.setattr(http._host_limiter, "wait", no_wait)
    monkeypatch.setattr(settings, "allow_private_networks", False)
    monkeypatch.setattr(settings, "require_egress_proxy", False)
    monkeypatch.setattr(settings, "egress_proxy_url", "")

    try:
        with pytest.raises(URLPolicyError):
            await http.fetch_response(
                f"http://redirect.test:{port}/start",
                max_redirects=1,
            )
        assert request_lines == ["GET /start HTTP/1.1"]
    finally:
        server.close()
        await server.wait_closed()
