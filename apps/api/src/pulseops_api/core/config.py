from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PulseOps API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://pulseops:pulseops@localhost:5432/pulseops"
    )
    max_upload_bytes: int = 10 * 1024 * 1024

    auth_session_minutes: int = 480
    auth_cookie_name: str = "pulseops_session"
    auth_cookie_secure: bool = False
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_prefix="PULSEOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_frontend_origins(self) -> list[str]:
        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
