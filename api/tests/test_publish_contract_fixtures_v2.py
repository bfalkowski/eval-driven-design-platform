from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.services.publish_envelope import ParsePublishEnvelope, normalize_publish_envelope
from tests.test_eval_crud import create_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "contracts" / "publish" / "v2"

V2_FIXTURE_EXPECTATIONS: dict[str, dict[str, str]] = {
    "envelope-pass-demo-not-production.json": {
        "gate_status": "pass",
        "overall_status": "pass_for_demo_not_production",
        "production_status": "blocked",
    },
    "envelope-fail-failure-packet.json": {
        "gate_status": "fail",
        "overall_status": "fail",
        "production_status": "not_evaluated",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _prepare_envelope(
    fixture: dict[str, Any],
    *,
    eval_spec_id: str,
    run_suffix: str,
) -> dict[str, Any]:
    envelope = dict(fixture)
    envelope["eval_spec_id"] = eval_spec_id
    envelope["run_id"] = f"{envelope['run_id']}-{run_suffix}"
    if envelope.get("run"):
        envelope["run"] = dict(envelope["run"])
        envelope["run"]["id"] = envelope["run_id"]
    return envelope


def test_normalize_v2_envelope_extracts_tool_context() -> None:
    fixture = _load_json(CONTRACTS_DIR / "envelope-pass-demo-not-production.json")
    normalized = normalize_publish_envelope(ParsePublishEnvelope.model_validate(fixture))

    assert normalized.schema_version == "2"
    assert normalized.source == "edd-agent-lab"
    assert normalized.tool_mode_summary == "mock_local"
    assert normalized.production_ready is False
    assert normalized.target_id == "customer-escalation-triage-target-v1"
    assert normalized.eval_contract_ref_id == "customer-escalation-triage-eval-contract-v1"
    assert normalized.candidate_version == "v1-evidence-triage-graph"
    assert len(normalized.tool_bindings or []) == 2
    assert len(normalized.trace_links or []) == 1
    assert normalized.trace_links[0]["external_trace_id"] == "trace_v1_def456"


@pytest.mark.parametrize(
    ("fixture_name", "expected"),
    V2_FIXTURE_EXPECTATIONS.items(),
)
def test_publish_v2_contract_fixture_round_trip(
    client: TestClient,
    fixture_name: str,
    expected: dict[str, str],
) -> None:
    spec = create_spec(client, name=f"V2 contract {fixture_name}")
    fixture = _load_json(CONTRACTS_DIR / fixture_name)
    envelope = _prepare_envelope(
        fixture,
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )

    response = client.post("/v1/integrations/runs/publish", json=envelope)
    assert response.status_code == 201
    body = response.json()

    assert body["gate_status"] == expected["gate_status"]
    assert body["overall_status"] == expected["overall_status"]
    assert body["production_status"] == expected["production_status"]
    assert body["external_run_id"] == envelope["run_id"]

    ingest = body["experiment_run"]["ingest"]
    assert ingest is not None
    assert ingest["schema_version"] == "2"
    assert ingest["overall_status"] == expected["overall_status"]
    if fixture_name == "envelope-pass-demo-not-production.json":
        assert ingest["evidence"] is not None
        assert len(ingest["evidence"]["trace_links"]) == 1
        assert body["trace_link_ids"] == ["trace-link-v1-001"]


def test_publish_v2_idempotency_key_returns_existing_run(client: TestClient) -> None:
    spec = create_spec(client, name="V2 idempotency")
    fixture = _load_json(CONTRACTS_DIR / "envelope-pass-demo-not-production.json")
    idempotency_key = f"test-idempotency-{uuid.uuid4().hex[:8]}"
    envelope = _prepare_envelope(
        fixture,
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )
    envelope["idempotency_key"] = idempotency_key

    first = client.post("/v1/integrations/runs/publish", json=envelope)
    assert first.status_code == 201
    first_id = first.json()["platform_run_id"]

    envelope["run_id"] = f"{envelope['run_id']}-retry"
    envelope["run"]["id"] = envelope["run_id"]
    second = client.post("/v1/integrations/runs/publish", json=envelope)
    assert second.status_code == 201
    assert second.json()["platform_run_id"] == first_id
    assert second.json()["external_run_id"] != envelope["run_id"]


def test_publish_v2_response_matches_minimal_contract(client: TestClient) -> None:
    contract = _load_json(CONTRACTS_DIR / "response-minimal.json")
    spec = create_spec(client, name="V2 response shape")
    envelope = _prepare_envelope(
        _load_json(CONTRACTS_DIR / "envelope-pass-demo-not-production.json"),
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )

    response = client.post("/v1/integrations/runs/publish", json=envelope)
    assert response.status_code == 201
    body = response.json()

    for field in contract["required_top_level_fields"]:
        assert field in body, f"missing response field: {field}"
    assert body["gate_status"] in set(contract["gate_status_values"])
    assert body["overall_status"] in set(contract["overall_status_values"])

    ingest = body["experiment_run"]["ingest"]
    assert ingest is not None
    for field in contract["experiment_run_ingest_fields"]:
        assert field in ingest, f"missing ingest field: {field}"
