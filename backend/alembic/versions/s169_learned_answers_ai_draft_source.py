"""S169: learned_answers leert van verzonden AI-verweerconcepten.

Voegt `source_ai_draft_id` toe aan learned_answers. De backfill leert voortaan van
verzonden AI-concepten met een verweer-classificatie (echte verweer-reacties in de
juiste categorie), i.p.v. ruwe uitgaande mails (die bleken vooral sjabloon-sommaties
te bevatten — verkeerde voorbeelden).

Revision ID: s169_learned_answers_ai_draft
Revises: 1badcb2940ce
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s169_learned_answers_ai_draft"
down_revision: str | None = "1badcb2940ce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "learned_answers",
        sa.Column("source_ai_draft_id", sa.Uuid(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_learned_answers_source_ai_draft", "learned_answers", ["source_ai_draft_id"]
    )
    op.create_foreign_key(
        "fk_learned_answers_source_ai_draft",
        "learned_answers",
        "ai_drafts",
        ["source_ai_draft_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_learned_answers_source_ai_draft", "learned_answers", type_="foreignkey"
    )
    op.drop_constraint(
        "uq_learned_answers_source_ai_draft", "learned_answers", type_="unique"
    )
    op.drop_column("learned_answers", "source_ai_draft_id")
