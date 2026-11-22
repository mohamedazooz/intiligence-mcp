"""DNS resolver that validates and pins the exact addresses used by aiohttp."""

from __future__ import annotations

import asyncio
import ipaddress
import socket

from aiohttp.abc import AbstractResolver, ResolveResult


def _is_public_ip(value: str) -> bool:
    address = ipaddress.ip_address(value.split("%", 1)[0])
    return address.is_global and not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


class PinnedPublicResolver(AbstractResolver):
    """Resolve once per connector cache entry and return only the checked IPs.

    aiohttp connects to the returned numeric addresses while retaining the
    original URL hostname for HTTP Host and TLS certificate/SNI validation.
    """

    def __init__(self, *, allow_private: bool = False) -> None:
        self._allow_private = allow_private

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[ResolveResult]:
        loop = asyncio.get_running_loop()
        try:
            records = await loop.getaddrinfo(
                host,
                port,
                family=family,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        except OSError as exc:
            raise OSError("DNS resolution failed; outbound request denied") from exc

        resolved: list[ResolveResult] = []
        seen: set[tuple[int, str]] = set()
        for address_family, socktype, proto, _canonname, sockaddr in records:
            address = str(sockaddr[0]).split("%", 1)[0]
            if not self._allow_private and not _is_public_ip(address):
                raise OSError("DNS returned a non-public address; outbound request denied")
            key = (address_family, address)
            if key in seen:
                continue
            seen.add(key)
            resolved.append(
                {
                    "hostname": host,
                    "host": address,
                    "port": port,
                    "family": address_family,
                    "proto": proto or socket.IPPROTO_TCP,
                    "flags": 0,
                }
            )
        if not resolved:
            raise OSError("DNS returned no usable addresses; outbound request denied")
        return resolved

    async def close(self) -> None:
        return None
