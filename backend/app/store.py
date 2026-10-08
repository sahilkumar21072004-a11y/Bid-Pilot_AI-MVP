"""Small SQLAlchemy-backed storage adapter supporting SQLite and PostgreSQL."""
from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, MetaData, Table, Text, UniqueConstraint, create_engine, func, inspect, text
from sqlalchemy.engine import Connection, Row

from .config import settings

metadata = MetaData()
proposals = Table("proposals", metadata,
    Column("id", Integer, primary_key=True), Column("title", Text, nullable=False), Column("source_name", Text, nullable=False),
    Column("requirements", Text, nullable=False), Column("sections", Text, nullable=False), Column("status", Text, nullable=False, server_default="Draft"),
    Column("reviewer", Text, nullable=False, server_default=""), Column("comments", Text, nullable=False, server_default="[]"),
    Column("workflow", Text, nullable=False, server_default="{}"), Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    Column("updated_at", DateTime, nullable=False, server_default=func.current_timestamp()))
knowledge = Table("knowledge", metadata,
    Column("id", Integer, primary_key=True), Column("title", Text, nullable=False), Column("content", Text, nullable=False),
    Column("category", Text, nullable=False, server_default="General"), Column("tags", Text, nullable=False, server_default=""))
settings_table = Table("settings", metadata, Column("key", Text, primary_key=True), Column("value", Text, nullable=False))
templates = Table("templates", metadata, Column("id", Integer, primary_key=True), Column("name", Text, nullable=False), Column("sections", Text, nullable=False))
team = Table("team", metadata,
    Column("id", Integer, primary_key=True), Column("name", Text, nullable=False), Column("email", Text, nullable=False, unique=True),
    Column("role", Text, nullable=False, server_default="Reviewer"), Column("username", Text),
    Column("password_hash", Text), Column("active", Boolean, nullable=False, server_default=text("true")))
proposal_versions = Table("proposal_versions", metadata,
    Column("id", Integer, primary_key=True), Column("proposal_id", Integer, ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False),
    Column("version_number", Integer, nullable=False), Column("snapshot", Text, nullable=False), Column("created_by", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    UniqueConstraint("proposal_id", "version_number", name="uq_proposal_version"))
audit_events = Table("audit_events", metadata,
    Column("id", Integer, primary_key=True), Column("actor", Text, nullable=False), Column("action", Text, nullable=False),
    Column("entity_type", Text, nullable=False), Column("entity_id", Text, nullable=False), Column("details", Text, nullable=False, server_default="{}"),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()))

_url = settings.database_url.strip() or f"sqlite:///{settings.database_path}"
_engine_options: dict[str, Any] = {"pool_pre_ping": True}
if _url.startswith("sqlite:"):
    _engine_options["connect_args"] = {"check_same_thread": False, "timeout": 30}
engine = create_engine(_url, **_engine_options)


class CompatRow:
    def __init__(self, row: Row[Any]):
        self._row = row
        self._mapping = row._mapping

    def __getitem__(self, key: int | str) -> Any:
        return self._row[key] if isinstance(key, int) else self._mapping[key]

    def keys(self):
        return self._mapping.keys()


class CompatResult:
    def __init__(self, result: Any, lastrowid: int | None = None):
        self._result = result
        self.lastrowid = lastrowid
        self.rowcount = result.rowcount

    def fetchone(self) -> CompatRow | None:
        row = self._result.fetchone()
        return CompatRow(row) if row is not None else None

    def fetchall(self) -> list[CompatRow]:
        return [CompatRow(row) for row in self._result.fetchall()]


class CompatConnection:
    def __init__(self, connection: Connection):
        self._connection = connection

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] | dict[str, Any] = ()) -> CompatResult:
        statement = sql.strip()
        ignore_insert = statement.upper().startswith("INSERT OR IGNORE INTO")
        if ignore_insert:
            statement = re.sub(r"^INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", statement, flags=re.I)
            if "ON CONFLICT" not in statement.upper():
                statement += " ON CONFLICT DO NOTHING"
        values: dict[str, Any]
        if isinstance(params, dict):
            values = params
        else:
            index = 0
            def replace_parameter(_: re.Match[str]) -> str:
                nonlocal index
                name = f"p{index}"
                index += 1
                return f":{name}"
            statement = re.sub(r"\?", replace_parameter, statement)
            values = {f"p{i}": value for i, value in enumerate(params)}
        returns_id = bool(re.match(r"INSERT\s+INTO\s+(?:proposals|knowledge|templates|team|proposal_versions|audit_events)\b", statement, re.I)) and "RETURNING" in statement.upper()
        result = self._connection.execute(text(statement), values)
        lastrowid = None
        if returns_id:
            row = result.fetchone()
            lastrowid = int(row[0]) if row is not None else None
        return CompatResult(result, lastrowid)


@contextmanager
def connect() -> Iterator[CompatConnection]:
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield CompatConnection(connection)
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()


def initialize() -> None:
    metadata.create_all(engine)
    inspector = inspect(engine)
    migrations = {
        "proposals": {"workflow": "TEXT NOT NULL DEFAULT '{}'"},
        "team": {"username": "TEXT", "password_hash": "TEXT", "active": "BOOLEAN NOT NULL DEFAULT TRUE"},
    }
    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            existing = {item["name"] for item in inspector.get_columns(table_name)}
            for column_name, sql_type in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_team_username ON team(username)"))
        connection.execute(text("INSERT INTO settings(key,value) VALUES('company','{}') ON CONFLICT(key) DO NOTHING"))
        existing_template = connection.execute(text("SELECT id FROM templates WHERE name='Standard proposal' LIMIT 1")).first()
        if not existing_template:
            default_sections = '["Executive Summary", "Understanding the Requirements", "Delivery Approach", "Project Timeline", "Investment", "Risk and Governance"]'
            connection.execute(text("INSERT INTO templates(name,sections) VALUES('Standard proposal',:sections)"), {"sections": default_sections})


def row_dict(row: CompatRow | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row._mapping)
