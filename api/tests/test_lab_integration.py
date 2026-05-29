from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.services.run_ingest_service import compute_gate, extract_overall_score
from tests.test_eval_crud import create_spec


def _envelope(
    *,
    eval_spec_id: str | None = None,
    overall_score: float | None = 0.85,
    failure_packet: dict[str, object] | None = None,
    tenant_id: str = "tenant-a",
    source: str = "edd-agent-lab",
    run_id: str = "2026-05-29T13-29-10Z",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "1",
        "source": source,
        "run_id": run_id,
        "agent": "customer_solution_agent",
        "agent_version": "v1-discovery-graph",
        "suite": "overfitting",
        "tenant_id": tenant_id,
        "scenario_ids": ["healthcare_documentation", "legal_review"],
        "started_at": "2026-05-29T13-29-10Z",
        "completed_at": "2026-05-29T13-29-10Z",
        "outputs": {},
        "artifact_paths": {},
    }
    if eval_spec_id is not None:
        payload["eval_spec_id"] = eval_spec_id
    if overall_score is not None:
        payload["eval_summary"] = {"overall_score": overall_score}
    else:
        payload["eval_summary"] = None
    payload["failure_packet"] = failure_packet
    return payload


def test_lab_publish_creates_experiment_run(client: TestClient) -> None:
    spec = create_spec(client, name="Lab ingest workflow")
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), overall_score=0.85),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["platform_run_id"] == body["experiment_run_id"]
    assert body["lab_run_id"] == "2026-05-29T13-29-10Z"
    assert body["gate_status"] == "pass"
    assert body["experiment_run"]["candidate_version"] == "v1-discovery-graph"
    assert body["experiment_run"]["result_count"] == 2
    assert body["experiment_run"]["status"] == "completed"
    ingest = body["experiment_run"]["ingest"]
    assert ingest is not None
    assert ingest["source"] == "edd-agent-lab"
    assert ingest["external_run_id"] == "2026-05-29T13-29-10Z"
    assert ingest["subject_id"] == "customer_solution_agent"
    assert ingest["suite_id"] == "overfitting"
    assert ingest["gate_status"] == "pass"

    run = client.get(
        f"/v1/experiment-runs/{body['platform_run_id']}",
        params={"tenant_id": "tenant-a"},
    )
    assert run.status_code == 200
    persisted = run.json()
    assert persisted["ingest"] is not None
    assert persisted["ingest"]["source"] == "edd-agent-lab"
    assert persisted["ingest"]["external_run_id"] == "2026-05-29T13-29-10Z"
    assert persisted["ingest"]["gate_status"] == body["gate_status"]


def test_lab_publish_fails_gate_on_failure_packet(client: TestClient) -> None:
    spec = create_spec(client, name="Lab failure gate")
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(
            eval_spec_id=str(spec["eval_spec_id"]),
            overall_score=0.95,
            failure_packet={"failure_type": "overfitting", "summary": "High overfitting risk."},
        ),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["gate_status"] == "fail"
    assert "failure packet" in body["gate_explanation"].lower()
    assert body["experiment_run"]["status"] == "failed"


def test_lab_publish_fails_gate_on_low_score(client: TestClient) -> None:
    spec_response = client.post(
        "/v1/eval-specs",
        json={
            "tenant_id": "tenant-a",
            "name": "Lab low score gate",
            "rubric": "High bar.",
            "pass_threshold": 80,
        },
    )
    assert spec_response.status_code == 201
    spec = spec_response.json()
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), overall_score=0.65),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["gate_status"] == "fail"
    assert "below pass threshold" in body["gate_explanation"]


def test_lab_publish_insufficient_evidence_without_score(client: TestClient) -> None:
    spec = create_spec(client, name="Lab no score")
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), overall_score=None),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["gate_status"] == "insufficient_evidence"


def test_lab_publish_rejects_bad_schema(client: TestClient) -> None:
    spec = create_spec(client)
    payload = _envelope(eval_spec_id=str(spec["eval_spec_id"]))
    payload["schema_version"] = "99"
    response = client.post("/v1/integrations/lab/publish", json=payload)
    assert response.status_code == 400


def test_lab_publish_requires_eval_spec_id(client: TestClient) -> None:
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(eval_spec_id=None),
    )
    assert response.status_code == 400
    assert "eval_spec_id" in response.json()["error"]["message"]


def test_lab_publish_uses_default_eval_spec_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import create_app

    with TestClient(create_app()) as configured_client:
        spec = create_spec(configured_client, tenant_id="tenant-lab")
        monkeypatch.setenv("APP_LAB_DEFAULT_EVAL_SPEC_ID", str(spec["eval_spec_id"]))
        configured_client.app.state.settings = configured_client.app.state.settings.model_copy(
            update={"lab_default_eval_spec_id": UUID(str(spec["eval_spec_id"]))},
        )
        payload = _envelope(eval_spec_id=None, tenant_id="tenant-lab")
        response = configured_client.post("/v1/integrations/lab/publish", json=payload)
    assert response.status_code == 201
    assert response.json()["experiment_run"]["eval_spec_id"] == spec["eval_spec_id"]


