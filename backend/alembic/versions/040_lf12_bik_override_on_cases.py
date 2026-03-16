"""LF-12: bik_override on cases

Revision ID: 040_lf12_bik_override
Revises: 039_lf03_lf19_lf22
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "040_lf12_bik_override"
down_revision: Union[str, None] = "039_lf03_lf19_lf22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("bik_override", sa.Numeric(15, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "bik_override")
