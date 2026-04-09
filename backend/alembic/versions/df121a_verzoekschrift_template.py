"""Seed verzoekschrift_faillissement DOCX template as builtin managed template.

Revision ID: df121a
Revises: df120a
"""

import uuid
from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision = "df121a"
down_revision = "df120a"


TEMPLATE_KEY = "verzoekschrift_faillissement"
TEMPLATE_NAME = "Verzoekschrift faillissement (concept)"
TEMPLATE_DESCRIPTION = (
    "Concept verzoekschrift tot faillietverklaring (ex. art. 1 Fw) — "
    "meegestuurd als PDF-bijlage bij de dreigbrief."
)
TEMPLATE_FILENAME = "verzoekschrift_faillissement.docx"


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
    templates_dir = _find_templates_dir()
    if not templates_dir:
        print("WARNING: templates/ dir not found, skipping seed")
        return

    fpath = templates_dir / TEMPLATE_FILENAME
    if not fpath.exists():
        print(f"WARNING: {fpath} not found, skipping seed")
        return

    file_data = fpath.read_bytes()

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
        # Skip if a builtin already exists (idempotent re-run)
        existing = conn.execute(
            sa.text(
                "SELECT id FROM managed_templates "
                "WHERE tenant_id = :tid AND template_key = :key "
                "AND is_builtin = true"
            ),
            {"tid": tenant_id, "key": TEMPLATE_KEY},
        ).first()
        if existing:
            continue
        rows.append(
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "name": TEMPLATE_NAME,
                "description": TEMPLATE_DESCRIPTION,
                "template_key": TEMPLATE_KEY,
                "file_data": file_data,
                "original_filename": TEMPLATE_FILENAME,
                "file_size": len(file_data),
                "is_builtin": True,
                "is_active": True,
            }
        )

    if rows:
        op.bulk_insert(managed_table, rows)
        print(f"Seeded {TEMPLATE_KEY} template for {len(rows)} tenants")
    else:
        print(f"{TEMPLATE_KEY} already seeded for all tenants")


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM managed_templates "
            "WHERE template_key = :key AND is_builtin = true"
        ).bindparams(key=TEMPLATE_KEY)
    )
