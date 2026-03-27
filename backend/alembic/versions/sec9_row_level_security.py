"""SEC-9: Row-Level Security policies for tenant isolation

Adds RLS policies to all tenant-scoped tables. Each policy restricts
rows to the current tenant via: current_setting('app.current_tenant')::uuid

IMPORTANT: The application middleware MUST call
  SET LOCAL app.current_tenant = '<tenant_uuid>'
at the start of each request transaction, BEFORE any queries.

The table owner (used by Alembic migrations) is NOT affected by
FORCE ROW LEVEL SECURITY — only non-owner roles are forced.
This means migrations can still run without a tenant context.

Revision ID: sec9_rls_policies
Revises: sec12_refresh_tokens
Create Date: 2026-03-20

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "sec9_rls_policies"
down_revision: Union[str, None] = "sec12_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All tenant-scoped tables (have tenant_id column)
# All tenant-scoped tables with tenant_id column.
# Excluded: users (auth lookups need cross-tenant), tenants, interest_rates (global),
# alembic_version (system).
TENANT_TABLES = [
    "bank_statement_imports",
    "bank_transactions",
    "calendar_events",
    "case_activities",
    "case_files",
    "case_parties",
    "cases",
    "claims",
    "contact_links",
    "contacts",
    "derdengelden",
    "document_templates",
    "email_accounts",
    "email_attachments",
    "email_classifications",
    "expenses",
    "followup_recommendations",
    "generated_documents",
    "incasso_pipeline_steps",
    "intake_requests",
    "invoice_lines",
    "invoice_payments",
    "invoices",
    "kyc_verifications",
    "managed_templates",
    "payment_arrangement_installments",
    "payment_arrangements",
    "payment_matches",
    "payments",
    "refresh_tokens",
    "response_templates",
    "synced_emails",
    "time_entries",
    "trust_transactions",
    "workflow_rules",
    "workflow_statuses",
    "workflow_tasks",
    "workflow_transitions",
]


def upgrade() -> None:
    for table in TENANT_TABLES:
        # Enable RLS on the table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # Create tenant isolation policy
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.current_tenant')::uuid)"
        )
        # Note: we do NOT use FORCE ROW LEVEL SECURITY here.
        # The table owner (used by migrations and superuser) bypasses RLS by default.
        # Application connections should use a non-owner role for RLS enforcement.


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
