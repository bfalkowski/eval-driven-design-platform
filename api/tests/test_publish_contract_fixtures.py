from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.test_eval_crud import create_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "contracts" / "publish" / "v1"

FIXTURE_EXPECTATIONS: dict[str, str] = {
    "envelope-pass.json": "pass",
    "envelope-fail-failure-packet.json": "fail",
    "envelope-insufficient-evidence.json": "insufficient_evidence",
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
    return envelope


@pytest.mark.parametrize(
    ("fixture_name", "expected_gate_status"),
    FIXTURE_EXPECTATIONS.items(),
)
def test_publish_contract_fixture_round_trip(
    client: TestClient,
    fixture_name: str,
    expected_gate_status: str,
) -> None:
    spec = create_spec(client, name=f"Contract {fixture_name}")
    fixture = _load_json(CONTRACTS_DIR / fixture_name)
    envelope = _prepare_envelope(
        fixture,
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )

    response = client.post("/v1/integrations/runs/publish", json=envelope)
    assert response.status_code == 201
    body = response.json()

    assert body["gate_status"] == expected_gate_status
    assert body["external_run_id"] == envelope["run_id"]
    assert body["platform_run_id"] == body["experiment_run_id"]

    experiment_run = body["experiment_run"]
    ingest = experiment_run["ingest"]
    assert ingest is not None
    assert ingest["source"] == envelope["source"]
    assert ingest["external_run_id"] == envelope["run_id"]
    assert ingest["gate_status"] == expected_gate_status

    gate = client.get(
        f"/v1/experiment-runs/{body['platform_run_id']}/gate",
        params={"tenant_id": "tenant-a"},
    )
    assert gate.status_code == 200
    assert gate.json()["gate_status"] == expected_gate_status
    assert gate.json()["evaluation_source"] == "ingest"


def test_publish_response_matches_minimal_contract(client: TestClient) -> None:
    contract = _load_json(CONTRACTS_DIR / "response-minimal.json")
    required_fields = contract["required_top_level_fields"]
    ingest_fields = contract["experiment_run_ingest_fields"]
    allowed_gate_status = set(contract["gate_status_values"])

    spec = create_spec(client, name="Contract response shape")
    envelope = _prepare_envelope(
        _load_json(CONTRACTS_DIR / "envelope-pass.json"),
        eval_spec_id=str(spec["eval_spec_id"]),
        run_suffix=uuid.uuid4().hex[:8],
    )

    response = client.post("/v1/integrations/runs/publish", json=envelope)
    assert response.status_code == 201
    body = response.json()

    for field in required_fields:
        assert field in body, f"missing response field: {field}"
    assert body["gate_status"] in allowed_gate_status

    ingest = body["experiment_run"]["ingest"]
    assert ingest is not None
    for field in ingest_fields:
        assert field in ingest, f"missing ingest field: {field}"
