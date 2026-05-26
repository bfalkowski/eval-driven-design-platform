from __future__ import annotations

from app.core.config import Settings
from app.storage.base import PlatformRepository
from app.storage.in_memory import InMemoryPlatformRepository


async def build_repository(settings: Settings) -> PlatformRepository:
    if settings.storage_backend == "memory":
        return InMemoryPlatformRepository()
    if settings.storage_backend == "postgres":
        from app.storage.postgres import PostgresPlatformRepository

        repository = PostgresPlatformRepository(settings.database_url)
        if settings.auto_create_schema:
            await repository.init_schema()
        return repository
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
