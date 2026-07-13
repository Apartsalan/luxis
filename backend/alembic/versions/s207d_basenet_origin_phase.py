"""S207d: basenet_origin_phase op cases — de fijne BaseNet-werkfase.

De hoofdgroep (s207c) zegt óf een geïmporteerde zaak nog moet lopen; de
werkfase zegt wáár hij gebleven was ("B2C 3e sommatie verstuurd", "Procedure
loopt", ...). Nodig om bij de fase-heropening elke zaak op de juiste
pijplijnstap te zetten. De waarden komen uit de BaseNet-export
(incstatus → CustomProjectStatus.psdescription) en worden ná deze migratie
gevuld door scripts/backfill_basenet_phase (de export staat niet in de DB).

Revision ID: s207d_basenet_origin_phase
Revises: s207c_basenet_origin_status
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s207d_basenet_origin_phase"
down_revision: str | None = "s207c_basenet_origin_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("basenet_origin_phase", sa.String(length=60), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "basenet_origin_phase")
