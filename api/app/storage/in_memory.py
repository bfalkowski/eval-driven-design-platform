from __future__ import annotations


class InMemoryPlatformRepository:
    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        return None
