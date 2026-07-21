"""Add expiry time for pending contracts.

Revision ID: 002_contract_expiry
Revises: 001_payment_fields
"""
from alembic import op
import sqlalchemy as sa

revision = "002_contract_expiry"
down_revision = "001_payment_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("contract")}
    indexes = {index["name"] for index in inspector.get_indexes("contract")}

    if "expires_at" not in columns:
        op.add_column("contract", sa.Column("expires_at", sa.DateTime(), nullable=True))
    if "ix_contract_expires_at" not in indexes:
        op.create_index("ix_contract_expires_at", "contract", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contract_expires_at", table_name="contract")
    op.drop_column("contract", "expires_at")
