"""add default interest fields to contacts

Revision ID: edc1202caef9
Revises: 043_notifications
Create Date: 2026-03-30 13:07:28.831898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edc1202caef9'
down_revision: Union[str, None] = '043_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contacts', sa.Column('default_interest_type', sa.String(30), nullable=True))
    op.add_column('contacts', sa.Column('default_contractual_rate', sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('contacts', 'default_contractual_rate')
    op.drop_column('contacts', 'default_interest_type')
