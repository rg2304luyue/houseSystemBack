"""Add payment tracking fields to contract table.

Revision ID: 001
Revises: None (baseline for existing tables)
Create Date: 2026-07-17

This migration adds payment_status, payment_trade_no, and paid_at columns
to the contract table to support the payment state machine (P0.4).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "001_payment_fields"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("contract")}
    indexes = {index["name"] for index in inspector.get_indexes("contract")}

    if "payment_status" not in columns:
        op.add_column(
            "contract",
            sa.Column(
                "payment_status",
                sa.String(20),
                nullable=True,
                server_default="pending",
                comment="Payment state: pending/paid/cancelled/expired",
            ),
        )
    if "payment_trade_no" not in columns:
        op.add_column(
            "contract",
            sa.Column(
                "payment_trade_no",
                sa.String(64),
                nullable=True,
                comment="Alipay out_trade_no for idempotency",
            ),
        )
    if "paid_at" not in columns:
        op.add_column(
            "contract",
            sa.Column(
                "paid_at",
                sa.DateTime(),
                nullable=True,
                comment="Timestamp when payment was confirmed",
            ),
        )
    if "ix_contract_payment_trade_no" not in indexes:
        op.create_index(
            "ix_contract_payment_trade_no",
            "contract",
            ["payment_trade_no"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_contract_payment_trade_no", table_name="contract")
    op.drop_column("contract", "paid_at")
    op.drop_column("contract", "payment_trade_no")
    op.drop_column("contract", "payment_status")
