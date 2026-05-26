from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

LangfuseHealthStatus = Literal[
    "disabled",
    "misconfigured",
    "healthy",
    "degraded",
    "unreachable",
]


@dataclass(frozen=True, slots=True)
class LangfuseHealthResult:
    enabled: bool
    configured: bool
    status: LangfuseHealthStatus
    host: str
    reachable: bool
    authenticated: bool | None
    project_count: int | None
    message: str


class LangfuseClientAdapter:
    """Single integration point for Langfuse HTTP API calls."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    @property
    def enabled(self) -> bool:
        return self._settings.langfuse_enabled

    @property
    def configured(self) -> bool:
        return self.enabled and bool(self._settings.langfuse_public_key.strip()) and bool(
            self._settings.langfuse_secret_key.strip()
        )

    async def get_health(self) -> LangfuseHealthResult:
        host = self._settings.langfuse_host.rstrip("/")

        if not self.enabled:
            return LangfuseHealthResult(
                enabled=False,
                configured=False,
                status="disabled",
                host=host,
                reachable=False,
                authenticated=None,
                project_count=None,
                message="Langfuse integration is disabled.",
            )

        if not self.configured:
            return LangfuseHealthResult(
                enabled=True,
                configured=False,
                status="misconfigured",
                host=host,
                reachable=False,
                authenticated=None,
                project_count=None,
                message="Langfuse is enabled but public/secret keys are missing.",
            )

        try:
            async with self._client(host) as client:
                health_response = await client.get(
                    "/api/public/health",
                    params={"failIfDatabaseUnavailable": "true"},
                )
                if health_response.status_code != 200:
                    return LangfuseHealthResult(
                        enabled=True,
                        configured=True,
                        status="degraded",
                        host=host,
                        reachable=True,
                        authenticated=None,
                        project_count=None,
                        message="Langfuse responded but reported an unhealthy state.",
                    )

                auth_response = await client.get(
                    "/api/public/projects",
                    auth=self._basic_auth(),
                )
                if auth_response.status_code == 401:
                    return LangfuseHealthResult(
                        enabled=True,
                        configured=True,
                        status="degraded",
                        host=host,
                        reachable=True,
                        authenticated=False,
                        project_count=None,
                        message="Langfuse is reachable but API keys were rejected.",
                    )
                if auth_response.status_code >= 400:
                    return LangfuseHealthResult(
                        enabled=True,
                        configured=True,
                        status="degraded",
                        host=host,
                        reachable=True,
                        authenticated=False,
                        project_count=None,
                        message="Langfuse is reachable but project lookup failed.",
                    )

                project_count = self._project_count(auth_response.json())
                return LangfuseHealthResult(
                    enabled=True,
                    configured=True,
                    status="healthy",
                    host=host,
                    reachable=True,
                    authenticated=True,
                    project_count=project_count,
                    message="Langfuse is reachable and API keys are valid.",
                )
        except httpx.HTTPError:
            logger.warning("langfuse health check failed", extra={"host": host})
            return LangfuseHealthResult(
                enabled=True,
                configured=True,
                status="unreachable",
                host=host,
                reachable=False,
                authenticated=None,
                project_count=None,
                message=f"Unable to reach Langfuse at {host}.",
            )

    def _client(self, host: str) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=host,
            timeout=5.0,
            transport=self._transport,
        )

    def _basic_auth(self) -> tuple[str, str]:
        return (
            self._settings.langfuse_public_key.strip(),
            self._settings.langfuse_secret_key.strip(),
        )

    @staticmethod
    def _project_count(payload: Any) -> int | None:
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            projects = payload.get("data") or payload.get("projects")
            if isinstance(projects, list):
                return len(projects)
        return None
