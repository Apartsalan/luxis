"""Relations: contacts and contact_links tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Contacts table
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("contact_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("kvk_number", sa.String(20), nullable=True),
        sa.Column("btw_number", sa.String(30), nullable=True),
        sa.Column("visit_address", sa.String(500), nullable=True),
        sa.Column("visit_postcode", sa.String(10), nullable=True),
        sa.Column("visit_city", sa.String(255), nullable=True),
        sa.Column("postal_address", sa.String(500), nullable=True),
        sa.Column("postal_postcode", sa.String(10), nullable=True),
        sa.Column("postal_city", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_name", "contacts", ["name"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_index("ix_contacts_contact_type", "contacts", ["contact_type"])

    # Contact links table (person ↔ company)
    op.create_table(
        "contact_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("role_at_company", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["contacts.id"]),
        sa.UniqueConstraint("tenant_id", "person_id", "company_id", name="uq_contact_link"),
    )
    op.create_index("ix_contact_links_tenant_id", "contact_links", ["tenant_id"])
    op.create_index("ix_contact_links_person_id", "contact_links", ["person_id"])
    op.create_index("ix_contact_links_company_id", "contact_links", ["company_id"])


def downgrade() -> None:
    op.drop_table("contact_links")
    op.drop_table("contacts")
