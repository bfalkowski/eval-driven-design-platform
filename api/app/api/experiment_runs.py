from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import get_repository, tenant_from_context_or_request, tenant_query
from app.core.auth import RequestContext, get_request_context
from app.domain.models import (
    CreateExperimentRunRequest,
    ExperimentRunListResponse,
    ExperimentRunResponse,
    ExperimentRunSummaryResponse,
)
from app.integrations.langfuse_client import LangfuseClientAdapter
from app.services.experiment_service import ExperimentService
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/experiment-runs", tags=["experiment-runs"])


def get_experiment_service(request: Request) -> ExperimentService:
    repository = cast(EddRepository, request.app.state.repository)
    langfuse_adapter = cast(LangfuseClientAdapter, request.app.state.langfuse_adapter)
    return ExperimentService(repository, langfuse_adapter)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ExperimentRunResponse)
async def create_experiment_run(
    payload: CreateExperimentRunRequest,
    request: Request,
    service: ExperimentService = Depends(get_experiment_service),
    context: RequestContext | None = Depends(get_request_context),
) -> ExperimentRunResponse:
    tenant_id = tenant_from_context_or_request(context, payload.tenant_id)
    run, _results = await service.create_run(
        tenant_id=tenant_id,
        eval_spec_id=payload.eval_spec_id,
        candidate_version=payload.candidate_version,
        eval_case_ids=payload.eval_case_ids,
    )
    return ExperimentRunResponse(**run.model_dump(), request_id=request.state.request_id)


@router.get("", response_model=ExperimentRunListResponse)
async def list_experiment_runs(
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    eval_spec_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    repository: EddRepository = Depends(get_repository),
) -> ExperimentRunListResponse:
    runs = await repository.list_experiment_runs(
        tenant_id=tenant_id,
        eval_spec_id=eval_spec_id,
        limit=limit,
    )
    return ExperimentRunListResponse(
        experiment_runs=runs,
        request_id=request.state.request_id,
    )


@router.get("/{experiment_run_id}", response_model=ExperimentRunResponse)
async def get_experiment_run(
    experiment_run_id: UUID,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    repository: EddRepository = Depends(get_repository),
) -> ExperimentRunResponse:
    run = await repository.get_experiment_run(
        tenant_id=tenant_id,
        experiment_run_id=experiment_run_id,
    )
    return ExperimentRunResponse(**run.model_dump(), request_id=request.state.request_id)


@router.get("/{experiment_run_id}/summary", response_model=ExperimentRunSummaryResponse)
async def get_experiment_run_summary(
    experiment_run_id: UUID,
    request: Request,
    tenant_id: Annotated[str, Depends(tenant_query)],
    service: ExperimentService = Depends(get_experiment_service),
) -> ExperimentRunSummaryResponse:
    summary = await service.get_summary(
        tenant_id=tenant_id,
        experiment_run_id=experiment_run_id,
    )
    return ExperimentRunSummaryResponse(**summary.model_dump(), request_id=request.state.request_id)
