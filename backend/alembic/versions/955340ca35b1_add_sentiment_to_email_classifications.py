"""add sentiment to email_classifications

Revision ID: 955340ca35b1
Revises: 8f4a02b3c5d6
Create Date: 2026-03-28 13:39:26.893141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '955340ca35b1'
down_revision: Union[str, None] = '8f4a02b3c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('email_classifications', sa.Column('sentiment', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('email_classifications', 'sentiment')
