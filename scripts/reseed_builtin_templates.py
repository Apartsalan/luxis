"""Re-seed builtin managed_templates from /app/templates/*.docx.

Pure raw SQL via SQLAlchemy text() — geen ORM imports zodat het script
losstaat van het volledige model-bootstrap proces. Gebruikt de bestaande
DATABASE_URL uit de backend-omgeving.

Usage (inside backend container):
    python /app/reseed_templates.py
"""

import asyncio
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

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
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL ontbreekt in omgeving")
    engine = create_async_engine(db_url)
    total = 0
    async with engine.begin() as conn:
        for key, filename in BUILTIN.items():
            fpath = TEMPLATES_DIR / filename
            if not fpath.exists():
                print(f"  - {key}: file ontbreekt ({fpath})")
                continue
            data = fpath.read_bytes()
            result = await conn.execute(
                text(
                    "UPDATE managed_templates "
                    "SET file_data = :d, file_size = :s, updated_at = now() "
                    "WHERE template_key = :k AND is_builtin = true"
                ),
                {"d": data, "s": len(data), "k": key},
            )
            count = result.rowcount or 0
            total += count
            print(f"  - {key}: {count} rij(en) bijgewerkt")
    print(f"Klaar: {total} builtin-template rij(en) opnieuw geseed.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
