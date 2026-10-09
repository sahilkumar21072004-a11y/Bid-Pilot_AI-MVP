from pathlib import Path

from alembic.config import Config


def make_alembic_config() -> Config:
    backend_dir = Path(__file__).resolve().parents[1]
    return Config(str(backend_dir / "alembic.ini"))
