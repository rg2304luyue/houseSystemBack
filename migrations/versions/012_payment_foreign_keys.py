"""Clean proven orphans and add payment-domain foreign keys.

Revision ID: 012_payment_foreign_keys
Revises: 011_payment_capabilities
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "012_payment_foreign_keys"
down_revision = "011_payment_capabilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Historical landlord IDs that do not identify a platform user carry no
    # trustworthy ownership semantics; retain snapshots and clear only the ID.
    op.execute("UPDATE contract c LEFT JOIN user_info u ON u.id = c.landlordId SET c.landlordId = NULL WHERE c.landlordId IS NOT NULL AND u.id IS NULL")
    orphan_checks = {
        "contract.houseId": "SELECT COUNT(*) FROM contract c LEFT JOIN house_info h ON h.id = c.houseId WHERE c.houseId IS NOT NULL AND h.id IS NULL",
        "contract.tenantId": "SELECT COUNT(*) FROM contract c LEFT JOIN user_info u ON u.id = c.tenantId WHERE c.tenantId IS NOT NULL AND u.id IS NULL",
        "rental.house_id": "SELECT COUNT(*) FROM rental r LEFT JOIN house_info h ON h.id = r.house_id WHERE r.house_id IS NULL OR h.id IS NULL",
        "rental.contract_id": "SELECT COUNT(*) FROM rental r LEFT JOIN contract c ON c.id = r.contract_id WHERE r.contract_id IS NOT NULL AND c.id IS NULL",
        "rental.tenant_id": "SELECT COUNT(*) FROM rental r LEFT JOIN user_info u ON u.id = r.tenant_id WHERE r.tenant_id IS NOT NULL AND u.id IS NULL",
        "rental.landlord_id": "SELECT COUNT(*) FROM rental r LEFT JOIN user_info u ON u.id = r.landlord_id WHERE r.landlord_id IS NOT NULL AND u.id IS NULL",
        "house_info.landlord_id": "SELECT COUNT(*) FROM house_info h LEFT JOIN user_info u ON u.id = h.landlord_id WHERE h.landlord_id IS NOT NULL AND u.id IS NULL",
    }
    failures = [name for name, query in orphan_checks.items() if bind.execute(sa.text(query)).scalar_one()]
    if failures:
        raise RuntimeError(f"Cannot add payment-domain foreign keys; unresolved references: {', '.join(failures)}")

    op.alter_column("contract", "houseId", existing_type=sa.Integer(), type_=mysql.INTEGER(unsigned=True), existing_nullable=True)
    op.alter_column("rental", "house_id", existing_type=sa.Integer(), type_=mysql.INTEGER(unsigned=True), existing_nullable=True, nullable=False)
    indexes = {table: {item["name"] for item in sa.inspect(bind).get_indexes(table)} for table in ("contract", "rental")}
    for table, name, columns in (("contract", "ix_contract_tenantId", ["tenantId"]), ("contract", "ix_contract_landlordId", ["landlordId"]), ("rental", "ix_rental_house_id", ["house_id"])):
        if name not in indexes[table]:
            op.create_index(name, table, columns)

    foreign_keys = {table: {item["name"] for item in sa.inspect(bind).get_foreign_keys(table)} for table in ("house_info", "contract", "rental")}
    constraints = (
        ("house_info", "fk_house_landlord_user", "user_info", ["landlord_id"], ["id"], "SET NULL"),
        ("contract", "fk_contract_tenant_user", "user_info", ["tenantId"], ["id"], "SET NULL"),
        ("contract", "fk_contract_landlord_user", "user_info", ["landlordId"], ["id"], "SET NULL"),
        ("contract", "fk_contract_house", "house_info", ["houseId"], ["id"], "RESTRICT"),
        ("rental", "fk_rental_tenant_user", "user_info", ["tenant_id"], ["id"], "SET NULL"),
        ("rental", "fk_rental_landlord_user", "user_info", ["landlord_id"], ["id"], "SET NULL"),
        ("rental", "fk_rental_contract", "contract", ["contract_id"], ["id"], "RESTRICT"),
        ("rental", "fk_rental_house", "house_info", ["house_id"], ["id"], "RESTRICT"),
    )
    for table, name, referred_table, local_columns, remote_columns, ondelete in constraints:
        if name not in foreign_keys[table]:
            op.create_foreign_key(name, table, referred_table, local_columns, remote_columns, ondelete=ondelete)


def downgrade() -> None:
    for table, name in (
        ("rental", "fk_rental_house"), ("rental", "fk_rental_contract"),
        ("rental", "fk_rental_landlord_user"), ("rental", "fk_rental_tenant_user"),
        ("contract", "fk_contract_house"), ("contract", "fk_contract_landlord_user"),
        ("contract", "fk_contract_tenant_user"), ("house_info", "fk_house_landlord_user"),
    ):
        op.drop_constraint(name, table, type_="foreignkey")
    op.drop_index("ix_rental_house_id", table_name="rental")
    op.drop_index("ix_contract_landlordId", table_name="contract")
    op.drop_index("ix_contract_tenantId", table_name="contract")
    op.alter_column("rental", "house_id", existing_type=mysql.INTEGER(unsigned=True), type_=sa.Integer(), existing_nullable=False, nullable=True)
    op.alter_column("contract", "houseId", existing_type=mysql.INTEGER(unsigned=True), type_=sa.Integer(), existing_nullable=True)
