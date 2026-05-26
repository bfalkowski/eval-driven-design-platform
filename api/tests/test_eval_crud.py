from __future__ import annotations

from datetime import timedelta
from typing import cast

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from app.core.auth import create_demo_jwt
from app.core.config import Settings
from app.main import create_app


def auth_headers(
    monkeypatch: MonkeyPatch,
    *,
    tenant_id: str,
    subject: str = "user-1",
) -> dict[str, str]:
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.setenv("APP_AUTH_DEMO_SECRET", "test-secret")
    settings = Settings(auth_enabled=True, auth_demo_secret="test-secret")
    token = create_demo_jwt(
        settings=settings,
        tenant_id=tenant_id,
        subject=subject,
        expires_delta=timedelta(minutes=30),
    )
    return {"authorization": f"Bearer {token}"}


def create_spec(
    client: TestClient,
    *,
    tenant_id: str = "tenant-a",
    name: str = "Support quality",
) -> dict[str, object]:
    response = client.post(
        "/v1/eval-specs",
        json={
            "tenant_id": tenant_id,
            "name": name,
            "description": "Checks support answer quality",
            "rubric": "Mention resolution steps and empathy.",
            "pass_threshold": 75,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def test_create_spec_and_case_flow(client: TestClient) -> None:
    spec = create_spec(client)
    spec_id = spec["eval_spec_id"]

    case_response = client.post(
        "/v1/eval-cases",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": spec_id,
            "name": "Refund escalation",
            "input_payload": {"task": "Handle refund request"},
            "notes": "Manual seed case",
        },
    )
    assert case_response.status_code == 201
    case = case_response.json()
    assert case["eval_spec_id"] == spec_id
    assert case["source"] == "manual"

    list_specs = client.get("/v1/eval-specs", params={"tenant_id": "tenant-a"})
    assert list_specs.status_code == 200
    assert len(list_specs.json()["eval_specs"]) == 1

    list_cases = client.get("/v1/eval-cases", params={"tenant_id": "tenant-a"})
    assert list_cases.status_code == 200
    assert len(list_cases.json()["eval_cases"]) == 1


def test_list_is_scoped_by_tenant(client: TestClient) -> None:
    create_spec(client, tenant_id="tenant-a", name="Tenant A spec")
    create_spec(client, tenant_id="tenant-b", name="Tenant B spec")

    tenant_a_specs = client.get("/v1/eval-specs", params={"tenant_id": "tenant-a"})
    tenant_b_specs = client.get("/v1/eval-specs", params={"tenant_id": "tenant-b"})

    assert len(tenant_a_specs.json()["eval_specs"]) == 1
    assert tenant_a_specs.json()["eval_specs"][0]["name"] == "Tenant A spec"
    assert len(tenant_b_specs.json()["eval_specs"]) == 1
    assert tenant_b_specs.json()["eval_specs"][0]["name"] == "Tenant B spec"


def test_cross_tenant_read_returns_not_found(client: TestClient) -> None:
    spec = create_spec(client, tenant_id="tenant-a")
    spec_id = spec["eval_spec_id"]

    response = client.get(
        f"/v1/eval-specs/{spec_id}",
        params={"tenant_id": "tenant-b"},
    )
    assert response.status_code == 404


def test_update_and_delete_spec(client: TestClient) -> None:
    spec = create_spec(client)
    spec_id = spec["eval_spec_id"]

    patch_response = client.patch(
        f"/v1/eval-specs/{spec_id}",
        params={"tenant_id": "tenant-a"},
        json={"name": "Updated spec", "pass_threshold": 80},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Updated spec"
    assert patch_response.json()["pass_threshold"] == 80

    delete_response = client.delete(
        f"/v1/eval-specs/{spec_id}",
        params={"tenant_id": "tenant-a"},
    )
    assert delete_response.status_code == 204

    get_response = client.get(
        f"/v1/eval-specs/{spec_id}",
        params={"tenant_id": "tenant-a"},
    )
    assert get_response.status_code == 404


def test_auth_mode_uses_bearer_token(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_STORAGE_BACKEND", "memory")
    with TestClient(create_app()) as client:
        headers = auth_headers(monkeypatch, tenant_id="tenant-auth")
        create_response = client.post(
            "/v1/eval-specs",
            headers=headers,
            json={
                "name": "Auth spec",
                "rubric": "Check auth path",
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["tenant_id"] == "tenant-auth"

        list_response = client.get("/v1/eval-specs", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["eval_specs"]) == 1


def test_create_case_requires_existing_spec(client: TestClient) -> None:
    response = client.post(
        "/v1/eval-cases",
        json={
            "tenant_id": "tenant-a",
            "eval_spec_id": "00000000-0000-0000-0000-000000000099",
            "name": "Missing spec",
            "input_payload": {"task": "noop"},
        },
    )
    assert response.status_code == 404
