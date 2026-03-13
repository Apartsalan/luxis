"""add default_hourly_rate to users

Revision ID: 42aba19cd8b0
Revises: 038_payment_matching
Create Date: 2026-03-13 11:16:55.180428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '42aba19cd8b0'
down_revision: Union[str, None] = '038_payment_matching'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('default_hourly_rate', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'default_hourly_rate')
