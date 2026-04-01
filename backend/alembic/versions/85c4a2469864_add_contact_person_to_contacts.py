"""add contact_person to contacts

Revision ID: 85c4a2469864
Revises: edc1202caef9
Create Date: 2026-04-01 13:00:00.616972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '85c4a2469864'
down_revision: Union[str, None] = 'edc1202caef9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contacts', sa.Column('contact_person', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('contacts', 'contact_person')
