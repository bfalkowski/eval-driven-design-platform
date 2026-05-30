from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.api.run_integrations import get_run_ingest_service, publish_external_run
from app.core.auth import RequestContext, get_request_context
from app.domain.models import LabPublishEnvelope, LabPublishResponse
from app.services.publish_envelope import ParsePublishEnvelope
from app.services.run_ingest_service import RunIngestService

router = APIRouter(prefix="/v1/integrations/lab", tags=["integrations"])


@router.post(
    "/publish",
    status_code=status.HTTP_201_CREATED,
    response_model=LabPublishResponse,
    deprecated=True,
    summary="Publish lab run (legacy alias)",
    description="Deprecated: use POST /v1/integrations/runs/publish. Accepts the same envelope.",
)
async def publish_lab_run(
    payload: LabPublishEnvelope,
    request: Request,
    service: RunIngestService = Depends(get_run_ingest_service),
    context: RequestContext | None = Depends(get_request_context),
) -> LabPublishResponse:
    parse_payload = ParsePublishEnvelope.model_validate(payload.model_dump())
    return await publish_external_run(parse_payload, request, service, context)
