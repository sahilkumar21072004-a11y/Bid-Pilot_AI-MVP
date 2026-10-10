"""Store failed-login windows for shared throttling."""
from alembic import op
import sqlalchemy as sa

revision = "0002_auth_attempts"
down_revision = "0001_versioned_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "login_attempts" not in tables:
        op.create_table(
            "login_attempts",
            sa.Column("key", sa.String(length=64), primary_key=True),
            sa.Column("window_started_at", sa.Integer(), nullable=False),
            sa.Column("failures", sa.Integer(), server_default="0", nullable=False),
            sa.Column("locked_until", sa.Integer(), server_default="0", nullable=False),
        )


def downgrade() -> None:
    op.drop_table("login_attempts")
