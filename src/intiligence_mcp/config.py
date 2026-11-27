"""Runtime configuration with safe defaults."""

from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INTILIGENCE_", env_file=".env", extra="ignore")
    user_agent: str = "IntiligenceMCP/0.1 (+research; contact: operator)"
    request_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    max_response_bytes: int = Field(default=8_000_000, ge=1024, le=50_000_000)
    max_redirects: int = Field(default=5, ge=0, le=10)
    max_tool_output_chars: int = Field(default=12_000, ge=1_000, le=50_000)
    max_evidence_excerpt_chars: int = Field(default=20_000, ge=1, le=20_000)
    min_host_interval_seconds: float = Field(default=1.0, ge=0, le=3600)
    reviewer_id: str = ""
    source_registry_path: str = ".data/sources.sqlite3"
    allow_private_networks: bool = False
    egress_proxy_url: str = ""
    require_egress_proxy: bool = False
    redis_url: str = ""
    require_shared_rate_limiter: bool = False
    require_shared_robots_cache: bool = False
    domain_allowlist: str = ""
    domain_denylist: str = ""
    searxng_url: str = ""
    searxng_timeout_seconds: float = Field(default=10.0, gt=0, le=30)
    max_search_results: int = Field(default=10, ge=1, le=20)
    enable_onion_osint: bool = False
    tor_socks_url: str = ""
    onion_source_allowlist: str = ""
    max_onion_response_bytes: int = Field(default=1_000_000, ge=1024, le=5_000_000)
    refresh_worker_interval_seconds: int = Field(default=60, ge=10, le=3600)
    refresh_worker_batch_size: int = Field(default=10, ge=1, le=100)

    @field_validator("searxng_url")
    @classmethod
    def validate_searxng_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Invalid SearXNG URL") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise ValueError("SearXNG URL must be an HTTP(S) origin/path without credentials")
        return value.rstrip("/")

    @field_validator("tor_socks_url")
    @classmethod
    def validate_tor_socks_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Invalid Tor SOCKS URL") from exc
        if (
            parsed.scheme != "socks5"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1", "tor-gateway", "host.docker.internal"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or port is None
            or not 1 <= port <= 65535
        ):
            raise ValueError("Tor SOCKS URL must target a local, operator-controlled SOCKS5 proxy")
        return value

    def onion_hosts(self) -> set[str]:
        hosts = {item.strip().lower().rstrip(".") for item in self.onion_source_allowlist.split(",") if item.strip()}
        for host in hosts:
            label = host[:-6] if host.endswith(".onion") else ""
            if len(label) != 56 or any(char not in "abcdefghijklmnopqrstuvwxyz234567" for char in label):
                raise ValueError("Onion allowlist entries must be valid v3 .onion hostnames")
        return hosts

    @field_validator("egress_proxy_url")
    @classmethod
    def validate_egress_proxy_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Invalid egress proxy URL") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise ValueError("Egress proxy must be an HTTP(S) origin without credentials or path")
        return value.rstrip("/")

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Invalid Redis URL") from exc
        if (
            parsed.scheme not in {"redis", "rediss"}
            or not parsed.hostname
            or parsed.fragment
            or parsed.query
            or (parsed.path not in {"", "/"} and not parsed.path.lstrip("/").isdigit())
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise ValueError(
                "Redis URL must use redis/rediss with a host and optional database path"
            )
        return value

    def domains(self, raw: str) -> set[str]:
        return {x.strip().lower().rstrip(".") for x in raw.split(",") if x.strip()}


settings = Settings()
