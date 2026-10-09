"""Create the current schema and adopt existing local MVP databases."""
from alembic import op
import sqlalchemy as sa

revision = "0001_versioned_schema"
down_revision = None
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    tables = _tables()

    if "proposals" not in tables:
        op.create_table(
            "proposals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("source_name", sa.Text(), nullable=False),
            sa.Column("requirements", sa.Text(), nullable=False),
            sa.Column("sections", sa.Text(), nullable=False),
            sa.Column("status", sa.Text(), server_default="Draft", nullable=False),
            sa.Column("reviewer", sa.Text(), server_default="", nullable=False),
            sa.Column("comments", sa.Text(), server_default="[]", nullable=False),
            sa.Column("workflow", sa.Text(), server_default="{}", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )
    elif "workflow" not in _columns("proposals"):
        op.add_column("proposals", sa.Column("workflow", sa.Text(), server_default="{}", nullable=False))

    if "knowledge" not in tables:
        op.create_table(
            "knowledge",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("category", sa.Text(), server_default="General", nullable=False),
            sa.Column("tags", sa.Text(), server_default="", nullable=False),
        )

    if "settings" not in tables:
        op.create_table(
            "settings",
            sa.Column("key", sa.Text(), primary_key=True),
            sa.Column("value", sa.Text(), nullable=False),
        )

    if "templates" not in tables:
        op.create_table(
            "templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("sections", sa.Text(), nullable=False),
        )

    if "team" not in tables:
        op.create_table(
            "team",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("email", sa.Text(), nullable=False),
            sa.Column("role", sa.Text(), server_default="Reviewer", nullable=False),
            sa.Column("username", sa.Text()),
            sa.Column("password_hash", sa.Text()),
            sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.UniqueConstraint("email", name="uq_team_email"),
        )
    else:
        team_columns = _columns("team")
        if "username" not in team_columns:
            op.add_column("team", sa.Column("username", sa.Text()))
        if "password_hash" not in team_columns:
            op.add_column("team", sa.Column("password_hash", sa.Text()))
        if "active" not in team_columns:
            op.add_column("team", sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False))

    if "proposal_versions" not in tables:
        op.create_table(
            "proposal_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("snapshot", sa.Text(), nullable=False),
            sa.Column("created_by", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.UniqueConstraint("proposal_id", "version_number", name="uq_proposal_version"),
        )

    if "audit_events" not in tables:
        op.create_table(
            "audit_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("actor", sa.Text(), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("entity_type", sa.Text(), nullable=False),
            sa.Column("entity_id", sa.Text(), nullable=False),
            sa.Column("details", sa.Text(), server_default="{}", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("team")}
    if "uq_team_username" not in indexes:
        op.create_index("uq_team_username", "team", ["username"], unique=True)


def downgrade() -> None:
    raise NotImplementedError(
        "The baseline schema migration is forward-only to prevent accidental loss of proposal and audit data. "
        "Restore a verified backup to roll back."
    )
