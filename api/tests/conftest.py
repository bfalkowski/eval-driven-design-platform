from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("APP_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("APP_AUTH_ENABLED", "false")
    with TestClient(create_app()) as test_client:
        yield test_client
