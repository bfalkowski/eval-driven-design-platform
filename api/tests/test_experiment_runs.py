from __future__ import annotations

import json
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.integrations.langfuse_client import LangfuseClientAdapter
from tests.test_eval_crud import create_spec


def create_case(
    client: TestClient,
    *,
    tenant_id: str,
    eval_spec_id: str,
    name: str = "Refund escalation",
) -> dict[str, object]:
    response = client.post(
        "/v1/eval-cases",
        json={
            "tenant_id": tenant_id,
            "eval_spec_id": eval_spec_id,
            "name": name,
            "input_payload": {
                "task": "Handle refund request with empathy and clear next steps.",
            },
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def test_experiment_run_summary_is_deterministic(client: TestClient) -> None:
    spec = create_spec(
        client,
        name="Support workflow",
    )
    spec_id = spec["eval_spec_id"]
    case = create_case(client, tenant_id="tenant-a", eval_spec_id=str(spec_id))

    payload = {
        "tenant_id": "tenant-a",
        "eval_spec_id": spec_id,
        "candidate_version": "prompt_v4",
        "eval_case_ids": [case["eval_case_id"]],
    }
    first = client.post("/v1/experiment-runs", json=payload)
    second = client.post("/v1/experiment-runs", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201

    run_id = first.json()["experiment_run_id"]
    summary = client.get(
        f"/v1/experiment-runs/{run_id}/summary",
        params={"tenant_id": "tenant-a"},
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["result_count"] == 1
    assert body["average_score"] > 0
    assert 0 <= body["pass_rate"] <= 1

    results = client.get(
        "/v1/evaluation-results",
        params={"tenant_id": "tenant-a", "experiment_run_id": run_id},
    )
    assert results.status_code == 200
    assert len(results.json()["evaluation_results"]) == 1

    first_score = results.json()["evaluation_results"][0]["score"]
    second_results = client.get(
        "/v1/evaluation-results",
        params={
            "tenant_id": "tenant-a",
            "experiment_run_id": second.json()["experiment_run_id"],
        },
    )
    second_score = second_results.json()["evaluation_results"][0]["score"]
    assert first_score == second_score
    assert results.json()["evaluation_results"][0]["langfuse_trace_id"] is None
    assert results.json()["evaluation_results"][0]["langfuse_score_id"] is None


def test_experiment_run_requires_cases(client: TestClient) -> None:
    spec = create_spec(client)
    response = client.post(
        "/v1/experiment-runs",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "candidate_version": "prompt_v3",
        },
    )
    assert response.status_code == 400


def test_experiment_run_tenant_isolation(client: TestClient) -> None:
    spec = create_spec(client, tenant_id="tenant-a")
    case = create_case(client, tenant_id="tenant-a", eval_spec_id=str(spec["eval_spec_id"]))
    run = client.post(
        "/v1/experiment-runs",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "candidate_version": "prompt_v4",
            "eval_case_ids": [case["eval_case_id"]],
        },
    )
    run_id = run.json()["experiment_run_id"]
    cross_tenant = client.get(
        f"/v1/experiment-runs/{run_id}/summary",
        params={"tenant_id": "tenant-b"},
    )
    assert cross_tenant.status_code == 404


def test_experiment_run_stores_case_trace_when_langfuse_disabled(client: TestClient) -> None:
    spec = create_spec(client, name="Trace-backed workflow")
    case = create_case(client, tenant_id="tenant-a", eval_spec_id=str(spec["eval_spec_id"]))
    client.patch(
        f"/v1/eval-cases/{case['eval_case_id']}",
        params={"tenant_id": "tenant-a"},
        json={"langfuse_trace_id": "trace-disabled-path"},
    )
    run = client.post(
        "/v1/experiment-runs",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "candidate_version": "prompt_v4",
            "eval_case_ids": [case["eval_case_id"]],
        },
    )
    assert run.status_code == 201

    results = client.get(
        "/v1/evaluation-results",
        params={"tenant_id": "tenant-a", "experiment_run_id": run.json()["experiment_run_id"]},
    )
    assert results.status_code == 200
    result = results.json()["evaluation_results"][0]
    assert result["langfuse_trace_id"] == "trace-disabled-path"
    assert result["langfuse_score_id"] is None


@pytest.fixture
def langfuse_score_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("APP_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("APP_AUTH_ENABLED", "false")
    monkeypatch.setenv("APP_LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("APP_LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("APP_LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("APP_LANGFUSE_HOST", "http://langfuse.test")
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


def test_experiment_run_pushes_langfuse_score(langfuse_score_client: TestClient) -> None:
    score_calls: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/public/scores":
            score_calls.append(cast(dict[str, object], json.loads(request.read().decode())))
            return httpx.Response(200, json={"id": "score-123"})
        if request.url.path == "/api/public/traces":
            return httpx.Response(404)
        return httpx.Response(404)

    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
        langfuse_host="http://langfuse.test",
    )
    langfuse_score_client.app.state.langfuse_adapter = LangfuseClientAdapter(
        settings,
        transport=httpx.MockTransport(handler),
    )

    spec = create_spec(langfuse_score_client, name="Langfuse workflow")
    case = langfuse_score_client.post(
        "/v1/eval-cases",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "name": "Trace-backed case",
            "input_payload": {"task": "Handle refund request."},
            "langfuse_trace_id": "trace-abc",
        },
    )
    assert case.status_code == 201
    run = langfuse_score_client.post(
        "/v1/experiment-runs",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "candidate_version": "prompt_v5",
            "eval_case_ids": [case.json()["eval_case_id"]],
        },
    )
    assert run.status_code == 201

    results = langfuse_score_client.get(
        "/v1/evaluation-results",
        params={"tenant_id": "tenant-a", "experiment_run_id": run.json()["experiment_run_id"]},
    )
    assert results.status_code == 200
    result = results.json()["evaluation_results"][0]
    assert result["langfuse_trace_id"] == "trace-abc"
    assert result["langfuse_score_id"] == "score-123"
    assert len(score_calls) == 1
    assert score_calls[0]["traceId"] == "trace-abc"


def test_experiment_run_creates_langfuse_trace_when_case_has_none(
    langfuse_score_client: TestClient,
) -> None:
    trace_creates: list[dict[str, object]] = []
    score_calls: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/public/traces" and request.method == "POST":
            trace_creates.append(cast(dict[str, object], json.loads(request.read().decode())))
            return httpx.Response(200, json={"id": "trace-new-456"})
        if request.url.path == "/api/public/scores":
            score_calls.append(cast(dict[str, object], json.loads(request.read().decode())))
            return httpx.Response(200, json={"id": "score-456"})
        return httpx.Response(404)

    settings = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
        langfuse_host="http://langfuse.test",
    )
    langfuse_score_client.app.state.langfuse_adapter = LangfuseClientAdapter(
        settings,
        transport=httpx.MockTransport(handler),
    )

    spec = create_spec(langfuse_score_client, name="Auto trace workflow")
    case = create_case(
        langfuse_score_client,
        tenant_id="tenant-a",
        eval_spec_id=str(spec["eval_spec_id"]),
    )
    run = langfuse_score_client.post(
        "/v1/experiment-runs",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "candidate_version": "prompt_v6",
            "eval_case_ids": [case["eval_case_id"]],
        },
    )
    assert run.status_code == 201

    results = langfuse_score_client.get(
        "/v1/evaluation-results",
        params={"tenant_id": "tenant-a", "experiment_run_id": run.json()["experiment_run_id"]},
    )
    result = results.json()["evaluation_results"][0]
    assert len(trace_creates) == 1
    assert trace_creates[0]["name"] == "edd.experiment.Refund escalation"
    assert result["langfuse_trace_id"] == "trace-new-456"
    assert result["langfuse_score_id"] == "score-456"
    assert score_calls[0]["traceId"] == "trace-new-456"
