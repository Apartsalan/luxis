"""products: unique (tenant_id, code) among active rows (AUDIT-MEDIUM).

get_product_by_code() used scalar_one_or_none(), which crashes with
MultipleResultsFound the moment two rows share a (tenant_id, code). Nothing at
the DB level prevented duplicates. Add a partial-unique index over active rows
only, so a soft-deleted code can still be reused while two *active* products can
never collide. Mirrors Product.__table_args__ so create_all (tests) and the
migration (prod) stay in lockstep.

Revision ID: prod_uniq_active_code
Revises: s151_dead_pipeline_rules
"""

import sqlalchemy as sa

from alembic import op

revision = "prod_uniq_active_code"
down_revision = "s151_dead_pipeline_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_products_tenant_code_active",
        "products",
        ["tenant_id", "code"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index("uq_products_tenant_code_active", table_name="products")
