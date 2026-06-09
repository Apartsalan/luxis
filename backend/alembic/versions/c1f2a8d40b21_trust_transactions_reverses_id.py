"""trust_transactions.reverses_id — storno-tegenboeking (H15)

A reversal entry (transaction_type="reversal") points to the original
transaction it undoes via reverses_id; the original points back via the
existing reversed_by_id once the reversal is final.

Revision ID: c1f2a8d40b21
Revises: b0e5d35d5eb6
Create Date: 2026-06-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c1f2a8d40b21'
down_revision: Union[str, None] = 'b0e5d35d5eb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'trust_transactions', sa.Column('reverses_id', sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        'fk_trust_transactions_reverses_id',
        'trust_transactions',
        'trust_transactions',
        ['reverses_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_trust_transactions_reverses_id', 'trust_transactions', type_='foreignkey'
    )
    op.drop_column('trust_transactions', 'reverses_id')
