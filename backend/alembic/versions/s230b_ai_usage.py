"""S230b: ai_usage — verbruiksregel per AI-aanroep (kostenvraag Arsalan).

Er ging API-tegoed doorheen (~€10 in enkele dagen) zonder dat iemand kon zien
waaraan: token_count op ai_drafts bleef leeg en classificatie/intake
registreerden niets. Elke aanroep in kimi_client schrijft nu één regel met
doel, model, tokens en geschatte kosten.

Globale tabel (geen tenant_id) — net als scheduler_heartbeat en interest_rates;
het verbruik hangt aan de installatie-brede API-sleutel. Geen RLS nodig
(de drift-guard kijkt alleen naar tabellen mét tenant_id).

Revision ID: s230b_ai_usage
Revises: s230_handelsrente_2026_07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s230b_ai_usage"
down_revision: str | None = "s230_handelsrente_2026_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_called_at", "ai_usage", ["called_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_called_at", table_name="ai_usage")
    op.drop_table("ai_usage")
