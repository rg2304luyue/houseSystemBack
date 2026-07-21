"""Add stable user IDs to legacy channels and messages."""

from alembic import op
import sqlalchemy as sa


revision = "005_message_user_ids"
down_revision = "004_unique_payment_trade_no"
branch_labels = None
depends_on = None


def _add_columns_and_indexes(table: str, columns: tuple[str, ...]) -> None:
    inspector = sa.inspect(op.get_bind())
    existing_columns = {column["name"] for column in inspector.get_columns(table)}
    existing_indexes = {index["name"] for index in inspector.get_indexes(table)}
    for column in columns:
        if column not in existing_columns:
            op.add_column(table, sa.Column(column, sa.Integer(), nullable=True))
        index_name = f"ix_{table}_{column}"
        if index_name not in existing_indexes:
            op.create_index(index_name, table, [column], unique=False)


def upgrade() -> None:
    _add_columns_and_indexes("channel", ("tenant_id", "landlord_id"))
    _add_columns_and_indexes("message", ("sender_id", "receiver_id"))

    for table, id_column, name_column in (
        ("channel", "tenant_id", "tenant_username"),
        ("channel", "landlord_id", "landlord_username"),
        ("message", "sender_id", "sender_username"),
        ("message", "receiver_id", "receiver_username"),
    ):
        op.execute(sa.text(f"""
            UPDATE `{table}` AS target
            JOIN (
                SELECT name, MIN(id) AS user_id
                FROM user_info
                WHERE name IS NOT NULL AND name <> ''
                GROUP BY name
                HAVING COUNT(*) = 1
            ) AS users ON users.name = target.`{name_column}`
            SET target.`{id_column}` = users.user_id
            WHERE target.`{id_column}` IS NULL
        """))


def downgrade() -> None:
    for table, columns in (
        ("message", ("receiver_id", "sender_id")),
        ("channel", ("landlord_id", "tenant_id")),
    ):
        for column in columns:
            op.drop_index(f"ix_{table}_{column}", table_name=table)
            op.drop_column(table, column)
