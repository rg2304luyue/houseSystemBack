"""Reset unreviewed ownership and add payment reconciliation audit fields.

Revision ID: 013_reconciliation_workflow
Revises: 012_payment_foreign_keys
"""

from alembic import op
import sqlalchemy as sa


revision = "013_reconciliation_workflow"
down_revision = "012_payment_foreign_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No historical listing has completed the new administrator review flow.
    op.execute("UPDATE house_info SET ownership_status = 'pending' WHERE ownership_status = 'verified'")
    op.add_column("contract", sa.Column("reconciled_at", sa.DateTime(), nullable=True))
    op.add_column("contract", sa.Column("reconciled_by", sa.Integer(), nullable=True))
    op.add_column("contract", sa.Column("reconciliation_resolution", sa.String(32), nullable=True))
    op.add_column("contract", sa.Column("reconciliation_note", sa.String(500), nullable=True))
    op.create_index("ix_contract_reconciled_by", "contract", ["reconciled_by"])
    op.create_foreign_key(
        "fk_contract_reconciled_by_user",
        "contract",
        "user_info",
        ["reconciled_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_contract_reconciled_by_user", "contract", type_="foreignkey")
    op.drop_index("ix_contract_reconciled_by", table_name="contract")
    op.drop_column("contract", "reconciliation_note")
    op.drop_column("contract", "reconciliation_resolution")
    op.drop_column("contract", "reconciled_by")
    op.drop_column("contract", "reconciled_at")
