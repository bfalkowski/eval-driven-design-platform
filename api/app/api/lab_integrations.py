from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import tenant_from_context_or_request
from app.core.auth import RequestContext, get_request_context
from app.domain.models import LabPublishEnvelope, LabPublishResponse
from app.services.lab_publish_service import LabPublishService
from app.storage.base import EddRepository

router = APIRouter(prefix="/v1/integrations/lab", tags=["integrations"])


def get_lab_publish_service(request: Request) -> LabPublishService:
    repository = cast(EddRepository, request.app.state.repository)
    settings = request.app.state.settings
    return LabPublishService(
        repository,
        default_eval_spec_id=settings.lab_default_eval_spec_id,
    )


@router.post("/publish", status_code=status.HTTP_201_CREATED, response_model=LabPublishResponse)
async def publish_lab_run(
    payload: LabPublishEnvelope,
    request: Request,
    service: LabPublishService = Depends(get_lab_publish_service),
    context: RequestContext | None = Depends(get_request_context),
) -> LabPublishResponse:
    tenant_id = tenant_from_context_or_request(context, payload.tenant_id)
    result = await service.publish(tenant_id=tenant_id, envelope=payload)
    return result.model_copy(update={"request_id": request.state.request_id})
