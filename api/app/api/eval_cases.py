from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    get_repository,
    non_empty_updates,
    tenant_from_context_or_request,
    tenant_query,
)
from app.core.auth import RequestContext, get_request_context
from app.domain.models import (
    CreateEvalCaseRequest,
    EvalCaseListResponse,
    EvalCaseResponse,
    UpdateEvalCaseRequest,
)
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/eval-cases", tags=["eval-cases"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EvalCaseResponse)
async def create_eval_case(
    payload: CreateEvalCaseRequest,
    request: Request,
    repository: EddRepository = Depends(get_repository),
    context: RequestContext | None = Depends(get_request_context),
) -> EvalCaseResponse:
    tenant_id = tenant_from_context_or_request(context, payload.tenant_id)
    case = await repository.create_eval_case(
        tenant_id=tenant_id,
        eval_spec_id=payload.eval_spec_id,
        name=payload.name,
        input_payload=payload.input_payload,
        notes=payload.notes,
        source=payload.source,
        langfuse_trace_id=payload.langfuse_trace_id,
    )
    return EvalCaseResponse(**case.model_dump(), request_id=request.state.request_id)


@router.get("", response_model=EvalCaseListResponse)
async def list_eval_cases(
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    eval_spec_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    repository: EddRepository = Depends(get_repository),
) -> EvalCaseListResponse:
    cases = await repository.list_eval_cases(
        tenant_id=tenant_id,
        eval_spec_id=eval_spec_id,
        limit=limit,
    )
    return EvalCaseListResponse(
        eval_cases=cases,
        request_id=request.state.request_id,
    )


@router.get("/{eval_case_id}", response_model=EvalCaseResponse)
async def get_eval_case(
    eval_case_id: UUID,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> EvalCaseResponse:
    case = await repository.get_eval_case(tenant_id=tenant_id, eval_case_id=eval_case_id)
    return EvalCaseResponse(**case.model_dump(), request_id=request.state.request_id)


@router.patch("/{eval_case_id}", response_model=EvalCaseResponse)
async def update_eval_case(
    eval_case_id: UUID,
    payload: UpdateEvalCaseRequest,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> EvalCaseResponse:
    case = await repository.update_eval_case(
        tenant_id=tenant_id,
        eval_case_id=eval_case_id,
        updates=non_empty_updates(payload.model_dump()),
    )
    return EvalCaseResponse(**case.model_dump(), request_id=request.state.request_id)


@router.delete("/{eval_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eval_case(
    eval_case_id: UUID,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> None:
    await repository.delete_eval_case(tenant_id=tenant_id, eval_case_id=eval_case_id)
