import ipaddress
from pathlib import Path

import pytest

CONFIG = Path(__file__).parents[2] / "deploy" / "egress-proxy" / "squid.conf"


def blocked_networks():
    networks = []
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        if line.startswith("acl blocked_dst dst "):
            networks.extend(
                ipaddress.ip_network(value, strict=False)
                for value in line.split()[3:]
            )
    return networks


def is_blocked(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return any(ip.version == network.version and ip in network for network in blocked_networks())


@pytest.mark.parametrize(
    "address",
    [
        "0.0.0.0",
        "10.1.2.3",
        "100.100.100.200",
        "127.0.0.1",
        "169.254.169.254",
        "172.30.0.1",
        "192.168.1.1",
        "198.18.0.1",
        "224.0.0.1",
        "240.0.0.1",
        "255.255.255.255",
    ],
)
def test_squid_acl_blocks_special_use_ipv4_destinations(address):
    assert is_blocked(address)


@pytest.mark.parametrize(
    "address",
    [
        "::",
        "::1",
        "::ffff:192.168.1.1",
        "64:ff9b::a9fe:a9fe",
        "2001:db8::1",
        "2002::1",
        "fd00::1",
        "fe80::1",
        "ff02::1",
    ],
)
def test_squid_acl_blocks_special_use_ipv6_destinations(address):
    assert is_blocked(address)


@pytest.mark.parametrize("address", ["1.1.1.1", "8.8.8.8", "2606:4700:4700::1111"])
def test_squid_acl_does_not_block_representative_public_addresses(address):
    assert not is_blocked(address)
