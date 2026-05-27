from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.integrations.langfuse_client import LangfuseClientAdapter
from app.main import create_app


@pytest.fixture
def langfuse_enabled_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("APP_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("APP_AUTH_ENABLED", "false")
    monkeypatch.setenv("APP_LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("APP_LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("APP_LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("APP_LANGFUSE_HOST", "http://langfuse.test")
    with TestClient(create_app()) as test_client:
        yield test_client


def test_langfuse_health_disabled(client: TestClient) -> None:
    response = client.get("/v1/integrations/langfuse/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disabled"
    assert body["enabled"] is False
    assert body["configured"] is False


def test_langfuse_health_misconfigured(langfuse_enabled_client: TestClient) -> None:
    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="",
        langfuse_secret_key="",
    )
    langfuse_enabled_client.app.state.langfuse_adapter = LangfuseClientAdapter(settings)

    response = langfuse_enabled_client.get("/v1/integrations/langfuse/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "misconfigured"
    assert body["enabled"] is True
    assert body["configured"] is False


def test_langfuse_health_healthy(langfuse_enabled_client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/public/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/api/public/projects":
            return httpx.Response(200, json={"data": [{"id": "project-1"}]})
        return httpx.Response(404)

    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
        langfuse_host="http://langfuse.test",
    )
    langfuse_enabled_client.app.state.langfuse_adapter = LangfuseClientAdapter(
        settings,
        transport=httpx.MockTransport(handler),
    )

    response = langfuse_enabled_client.get("/v1/integrations/langfuse/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["reachable"] is True
    assert body["authenticated"] is True
    assert body["project_count"] == 1


def test_langfuse_health_unreachable(langfuse_enabled_client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
        langfuse_host="http://langfuse.test",
    )
    langfuse_enabled_client.app.state.langfuse_adapter = LangfuseClientAdapter(
        settings,
        transport=httpx.MockTransport(handler),
    )

    response = langfuse_enabled_client.get("/v1/integrations/langfuse/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unreachable"
    assert body["reachable"] is False


def test_langfuse_trace_preview(langfuse_enabled_client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/public/traces/trace-123":
            return httpx.Response(
                200,
                json={
                    "id": "trace-123",
                    "name": "Refund flow",
                    "input": {"task": "Handle refund"},
                    "observations": [{"id": "obs-1"}],
                    "timestamp": "2026-05-27T01:00:00Z",
                },
            )
        return httpx.Response(404)

    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
        langfuse_host="http://langfuse.test",
    )
    langfuse_enabled_client.app.state.langfuse_adapter = LangfuseClientAdapter(
        settings,
        transport=httpx.MockTransport(handler),
    )

    response = langfuse_enabled_client.get("/v1/integrations/langfuse/traces/trace-123")
    assert response.status_code == 200
    body = response.json()["trace"]
    assert body["trace_id"] == "trace-123"
    assert body["name"] == "Refund flow"
    assert body["has_observations"] is True


def test_import_langfuse_trace_as_case(langfuse_enabled_client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/public/traces/trace-xyz":
            return httpx.Response(
                200,
                json={
                    "id": "trace-xyz",
                    "name": "Support ticket",
                    "input": {"task": "Escalate unhappy customer"},
                    "observations": [{"id": "o1"}, {"id": "o2"}],
                },
            )
        return httpx.Response(404)

    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
        langfuse_host="http://langfuse.test",
    )
    langfuse_enabled_client.app.state.langfuse_adapter = LangfuseClientAdapter(
        settings,
        transport=httpx.MockTransport(handler),
    )

    spec_response = langfuse_enabled_client.post(
        "/v1/eval-specs",
        json={
            "tenant_id": "tenant-a",
            "name": "Support spec",
            "rubric": "Be clear and empathetic.",
            "pass_threshold": 70,
        },
    )
    assert spec_response.status_code == 201
    spec_id = spec_response.json()["eval_spec_id"]

    import_response = langfuse_enabled_client.post(
        "/v1/integrations/langfuse/import-case",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec_id,
            "trace_id": "trace-xyz",
        },
    )
    assert import_response.status_code == 201
    created = import_response.json()
    assert created["source"] == "langfuse_import"
    assert created["langfuse_trace_id"] == "trace-xyz"
