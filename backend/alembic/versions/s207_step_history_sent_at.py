"""S207: verzend-tijdstempel op de staphistorie (14-dagenbrief-klok, review S205).

De 14-dagenbrief-gate eiste sinds S205 terecht een échte verzending
(`email_sent`), maar rekende de wettelijke 15-dagen-wachttijd nog vanaf
`entered_at` (stap-BINNENKOMST). Gaat de brief pas dagen ná binnenkomst de deur
uit (batch later gedraaid), dan startte de klok te vroeg → een sommatie kon te
vroeg door de gate (art. 6:96 lid 6 BW). Deze kolom legt het echte
verzendmoment vast; de gate rekent voortaan daarop (fallback: entered_at voor
oude rijen — prod heeft er op dit moment nul, dus geen legacy-data).

Revision ID: s207_step_history_sent_at
Revises: s205_dagenbrief_template
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "s207_step_history_sent_at"
down_revision: str | None = "s205_dagenbrief_template"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "case_step_history",
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("case_step_history", "email_sent_at")
