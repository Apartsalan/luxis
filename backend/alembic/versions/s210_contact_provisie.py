"""S210: default_provisie_percentage op contacts — standaard provisie per cliënt.

De klantkaart kende al standaarden voor rente, incassokosten en het
provisie-minimum, maar niet het provisie-percentage zelf. Daardoor moest de
succesprovisie op elk dossier apart gezet worden. Deze migratie voegt het
standaardpercentage toe zodat elk nieuw dossier het van de cliënt erft
(net als default_bik_override_percentage). Puur additief (nullable); contacts
heeft al RLS, dus de nieuwe kolom valt automatisch onder de bestaande policy.

Revision ID: s210_contact_provisie
Revises: s209_contact_country
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s210_contact_provisie"
down_revision: str | None = "s209_contact_country"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("default_provisie_percentage", sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contacts", "default_provisie_percentage")
