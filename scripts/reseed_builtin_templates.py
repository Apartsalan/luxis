"""Re-seed builtin managed_templates from /app/templates/*.docx.

Run after regenerating DOCX files (templates/_generate_templates.py). The
initial seed happens in migration 034; later schema/footer changes in the
DOCX source require this script to push the new bytes to all tenants.

Usage (inside backend container):
    python -m scripts.reseed_builtin_templates
"""

import asyncio
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database import engine
from app.documents.models import ManagedTemplate

TEMPLATES_DIR = Path("/app/templates")

BUILTIN = {
    "herinnering": "herinnering.docx",
    "aanmaning": "aanmaning.docx",
    "14_dagenbrief": "14_dagenbrief.docx",
    "sommatie": "sommatie.docx",
    "tweede_sommatie": "tweede_sommatie.docx",
    "dagvaarding": "dagvaarding.docx",
    "renteoverzicht": "renteoverzicht.docx",
    "verzoekschrift_faillissement": "verzoekschrift_faillissement.docx",
}


async def main() -> None:
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as db:
        total = 0
        for key, filename in BUILTIN.items():
            fpath = TEMPLATES_DIR / filename
            if not fpath.exists():
                print(f"  - {key}: file ontbreekt ({fpath})")
                continue
            data = fpath.read_bytes()
            stmt = (
                update(ManagedTemplate)
                .where(
                    ManagedTemplate.template_key == key,
                    ManagedTemplate.is_builtin.is_(True),
                )
                .values(file_data=data, file_size=len(data))
            )
            result = await db.execute(stmt)
            total += result.rowcount or 0
            print(f"  - {key}: {result.rowcount or 0} rij(en) bijgewerkt")
        await db.commit()
        print(f"Klaar: {total} builtin-template rij(en) opnieuw geseed.")


if __name__ == "__main__":
    asyncio.run(main())
