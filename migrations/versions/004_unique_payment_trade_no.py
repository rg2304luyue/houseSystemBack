"""Make payment trade numbers unique for callback idempotency."""

from alembic import op
import sqlalchemy as sa


revision = "004_unique_payment_trade_no"
down_revision = "003_stable_ownership_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    indexes = {index["name"]: index for index in sa.inspect(bind).get_indexes("contract")}
    current = indexes.get("ix_contract_payment_trade_no")
    if current and current.get("unique"):
        return

    duplicate = bind.execute(sa.text("""
        SELECT payment_trade_no
        FROM contract
        WHERE payment_trade_no IS NOT NULL
        GROUP BY payment_trade_no
        HAVING COUNT(*) > 1
        LIMIT 1
    """)).scalar()
    if duplicate is not None:
        raise RuntimeError(
            "Cannot make contract.payment_trade_no unique: duplicate values exist"
        )

    if current:
        op.drop_index("ix_contract_payment_trade_no", table_name="contract")
    op.create_index(
        "ix_contract_payment_trade_no",
        "contract",
        ["payment_trade_no"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_contract_payment_trade_no", table_name="contract")
    op.create_index(
        "ix_contract_payment_trade_no",
        "contract",
        ["payment_trade_no"],
        unique=False,
    )
