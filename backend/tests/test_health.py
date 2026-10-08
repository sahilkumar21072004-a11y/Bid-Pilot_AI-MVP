from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_application_and_status() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["application"] == "BID-PILOT AI"
    assert response.json()["status"] == "healthy"
