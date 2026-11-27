import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    searxng_url: str = "http://searxng:8080"
    crawl4ai_url: str = "http://crawl4ai:11235"
    scrapling_url: str = "http://scrapling-worker:8000"
    tor_socks_url: str = "socks5h://tor-proxy:9050"
    sqlite_path: str = "/data/omnipulse.db"
    max_depth: int = 2
    max_pivots: int = 15
    per_adapter_timeout: float = 25.0
    max_response_tokens: int = 8000
    api_token: str = os.getenv("OMNIPULSE_API_TOKEN", "")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
LIMITS_PATH = Path("/app/config/limits.yaml")
