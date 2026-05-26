from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_repository, tenant_query
from app.domain.models import EvaluationResultListResponse, EvaluationResultResponse
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/evaluation-results", tags=["evaluation-results"])


@router.get("", response_model=EvaluationResultListResponse)
async def list_evaluation_results(
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    experiment_run_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    repository: EddRepository = Depends(get_repository),
) -> EvaluationResultListResponse:
    results = await repository.list_evaluation_results(
        tenant_id=tenant_id,
        experiment_run_id=experiment_run_id,
        limit=limit,
    )
    return EvaluationResultListResponse(
        evaluation_results=results,
        request_id=request.state.request_id,
    )


@router.get("/{evaluation_result_id}", response_model=EvaluationResultResponse)
async def get_evaluation_result(
    evaluation_result_id: UUID,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> EvaluationResultResponse:
    result = await repository.get_evaluation_result(
        tenant_id=tenant_id,
        evaluation_result_id=evaluation_result_id,
    )
    return EvaluationResultResponse(**result.model_dump(), request_id=request.state.request_id)
