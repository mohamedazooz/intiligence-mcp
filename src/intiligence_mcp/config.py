"""Runtime configuration with safe defaults."""

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
    domain_allowlist: str = ""
    domain_denylist: str = ""

    def domains(self, raw: str) -> set[str]:
        return {x.strip().lower().rstrip(".") for x in raw.split(",") if x.strip()}


settings = Settings()
