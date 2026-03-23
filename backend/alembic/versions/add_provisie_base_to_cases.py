"""add provisie_base to cases

Revision ID: 8f4a02b3c5d6
Revises: 7e3f01a2b9c4
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8f4a02b3c5d6"
down_revision: Union[str, None] = "7e3f01a2b9c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column(
            "provisie_base",
            sa.String(length=20),
            nullable=False,
            server_default="collected_amount",
        ),
    )


def downgrade() -> None:
    op.drop_column("cases", "provisie_base")
