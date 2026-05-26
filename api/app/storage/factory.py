from __future__ import annotations

from app.core.config import Settings
from app.storage.base import EddRepository
from app.storage.in_memory import InMemoryEddRepository


async def build_repository(settings: Settings) -> EddRepository:
    if settings.storage_backend == "memory":
        return InMemoryEddRepository()
    if settings.storage_backend == "postgres":
        from app.storage.postgres import PostgresEddRepository

        repository = PostgresEddRepository(settings.database_url)
        if settings.auto_create_schema:
            await repository.init_schema()
        return repository
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
