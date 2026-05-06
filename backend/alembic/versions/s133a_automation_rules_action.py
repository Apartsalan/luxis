"""Pivot step_transitions → automation rules + align pipeline steps with Lisanne workflow.

Revision ID: s133a01
Revises: s131a01
Create Date: 2026-05-06

Sessie 133: Pivot van branching state-machine naar lineaire pipeline + automation rules.
- Voegt 'action' veld toe aan step_transitions (advance_to_step, jump_to_step, pause, notify_lawyer)
- Deactiveert pipeline-stappen die niet in Lisanne's officiele workflow staan
  (bron: docs/lisanne-incasso-workflow.md)
- Behoudt FK-integriteit: stappen worden niet gedropt, alleen is_active=false

Bestaande dossiers met current_step_id verwijzend naar gedeactiveerde stappen blijven werken;
ze worden alleen niet meer aangeboden in nieuwe selecties.
"""

import sqlalchemy as sa
from alembic import op

revision = "s133a01"
down_revision = "s131a01"
branch_labels = None
depends_on = None


# Stappen die buiten Lisanne's officiele workflow vallen (zie docs/lisanne-incasso-workflow.md).
# Deze worden uitgezet, niet verwijderd, om FK-integriteit met bestaande dossiers te behouden.
DEACTIVATE_STEP_NAMES = [
    "14-dagenbrief",
    "Ingebrekestelling",
    "Laatste sommatie (ank. verzoekschrift)",
    "Laatste sommatie (ank. dagvaarding)",
    "Dagvaarding",
    "Vonnis",
    "Verstuurd naar deurwaarder",
    "Beslag gelegd",
    "Regeling voorgesteld",
    "Betalingsregeling getroffen",
    "Info opgevraagd bij cliënt",
    "Wacht op informatie",
    "Procedure voorgesteld aan cliënt",
    "Cliënt akkoord procedure",
]


def upgrade() -> None:
    # 1. Voeg action-kolom toe (default: bestaande rijen krijgen 'advance_to_step')
    op.add_column(
        "step_transitions",
        sa.Column(
            "action",
            sa.String(30),
            nullable=False,
            server_default="advance_to_step",
        ),
    )

    # 2. Deactiveer pipeline-stappen buiten Lisanne's workflow (alle tenants)
    op.execute(
        sa.text(
            "UPDATE incasso_pipeline_steps SET is_active = false "
            "WHERE name = ANY(:names)"
        ).bindparams(names=DEACTIVATE_STEP_NAMES)
    )


def downgrade() -> None:
    # Heractiveer alle gedeactiveerde stappen
    op.execute(
        sa.text(
            "UPDATE incasso_pipeline_steps SET is_active = true "
            "WHERE name = ANY(:names)"
        ).bindparams(names=DEACTIVATE_STEP_NAMES)
    )
    op.drop_column("step_transitions", "action")
