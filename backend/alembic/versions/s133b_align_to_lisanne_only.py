"""Deactiveer alle pipeline-stappen die niet in Lisanne's officiele workflow staan.

Revision ID: s133b01
Revises: s133a01
Create Date: 2026-05-06

Achtergrond: bij Kesting Legal bestonden ook custom stappen (Aanmaning, Sommatie,
2e Sommatie, Executie) die niet door de standaard-seed waren aangemaakt en daarom
niet in s133a's DEACTIVATE_STEP_NAMES lijst zaten.

Deze migration zet álle stappen op is_active=false behalve de exacte 14 namen uit
Lisanne's officiele workflow (docs/lisanne-incasso-workflow.md). FK-integriteit
blijft behouden — bestaande dossiers met current_step_id verwijzend naar oude
stappen blijven werken; ze worden alleen niet meer aangeboden in selecties.
"""

import sqlalchemy as sa
from alembic import op

revision = "s133b01"
down_revision = "s133a01"
branch_labels = None
depends_on = None


# Exact 14 stappen uit docs/lisanne-incasso-workflow.md
LISANNE_ACTIVE_STEPS = [
    # Hoofdpad
    "Eerste sommatie",
    "Tweede sommatie",
    "Derde sommatie",
    "Sommatie laatste mogelijkheid",
    "Verzoekschrift faillissement",
    # Auto-trigger
    "Verweer beantwoorden",
    # Tussenstappen handmatig
    "Opvragen stukken bij cliënt",
    "Voorstel dagvaarding",
    "Treffen van regeling",
    "Bijhouden regeling",
    "Akkoord dagvaarden",
    "On hold",
    # Afsluiting
    "Betaald",
    "Afgesloten",
]


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE incasso_pipeline_steps SET is_active = false "
            "WHERE name <> ALL(:names)"
        ).bindparams(names=LISANNE_ACTIVE_STEPS)
    )


def downgrade() -> None:
    # Niet automatisch reactiveren — onbekend welke stappen vóór deze migration actief waren.
    # Indien rollback nodig: handmatig is_active=true zetten op gewenste namen.
    pass
