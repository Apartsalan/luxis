"""Create managed_templates table and seed builtin templates from disk.

Revision ID: 034_managed_templates
Revises: 033_incasso_max_wait_days
"""

import uuid
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "034_managed_templates"
down_revision = "033_incasso_max_wait_days"

# Template key -> (Dutch name, filename on disk)
BUILTIN_TEMPLATES = {
    "herinnering": ("Herinnering", "herinnering.docx"),
    "aanmaning": ("Aanmaning", "aanmaning.docx"),
    "14_dagenbrief": ("14-dagenbrief", "14_dagenbrief.docx"),
    "sommatie": ("Sommatie", "sommatie.docx"),
    "tweede_sommatie": ("Tweede sommatie", "tweede_sommatie.docx"),
    "dagvaarding": ("Dagvaarding", "dagvaarding.docx"),
    "renteoverzicht": ("Renteoverzicht", "renteoverzicht.docx"),
}


def _find_templates_dir() -> Path | None:
    """Find the templates directory (works in Docker and locally)."""
    candidates = [
        Path("/app/templates"),  # Docker
        Path(__file__).resolve().parents[3] / "templates",  # Local
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def upgrade() -> None:
    op.create_table(
        "managed_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_key", sa.String(50), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column(
            "is_builtin",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_managed_templates_tenant_key",
        "managed_templates",
        ["tenant_id", "template_key"],
    )

    # Seed builtin templates for each tenant
    templates_dir = _find_templates_dir()
    if not templates_dir:
        print("WARNING: templates/ dir not found, skipping seed")
        return

    conn = op.get_bind()
    tenants = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()

    if not tenants:
        print("No tenants found, skipping seed")
        return

    managed_table = sa.table(
        "managed_templates",
        sa.column("id", sa.Uuid()),
        sa.column("tenant_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("template_key", sa.String()),
        sa.column("file_data", sa.LargeBinary()),
        sa.column("original_filename", sa.String()),
        sa.column("file_size", sa.Integer()),
        sa.column("is_builtin", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
    )

    rows = []
    for tenant_row in tenants:
        tenant_id = tenant_row[0]
        for key, (name, filename) in BUILTIN_TEMPLATES.items():
            fpath = templates_dir / filename
            if not fpath.exists():
                print(f"WARNING: {fpath} not found, skipping")
                continue
            file_data = fpath.read_bytes()
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "tenant_id": tenant_id,
                    "name": name,
                    "description": f"Standaard {name.lower()} sjabloon",
                    "template_key": key,
                    "file_data": file_data,
                    "original_filename": filename,
                    "file_size": len(file_data),
                    "is_builtin": True,
                    "is_active": True,
                }
            )

    if rows:
        op.bulk_insert(managed_table, rows)
        print(f"Seeded {len(rows)} builtin templates")


def downgrade() -> None:
    op.drop_index("ix_managed_templates_tenant_key")
    op.drop_table("managed_templates")
