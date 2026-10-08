from app.security import issue_token, verify_token
from fastapi.testclient import TestClient
from app.main import app


def test_signed_token_round_trip(monkeypatch) -> None:
    monkeypatch.setattr("app.security.settings.session_secret", "test-only-session-secret")
    token = issue_token("admin")
    assert verify_token(token) == {"username": "admin", "role": "admin"}


def test_invalid_signature_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr("app.security.settings.session_secret", "test-only-session-secret")
    token = issue_token("admin")
    assert verify_token(token + "x") is None


def test_login_protects_api_and_accepts_admin_token(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.auth_enabled", True)
    monkeypatch.setattr("app.main.settings.admin_username", "admin-test")
    monkeypatch.setattr("app.main.settings.admin_password", "private-test-password")
    monkeypatch.setattr("app.main.settings.session_secret", "private-test-session-secret")
    with TestClient(app) as client:
        assert client.get("/api/proposals").status_code == 401
        login = client.post("/api/auth/login", json={"username": "admin-test", "password": "private-test-password"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        assert client.get("/api/proposals", headers={"Authorization": f"Bearer {token}"}).status_code == 200
