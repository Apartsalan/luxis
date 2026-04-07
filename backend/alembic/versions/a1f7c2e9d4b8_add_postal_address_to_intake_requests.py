"""add postal address fields to intake_requests

Revision ID: a1f7c2e9d4b8
Revises: 85c4a2469864
Create Date: 2026-04-07 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1f7c2e9d4b8'
down_revision: Union[str, None] = '85c4a2469864'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('intake_requests', sa.Column('debtor_postal_address', sa.String(length=500), nullable=True))
    op.add_column('intake_requests', sa.Column('debtor_postal_postcode', sa.String(length=10), nullable=True))
    op.add_column('intake_requests', sa.Column('debtor_postal_city', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('intake_requests', 'debtor_postal_city')
    op.drop_column('intake_requests', 'debtor_postal_postcode')
    op.drop_column('intake_requests', 'debtor_postal_address')
