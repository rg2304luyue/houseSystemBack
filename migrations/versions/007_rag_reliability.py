"""Add AI leases and privacy-filtered RAG failure feedback."""

from alembic import op
import sqlalchemy as sa


revision = "007_rag_reliability"
down_revision = "006_ai_agent_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns("ai_agent_run")}
    additions = (
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("lease_token", sa.String(36), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    for column in additions:
        if column.name not in columns:
            op.add_column("ai_agent_run", column)

    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("ai_agent_run")}
    for name, fields in (
        ("ix_ai_agent_run_status_lease", ["status", "lease_expires_at"]),
        ("ix_ai_agent_run_status_retry", ["status", "next_retry_at"]),
    ):
        if name not in indexes:
            op.create_index(name, "ai_agent_run", fields)

    inspector = sa.inspect(bind)
    if "rag_failure_case" not in inspector.get_table_names():
        op.create_table(
            "rag_failure_case",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("request_id", sa.String(36), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("origin", sa.String(20), nullable=False, server_default="user_feedback"),
            sa.Column("query_hash", sa.String(64), nullable=False),
            sa.Column("sanitized_query", sa.Text(), nullable=True),
            sa.Column("route", sa.String(30), nullable=True),
            sa.Column("failure_type", sa.String(40), nullable=False),
            sa.Column("index_signature", sa.String(64), nullable=True),
            sa.Column("retrieval_trace", sa.JSON(), nullable=True),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("expected_route", sa.String(30), nullable=True),
            sa.Column("expected_sources", sa.JSON(), nullable=True),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["request_id"], ["ai_agent_run.request_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["user_info.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("request_id", name="uq_rag_failure_case_request_id"),
        )
        op.create_index("ix_rag_failure_case_user_id", "rag_failure_case", ["user_id"])
        op.create_index("ix_rag_failure_case_review_status", "rag_failure_case", ["review_status"])


def downgrade() -> None:
    op.drop_table("rag_failure_case")
    for name in ("ix_ai_agent_run_status_retry", "ix_ai_agent_run_status_lease"):
        op.drop_index(name, table_name="ai_agent_run")
    for name in (
        "finished_at", "next_retry_at", "lease_expires_at", "lease_token",
        "heartbeat_at", "attempt_count",
    ):
        op.drop_column("ai_agent_run", name)
