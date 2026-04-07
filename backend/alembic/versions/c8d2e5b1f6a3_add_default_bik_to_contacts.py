"""add default bik fields to contacts

Revision ID: c8d2e5b1f6a3
Revises: b3c7e1f9a2d4
Create Date: 2026-04-07 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d2e5b1f6a3'
down_revision: Union[str, None] = 'b3c7e1f9a2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'contacts',
        sa.Column('default_bik_override', sa.Numeric(15, 2), nullable=True),
    )
    op.add_column(
        'contacts',
        sa.Column('default_bik_override_percentage', sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('contacts', 'default_bik_override_percentage')
    op.drop_column('contacts', 'default_bik_override')
