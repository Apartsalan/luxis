"""S151: heal missing email_logs table (AUDIT-H9).

Migration 011 created ``email_logs``, but on databases that were stamped past
011 without ever executing it (restored production dumps / drifted dev DBs) the
table is absent while ``alembic_version`` already points at head. The drift is
real and known: ``sec13_rls_email_logs`` guards its whole body with
``IF EXISTS ... email_logs  -- may not exist on all environments``.

Symptom: ``GET /api/documents/cases/{id}/email-logs`` 500s with UndefinedTable,
so sent SMTP mails silently disappear from the correspondence view.

This migration is idempotent and self-healing: it creates the table + indexes
``IF NOT EXISTS`` and (re)applies the exact ``tenant_isolation`` RLS that
``h2_rls_complete`` applies to every other tenant table. It is a no-op on
databases where the table already exists (production), and a heal where it does
not.

Revision ID: s151_heal_email_logs
Revises: h2_rls_complete
"""

from alembic import op

revision = "s151_heal_email_logs"
down_revision = "h2_rls_complete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Mirror migration 011's schema exactly, but IF NOT EXISTS so it is a no-op
    # where the table already exists.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS email_logs (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            case_id UUID REFERENCES cases(id),
            document_id UUID REFERENCES generated_documents(id),
            template VARCHAR(100) NOT NULL,
            recipient VARCHAR(320) NOT NULL,
            subject VARCHAR(500) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'sent',
            error_message TEXT,
            sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_logs_tenant_id ON email_logs (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_logs_case_id ON email_logs (case_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_logs_sent_at ON email_logs (sent_at)")

    # Apply the same tenant isolation every other tenant table gets
    # (h2_rls_complete). Idempotent: the policy is dropped first; ENABLE/FORCE
    # are no-ops if already set. WITH CHECK mirrors USING so cross-tenant
    # INSERT/UPDATE are rejected, not just hidden.
    op.execute("ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_logs FORCE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON email_logs")
    op.execute(
        "CREATE POLICY tenant_isolation ON email_logs "
        "USING (tenant_id = current_setting('app.current_tenant')::uuid) "
        "WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid)"
    )
    # The GRANT is guarded on the role existing — it does not in CI/test, where
    # RLS is proven by the dedicated tests/test_rls_isolation.py instead.
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'luxis_app') THEN
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON email_logs TO luxis_app';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Non-destructive: the table predates this migration on most databases, so we
    # never drop it. Only roll back the RLS this migration (re)applied, and only
    # if the table is present.
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name = 'email_logs'
            ) THEN
                EXECUTE 'DROP POLICY IF EXISTS tenant_isolation ON email_logs';
                EXECUTE 'ALTER TABLE email_logs NO FORCE ROW LEVEL SECURITY';
                EXECUTE 'ALTER TABLE email_logs DISABLE ROW LEVEL SECURITY';
            END IF;
        END $$;
        """
    )
