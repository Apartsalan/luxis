"""S246: scheduled_emails — wachtrij achter 'Verstuur later'.

Lisanne werkt 's avonds; incassomail hoort op nette tijden weg te gaan. Een
geplande mail belandt in deze tabel en wordt op het geplande moment door de
minuut-bezorger via exact dezelfde verzendfunctie verstuurd.

Tenant-tabel → RLS in DEZELFDE migratie (huisregel S183-1): `apply_rls` is
idempotent en ontdekt de nieuwe tabel zelf. Zonder deze aanroep blokkeert de
opstartcontrole (app.main.lifespan) + de drift-guard-test de deploy.

Revision ID: s246_scheduled_emails
Revises: s233_ai_draft_attach_invoices
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.security.rls import apply_rls

revision: str = "s246_scheduled_emails"
down_revision: str | None = "s233_ai_draft_attach_invoices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduled_emails",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("recipients", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("advance_draft_id", sa.Uuid(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduled_emails_tenant_id", "scheduled_emails", ["tenant_id"])
    op.create_index("ix_scheduled_emails_case_id", "scheduled_emails", ["case_id"])
    op.create_index("ix_scheduled_emails_created_by_id", "scheduled_emails", ["created_by_id"])
    op.create_index("ix_scheduled_emails_status", "scheduled_emails", ["status"])
    # De bezorger zoekt elke minuut op (status, scheduled_at) — samengestelde index.
    op.create_index(
        "ix_scheduled_emails_status_scheduled_at",
        "scheduled_emails",
        ["status", "scheduled_at"],
    )

    # Huisregel S183-1: nieuwe tenant-tabel → RLS in DEZELFDE migratie.
    apply_rls(op.get_bind())


def downgrade() -> None:
    op.drop_index("ix_scheduled_emails_status_scheduled_at", table_name="scheduled_emails")
    op.drop_index("ix_scheduled_emails_status", table_name="scheduled_emails")
    op.drop_index("ix_scheduled_emails_created_by_id", table_name="scheduled_emails")
    op.drop_index("ix_scheduled_emails_case_id", table_name="scheduled_emails")
    op.drop_index("ix_scheduled_emails_tenant_id", table_name="scheduled_emails")
    op.drop_table("scheduled_emails")
