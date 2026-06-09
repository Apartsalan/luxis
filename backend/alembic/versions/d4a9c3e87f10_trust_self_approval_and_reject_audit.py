"""H14 tenant-setting self-approval + reject-audit op trust_transactions

- tenants.trust_allow_self_approval vervangt de env-flag
  TRUST_FUNDS_ALLOW_SELF_APPROVAL (alleen relevant bij 1 actieve gebruiker;
  bij 2+ gebruikers geldt altijd strikt vier-ogen).
- trust_transactions krijgt rejected_by/rejected_at/reject_reason zodat
  zichtbaar is wie een transactie afwees en waarom.

Revision ID: d4a9c3e87f10
Revises: c1f2a8d40b21
Create Date: 2026-06-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4a9c3e87f10'
down_revision: Union[str, None] = 'c1f2a8d40b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tenants',
        sa.Column(
            'trust_allow_self_approval',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        ),
    )
    op.add_column(
        'trust_transactions', sa.Column('rejected_by', sa.Uuid(), nullable=True)
    )
    op.add_column(
        'trust_transactions',
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'trust_transactions', sa.Column('reject_reason', sa.Text(), nullable=True)
    )
    op.create_foreign_key(
        'fk_trust_transactions_rejected_by',
        'trust_transactions',
        'users',
        ['rejected_by'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_trust_transactions_rejected_by', 'trust_transactions', type_='foreignkey'
    )
    op.drop_column('trust_transactions', 'reject_reason')
    op.drop_column('trust_transactions', 'rejected_at')
    op.drop_column('trust_transactions', 'rejected_by')
    op.drop_column('tenants', 'trust_allow_self_approval')
