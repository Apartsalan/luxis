"""BUG-71: fix case_step_history RLS policy to use app.current_tenant

s126a_pipeline_overhaul.py created the policy with 'app.current_tenant_id',
but middleware/other policies use 'app.current_tenant'. This recreates the
policy with the correct setting name so prod is aligned with from-scratch DBs.

Revision ID: bug71_csh
Revises: 1f7244b8d57e
Create Date: 2026-05-13
"""

from alembic import op

revision = "bug71_csh"
down_revision = "1f7244b8d57e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_case_step_history ON case_step_history"
    )
    op.execute("""
        CREATE POLICY tenant_isolation_case_step_history
        ON case_step_history
        USING (tenant_id = current_setting('app.current_tenant')::uuid)
    """)


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_case_step_history ON case_step_history"
    )
    op.execute("""
        CREATE POLICY tenant_isolation_case_step_history
        ON case_step_history
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
