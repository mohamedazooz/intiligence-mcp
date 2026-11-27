import pytest
from omnipulse.guard import is_public_ip, validate_url


def test_ssrf_loopback():
    ok, _ = validate_url("http://127.0.0.1/x")
    assert not ok


def test_ssrf_metadata():
    ok, _ = validate_url("http://169.254.169.254/latest/meta-data/")
    assert not ok


def test_ssrf_private():
    ok, _ = validate_url("http://192.168.1.1/x")
    assert not ok


def test_public_ip_allowed():
    assert is_public_ip("8.8.8.8")
