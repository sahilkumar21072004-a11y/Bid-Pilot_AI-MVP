from fastapi.testclient import TestClient

from app.main import app


def test_login_is_throttled_after_repeated_failures(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.auth_enabled", True)
    monkeypatch.setattr("app.main.settings.admin_username", "admin-rate-test")
    monkeypatch.setattr("app.main.settings.admin_password", "private-test-password")
    monkeypatch.setattr("app.main.settings.session_secret", "private-test-session-secret-rate-test")
    username = "throttle-user-unique"

    with TestClient(app) as client:
        for _ in range(5):
            response = client.post("/api/auth/login", json={"username": username, "password": "wrong-password"})
            assert response.status_code == 401
        limited = client.post("/api/auth/login", json={"username": username, "password": "wrong-password"})
        assert limited.status_code == 429
        assert int(limited.headers["retry-after"]) > 0


def test_login_rate_limit_clears_after_success(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.auth_enabled", True)
    monkeypatch.setattr("app.main.settings.admin_username", "admin-success-test")
    monkeypatch.setattr("app.main.settings.admin_password", "private-test-password")
    monkeypatch.setattr("app.main.settings.session_secret", "private-test-session-secret-success")
    username = "throttle-success-unique"

    with TestClient(app) as client:
        for _ in range(4):
            assert client.post("/api/auth/login", json={"username": username, "password": "wrong"}).status_code == 401
        success = client.post("/api/auth/login", json={"username": "admin-success-test", "password": "private-test-password"})
        assert success.status_code == 200
