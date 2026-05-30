from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import tenant_from_context_or_request
from app.core.auth import RequestContext, get_request_context
from app.domain.models import RunIngestResponse
from app.services.publish_envelope import ParsePublishEnvelope, normalize_publish_envelope
from app.services.run_ingest_service import RunIngestService
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/integrations/runs", tags=["integrations"])


def get_run_ingest_service(request: Request) -> RunIngestService:
    repository = cast(EddRepository, request.app.state.repository)
    settings = request.app.state.settings
    default_eval_spec_id = (
        settings.ingest_default_eval_spec_id or settings.lab_default_eval_spec_id
    )
    return RunIngestService(
        repository,
        default_eval_spec_id=default_eval_spec_id,
        allowed_sources=settings.ingest_allowed_sources,
    )


@router.post("/publish", status_code=status.HTTP_201_CREATED, response_model=RunIngestResponse)
async def publish_external_run(
    payload: ParsePublishEnvelope,
    request: Request,
    service: RunIngestService = Depends(get_run_ingest_service),
    context: RequestContext | None = Depends(get_request_context),
) -> RunIngestResponse:
    tenant_id = tenant_from_context_or_request(context, payload.tenant_id)
    envelope = normalize_publish_envelope(payload)
    result = await service.publish(tenant_id=tenant_id, envelope=envelope)
    return result.model_copy(update={"request_id": request.state.request_id})
