from omnipulse.router import classify


def test_router_build():
    assert "BUILD" in classify("build fastapi rust project", "auto")


def test_router_osint():
    assert "OSINT_DARK" in classify("check domain example.com leak", "auto")


def test_router_mode_override():
    assert classify("anything", "build") == ["BUILD"]
