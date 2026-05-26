from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.api.health import legacy_router as legacy_health_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler, unhandled_error_handler
from app.core.logging import configure_logging, new_request_id, request_id_var
from app.core.metrics import record_http_request
from app.core.tracing import configure_tracing
from app.storage.factory import build_repository

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", new_request_id())
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            request_id_var.reset(token)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started_at = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", request.url.path)
        if route != "/metrics":
            record_http_request(
                method=request.method,
                route=route,
                status_code=response.status_code,
                duration_seconds=time.perf_counter() - started_at,
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    repository = await build_repository(settings)
    app.state.repository = repository
    logger.info("service started", extra={"environment": settings.environment})
    try:
        yield
    finally:
        await repository.close()
        logger.info("service stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Eval Driven Design Platform",
        version="0.1.0",
        description="Control plane for eval-driven AI development on top of Langfuse.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["content-type", "authorization", "x-request-id"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(health_router, prefix="/v1")
    app.include_router(legacy_health_router)
    app.include_router(metrics_router)
    configure_tracing(
        app,
        settings.service_name,
        settings.otel_enabled,
        settings.otel_exporter,
        settings.otel_otlp_endpoint,
    )
    app.state.settings = settings
    return app


app = create_app()
