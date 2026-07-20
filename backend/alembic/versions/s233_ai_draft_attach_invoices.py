"""S233: ai_drafts krijgt attach_invoices — factuur-signaal uit de behandelaar-instructie.

Taak 2: vraagt de behandelaar in een AI-antwoord "doe de facturen erbij", dan zet de
AI dit signaal en opent het concept met de factuur-PDF's al aangevinkt. Additief,
NOT NULL met server_default false zodat bestaande rijen (en stap-/batch-concepten die
geen instructie dragen) op False staan.

`ai_drafts` heeft al RLS (tenant-tabel, gedekt door apply_rls); deze migratie voegt
alleen een kolom toe.

Revision ID: s233_ai_draft_attach_invoices
Revises: s230b_ai_usage
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s233_ai_draft_attach_invoices"
down_revision: str | None = "s230b_ai_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ai_drafts",
        sa.Column(
            "attach_invoices",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_drafts", "attach_invoices")
