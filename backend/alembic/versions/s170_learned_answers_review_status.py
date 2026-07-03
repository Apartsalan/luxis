"""S170: verweer-antwoord-bibliotheek met goedkeuring (herziening shadow-learning).

Na een kritische review (S167) is shadow-learning omgebouwd van 'stil automatisch leren'
naar 'kandidaten die de advocaat goedkeurt'. Dit voegt de daarvoor benodigde velden toe
aan learned_answers:

* status         — 'kandidaat' / 'goedgekeurd' / 'afgewezen'; alleen goedgekeurde voeden de AI.
* anonymized_body — de door de advocaat bevestigde, geanonimiseerde tekst (enige dat de AI in mag).
* defense_type   — type verweer (library-key of 'overig') voor gerichte matching.
* reviewed_at    — moment van goedkeuren/afwijzen.

Bestaande actieve voorbeelden (is_active=true) worden als 'goedgekeurd' overgenomen met hun
huidige body als geanonimiseerde tekst, zodat gedrag behouden blijft (op productie 0 rijen).

Revision ID: s170_learned_answers_review
Revises: s169_learned_answers_ai_draft
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s170_learned_answers_review"
down_revision: str | None = "s169_learned_answers_ai_draft"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "learned_answers",
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="kandidaat"
        ),
    )
    op.add_column(
        "learned_answers",
        sa.Column("anonymized_body", sa.Text(), nullable=True),
    )
    op.add_column(
        "learned_answers",
        sa.Column("defense_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "learned_answers",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_learned_answers_status", "learned_answers", ["status"]
    )
    # Bestaande actieve voorbeelden overnemen als goedgekeurd (behoud van gedrag).
    op.execute(
        "UPDATE learned_answers "
        "SET status = 'goedgekeurd', anonymized_body = body "
        "WHERE is_active = true"
    )


def downgrade() -> None:
    op.drop_index("ix_learned_answers_status", table_name="learned_answers")
    op.drop_column("learned_answers", "reviewed_at")
    op.drop_column("learned_answers", "defense_type")
    op.drop_column("learned_answers", "anonymized_body")
    op.drop_column("learned_answers", "status")
