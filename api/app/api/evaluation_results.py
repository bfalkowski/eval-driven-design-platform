from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_repository, tenant_query
from app.domain.models import (
    EvaluationResult,
    EvaluationResultListResponse,
    EvaluationResultResponse,
)
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/evaluation-results", tags=["evaluation-results"])


async def _with_case_trace_ids(
    repository: EddRepository,
    *,
    tenant_id: str,
    results: list[EvaluationResult],
) -> list[EvaluationResult]:
    case_traces: dict[UUID, str | None] = {}
    enriched: list[EvaluationResult] = []
    for result in results:
        if result.langfuse_trace_id:
            enriched.append(result)
            continue
        case_id = result.eval_case_id
        if case_id not in case_traces:
            case = await repository.get_eval_case(tenant_id=tenant_id, eval_case_id=case_id)
            case_traces[case_id] = case.langfuse_trace_id
        trace_id = case_traces[case_id]
        if trace_id:
            enriched.append(result.model_copy(update={"langfuse_trace_id": trace_id}))
        else:
            enriched.append(result)
    return enriched


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
    results = await _with_case_trace_ids(repository, tenant_id=tenant_id, results=results)
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
    enriched = await _with_case_trace_ids(repository, tenant_id=tenant_id, results=[result])
    return EvaluationResultResponse(**enriched[0].model_dump(), request_id=request.state.request_id)
