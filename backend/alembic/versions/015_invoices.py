"""Add invoices, invoice_lines, and expenses tables.

Facturatiemodule — Invoice with auto-numbering (F2026-00001),
InvoiceLine with optional time_entry/expense FK, and Expense (verschotten).

Revision ID: 015
Revises: 014
Create Date: 2026-02-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expenses table (must come before invoice_lines due to FK)
    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            sa.Uuid(),
            sa.ForeignKey("cases.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column(
            "category",
            sa.String(50),
            nullable=False,
            server_default="overig",
        ),
        sa.Column("billable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("invoiced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("invoice_number", sa.String(20), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="concept",
        ),
        sa.Column(
            "contact_id",
            sa.Uuid(),
            sa.ForeignKey("contacts.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            sa.Uuid(),
            sa.ForeignKey("cases.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column(
            "subtotal",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "btw_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="21.00",
        ),
        sa.Column(
            "btw_amount",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total",
            sa.Numeric(15, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Invoice lines table
    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "invoice_id",
            sa.Uuid(),
            sa.ForeignKey("invoices.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("line_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "quantity",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="1",
        ),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(15, 2), nullable=False),
        sa.Column(
            "time_entry_id",
            sa.Uuid(),
            sa.ForeignKey("time_entries.id"),
            nullable=True,
        ),
        sa.Column(
            "expense_id",
            sa.Uuid(),
            sa.ForeignKey("expenses.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("invoice_lines")
    op.drop_table("invoices")
    op.drop_table("expenses")
