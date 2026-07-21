"""Add persistent idempotency and cancellation state for AI agent runs."""

from alembic import op
import sqlalchemy as sa


revision = "006_ai_agent_runs"
down_revision = "005_message_user_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ai_agent_run" not in inspector.get_table_names():
        op.create_table(
            "ai_agent_run",
            sa.Column("request_id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("user_message_id", sa.Integer(), nullable=False),
            sa.Column("assistant_message_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="running"),
            sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("error_code", sa.String(50), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["user_info.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["session_id"], ["chat_session.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_message_id"], ["chat_message.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assistant_message_id"], ["chat_message.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("user_message_id", name="uq_ai_agent_run_user_message_id"),
            sa.UniqueConstraint("assistant_message_id", name="uq_ai_agent_run_assistant_message_id"),
        )

    existing_indexes = {
        item["name"] for item in sa.inspect(op.get_bind()).get_indexes("ai_agent_run")
    }
    for name, columns in (
        ("ix_ai_agent_run_user_id", ["user_id"]),
        ("ix_ai_agent_run_session_id", ["session_id"]),
        ("ix_ai_agent_run_status", ["status"]),
    ):
        if name not in existing_indexes:
            op.create_index(name, "ai_agent_run", columns)


def downgrade() -> None:
    op.drop_table("ai_agent_run")
