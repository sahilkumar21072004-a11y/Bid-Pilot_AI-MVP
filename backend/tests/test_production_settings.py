import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_unsafe_defaults() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production")


def test_production_accepts_explicit_auth_and_scanner_configuration() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_enabled=True,
        admin_password="a-long-private-admin-password",
        session_secret="s" * 48,
        clamav_enabled=True,
        frontend_origin="https://bids.example.com",
    )
    assert settings.is_production
