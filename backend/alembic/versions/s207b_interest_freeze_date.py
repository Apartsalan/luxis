"""S207: rentedatum / bevriezing op de zaak.

Datum tot waar rente wordt berekend. NULL = tot vandaag (lopende rente). Gezet =
rente stopt daar en het systeem rekent terug. Wordt bij het afsluiten van een
zaak automatisch op de laatste betaaldatum gezet (het afwikkelmoment), maar is
ook handmatig aanpasbaar — zodat een afgewikkelde zaak niet eeuwig doorrent
(IN100350) en je een berekening op een gekozen peildatum kunt vastzetten.

Revision ID: s207b_interest_freeze_date
Revises: s207_step_history_sent_at
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s207b_interest_freeze_date"
down_revision: str | None = "s207_step_history_sent_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("interest_freeze_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "interest_freeze_date")
