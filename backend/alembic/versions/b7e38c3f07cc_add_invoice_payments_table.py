"""add invoice_payments table

Revision ID: b7e38c3f07cc
Revises: 50df3c184291
Create Date: 2026-02-20 08:00:42.208420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e38c3f07cc'
down_revision: Union[str, None] = '50df3c184291'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('invoice_payments',
    sa.Column('invoice_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('payment_date', sa.Date(), nullable=False),
    sa.Column('payment_method', sa.String(length=30), nullable=False),
    sa.Column('reference', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_payments_invoice_id'), 'invoice_payments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_invoice_payments_tenant_id'), 'invoice_payments', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_invoice_payments_tenant_id'), table_name='invoice_payments')
    op.drop_index(op.f('ix_invoice_payments_invoice_id'), table_name='invoice_payments')
    op.drop_table('invoice_payments')
