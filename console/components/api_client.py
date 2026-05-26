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
