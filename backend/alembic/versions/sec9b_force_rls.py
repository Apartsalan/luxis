"""SEC-9b: Force RLS + create non-superuser app role

The original SEC-9 migration enabled RLS but the app connects as the
superuser 'luxis' which always bypasses RLS. This migration:

1. Creates a 'luxis_app' role (non-superuser, non-owner)
2. Grants SELECT/INSERT/UPDATE/DELETE on all tables + USAGE on sequences
3. Adds FORCE ROW LEVEL SECURITY on all tenant-scoped tables

The app middleware uses SET LOCAL ROLE luxis_app for each request,
so RLS policies are enforced. Alembic continues as superuser 'luxis'.

Revision ID: sec9b_force_rls
Revises: sec9_rls_policies
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'sec9b_force_rls'
down_revision: Union[str, None] = 'sec9_rls_policies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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
    # 1. Create non-superuser app role (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'luxis_app') THEN
                CREATE ROLE luxis_app NOLOGIN;
            END IF;
        END
        $$;
    """)

    # 2. Grant luxis_app to luxis so SET ROLE works
    op.execute("GRANT luxis_app TO luxis")

    # 3. Grant table permissions to luxis_app
    op.execute("GRANT USAGE ON SCHEMA public TO luxis_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO luxis_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO luxis_app")

    # 4. Default privileges for future tables
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO luxis_app")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO luxis_app")

    # 5. Force RLS on all tenant tables (applies even to table owner when SET ROLE is used)
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")

    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM luxis_app")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON SEQUENCES FROM luxis_app")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM luxis_app")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM luxis_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM luxis_app")
    op.execute("REVOKE luxis_app FROM luxis")
    op.execute("DROP ROLE IF EXISTS luxis_app")
