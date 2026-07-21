"""Add stable user/contract identifiers for listings and rentals.

Revision ID: 003_stable_ownership_ids
Revises: 002_contract_expiry

Legacy names and phone numbers are not unique.  This migration therefore
keeps every new identifier nullable and only backfills rows for which a
single user can be identified.  Ambiguous rows remain unassigned for an
administrator to reconcile later.
"""

from alembic import op
import sqlalchemy as sa


revision = "003_stable_ownership_ids"
down_revision = "002_contract_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL DDL is non-transactional.  The guards also make recovery safe if
    # a previous run stopped after adding only part of this expand migration.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    house_columns = {column["name"] for column in inspector.get_columns("house_info")}
    rental_columns = {column["name"] for column in inspector.get_columns("rental")}
    house_indexes = {index["name"] for index in inspector.get_indexes("house_info")}
    rental_indexes = {index["name"] for index in inspector.get_indexes("rental")}

    if "landlord_id" not in house_columns:
        op.add_column("house_info", sa.Column("landlord_id", sa.Integer(), nullable=True))
    if "ix_house_info_landlord_id" not in house_indexes:
        op.create_index("ix_house_info_landlord_id", "house_info", ["landlord_id"], unique=False)

    for column_name in ("contract_id", "tenant_id", "landlord_id"):
        if column_name not in rental_columns:
            op.add_column("rental", sa.Column(column_name, sa.Integer(), nullable=True))
    if "uq_rental_contract_id" not in rental_indexes:
        op.create_index("uq_rental_contract_id", "rental", ["contract_id"], unique=True)
    if "ix_rental_tenant_id" not in rental_indexes:
        op.create_index("ix_rental_tenant_id", "rental", ["tenant_id"], unique=False)
    if "ix_rental_landlord_id" not in rental_indexes:
        op.create_index("ix_rental_landlord_id", "rental", ["landlord_id"], unique=False)

    # MySQL-compatible conservative backfills.  A duplicated phone/name is
    # deliberately ignored rather than granting a listing to the wrong user.
    op.execute(sa.text("""
        UPDATE house_info AS h
        JOIN (
            SELECT phone, MIN(id) AS user_id
            FROM user_info
            WHERE phone IS NOT NULL AND phone <> ''
            GROUP BY phone
            HAVING COUNT(*) = 1
        ) AS u ON u.phone = h.phone_num
        SET h.landlord_id = u.user_id
        WHERE h.landlord_id IS NULL
    """))
    op.execute(sa.text("""
        UPDATE rental AS r
        JOIN (
            SELECT name, MIN(id) AS user_id
            FROM user_info
            WHERE name IS NOT NULL AND name <> ''
            GROUP BY name
            HAVING COUNT(*) = 1
        ) AS u ON u.name = r.tenant_username
        SET r.tenant_id = u.user_id
        WHERE r.tenant_id IS NULL
    """))
    op.execute(sa.text("""
        UPDATE rental AS r
        JOIN house_info AS h ON h.id = r.house_id
        SET r.landlord_id = h.landlord_id
        WHERE r.landlord_id IS NULL AND h.landlord_id IS NOT NULL
    """))

    # contract_id is intentionally not guessed for legacy rentals.  Existing
    # contract status and identity data are inconsistent; all newly confirmed
    # payments populate this field deterministically in application code.


def downgrade() -> None:
    op.drop_index("ix_rental_landlord_id", table_name="rental")
    op.drop_index("ix_rental_tenant_id", table_name="rental")
    op.drop_index("uq_rental_contract_id", table_name="rental")
    op.drop_column("rental", "landlord_id")
    op.drop_column("rental", "tenant_id")
    op.drop_column("rental", "contract_id")
    op.drop_index("ix_house_info_landlord_id", table_name="house_info")
    op.drop_column("house_info", "landlord_id")
