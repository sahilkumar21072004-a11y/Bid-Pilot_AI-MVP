from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BID-PILOT AI"
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
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")


settings = Settings()
