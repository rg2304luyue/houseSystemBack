"""Widen rental username columns to match their String(255) sources.

Revision ID: 014_rental_username_length
Revises: 013_reconciliation_workflow

_ensure_rental copies contract.tenantName / landlordName (String(255), sourced
from user_info.name / house_info.landlord, both String(255)) into
rental.tenant_username / landlord_username (String(50)).  A name longer than
50 characters makes the payment-confirmation insert fail under MySQL strict
mode, leaving a paid contract stuck in pending.
"""

from alembic import op


revision = "014_rental_username_length"
down_revision = "013_reconciliation_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE rental MODIFY tenant_username VARCHAR(255) NOT NULL")
    op.execute("ALTER TABLE rental MODIFY landlord_username VARCHAR(255) NOT NULL")


def downgrade() -> None:
    # Truncate first so the narrow column cannot fail on existing long values.
    op.execute("UPDATE rental SET tenant_username = LEFT(tenant_username, 50)")
    op.execute("UPDATE rental SET landlord_username = LEFT(landlord_username, 50)")
    op.execute("ALTER TABLE rental MODIFY tenant_username VARCHAR(50) NOT NULL")
    op.execute("ALTER TABLE rental MODIFY landlord_username VARCHAR(50) NOT NULL")
