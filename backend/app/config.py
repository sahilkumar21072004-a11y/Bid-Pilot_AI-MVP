from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BID-PILOT AI"
    app_env: str = "development"
    database_path: str = "./bidpilot.db"
    database_url: str = ""
    frontend_origin: str = "http://localhost:5173"
    demo_mode: bool = True
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    tesseract_cmd: str = ""
    auth_enabled: bool = False
    admin_username: str = "admin"
    admin_password: str = ""
    session_secret: str = ""
    clamav_enabled: bool = False
    clamav_host: str = "127.0.0.1"
    clamav_port: int = 3310

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.is_production:
            return self
        problems = []
        if not self.auth_enabled:
            problems.append("AUTH_ENABLED=true is required")
        if len(self.admin_password) < 16:
            problems.append("ADMIN_PASSWORD must contain at least 16 characters")
        if len(self.session_secret) < 32:
            problems.append("SESSION_SECRET must contain at least 32 characters")
        if not self.clamav_enabled:
            problems.append("CLAMAV_ENABLED=true is required")
        if not self.frontend_origin.startswith("https://"):
            problems.append("FRONTEND_ORIGIN must use HTTPS")
        if problems:
            raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")


settings = Settings()
