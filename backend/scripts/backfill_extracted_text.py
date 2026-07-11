"""S199: vul doorzoekbare tekst voor bestaande dossierstukken.

Run vanuit de backend-container:
    python scripts/backfill_extracted_text.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app.main  # noqa: F401 - registreert alle modellen voor SQLAlchemy
from app.auth.models import Tenant
from app.cases import files_service
from app.cases.models import CaseFile
from app.database import engine
from app.search.extract import extract_text

SUPPORTED_CONTENT_TYPES = ("application/pdf", "text/html", "text/plain")
BATCH_SIZE = 100


async def backfill() -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    processed = with_text = without_text = missing_file = 0

    async with session_factory() as db:
        tenant_ids = list((await db.execute(select(Tenant.id))).scalars().all())

        for tenant_id in tenant_ids:
            rows = (
                await db.execute(
                    select(
                        CaseFile.id,
                        CaseFile.tenant_id,
                        CaseFile.case_id,
                        CaseFile.stored_filename,
                        CaseFile.content_type,
                    ).where(
                        CaseFile.tenant_id == tenant_id,
                        CaseFile.extracted_text.is_(None),
                        CaseFile.is_active.is_(True),
                        CaseFile.content_type.in_(SUPPORTED_CONTENT_TYPES),
                    )
                )
            ).all()

            for case_file in rows:
                processed += 1
                file_path = files_service.get_file_path(case_file)
                if not file_path.is_file():
                    missing_file += 1
                else:
                    text = extract_text(file_path.read_bytes(), case_file.content_type)
                    if text is None:
                        without_text += 1
                    else:
                        await db.execute(
                            update(CaseFile)
                            .where(
                                CaseFile.id == case_file.id,
                                CaseFile.tenant_id == tenant_id,
                            )
                            .values(extracted_text=text)
                        )
                        with_text += 1

                if processed % BATCH_SIZE == 0:
                    await db.commit()

        await db.commit()

    print(f"Verwerkt: {processed}")
    print(f"Met tekst: {with_text}")
    print(f"Zonder tekst: {without_text}")
    print(f"Bestand ontbreekt: {missing_file}")


if __name__ == "__main__":
    asyncio.run(backfill())
