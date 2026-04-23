"""AUD124-08: Add RLS policies to 4 missing tenant-scoped tables

products, exact_online_connections, exact_sync_log, notifications
all inherit TenantBase but were missed in the original RLS migration.

Revision ID: aud12408
Revises: aud12403
Create Date: 2026-04-22

"""

from typing import Sequence, Union

from alembic import op


revision: str = "aud12408"
down_revision: Union[str, None] = "aud12403"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MISSING_TABLES = [
    "exact_online_connections",
    "exact_sync_log",
    "notifications",
    "products",
]


def upgrade() -> None:
    for table in MISSING_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.current_tenant')::uuid)"
        )


def downgrade() -> None:
    for table in reversed(MISSING_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
