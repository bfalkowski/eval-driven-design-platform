from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    repository = getattr(request.app.state, "repository", None)
    if repository is not None and not await repository.health_check():
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(content={"status": "ready"})


legacy_router = APIRouter(tags=["health"])


@legacy_router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@legacy_router.get("/health/ready")
async def ready_legacy(request: Request) -> JSONResponse:
    return await ready(request)
