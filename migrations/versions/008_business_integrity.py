"""Expand appointments with stable participants, status, and audit timestamps."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "008_business_integrity"
down_revision = "007_rag_reliability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns("appointment")}
    additions = (
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("house_id", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("landlord_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for column in additions:
        if column.name not in columns:
            op.add_column("appointment", column)

    # house_info.id is INT UNSIGNED in the legacy schema. This alter also
    # repairs a partially applied MySQL migration that created a signed column
    # before the foreign-key step failed.
    op.alter_column(
        "appointment", "house_id",
        existing_type=sa.Integer(),
        type_=mysql.INTEGER(unsigned=True),
        existing_nullable=True,
    )

    inspector = sa.inspect(bind)
    indexes = {item["name"] for item in inspector.get_indexes("appointment")}
    for name, fields in (
        ("ix_appointment_user_time", ["user_id", "time"]),
        ("ix_appointment_landlord_time", ["landlord_id", "time"]),
        ("ix_appointment_house_time", ["house_id", "time"]),
        ("ix_appointment_status", ["status"]),
    ):
        if name not in indexes:
            op.create_index(name, "appointment", fields)

    foreign_keys = {item.get("name") for item in sa.inspect(bind).get_foreign_keys("appointment")}
    for name, local, remote in (
        ("fk_appointment_user", "user_id", "user_info.id"),
        ("fk_appointment_house", "house_id", "house_info.id"),
        ("fk_appointment_landlord", "landlord_id", "user_info.id"),
    ):
        if name not in foreign_keys:
            table, column = remote.split(".")
            op.create_foreign_key(name, "appointment", table, [local], [column], ondelete="SET NULL")


def downgrade() -> None:
    for name in ("fk_appointment_landlord", "fk_appointment_house", "fk_appointment_user"):
        op.drop_constraint(name, "appointment", type_="foreignkey")
    for name in (
        "ix_appointment_status", "ix_appointment_house_time",
        "ix_appointment_landlord_time", "ix_appointment_user_time",
    ):
        op.drop_index(name, table_name="appointment")
    for name in ("updated_at", "created_at", "status", "landlord_id", "house_id", "user_id"):
        op.drop_column("appointment", name)
