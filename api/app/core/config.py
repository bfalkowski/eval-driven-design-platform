from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    service_name: str = "edd-api"
    environment: str = "local"
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    otel_enabled: bool = True
    otel_exporter: Literal["console", "otlp", "none"] = "console"
    otel_otlp_endpoint: str | None = None
    storage_backend: str = "memory"
    database_url: str = "postgresql+asyncpg://edd:edd@localhost:5432/edd"
    auto_create_schema: bool = True
    auth_enabled: bool = False
    auth_issuer: str = "edd-api"
    auth_audience: str = "edd-api"
    auth_demo_secret: str = "local-demo-secret"
    langfuse_enabled: bool = False
    langfuse_host: str = "http://localhost:3001"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_project_name: str = "local-demo"
    lab_default_eval_spec_id: UUID | None = None
    ingest_default_eval_spec_id: UUID | None = None
    ingest_allowed_sources: list[str] = []


def get_settings() -> Settings:
    return Settings()
