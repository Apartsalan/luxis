"""add payment arrangement installments

Revision ID: 2e1747ba61ca
Revises: f90362436e4a
Create Date: 2026-03-16 12:49:03.894614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e1747ba61ca'
down_revision: Union[str, None] = 'f90362436e4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('payment_arrangement_installments',
        sa.Column('arrangement_id', sa.Uuid(), nullable=False),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('payment_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['arrangement_id'], ['payment_arrangements.id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_payment_arrangement_installments_tenant_id'),
        'payment_arrangement_installments',
        ['tenant_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_payment_arrangement_installments_tenant_id'),
        table_name='payment_arrangement_installments',
    )
    op.drop_table('payment_arrangement_installments')
