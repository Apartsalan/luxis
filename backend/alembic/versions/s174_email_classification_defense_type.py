"""S174 V4: verweer-type op de e-mailclassificatie.

Voegt `defense_type` toe aan email_classifications. De AI-classificatie van een inkomende
mail kiest voortaan óók een verweer-type uit de 13 (alleen bij betwisting/juridisch_verweer),
zodat get_learned_examples voorbeelden van datzelfde type voorrang kan geven — de kern van
de "herken dit type verweer → pak het goedgekeurde schabloon"-loop.

Revision ID: s174_classification_defense_type
Revises: s170_settlement_flow
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s174_classification_defense_type"
down_revision: str | None = "s170_settlement_flow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_classifications",
        sa.Column("defense_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_classifications", "defense_type")
