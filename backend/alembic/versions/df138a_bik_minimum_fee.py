"""DF138-16: aparte BIK-minimum velden op contacts + cases.

Eerder werd `minimum_fee` (provisie/honorarium-bodem) ten onrechte gebruikt
als bodem voor BIK-percentage. Lisanne maakt onderscheid: minimum provisie
is voor eigen factuur naar de cliënt; minimum incassokosten is een aparte
bodem die geldt voor de vordering aan de debiteur.

Revision ID: df138a_bik_min
Revises: bug71_csh
"""

import sqlalchemy as sa
from alembic import op

revision = "df138a_bik_min"
down_revision = "bug71_csh"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Klant-default: minimum incassokosten (bodem voor BIK-percentage)
    op.add_column(
        "contacts",
        sa.Column("default_bik_minimum_fee", sa.Numeric(15, 2), nullable=True),
    )
    # Cascade-doelveld op dossier
    op.add_column(
        "cases",
        sa.Column("bik_minimum_fee", sa.Numeric(15, 2), nullable=True),
    )
    # Data-migratie: pre-DF138 werd `minimum_fee` als bodem voor zowel
    # honorarium-factuur als BIK gebruikt. Klanten/dossiers die nu een waarde
    # in minimum_fee hebben staan, krijgen die ook in het nieuwe veld zodat
    # bestaande BIK-bodem niet wegvalt. Lisanne kan ze daarna apart aanpassen.
    op.execute(
        "UPDATE contacts SET default_bik_minimum_fee = default_minimum_fee "
        "WHERE default_minimum_fee IS NOT NULL"
    )
    op.execute(
        "UPDATE cases SET bik_minimum_fee = minimum_fee "
        "WHERE minimum_fee IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("cases", "bik_minimum_fee")
    op.drop_column("contacts", "default_bik_minimum_fee")
