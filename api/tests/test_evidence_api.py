from __future__ import annotations

import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.domain.edd.artifacts import load_yaml_document
from tests.test_eval_crud import create_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = REPO_ROOT / "examples" / "customer_escalation_triage"


def _publish_reference_v0_failure(
    client: TestClient,
    *,
    eval_spec_id: str,
    run_suffix: str,
) -> dict[str, object]:
    failure_doc = load_yaml_document(SCENARIO_DIR / "failure-packet-v0.yaml")
    envelope = {
        "schema_version": "1",
        "source": "edd-agent-lab",
        "run_id": f"evidence-v0-fail-{run_suffix}",
        "tenant_id": "tenant-a",
        "agent": "customer_escalation_triage",
        "agent_version": "v0-baseline",
        "suite": "escalation_triage",
        "scenario_ids": ["escalation-latency-quality-regression-001"],
        "eval_spec_id": eval_spec_id,
        "eval_summary": {"overall_score": 0.95},
        "failure_packet": failure_doc["failure_packet"],
        "outputs": {},
        "artifact_paths": {},
    }
    response = client.post("/v1/integrations/runs/publish", json=envelope)
    assert response.status_code == 201
    return response.json()


def test_publish_structured_failure_packet_sets_evidence(client: TestClient) -> None:
    spec = create_spec(client, name="Evidence v0 failure")
    body = _publish_reference_v0_failure(
        client,
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )

    assert body["gate_status"] == "fail"
    assert "separate_facts_from_hypotheses" in body["gate_explanation"]

    ingest = body["experiment_run"]["ingest"]
    assert ingest is not None
    assert ingest["evidence"] is not None
    assert ingest["evidence"]["failure_packet"]["id"] == "fp-v0-unsupported-root-cause"
    assert (
        ingest["evidence"]["failure_packet"]["failed_behavior_rule_id"]
        == "separate_facts_from_hypotheses"
    )


def test_get_experiment_run_evidence_endpoint(client: TestClient) -> None:
    spec = create_spec(client, name="Evidence GET")
    body = _publish_reference_v0_failure(
        client,
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )
    run_id = body["platform_run_id"]

    response = client.get(
        f"/v1/experiment-runs/{run_id}/evidence",
        params={"tenant_id": "tenant-a"},
    )
    assert response.status_code == 200
    evidence = response.json()
    assert evidence["experiment_run_id"] == run_id
    assert evidence["failure_packet"]["failed_behavior_rule_id"] == "separate_facts_from_hypotheses"


def test_publish_with_fix_plan_and_comparison(client: TestClient) -> None:
    spec = create_spec(client, name="Evidence v1 bundle")
    fix_plan_doc = load_yaml_document(SCENARIO_DIR / "fix-plan-v1.yaml")
    comparison_doc = load_yaml_document(SCENARIO_DIR / "comparison-v0-v1.yaml")
    gate_doc = load_yaml_document(SCENARIO_DIR / "gate-result-v1.yaml")

    envelope = {
        "schema_version": "2",
        "source": "edd-agent-lab",
        "tenant_id": "tenant-a",
        "run_id": f"evidence-v1-pass-{uuid.uuid4().hex[:8]}",
        "producer": {
            "name": "edd-agent-lab",
            "environment": "local_demo",
            "run_mode": "mock_local",
        },
        "agent": {"id": "customer-escalation-triage-agent"},
        "agent_version": {"version_label": "v1-evidence-triage-graph"},
        "suite": "escalation_triage",
        "eval_spec_id": str(spec["eval_spec_id"]),
        "tool_context": {
            "tool_mode_summary": "mock_local",
            "production_ready": False,
        },
        "eval_summary": {"overall_score": 0.91},
        "fix_plan": fix_plan_doc["fix_plan"],
        "comparison": comparison_doc["comparison"],
        "gate_result": gate_doc["gate_result"],
        "outputs": {},
        "artifact_paths": {},
    }

    publish = client.post("/v1/integrations/runs/publish", json=envelope)
    assert publish.status_code == 201
    run_id = publish.json()["platform_run_id"]

    response = client.get(
        f"/v1/experiment-runs/{run_id}/evidence",
        params={"tenant_id": "tenant-a"},
    )
    assert response.status_code == 200
    evidence = response.json()
    assert evidence["fix_plan"]["id"] == "fix-v1-evidence-first-triage"
    assert evidence["comparison"]["id"] == "compare-v0-v1-escalation-triage"
    assert evidence["gate_result"]["overall_status"] == "pass_for_demo_not_production"
