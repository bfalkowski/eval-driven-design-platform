from __future__ import annotations

import json
from typing import Any, cast

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_repository, tenant_from_context_or_request
from app.core.auth import RequestContext, get_request_context
from app.core.errors import BadRequestError
from app.domain.models import (
    EvalCaseResponse,
    ImportLangfuseTraceRequest,
    LangfuseHealthResponse,
    LangfuseTracePreview,
    LangfuseTraceResponse,
)
from app.integrations.langfuse_client import LangfuseClientAdapter
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/integrations/langfuse", tags=["integrations"])


def get_langfuse_adapter(request: Request) -> LangfuseClientAdapter:
    return cast(LangfuseClientAdapter, request.app.state.langfuse_adapter)


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


@router.get("/traces/{trace_id}", response_model=LangfuseTraceResponse)
async def langfuse_trace(
    trace_id: str,
    request: Request,
) -> LangfuseTraceResponse:
    adapter = get_langfuse_adapter(request)
    result = await adapter.get_trace(trace_id=trace_id)
    if not result.success or result.trace is None:
        raise BadRequestError(result.message)
    return LangfuseTraceResponse(
        trace=_to_trace_preview(trace_id, result.trace),
        request_id=request.state.request_id,
    )


@router.post("/import-case", status_code=status.HTTP_201_CREATED, response_model=EvalCaseResponse)
async def import_langfuse_trace_case(
    payload: ImportLangfuseTraceRequest,
    request: Request,
    repository: EddRepository = Depends(get_repository),
    context: RequestContext | None = Depends(get_request_context),
) -> EvalCaseResponse:
    adapter = get_langfuse_adapter(request)
    trace_result = await adapter.get_trace(trace_id=payload.trace_id)
    if not trace_result.success or trace_result.trace is None:
        raise BadRequestError(trace_result.message)

    tenant_id = tenant_from_context_or_request(context, payload.tenant_id)
    case = await repository.create_eval_case(
        tenant_id=tenant_id,
        eval_spec_id=payload.eval_spec_id,
        name=payload.name or _default_case_name(trace_result.trace, payload.trace_id),
        input_payload=_trace_input_payload(trace_result.trace, payload.trace_id),
        notes=payload.notes,
        source="langfuse_import",
        langfuse_trace_id=payload.trace_id,
    )
    return EvalCaseResponse(**case.model_dump(), request_id=request.state.request_id)


def _to_trace_preview(trace_id: str, trace: dict[str, Any]) -> LangfuseTracePreview:
    return LangfuseTracePreview(
        trace_id=trace_id,
        name=_optional_str(trace.get("name")),
        timestamp=_optional_str(trace.get("timestamp") or trace.get("createdAt")),
        input_preview=_input_preview(trace.get("input")),
        has_observations=bool(_extract_observations(trace)),
    )


def _trace_input_payload(trace: dict[str, Any], trace_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"langfuse_trace_id": trace_id}
    trace_input = trace.get("input")
    if trace_input is not None:
        payload["trace_input"] = trace_input
    observations = _extract_observations(trace)
    if observations:
        payload["observation_count"] = len(observations)
    return payload


def _extract_observations(trace: dict[str, Any]) -> list[Any]:
    observations = trace.get("observations")
    if isinstance(observations, list):
        return observations
    return []


def _default_case_name(trace: dict[str, Any], trace_id: str) -> str:
    trace_name = _optional_str(trace.get("name"))
    if trace_name:
        return f"Imported trace: {trace_name}"
    return f"Imported trace {trace_id[:8]}"


def _optional_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _input_preview(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value[:240]
    try:
        return json.dumps(value, sort_keys=True)[:240]
    except TypeError:
        return str(value)[:240]
