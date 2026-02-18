"""Document system unification: Tenant iban/phone/email, Case debtor_type,
GeneratedDocument template_type/template_snapshot

Revision ID: 008
Revises: 007
Create Date: 2026-02-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Tenant: add iban, phone, email for kantoor merge fields
    op.add_column("tenants", sa.Column("iban", sa.String(34), nullable=True))
    op.add_column("tenants", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("tenants", sa.Column("email", sa.String(320), nullable=True))

    # Case: add debtor_type (b2b/b2c)
    op.add_column(
        "cases",
        sa.Column(
            "debtor_type",
            sa.String(10),
            nullable=False,
            server_default="b2b",
        ),
    )

    # GeneratedDocument: add template_type and template_snapshot for DOCX system
    op.add_column(
        "generated_documents",
        sa.Column("template_type", sa.String(50), nullable=True),
    )
    op.add_column(
        "generated_documents",
        sa.Column("template_snapshot", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_documents", "template_snapshot")
    op.drop_column("generated_documents", "template_type")
    op.drop_column("cases", "debtor_type")
    op.drop_column("tenants", "email")
    op.drop_column("tenants", "phone")
    op.drop_column("tenants", "iban")
