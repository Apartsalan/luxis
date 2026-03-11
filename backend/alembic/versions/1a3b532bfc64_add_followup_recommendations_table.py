"""add followup_recommendations table

Revision ID: 1a3b532bfc64
Revises: 037_intake_requests
Create Date: 2026-03-11 13:39:18.783241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a3b532bfc64'
down_revision: Union[str, None] = '037_intake_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('followup_recommendations',
    sa.Column('case_id', sa.Uuid(), nullable=False),
    sa.Column('incasso_step_id', sa.Uuid(), nullable=False),
    sa.Column('recommended_action', sa.String(length=50), nullable=False),
    sa.Column('reasoning', sa.Text(), nullable=False),
    sa.Column('days_in_step', sa.Integer(), nullable=False),
    sa.Column('outstanding_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('urgency', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('reviewed_by_id', sa.Uuid(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('execution_result', sa.Text(), nullable=True),
    sa.Column('generated_document_id', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['generated_document_id'], ['generated_documents.id'], ),
    sa.ForeignKeyConstraint(['incasso_step_id'], ['incasso_pipeline_steps.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_followup_recommendations_case_id'), 'followup_recommendations', ['case_id'], unique=False)
    op.create_index(op.f('ix_followup_recommendations_tenant_id'), 'followup_recommendations', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_followup_recommendations_tenant_id'), table_name='followup_recommendations')
    op.drop_index(op.f('ix_followup_recommendations_case_id'), table_name='followup_recommendations')
    op.drop_table('followup_recommendations')
