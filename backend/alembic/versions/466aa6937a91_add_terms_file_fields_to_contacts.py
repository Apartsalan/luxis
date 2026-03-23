"""add terms file fields to contacts

AI-UX-11: Algemene Voorwaarden per client — upload/opslag

Revision ID: 466aa6937a91
Revises: sec20_account_lockout
Create Date: 2026-03-23 08:11:42.744106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '466aa6937a91'
down_revision: Union[str, None] = 'sec20_account_lockout'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contacts', sa.Column('terms_file_path', sa.String(length=500), nullable=True))
    op.add_column('contacts', sa.Column('terms_file_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('contacts', 'terms_file_name')
    op.drop_column('contacts', 'terms_file_path')
