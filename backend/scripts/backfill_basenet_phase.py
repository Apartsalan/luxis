"""S207d: BaseNet-werkfase (basenet_origin_phase) vullen uit de export.

Leest /tmp/basenet_fase.json ({inccode: werkfase}, gebouwd uit de XML-export:
incstatus → CustomProjectStatus.psdescription) en zet de fase op elke zaak.
Idempotent: overschrijft alleen zaken waarvan de fase afwijkt of leeg is.

Vooraf: docker compose exec -T backend sh -c 'cat > /tmp/basenet_fase.json' < basenet_fase.json

    python /app/scripts/backfill_basenet_phase.py            # dry-run
    python /app/scripts/backfill_basenet_phase.py --execute
"""

from __future__ import annotations

import argparse
import asyncio
import json

from sqlalchemy import select

import app.main  # noqa: F401 — registreert alle ORM-modellen
from app.cases.models import Case
from app.database import async_session

FASE_JSON = "/tmp/basenet_fase.json"


async def run(execute: bool) -> None:
    fases: dict[str, str] = json.load(open(FASE_JSON))
    async with async_session() as db:
        cases = (await db.execute(select(Case))).scalars().all()
        gezet = al_goed = geen_bron = 0
        for case in cases:
            fase = fases.get(case.case_number)
            if fase is None:
                geen_bron += 1  # niet uit de BaseNet-import (Luxis-eigen zaak)
                continue
            if case.basenet_origin_phase == fase:
                al_goed += 1
                continue
            case.basenet_origin_phase = fase[:60]
            gezet += 1

        if execute:
            await db.commit()
        else:
            await db.rollback()

        print("S207d — BaseNet-werkfase backfill", "(EXECUTE)" if execute else "(DRY RUN)")
        print(f"  gezet: {gezet} | al goed: {al_goed} | geen BaseNet-bron: {geen_bron}")
        print(f"  {'GESCHREVEN' if execute else 'DRY RUN — niets geschreven'}")


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet-werkfase backfill (S207d)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    args = p.parse_args()
    asyncio.run(run(execute=args.execute))


if __name__ == "__main__":
    main()
