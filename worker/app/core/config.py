from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    service_name: str = "edd-worker"
    environment: str = "local"
    log_level: str = "INFO"
    otel_enabled: bool = True
    otel_exporter: Literal["console", "otlp", "none"] = "console"
    otel_otlp_endpoint: str | None = None


def get_settings() -> Settings:
    return Settings()
