"""S207c: basenet_origin_status op cases + backfill uit de import-notitie.

Onderscheidt BaseNet-import-dossiers die nog LIEPEN (Lopend/Wacht → in fases
heropenen) van dossiers die al AFGEHANDELD waren (Gereed/Geannuleerd/Offerte →
blijven dicht). De originele status stond al als vrije tekst in `debtor_notes`
("[BaseNet-import] ... BaseNet-status: Lopend"); deze migratie tilt dat naar een
echt, doorzoekbaar veld. Idempotent: leest alleen wat de import zelf schreef.

Revision ID: s207c_basenet_origin_status
Revises: s207b_interest_freeze_date
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s207c_basenet_origin_status"
down_revision: str | None = "s207b_interest_freeze_date"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("basenet_origin_status", sa.String(length=20), nullable=True),
    )
    # Backfill uit de import-notitie. De import schreef exact "BaseNet-status: X"
    # met X ∈ {Lopend, Wacht, Gereed, Geannuleerd, Offerte}. substring pakt het
    # eerste woord na de dubbele punt; onbekende/afwezige notities blijven NULL.
    op.execute(
        r"""
        UPDATE cases
        SET basenet_origin_status =
            substring(debtor_notes FROM 'BaseNet-status:\s*([A-Za-z]+)')
        WHERE debtor_notes LIKE '%BaseNet-status:%'
          AND basenet_origin_status IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("cases", "basenet_origin_status")
