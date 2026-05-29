from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_API_BASE_URL = "http://localhost:8000"


def get_api_base_url() -> str:
    return os.getenv("EDD_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


class ServiceClient:
    def __init__(
        self,
        base_url: str | None = None,
        bearer_token: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        configured_url = base_url or get_api_base_url()
        self.base_url = configured_url.rstrip("/")
        self._bearer_token = bearer_token.strip() if bearer_token else None
        self._transport = transport

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health")

    def ready(self) -> dict[str, Any]:
        return self._request("GET", "/v1/ready")

    def metrics(self) -> str:
        return self._request_text("GET", "/metrics")

    def list_eval_specs(self, *, tenant_id: str | None, limit: int = 50) -> dict[str, Any]:
        return self._request(
            "GET",
            "/v1/eval-specs",
            params={"limit": limit, **self._tenant_params(tenant_id)},
        )

    def create_eval_spec(
        self,
        *,
        tenant_id: str | None,
        name: str,
        rubric: str,
        description: str | None = None,
        pass_threshold: float = 70.0,
        version: str = "1",
    ) -> dict[str, Any]:
        payload = self._tenant_body(
            {
                "name": name,
                "description": description,
                "version": version,
                "rubric": rubric,
                "pass_threshold": pass_threshold,
            },
            tenant_id,
        )
        return self._request("POST", "/v1/eval-specs", json=payload)

    def list_eval_cases(
        self,
        *,
        tenant_id: str | None,
        eval_spec_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, **self._tenant_params(tenant_id)}
        if eval_spec_id:
            params["eval_spec_id"] = eval_spec_id
        return self._request("GET", "/v1/eval-cases", params=params)

    def create_eval_case(
        self,
        *,
        tenant_id: str | None,
        eval_spec_id: str,
        name: str,
        task: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        payload = self._tenant_body(
            {
                "eval_spec_id": eval_spec_id,
                "name": name,
                "input_payload": {"task": task},
                "notes": notes,
                "source": "manual",
            },
            tenant_id,
        )
        return self._request("POST", "/v1/eval-cases", json=payload)

    def list_experiment_runs(
        self,
        *,
        tenant_id: str | None,
        eval_spec_id: str | None = None,
        ingest_source: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, **self._tenant_params(tenant_id)}
        if eval_spec_id:
            params["eval_spec_id"] = eval_spec_id
        if ingest_source:
            params["ingest_source"] = ingest_source
        return self._request("GET", "/v1/experiment-runs", params=params)

    def create_experiment_run(
        self,
        *,
        tenant_id: str | None,
        eval_spec_id: str,
        candidate_version: str,
        eval_case_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = self._tenant_body(
            {
                "eval_spec_id": eval_spec_id,
                "candidate_version": candidate_version,
                "eval_case_ids": eval_case_ids,
            },
            tenant_id,
        )
        return self._request("POST", "/v1/experiment-runs", json=payload)

    def get_experiment_run_summary(
        self,
        *,
        tenant_id: str | None,
        experiment_run_id: str,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/experiment-runs/{experiment_run_id}/summary",
            params=self._tenant_params(tenant_id),
        )

    def get_experiment_run_gate(
        self,
        *,
        tenant_id: str | None,
        experiment_run_id: str,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/experiment-runs/{experiment_run_id}/gate",
            params=self._tenant_params(tenant_id),
        )

    def list_evaluation_results(
        self,
        *,
        tenant_id: str | None,
        experiment_run_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, **self._tenant_params(tenant_id)}
        if experiment_run_id:
            params["experiment_run_id"] = experiment_run_id
        return self._request("GET", "/v1/evaluation-results", params=params)

    def get_langfuse_health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/integrations/langfuse/health")

    def get_langfuse_trace(self, *, trace_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/integrations/langfuse/traces/{trace_id}")

    def import_langfuse_trace_case(
        self,
        *,
        tenant_id: str | None,
        eval_spec_id: str,
        trace_id: str,
        name: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        payload = self._tenant_body(
            {
                "eval_spec_id": eval_spec_id,
                "trace_id": trace_id,
                "name": name,
                "notes": notes,
            },
            tenant_id,
        )
        return self._request("POST", "/v1/integrations/langfuse/import-case", json=payload)

    def _tenant_params(self, tenant_id: str | None) -> dict[str, str]:
        if self._bearer_token or tenant_id is None:
            return {}
        return {"tenant_id": tenant_id}

    def _tenant_body(self, payload: dict[str, Any], tenant_id: str | None) -> dict[str, Any]:
        body = dict(payload)
        if self._bearer_token:
            body.pop("tenant_id", None)
        elif tenant_id:
            body["tenant_id"] = tenant_id
        return body

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self._send(method, path, **kwargs)
        return response.json()

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        response = self._send(method, path, **kwargs)
        return response.text

    def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            headers = dict(kwargs.pop("headers", {}))
            if self._bearer_token:
                headers["authorization"] = f"Bearer {self._bearer_token}"
            with httpx.Client(
                base_url=self.base_url,
                timeout=10.0,
                transport=self._transport,
            ) as client:
                response = client.request(method, path, headers=headers, **kwargs)
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise RuntimeError(detail or f"Service returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Unable to reach service at {self.base_url}") from exc
