from __future__ import annotations

from fastapi import APIRouter, Request

from app.domain.models import LangfuseHealthResponse
from app.integrations.langfuse_client import LangfuseClientAdapter

router = APIRouter(prefix="/v1/integrations/langfuse", tags=["integrations"])


def get_langfuse_adapter(request: Request) -> LangfuseClientAdapter:
    return request.app.state.langfuse_adapter


@router.get("/health", response_model=LangfuseHealthResponse)
async def langfuse_health(request: Request) -> LangfuseHealthResponse:
    adapter = get_langfuse_adapter(request)
    result = await adapter.get_health()
    return LangfuseHealthResponse(
        enabled=result.enabled,
        configured=result.configured,
        status=result.status,
        host=result.host,
        reachable=result.reachable,
        authenticated=result.authenticated,
        project_count=result.project_count,
        project_name=request.app.state.settings.langfuse_project_name,
        message=result.message,
        request_id=request.state.request_id,
    )
