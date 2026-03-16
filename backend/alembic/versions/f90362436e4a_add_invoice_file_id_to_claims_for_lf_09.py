"""add invoice_file_id to claims for LF-09

Revision ID: f90362436e4a
Revises: 040_lf12_bik_override
Create Date: 2026-03-16 10:41:38.593989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f90362436e4a'
down_revision: Union[str, None] = '040_lf12_bik_override'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('claims', sa.Column('invoice_file_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_claims_invoice_file_id',
        'claims', 'case_files',
        ['invoice_file_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_claims_invoice_file_id', 'claims', type_='foreignkey')
    op.drop_column('claims', 'invoice_file_id')
