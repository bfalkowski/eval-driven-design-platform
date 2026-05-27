from __future__ import annotations

import json

import httpx

from components.api_client import ServiceClient


def test_create_eval_spec_uses_tenant_query_when_auth_disabled() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(201, json={"eval_spec_id": "spec-1", "name": "Demo"})

    client = ServiceClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    client.create_eval_spec(
        tenant_id="tenant-a",
        name="Support quality",
        rubric="Mention empathy.",
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/eval-specs"
    assert captured["body"]["tenant_id"] == "tenant-a"


def test_list_eval_specs_omits_tenant_when_bearer_token_set() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"eval_specs": []})

    client = ServiceClient(
        base_url="http://testserver",
        bearer_token="demo-token",
        transport=httpx.MockTransport(handler),
    )
    client.list_eval_specs(tenant_id="tenant-a")

    assert captured["params"] == {"limit": "50"}
    assert captured["headers"]["authorization"] == "Bearer demo-token"


def test_import_langfuse_trace_case_sends_expected_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(201, json={"eval_case_id": "case-1"})

    client = ServiceClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    client.import_langfuse_trace_case(
        tenant_id="tenant-a",
        eval_spec_id="spec-1",
        trace_id="trace-1",
        name="Imported",
        notes="note",
    )

    assert captured["path"] == "/v1/integrations/langfuse/import-case"
    assert captured["body"]["tenant_id"] == "tenant-a"
    assert captured["body"]["eval_spec_id"] == "spec-1"
    assert captured["body"]["trace_id"] == "trace-1"
