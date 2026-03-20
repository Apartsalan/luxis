"""DF-13: add settlement_type to invoices for voorschotnota verrekening

Revision ID: df13_settlement_type
Revises: f90362436e4a
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df13_settlement_type'
down_revision: Union[str, None] = '041_df12_expense'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'invoices',
        sa.Column('settlement_type', sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('invoices', 'settlement_type')
