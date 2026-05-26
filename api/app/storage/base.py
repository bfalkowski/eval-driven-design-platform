from __future__ import annotations

from typing import Protocol


class PlatformRepository(Protocol):
    async def health_check(self) -> bool: ...

    async def close(self) -> None: ...
