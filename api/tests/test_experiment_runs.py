from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient

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
