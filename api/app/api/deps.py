from __future__ import annotations

from typing import Any, cast

from fastapi import Depends, Query, Request

from app.core.auth import RequestContext, get_request_context
from app.core.errors import BadRequestError
from app.storage.base import EddRepository


def get_repository(request: Request) -> EddRepository:
    return cast(EddRepository, request.app.state.repository)


def tenant_from_context_or_request(
    context: RequestContext | None,
    tenant_id: str | None,
) -> str:
    if context is not None:
        return context.tenant_id
    if tenant_id is None:
        raise BadRequestError("tenant_id is required.")
    return tenant_id


def tenant_query(
    tenant_id: str | None = Query(default=None, min_length=1, max_length=128),
    context: RequestContext | None = Depends(get_request_context),
) -> str:
    return tenant_from_context_or_request(context, tenant_id)


def non_empty_updates(updates: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in updates.items() if value is not None}
