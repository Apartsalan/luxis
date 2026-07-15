"""S221: ai_drafts krijgt intent + step_id — ontdubbelen en zombie-opruiming.

Concepten misten een koppeling aan (a) hun bedoeling (volgende stap / antwoord /
vrij opstellen) en (b) de pijplijnstap waarvoor ze gemaakt zijn. Daardoor kon
dezelfde zaak+stap twee identieke concepten krijgen (dubbelklik) en bleven oude
stap-concepten open staan na een stap-wissel. Beide nullable en additief.

`ai_drafts` heeft al RLS (tenant-tabel, gedekt door apply_rls); deze migratie
voegt alleen kolommen toe.

Revision ID: s221_ai_draft_intent_step
Revises: s214_payment_date_null
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s221_ai_draft_intent_step"
down_revision: str | None = "s214_payment_date_null"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_drafts", sa.Column("intent", sa.String(length=20), nullable=True))
    op.add_column(
        "ai_drafts",
        sa.Column("step_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_ai_drafts_step_id",
        "ai_drafts",
        "incasso_pipeline_steps",
        ["step_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_drafts_step_id", "ai_drafts", type_="foreignkey")
    op.drop_column("ai_drafts", "step_id")
    op.drop_column("ai_drafts", "intent")
