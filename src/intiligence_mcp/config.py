"""Runtime configuration with safe defaults."""

from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INTILIGENCE_", env_file=".env", extra="ignore")
    user_agent: str = "IntiligenceMCP/0.1 (+research; contact: operator)"
    request_timeout_seconds: float = 20.0
    max_response_bytes: int = 8_000_000
    max_redirects: int = 5
    min_host_interval_seconds: float = 1.0
    source_registry_path: str = ".data/sources.sqlite3"
    allow_private_networks: bool = False
    egress_proxy_url: str = ""
    require_egress_proxy: bool = False
    domain_allowlist: str = ""
    domain_denylist: str = ""

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

    def domains(self, raw: str) -> set[str]:
        return {x.strip().lower().rstrip(".") for x in raw.split(",") if x.strip()}


settings = Settings()
