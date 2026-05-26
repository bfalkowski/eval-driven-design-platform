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
    CreateEvalSpecRequest,
    EvalSpecListResponse,
    EvalSpecResponse,
    UpdateEvalSpecRequest,
)
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/eval-specs", tags=["eval-specs"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EvalSpecResponse)
async def create_eval_spec(
    payload: CreateEvalSpecRequest,
    request: Request,
    repository: EddRepository = Depends(get_repository),
    context: RequestContext | None = Depends(get_request_context),
) -> EvalSpecResponse:
    tenant_id = tenant_from_context_or_request(context, payload.tenant_id)
    spec = await repository.create_eval_spec(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        version=payload.version,
        rubric=payload.rubric,
        pass_threshold=payload.pass_threshold,
        judge_config=payload.judge_config,
    )
    return EvalSpecResponse(**spec.model_dump(), request_id=request.state.request_id)


@router.get("", response_model=EvalSpecListResponse)
async def list_eval_specs(
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    repository: EddRepository = Depends(get_repository),
) -> EvalSpecListResponse:
    specs = await repository.list_eval_specs(tenant_id=tenant_id, limit=limit)
    return EvalSpecListResponse(
        eval_specs=specs,
        request_id=request.state.request_id,
    )


@router.get("/{eval_spec_id}", response_model=EvalSpecResponse)
async def get_eval_spec(
    eval_spec_id: UUID,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> EvalSpecResponse:
    spec = await repository.get_eval_spec(tenant_id=tenant_id, eval_spec_id=eval_spec_id)
    return EvalSpecResponse(**spec.model_dump(), request_id=request.state.request_id)


@router.patch("/{eval_spec_id}", response_model=EvalSpecResponse)
async def update_eval_spec(
    eval_spec_id: UUID,
    payload: UpdateEvalSpecRequest,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> EvalSpecResponse:
    spec = await repository.update_eval_spec(
        tenant_id=tenant_id,
        eval_spec_id=eval_spec_id,
        updates=non_empty_updates(payload.model_dump()),
    )
    return EvalSpecResponse(**spec.model_dump(), request_id=request.state.request_id)


@router.delete("/{eval_spec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eval_spec(
    eval_spec_id: UUID,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> None:
    await repository.delete_eval_spec(tenant_id=tenant_id, eval_spec_id=eval_spec_id)
