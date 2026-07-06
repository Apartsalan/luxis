"""S177: rente-afspraak gelezen uit de AV, op de cliënt.

Voegt de `terms_interest_*`-velden toe aan contacts: de rente zoals GELEZEN uit de
algemene voorwaarden van de cliënt (apart van de handmatige default_*-override).
Vormt de laag "uit AV gelezen" in de hiërarchie dossier > klantkaart > uit-AV > wettelijk.

Revision ID: s177_terms_interest
Revises: s174_classification_defense_type
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s177_terms_interest"
down_revision: str | None = "s174_classification_defense_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("terms_interest_rate", sa.Numeric(5, 2), nullable=True))
    op.add_column("contacts", sa.Column("terms_interest_basis", sa.String(length=10), nullable=True))
    op.add_column("contacts", sa.Column("terms_interest_compound", sa.Boolean(), nullable=True))
    op.add_column("contacts", sa.Column("terms_interest_source", sa.String(length=200), nullable=True))
    op.add_column(
        "contacts",
        sa.Column("terms_interest_read_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contacts", "terms_interest_read_at")
    op.drop_column("contacts", "terms_interest_source")
    op.drop_column("contacts", "terms_interest_compound")
    op.drop_column("contacts", "terms_interest_basis")
    op.drop_column("contacts", "terms_interest_rate")
