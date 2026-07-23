"""S246c: soorten in de verzend-wachtrij — ook batch en follow-up uitstelbaar.

'Verstuur later' dekte alleen zelf-opgestelde mails (compose). Nu kan de
wachtrij ook een batch-stapverzending (per dossier) en een follow-up-uitvoering
dragen. Twee nieuwe kolommen:

- kind: wat de bezorger op het verzendmoment draait ('compose' | 'batch_step'
  | 'followup'); bestaande rijen zijn per definitie 'compose'.
- step_id_at_schedule: bij 'batch_step' de pijplijnstap op het inplanmoment —
  staat het dossier bij verzending op een andere stap, dan gaat er NIET de
  verkeerde brief uit (mislukt + melding).

Geen nieuwe tabel → RLS van scheduled_emails blijft gewoon gelden.

Revision ID: s246c_sched_kinds
Revises: s246b_sched_ts
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s246c_sched_kinds"
down_revision: str | None = "s246b_sched_ts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "scheduled_emails",
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="compose"),
    )
    op.add_column(
        "scheduled_emails",
        sa.Column("step_id_at_schedule", sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scheduled_emails", "step_id_at_schedule")
    op.drop_column("scheduled_emails", "kind")
