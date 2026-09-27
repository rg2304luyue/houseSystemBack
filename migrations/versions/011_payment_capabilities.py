"""Add listing capabilities and payment reconciliation audit fields.

Revision ID: 011_payment_capabilities
Revises: 010_listing_title_consistency
"""

from alembic import op
import sqlalchemy as sa


revision = "011_payment_capabilities"
down_revision = "010_listing_title_consistency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("house_info", sa.Column("ownership_status", sa.String(20), nullable=False, server_default="pending"))
    op.alter_column("contract", "payment_status", existing_type=sa.String(20), type_=sa.String(32), existing_nullable=True)
    op.add_column("contract", sa.Column("payment_notified_at", sa.DateTime(), nullable=True))
    op.add_column("contract", sa.Column("payment_notify_trade_no", sa.String(64), nullable=True))
    op.add_column("contract", sa.Column("payment_notify_amount", sa.Numeric(10, 2), nullable=True))
    op.add_column("contract", sa.Column("reconciliation_reason", sa.String(255), nullable=True))
    op.add_column("rental", sa.Column("source", sa.String(20), nullable=False, server_default="legacy"))


def downgrade() -> None:
    op.execute("UPDATE contract SET payment_status = 'expired' WHERE payment_status = 'reconciliation_required'")
    op.drop_column("rental", "source")
    op.drop_column("contract", "reconciliation_reason")
    op.drop_column("contract", "payment_notify_amount")
    op.drop_column("contract", "payment_notify_trade_no")
    op.drop_column("contract", "payment_notified_at")
    op.alter_column("contract", "payment_status", existing_type=sa.String(32), type_=sa.String(20), existing_nullable=True)
    op.drop_column("house_info", "ownership_status")
