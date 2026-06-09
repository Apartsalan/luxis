"""bank transaction dedup fields + import duplicate_count (H17)

Adds traceability + duplicate-detection columns to bank_transactions
(sequence_number/Volgnr, payment_reference/Betalingskenmerk, dedup_key)
with a per-tenant unique constraint, and a duplicate_count stat on
bank_statement_imports.

Existing rows get NULL dedup keys — the unique constraint allows multiple
NULLs, and new imports compare against stored keys only, so pre-existing
transactions are unaffected.

Revision ID: b0e5d35d5eb6
Revises: prod_uniq_active_code
Create Date: 2026-06-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b0e5d35d5eb6'
down_revision: Union[str, None] = 'prod_uniq_active_code'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bank_statement_imports',
        sa.Column('duplicate_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'bank_transactions', sa.Column('sequence_number', sa.String(length=35), nullable=True)
    )
    op.add_column(
        'bank_transactions', sa.Column('payment_reference', sa.String(length=255), nullable=True)
    )
    op.add_column(
        'bank_transactions', sa.Column('dedup_key', sa.String(length=128), nullable=True)
    )
    op.create_unique_constraint(
        'uq_bank_transactions_dedup', 'bank_transactions', ['tenant_id', 'dedup_key']
    )


def downgrade() -> None:
    op.drop_constraint('uq_bank_transactions_dedup', 'bank_transactions', type_='unique')
    op.drop_column('bank_transactions', 'dedup_key')
    op.drop_column('bank_transactions', 'payment_reference')
    op.drop_column('bank_transactions', 'sequence_number')
    op.drop_column('bank_statement_imports', 'duplicate_count')
