import asyncio
import socket

import pytest
from aiohttp.abc import AbstractResolver

from intiligence_mcp.acquisition import http
from intiligence_mcp.acquisition.http import AcquisitionPolicyDenied
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


async def _start_redirect_server():
    request_paths = []

    async def handler(reader, writer):
        request_line = (await reader.readline()).decode().strip()
        path = request_line.split(" ")[1]
        request_paths.append(path)
        while await reader.readline() not in (b"\r\n", b""):
            pass
        if path == "/start":
            response = (
                b"HTTP/1.1 302 Found\r\n"
                b"Location: /final\r\n"
                b"Content-Length: 0\r\nConnection: close\r\n\r\n"
            )
        else:
            response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
        writer.write(response)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1], request_paths


def _patch_transport(monkeypatch, port):
    async def no_wait(_host):
        return None

    monkeypatch.setattr(http, "PinnedPublicResolver", lambda **_kwargs: LoopbackResolver())
    monkeypatch.setattr(http, "validate_url", lambda _url, **_kwargs: "redirect.test")
    monkeypatch.setattr(http._host_limiter, "wait", no_wait)
    monkeypatch.setattr(settings, "allow_private_networks", False)
    monkeypatch.setattr(settings, "require_egress_proxy", False)
    monkeypatch.setattr(settings, "egress_proxy_url", "")


@pytest.mark.asyncio
async def test_policy_is_checked_for_initial_and_each_redirect_url(monkeypatch):
    server, port, request_paths = await _start_redirect_server()
    checked_urls = []

    async def policy_check(url):
        checked_urls.append(url)
        return True

    _patch_transport(monkeypatch, port)
    try:
        result = await http.fetch_response_details(
            f"http://redirect.test:{port}/start",
            max_redirects=1,
            policy_check=policy_check,
        )
        assert result.status == 200
        assert result.text == "ok"
        assert request_paths == ["/start", "/final"]
        assert checked_urls == [
            f"http://redirect.test:{port}/start",
            f"http://redirect.test:{port}/final",
        ]
        assert result.redirect_chain == (
            {
                "status": 302,
                "from": f"http://redirect.test:{port}/start",
                "to": f"http://redirect.test:{port}/final",
            },
        )
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_denied_redirect_policy_stops_before_second_request(monkeypatch):
    server, port, request_paths = await _start_redirect_server()
    checked_urls = []

    async def policy_check(url):
        checked_urls.append(url)
        return url.endswith("/start")

    _patch_transport(monkeypatch, port)
    try:
        with pytest.raises(AcquisitionPolicyDenied):
            await http.fetch_response_details(
                f"http://redirect.test:{port}/start",
                max_redirects=1,
                policy_check=policy_check,
            )
        assert request_paths == ["/start"]
        assert checked_urls[-1].endswith("/final")
    finally:
        server.close()
        await server.wait_closed()