def test_lab_publish_tenant_isolation(client: TestClient) -> None:
    spec = create_spec(client, tenant_id="tenant-a")
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), tenant_id="tenant-a"),
    )
    run_id = response.json()["platform_run_id"]
    cross_tenant = client.get(
        f"/v1/experiment-runs/{run_id}",
        params={"tenant_id": "tenant-b"},
    )
    assert cross_tenant.status_code == 404


def test_extract_overall_score_normalizes_zero_to_one_scale() -> None:
    assert extract_overall_score({"overall_score": 0.773}) == pytest.approx(77.3)


def test_extract_overall_score_preserves_hundred_scale() -> None:
    assert extract_overall_score({"overall_score": 82.5}) == pytest.approx(82.5)


def test_compute_gate_pass_and_fail() -> None:
    status, _ = compute_gate(pass_threshold=70.0, overall_score=77.3, failure_packet=None)
    assert status == "pass"
    status, _ = compute_gate(pass_threshold=80.0, overall_score=77.3, failure_packet=None)
    assert status == "fail"
    status, explanation = compute_gate(
        pass_threshold=70.0,
        overall_score=90.0,
        failure_packet=cast(dict[str, object], {"failure_type": "overfitting"}),
    )
    assert status == "fail"
    assert "overfitting" in explanation


def test_run_ingest_generic_endpoint(client: TestClient) -> None:
    spec = create_spec(client, name="Generic ingest")
    response = client.post(
        "/v1/integrations/runs/publish",
        json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), source="ci"),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["external_run_id"] == "2026-05-29T13-29-10Z"
    assert body["experiment_run"]["ingest"]["source"] == "ci"


def test_run_ingest_rejects_disallowed_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import create_app

    with TestClient(create_app()) as configured_client:
        spec = create_spec(configured_client)
        configured_client.app.state.settings = configured_client.app.state.settings.model_copy(
            update={"ingest_allowed_sources": ["edd-agent-lab"]},
        )
        response = configured_client.post(
            "/v1/integrations/runs/publish",
            json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), source="ci"),
        )
    assert response.status_code == 400
    assert "APP_INGEST_ALLOWED_SOURCES" in response.json()["error"]["message"]


def test_list_experiment_runs_filter_by_ingest_source(client: TestClient) -> None:
    spec = create_spec(client, name="Ingest source filter")
    lab = client.post(
        "/v1/integrations/runs/publish",
        json=_envelope(eval_spec_id=str(spec["eval_spec_id"]), source="edd-agent-lab"),
    )
    ci = client.post(
        "/v1/integrations/runs/publish",
        json=_envelope(
            eval_spec_id=str(spec["eval_spec_id"]),
            source="ci",
            overall_score=0.9,
        ),
    )
    assert lab.status_code == 201
    assert ci.status_code == 201

    lab_only = client.get(
        "/v1/experiment-runs",
        params={"tenant_id": "tenant-a", "ingest_source": "edd-agent-lab"},
    )
    assert lab_only.status_code == 200
    sources = {run["ingest"]["source"] for run in lab_only.json()["experiment_runs"]}
    assert sources == {"edd-agent-lab"}


def test_legacy_lab_publish_alias_returns_external_run_id(client: TestClient) -> None:
    spec = create_spec(client, name="Legacy alias")
    response = client.post(
        "/v1/integrations/lab/publish",
        json=_envelope(
            eval_spec_id=str(spec["eval_spec_id"]),
            run_id="legacy-alias-run-1",
            overall_score=0.9,
        ),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["external_run_id"] == "legacy-alias-run-1"
    assert body["lab_run_id"] == "legacy-alias-run-1"
    assert body["experiment_run"]["ingest"]["external_run_id"] == "legacy-alias-run-1"


def test_list_experiment_runs_includes_published_run_by_id(client: TestClient) -> None:
    spec = create_spec(client, name="List includes published run")
    publish = client.post(
        "/v1/integrations/runs/publish",
        json=_envelope(
            eval_spec_id=str(spec["eval_spec_id"]),
            run_id="list-filter-target-run",
            source="edd-agent-lab",
        ),
    )
    assert publish.status_code == 201
    run_id = publish.json()["platform_run_id"]

    listed = client.get(
        "/v1/experiment-runs",
        params={"tenant_id": "tenant-a", "ingest_source": "edd-agent-lab"},
    )
    assert listed.status_code == 200
    listed_ids = {run["experiment_run_id"] for run in listed.json()["experiment_runs"]}
    assert run_id in listed_ids
