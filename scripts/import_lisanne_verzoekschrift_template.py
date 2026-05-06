"""Importeer Lisanne's Verzoekschrift Bijlage DOCX als ManagedTemplate.

Bron: `templates/lisanne/Template Verzoekschrift Bijlage.docx`.
Doel: bij stap "Verzoekschrift faillissement" wordt deze DOCX als bijlage
gebruikt. Per zaak wordt een kopie gemaakt, AI vult zaakgegevens in, render
naar PDF, attach aan email. Origineel wordt nooit gemuteerd.

template_key = "verzoekschrift_bijlage"
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select, text

# Laad alle modellen via main
import app.main  # noqa: F401
from app.auth.models import Tenant
from app.database import async_session
from app.documents.models import ManagedTemplate

TEMPLATE_FILE = Path("/app/templates/lisanne/Template Verzoekschrift Bijlage.docx")
if not TEMPLATE_FILE.exists():
    TEMPLATE_FILE = (
        Path(__file__).resolve().parents[1]
        / "templates" / "lisanne" / "Template Verzoekschrift Bijlage.docx"
    )

TEMPLATE_KEY = "verzoekschrift_bijlage"
TEMPLATE_NAME = "Verzoekschrift faillissement (bijlage)"
TEMPLATE_DESC = (
    "Concept-verzoekschrift dat als bijlage meegaat bij de stap "
    "'Verzoekschrift faillissement'. AI personaliseert per zaak; "
    "origineel wordt nooit gemuteerd."
)


async def main() -> int:
    if not TEMPLATE_FILE.exists():
        print(f"FOUT: bestand niet gevonden: {TEMPLATE_FILE}")
        return 1

    file_data = TEMPLATE_FILE.read_bytes()
    print(f"Geladen: {TEMPLATE_FILE.name} ({len(file_data)} bytes)")

    async with async_session() as session:
        tenants = (await session.execute(
            select(Tenant).where(Tenant.is_active.is_(True))
        )).scalars().all()

        for tenant in tenants:
            await session.execute(text(f"SET app.current_tenant = '{tenant.id}'"))

            existing = (await session.execute(
                select(ManagedTemplate).where(
                    ManagedTemplate.tenant_id == tenant.id,
                    ManagedTemplate.template_key == TEMPLATE_KEY,
                )
            )).scalar_one_or_none()

            if existing:
                existing.file_data = file_data
                existing.file_size = len(file_data)
                existing.original_filename = TEMPLATE_FILE.name
                existing.name = TEMPLATE_NAME
                existing.description = TEMPLATE_DESC
                existing.is_active = True
                action = "bijgewerkt"
            else:
                tpl = ManagedTemplate(
                    tenant_id=tenant.id,
                    name=TEMPLATE_NAME,
                    description=TEMPLATE_DESC,
                    template_key=TEMPLATE_KEY,
                    file_data=file_data,
                    file_size=len(file_data),
                    original_filename=TEMPLATE_FILE.name,
                    is_builtin=True,
                    is_active=True,
                )
                session.add(tpl)
                action = "aangemaakt"

            await session.commit()
            print(f"{tenant.name}: ManagedTemplate '{TEMPLATE_KEY}' {action}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
