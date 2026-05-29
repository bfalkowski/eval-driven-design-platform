from __future__ import annotations

from fastapi.testclient import TestClient

from tests.test_eval_crud import create_spec
from tests.test_experiment_runs import create_case


def test_quality_gate_for_platform_experiment_run(client: TestClient) -> None:
    spec = create_spec(client, name="Gate platform run")
    case = create_case(
        client,
        tenant_id="tenant-a",
        eval_spec_id=str(spec["eval_spec_id"]),
        name="Gate case",
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
    run_id = run.json()["experiment_run_id"]

    gate = client.get(
        f"/v1/experiment-runs/{run_id}/gate",
        params={"tenant_id": "tenant-a"},
    )
    assert gate.status_code == 200
    body = gate.json()
    assert body["evaluation_source"] == "experiment_results"
    assert body["gate_status"] in {"pass", "fail", "insufficient_evidence"}
    assert body["pass_threshold"] == 75
    assert body["average_score"] is not None


def test_quality_gate_for_ingested_run(client: TestClient) -> None:
    spec = create_spec(client, name="Gate ingest run")
    publish = client.post(
        "/v1/integrations/runs/publish",
        json={
            "schema_version": "1",
            "source": "edd-agent-lab",
            "run_id": "gate-ingest-run-1",
            "agent": "customer_solution_agent",
            "agent_version": "v1-discovery-graph",
            "suite": "overfitting",
            "tenant_id": "tenant-a",
            "eval_spec_id": spec["eval_spec_id"],
            "scenario_ids": ["healthcare_documentation"],
            "eval_summary": {"overall_score": 0.92},
            "failure_packet": None,
            "outputs": {},
            "artifact_paths": {},
        },
    )
    assert publish.status_code == 201
    run_id = publish.json()["platform_run_id"]

    gate = client.get(
        f"/v1/experiment-runs/{run_id}/gate",
        params={"tenant_id": "tenant-a"},
    )
    assert gate.status_code == 200
    body = gate.json()
    assert body["evaluation_source"] == "ingest"
    assert body["gate_status"] == "pass"
    assert body["ingest_source"] == "edd-agent-lab"
    assert body["external_run_id"] == "gate-ingest-run-1"


def test_quality_gate_tenant_isolation(client: TestClient) -> None:
    spec = create_spec(client, tenant_id="tenant-a")
    case = create_case(
        client,
        tenant_id="tenant-a",
        eval_spec_id=str(spec["eval_spec_id"]),
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
    run_id = run.json()["experiment_run_id"]
    cross_tenant = client.get(
        f"/v1/experiment-runs/{run_id}/gate",
        params={"tenant_id": "tenant-b"},
    )
    assert cross_tenant.status_code == 404
