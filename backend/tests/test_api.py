from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_service_and_revision(monkeypatch) -> None:
    monkeypatch.setenv("APP_REVISION", "abc123")

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "dataops-demo-api",
        "revision": "abc123",
    }


def test_demo_message_is_stable() -> None:
    response = client.get("/api/message")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Next.js + FastAPI deployed by a self-hosted runner",
    }
