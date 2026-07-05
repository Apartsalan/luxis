"""S170: dossier-afwikkelflow (FIN-2 restant / CONN-7).

Voegt de velden toe voor het afwikkel-paneel op een dossier:

* cases.settlement_route            — 'verrekenen' | 'doorbetalen' | NULL; per-dossier
                                      keuze hoe het geincasseerde geld wordt afgewikkeld.
* incasso_pipeline_steps.requires_settled — stap mag pas ingegaan worden als er geen
                                      onafgewikkelde derdengelden op het dossier staan.
                                      Aan voor de eindstap "Afgesloten", uit voor "Betaald"
                                      (op "Betaald" staat het geld terecht op de stichting,
                                      wachtend op uitbetaling — dat mag niet blokkeren).

Data-seed: zet requires_settled=true voor bestaande "Afgesloten"-stappen (per tenant).

Revision ID: s170_settlement_flow
Revises: s170_learned_answers_review
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s170_settlement_flow"
down_revision: str | None = "s170_learned_answers_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("settlement_route", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column(
            "requires_settled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    # Seed: de bestaande eindstap "Afgesloten" mag pas in als de derdengelden
    # afgewikkeld zijn. "Betaald" bewust NIET (geld staat daar terecht, wachtend
    # op uitbetaling). Naam-match hier is eenmalige seed-data, geen runtime-code.
    op.execute(
        "UPDATE incasso_pipeline_steps SET requires_settled = true "
        "WHERE name = 'Afgesloten'"
    )


def downgrade() -> None:
    op.drop_column("incasso_pipeline_steps", "requires_settled")
    op.drop_column("cases", "settlement_route")
