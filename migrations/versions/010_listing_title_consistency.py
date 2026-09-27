"""Align imported listing titles with their structured room fields.

Revision ID: 010_listing_title_consistency
Revises: 009_legacy_state_cleanup
"""

from alembic import op
import sqlalchemy as sa


revision = "010_listing_title_consistency"
down_revision = "009_legacy_state_cleanup"
branch_labels = None
depends_on = None


_TITLE_CHANGES = {
    47: ("整租·九龙小区 3室1厅 北", "整租·九龙小区 2室1厅 北"),
    49: ("整租·黄金一区 3室2厅 北", "整租·黄金一区 2室1厅 北"),
    50: ("整租·桃花村 3室1厅 南北", "整租·桃花村 2室1厅 南北"),
    51: ("整租·锦源小区 1室1厅 东西", "整租·锦源小区 2室1厅 东西"),
}


def _apply_titles(reverse: bool = False) -> None:
    house = sa.table(
        "house_info",
        sa.column("id", sa.Integer()),
        sa.column("title", sa.String()),
    )
    bind = op.get_bind()
    for house_id, (old_title, new_title) in _TITLE_CHANGES.items():
        source, target = (new_title, old_title) if reverse else (old_title, new_title)
        bind.execute(
            house.update()
            .where(house.c.id == house_id)
            .where(house.c.title == source)
            .values(title=target)
        )


def upgrade() -> None:
    _apply_titles()


def downgrade() -> None:
    _apply_titles(reverse=True)
