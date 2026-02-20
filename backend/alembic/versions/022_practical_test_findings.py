"""Add fields from Lisanne's practical test findings (F3, F4, F5).

F3: date_of_birth on contacts (for persons)
F4: external_reference on case_parties (other party's reference number)
F5: court_case_number on cases (rolnummer/zaaknummer rechtbank)

Revision ID: 022_practical_test_findings
Revises: 021_credit_notes
Create Date: 2026-02-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "022_practical_test_findings"
down_revision: Union[str, None] = "021_credit_notes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # F3: Geboortedatum bij personen
    op.add_column(
        "contacts",
        sa.Column("date_of_birth", sa.Date(), nullable=True),
    )

    # F4: Referentienummer van de andere partij (per case_party koppeling)
    op.add_column(
        "case_parties",
        sa.Column(
            "external_reference",
            sa.String(100),
            nullable=True,
        ),
    )

    # F5: Zaaknummer/rolnummer bij de rechtbank
    op.add_column(
        "cases",
        sa.Column(
            "court_case_number",
            sa.String(100),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("cases", "court_case_number")
    op.drop_column("case_parties", "external_reference")
    op.drop_column("contacts", "date_of_birth")
