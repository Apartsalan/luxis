"""add bik_override_percentage to cases

Revision ID: b3c7e1f9a2d4
Revises: a1f7c2e9d4b8
Create Date: 2026-04-07 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c7e1f9a2d4'
down_revision: Union[str, None] = 'a1f7c2e9d4b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'cases',
        sa.Column('bik_override_percentage', sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('cases', 'bik_override_percentage')
