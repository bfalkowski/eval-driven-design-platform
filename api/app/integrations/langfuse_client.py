from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal, cast

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


@dataclass(frozen=True, slots=True)
class LangfuseScorePushResult:
    attempted: bool
    success: bool
    trace_id: str | None
    score_id: str | None
    message: str


@dataclass(frozen=True, slots=True)
class LangfuseTraceFetchResult:
    success: bool
    trace_id: str
    trace: dict[str, Any] | None
    message: str


@dataclass(frozen=True, slots=True)
class LangfuseTraceCreateResult:
    attempted: bool
    success: bool
    trace_id: str | None
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

    async def create_trace(
        self,
        *,
        name: str,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LangfuseTraceCreateResult:
        host = self._settings.langfuse_host.rstrip("/")
        if not self.enabled:
            return LangfuseTraceCreateResult(
                attempted=False,
                success=False,
                trace_id=None,
                message="Langfuse integration is disabled.",
            )
        if not self.configured:
            return LangfuseTraceCreateResult(
                attempted=False,
                success=False,
                trace_id=None,
                message="Langfuse is enabled but not configured.",
            )

        body: dict[str, Any] = {"name": name}
        if input_payload is not None:
            body["input"] = input_payload
        if output_payload is not None:
            body["output"] = output_payload
        if metadata:
            body["metadata"] = metadata

        try:
            async with self._client(host) as client:
                response = await client.post(
                    "/api/public/traces",
                    auth=self._basic_auth(),
                    json=body,
                )
                if response.status_code >= 400:
                    logger.warning(
                        "langfuse trace create failed",
                        extra={"status_code": response.status_code},
                    )
                    return LangfuseTraceCreateResult(
                        attempted=True,
                        success=False,
                        trace_id=None,
                        message=f"Langfuse trace create failed with status {response.status_code}.",
                    )
                trace_id = self._created_trace_id(response.json())
                if not trace_id:
                    return LangfuseTraceCreateResult(
                        attempted=True,
                        success=False,
                        trace_id=None,
                        message="Langfuse trace create returned no trace id.",
                    )
                return LangfuseTraceCreateResult(
                    attempted=True,
                    success=True,
                    trace_id=trace_id,
                    message="Langfuse trace created.",
                )
        except httpx.HTTPError:
            logger.warning("langfuse trace create unreachable", extra={"host": host})
            return LangfuseTraceCreateResult(
                attempted=True,
                success=False,
                trace_id=None,
                message=f"Unable to reach Langfuse at {host}.",
            )

    async def push_score(
        self,
        *,
        trace_id: str | None,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> LangfuseScorePushResult:
        host = self._settings.langfuse_host.rstrip("/")
        if not self.enabled:
            return LangfuseScorePushResult(
                attempted=False,
                success=False,
                trace_id=trace_id,
                score_id=None,
                message="Langfuse integration is disabled.",
            )
        if not self.configured:
            return LangfuseScorePushResult(
                attempted=False,
                success=False,
                trace_id=trace_id,
                score_id=None,
                message="Langfuse is enabled but not configured.",
            )
        if not trace_id:
            return LangfuseScorePushResult(
                attempted=False,
                success=False,
                trace_id=None,
                score_id=None,
                message="No trace id available for score push.",
            )

        payload: dict[str, Any] = {
            "traceId": trace_id,
            "name": name,
            "value": value,
        }
        if comment:
            payload["comment"] = comment
        try:
            async with self._client(host) as client:
                response = await client.post(
                    "/api/public/scores",
                    auth=self._basic_auth(),
                    json=payload,
                )
                if response.status_code >= 400:
                    logger.warning(
                        "langfuse score push failed",
                        extra={"status_code": response.status_code, "trace_id": trace_id},
                    )
                    return LangfuseScorePushResult(
                        attempted=True,
                        success=False,
                        trace_id=trace_id,
                        score_id=None,
                        message=f"Langfuse score push failed with status {response.status_code}.",
                    )
                score_id = self._score_id(response.json())
                return LangfuseScorePushResult(
                    attempted=True,
                    success=True,
                    trace_id=trace_id,
                    score_id=score_id,
                    message="Langfuse score push succeeded.",
                )
        except httpx.HTTPError:
            logger.warning(
                "langfuse score push unreachable",
                extra={"trace_id": trace_id, "host": host},
            )
            return LangfuseScorePushResult(
                attempted=True,
                success=False,
                trace_id=trace_id,
                score_id=None,
                message=f"Unable to reach Langfuse at {host}.",
            )

    async def get_trace(self, *, trace_id: str) -> LangfuseTraceFetchResult:
        host = self._settings.langfuse_host.rstrip("/")
        if not self.enabled:
            return LangfuseTraceFetchResult(
                success=False,
                trace_id=trace_id,
                trace=None,
                message="Langfuse integration is disabled.",
            )
        if not self.configured:
            return LangfuseTraceFetchResult(
                success=False,
                trace_id=trace_id,
                trace=None,
                message="Langfuse is enabled but not configured.",
            )
        try:
            async with self._client(host) as client:
                response = await client.get(
                    f"/api/public/traces/{trace_id}",
                    auth=self._basic_auth(),
                )
                if response.status_code >= 400:
                    return LangfuseTraceFetchResult(
                        success=False,
                        trace_id=trace_id,
                        trace=None,
                        message=f"Langfuse trace lookup failed with status {response.status_code}.",
                    )
                payload = response.json()
                trace = self._extract_trace(payload)
                if trace is None:
                    return LangfuseTraceFetchResult(
                        success=False,
                        trace_id=trace_id,
                        trace=None,
                        message="Langfuse returned an unexpected trace payload.",
                    )
                return LangfuseTraceFetchResult(
                    success=True,
                    trace_id=trace_id,
                    trace=trace,
                    message="Langfuse trace retrieved.",
                )
        except httpx.HTTPError:
            return LangfuseTraceFetchResult(
                success=False,
                trace_id=trace_id,
                trace=None,
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

    @staticmethod
    def _created_trace_id(payload: Any) -> str | None:
        if isinstance(payload, dict):
            trace_id = payload.get("id")
            if isinstance(trace_id, str) and trace_id:
                return trace_id
        return None

    @staticmethod
    def _score_id(payload: Any) -> str | None:
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict):
                score_id = data.get("id")
                if isinstance(score_id, str) and score_id:
                    return score_id
            score_id = payload.get("id") or payload.get("scoreId")
            if isinstance(score_id, str) and score_id:
                return score_id
        return None

    @staticmethod
    def _extract_trace(payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict):
                return cast(dict[str, Any], data)
            return cast(dict[str, Any], payload)
        return None
