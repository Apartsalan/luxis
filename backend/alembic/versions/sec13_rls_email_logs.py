"""SEC-13: Add RLS policy to email_logs table

The email_logs table has tenant_id but was missing from the original
RLS migration. This adds the same tenant isolation policy.

Revision ID: sec13_rls_email_logs
Revises: sec9b_force_rls
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'sec13_rls_email_logs'
down_revision: Union[str, None] = 'sec9b_force_rls'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable RLS
    op.execute("ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY")
    # Create tenant isolation policy
    op.execute(
        "CREATE POLICY tenant_isolation ON email_logs "
        "USING (tenant_id = current_setting('app.current_tenant')::uuid)"
    )
    # Force RLS (so luxis_app role is subject to it)
    op.execute("ALTER TABLE email_logs FORCE ROW LEVEL SECURITY")
    # Grant permissions to luxis_app role
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON email_logs TO luxis_app")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON email_logs")
    op.execute("ALTER TABLE email_logs NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_logs DISABLE ROW LEVEL SECURITY")
