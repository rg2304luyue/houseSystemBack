"""Normalize unambiguous legacy reservation and appointment states.

Revision ID: 009_legacy_state_cleanup
Revises: 008_business_integrity
"""

from alembic import op
import sqlalchemy as sa


revision = "009_legacy_state_cleanup"
down_revision = "008_business_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    now = sa.func.now()
    contract = sa.table(
        "contract",
        sa.column("payment_status", sa.String()),
        sa.column("currentDate", sa.DateTime()),
        sa.column("expires_at", sa.DateTime()),
    )
    appointment = sa.table(
        "appointment",
        sa.column("time", sa.DateTime()),
        sa.column("status", sa.String()),
        sa.column("updated_at", sa.DateTime()),
    )

    # Legacy contracts acquired payment_status='pending' when the column was
    # introduced. Derive the same 30-minute deadline used by new contracts.
    bind.execute(
        contract.update()
        .where(contract.c.payment_status == "pending")
        .where(contract.c.expires_at.is_(None))
        .values(
            expires_at=sa.func.coalesce(
                sa.func.date_add(contract.c.currentDate, sa.text("INTERVAL 30 MINUTE")),
                now,
            )
        )
    )
    bind.execute(
        contract.update()
        .where(contract.c.payment_status == "pending")
        .where(contract.c.expires_at <= now)
        .values(payment_status="expired")
    )
    bind.execute(
        appointment.update()
        .where(appointment.c.status == "pending")
        .where(appointment.c.time <= now)
        .values(status="expired", updated_at=now)
    )


def downgrade() -> None:
    # Data-state normalization is intentionally irreversible: reverting rows
    # to pending would recreate reservations that have already expired.
    pass
