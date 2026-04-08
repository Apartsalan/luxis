"""drop legacy derdengelden table, rename payment_matches.derdengelden_id

Sessie 118 — DF117-21 stap 1: consolidate derdengelden into trust_funds module.

Drops the unused legacy `derdengelden` table (replaced by `trust_transactions`).
Renames the FK column `payment_matches.derdengelden_id` to `trust_transaction_id`
and re-points it at `trust_transactions.id`.

Revision ID: df11801a
Revises: c8d2e5b1f6a3
Create Date: 2026-04-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "df11801a"
down_revision: Union[str, None] = "c8d2e5b1f6a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename payment_matches.derdengelden_id → trust_transaction_id and
    #    re-point the FK at trust_transactions.
    #    Find the existing FK constraint by inspecting metadata generically.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fk_names = [
        fk["name"]
        for fk in inspector.get_foreign_keys("payment_matches")
        if "derdengelden_id" in fk.get("constrained_columns", [])
    ]
    for fk_name in fk_names:
        if fk_name:
            op.drop_constraint(fk_name, "payment_matches", type_="foreignkey")

    op.alter_column(
        "payment_matches",
        "derdengelden_id",
        new_column_name="trust_transaction_id",
    )
    op.create_foreign_key(
        "fk_payment_matches_trust_transaction_id",
        "payment_matches",
        "trust_transactions",
        ["trust_transaction_id"],
        ["id"],
    )

    # 2. Drop the legacy derdengelden table (no production data — pre-launch).
    op.drop_table("derdengelden")


def downgrade() -> None:
    # Recreate legacy derdengelden table (best-effort, columns from 004_collections).
    op.create_table(
        "derdengelden",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("counterparty", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Revert payment_matches column rename
    op.drop_constraint(
        "fk_payment_matches_trust_transaction_id", "payment_matches", type_="foreignkey"
    )
    op.alter_column(
        "payment_matches",
        "trust_transaction_id",
        new_column_name="derdengelden_id",
    )
    op.create_foreign_key(
        None,
        "payment_matches",
        "derdengelden",
        ["derdengelden_id"],
        ["id"],
    )
