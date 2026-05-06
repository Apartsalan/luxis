"""Herstel sort_order + min/max wait_days op de 14 Lisanne-stappen.

Idempotent. Run op dev + prod na initiële seed.

Volgorde + dagen volgens docs/lisanne-incasso-workflow.md:
  Hoofdpad (5):  Eerste sommatie → Tweede → Derde → Sommatie laatste → Verzoekschrift
  Auto (1):      Verweer beantwoorden
  Tussenstap (6): Opvragen stukken / Voorstel dagvaarding / Treffen / Bijhouden / Akkoord / On hold
  Afsluiting (2): Betaald / Afgesloten

Hoofdpad: 4 dagen tussen stappen. Tussenstappen + auto + afsluiting: geen wachttijd.
"""

import asyncio
import sys

from sqlalchemy import select, text

import app.main  # noqa: F401  — load all models
from app.auth.models import Tenant
from app.database import async_session
from app.incasso.models import IncassoPipelineStep

# (name, sort_order, min_wait_days, max_wait_days)
LISANNE_LAYOUT: list[tuple[str, int, int, int]] = [
    ("Eerste sommatie", 1, 0, 4),
    ("Tweede sommatie", 2, 4, 4),
    ("Derde sommatie", 3, 4, 4),
    ("Sommatie laatste mogelijkheid", 4, 4, 4),
    ("Verzoekschrift faillissement", 5, 4, 4),
    ("Verweer beantwoorden", 6, 0, 0),
    ("Opvragen stukken bij cliënt", 7, 0, 0),
    ("Voorstel dagvaarding", 8, 0, 0),
    ("Treffen van regeling", 9, 0, 0),
    ("Bijhouden regeling", 10, 0, 0),
    ("Akkoord dagvaarden", 11, 0, 0),
    ("On hold", 12, 0, 0),
    ("Betaald", 13, 0, 0),
    ("Afgesloten", 14, 0, 0),
]


async def main() -> int:
    async with async_session() as session:
        tenants = (await session.execute(
            select(Tenant).where(Tenant.is_active.is_(True))
        )).scalars().all()

        for tenant in tenants:
            await session.execute(text(f"SET app.current_tenant = '{tenant.id}'"))
            steps = (await session.execute(
                select(IncassoPipelineStep).where(
                    IncassoPipelineStep.tenant_id == tenant.id,
                )
            )).scalars().all()

            by_name = {s.name: s for s in steps}
            updated = 0
            for name, order, min_d, max_d in LISANNE_LAYOUT:
                step = by_name.get(name)
                if not step:
                    print(f"  ! ontbreekt: {name} (run seed_default_steps eerst)")
                    continue
                changed = False
                if step.sort_order != order:
                    step.sort_order = order
                    changed = True
                if step.min_wait_days != min_d:
                    step.min_wait_days = min_d
                    changed = True
                if step.max_wait_days != max_d:
                    step.max_wait_days = max_d
                    changed = True
                if changed:
                    updated += 1

            # Niet-Lisanne stappen achteraan plaatsen (sort_order > 14) zodat ze
            # niet in de weg zitten als ze ooit weer geactiveerd worden.
            non_lisanne = [s for s in steps if s.name not in {n for n, *_ in LISANNE_LAYOUT}]
            for i, s in enumerate(sorted(non_lisanne, key=lambda x: x.sort_order)):
                target = 100 + i
                if s.sort_order != target:
                    s.sort_order = target

            await session.commit()
            print(f"{tenant.name}: {updated} Lisanne-stappen gealigneerd, "
                  f"{len(non_lisanne)} oude stappen verplaatst")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
