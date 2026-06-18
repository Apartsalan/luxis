"""S168 learned_answers — shadow-learning opslag.

Nieuwe tabel `learned_answers`: Lisanne's eigen eerder verzonden antwoorden, bewaard
per classificatie-categorie als voorbeeld voor toekomstige conceptgeneratie (zie
app/ai_agent/learned_answers.py + models.LearnedAnswer).

NB: de autogenerate-versie bevatte veel valse drift (drop_index/drop_constraint op
bestaande tabellen omdat custom/composite indexen niet 1-op-1 round-trippen). Die zijn
verwijderd — deze migratie maakt UITSLUITEND de nieuwe tabel + bijbehorende indexen aan.

Revision ID: 1badcb2940ce
Revises: s167_14dagenbrief_active
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "1badcb2940ce"
down_revision: str | None = "s167_14dagenbrief_active"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learned_answers",
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("source_synced_email_id", sa.Uuid(), nullable=True),
        sa.Column("source_case_id", sa.Uuid(), nullable=True),
        sa.Column("use_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["source_synced_email_id"], ["synced_emails.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_synced_email_id"),
    )
    op.create_index(
        op.f("ix_learned_answers_category"), "learned_answers", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_learned_answers_tenant_id"), "learned_answers", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learned_answers_tenant_id"), table_name="learned_answers")
    op.drop_index(op.f("ix_learned_answers_category"), table_name="learned_answers")
    op.drop_table("learned_answers")
