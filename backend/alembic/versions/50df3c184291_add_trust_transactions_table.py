"""add trust_transactions table

Revision ID: 50df3c184291
Revises: 017
Create Date: 2026-02-20 07:37:05.030006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50df3c184291'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('trust_transactions',
    sa.Column('case_id', sa.Uuid(), nullable=False),
    sa.Column('contact_id', sa.Uuid(), nullable=False),
    sa.Column('transaction_type', sa.String(length=20), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('payment_method', sa.String(length=50), nullable=True),
    sa.Column('reference', sa.String(length=255), nullable=True),
    sa.Column('beneficiary_name', sa.String(length=255), nullable=True),
    sa.Column('beneficiary_iban', sa.String(length=34), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('approved_by_1', sa.Uuid(), nullable=True),
    sa.Column('approved_at_1', sa.DateTime(timezone=True), nullable=True),
    sa.Column('approved_by_2', sa.Uuid(), nullable=True),
    sa.Column('approved_at_2', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['approved_by_1'], ['users.id'], ),
    sa.ForeignKeyConstraint(['approved_by_2'], ['users.id'], ),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
    sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trust_transactions_case_id'), 'trust_transactions', ['case_id'], unique=False)
    op.create_index(op.f('ix_trust_transactions_tenant_id'), 'trust_transactions', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_trust_transactions_tenant_id'), table_name='trust_transactions')
    op.drop_index(op.f('ix_trust_transactions_case_id'), table_name='trust_transactions')
    op.drop_table('trust_transactions')
