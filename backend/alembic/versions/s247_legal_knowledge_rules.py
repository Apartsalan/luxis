"""S248: legal_knowledge_rules — curated juridische kennisregels.

Proactieve kennis ('déze standaard-stelling is onjuist, dít is de weerlegging,
art. X BW') met een HARDE toepasbaarheids-poort. Anders dan learned_answers
(empirisch, met bronmail) — deelt alleen de goedkeur-flow, niet de backfill.

Tenant-tabel → RLS in DEZELFDE migratie (huisregel S183-1): `apply_rls` is
idempotent en ontdekt de nieuwe tabel zelf. Zonder deze aanroep blokkeert de
opstartcontrole (app.main.lifespan) + de drift-guard-test de deploy.

Revision ID: s247_legal_knowledge_rules
Revises: s246c_sched_kinds
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.security.rls import apply_rls

revision: str = "s247_legal_knowledge_rules"
down_revision: str | None = "s246c_sched_kinds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "legal_knowledge_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("defense_type", sa.String(length=50), nullable=False),
        sa.Column("applies_to", sa.String(length=10), nullable=False, server_default="alle"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("claim_description", sa.Text(), nullable=True),
        sa.Column("rebuttal_body", sa.Text(), nullable=False),
        sa.Column("legal_basis", sa.String(length=200), nullable=True),
        sa.Column("language", sa.String(length=5), nullable=False, server_default="nl"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="kandidaat"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        # server_default verplicht: TimestampMixin vult deze niet in Python (prod uit de
        # migratie, testDB uit de modellen — zie s246_scheduled_emails).
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_legal_knowledge_rules_tenant_id", "legal_knowledge_rules", ["tenant_id"]
    )
    op.create_index(
        "ix_legal_knowledge_rules_defense_type", "legal_knowledge_rules", ["defense_type"]
    )
    op.create_index(
        "ix_legal_knowledge_rules_status", "legal_knowledge_rules", ["status"]
    )

    # Huisregel S183-1: nieuwe tenant-tabel → RLS in DEZELFDE migratie.
    apply_rls(op.get_bind())


def downgrade() -> None:
    op.drop_index("ix_legal_knowledge_rules_status", table_name="legal_knowledge_rules")
    op.drop_index("ix_legal_knowledge_rules_defense_type", table_name="legal_knowledge_rules")
    op.drop_index("ix_legal_knowledge_rules_tenant_id", table_name="legal_knowledge_rules")
    op.drop_table("legal_knowledge_rules")
