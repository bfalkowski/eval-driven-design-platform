from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready() -> None:
    response = client.get("/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_legacy_health_paths() -> None:
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_metrics() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
