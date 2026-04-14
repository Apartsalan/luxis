"""Add products catalog table and product_id + gl_account_code to invoice_lines.

Revision ID: df122a
Revises: df121a
"""

import sqlalchemy as sa
from alembic import op

revision = "df122a"
down_revision = "df121a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("default_price", sa.Numeric(15, 2), nullable=True),
        sa.Column("gl_account_code", sa.String(20), nullable=False),
        sa.Column("gl_account_name", sa.String(200), nullable=False),
        sa.Column("vat_type", sa.String(20), nullable=False, server_default="21"),
        sa.Column("vat_percentage", sa.Numeric(5, 2), nullable=False, server_default="21.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])
    op.create_index("ix_products_code", "products", ["code"])

    # Add product_id and gl_account_code to invoice_lines
    op.add_column("invoice_lines", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.add_column("invoice_lines", sa.Column("gl_account_code", sa.String(20), nullable=True))
    op.create_foreign_key(
        "fk_invoice_lines_product_id",
        "invoice_lines",
        "products",
        ["product_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_invoice_lines_product_id", "invoice_lines", type_="foreignkey")
    op.drop_column("invoice_lines", "gl_account_code")
    op.drop_column("invoice_lines", "product_id")
    op.drop_index("ix_products_code", table_name="products")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_table("products")
