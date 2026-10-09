from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from app import store
from app.migrations import make_alembic_config
from migrations.versions.v0001_versioned_schema import upgrade


def _run_upgrade(connection) -> None:
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        upgrade()


def test_fresh_database_receives_all_versioned_tables() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        _run_upgrade(connection)
        tables = set(inspect(connection).get_table_names())
    assert {"proposals", "knowledge", "settings", "templates", "team", "proposal_versions", "audit_events"} <= tables
    engine.dispose()


def test_existing_mvp_database_is_adopted_without_losing_proposals() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE proposals (id INTEGER PRIMARY KEY, title TEXT NOT NULL, source_name TEXT NOT NULL, "
            "requirements TEXT NOT NULL, sections TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Draft', "
            "reviewer TEXT NOT NULL DEFAULT '', comments TEXT NOT NULL DEFAULT '[]', "
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        ))
        connection.execute(text(
            "CREATE TABLE team (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, role TEXT NOT NULL DEFAULT 'Reviewer')"
        ))
        connection.execute(text(
            "INSERT INTO proposals (title,source_name,requirements,sections) VALUES ('Existing','rfp.txt','[]','[]')"
        ))
        _run_upgrade(connection)
        assert connection.execute(text("SELECT title FROM proposals WHERE id=1")).scalar_one() == "Existing"
        assert "workflow" in {column["name"] for column in inspect(connection).get_columns("proposals")}
        assert {"username", "password_hash", "active"} <= {column["name"] for column in inspect(connection).get_columns("team")}
        assert "alembic_version" not in inspect(connection).get_table_names()
    engine.dispose()


def test_startup_records_the_applied_migration(tmp_path, monkeypatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'migrated.db'}")
    monkeypatch.setattr(store, "engine", engine)
    store.initialize()
    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "0001_versioned_schema"
    engine.dispose()
