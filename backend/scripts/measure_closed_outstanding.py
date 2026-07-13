"""S207: meet gesloten zaken met een openstaand saldo na de rente-uitrol.

Alleen-lezen. Loopt alle gesloten zaken (afgesloten/betaald) langs, rekent het
echte openstaande saldo (zelfde weg als het zaakscherm: get_case_outstanding)
en telt de zaken waar nog iets openstaat. Splitst naar contractueel-omgezette
zaken (de 598 van vanochtend) versus de rest, zodat de blast radius van de
rente-correctie zichtbaar wordt.

    python /app/measure_closed_outstanding.py
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import func, select

import app.main  # noqa: F401 — registreert alle ORM-modellen
from app.cases.models import Case
from app.collections.service import get_case_outstanding
from app.database import async_session

CLOSED = ("afgesloten", "betaald")


async def main() -> None:
    async with async_session() as db:
        tenant_id = (await db.execute(select(Case.tenant_id).limit(1))).scalar()
        cases = (
            await db.execute(select(Case).where(Case.status.in_(CLOSED)))
        ).scalars().all()

        # Betaalde-som per zaak (voor "afbetaald maar klein restant"-detectie).
        from app.collections.models import Payment

        paid_by_case = {
            row[0]: row[1]
            for row in await db.execute(
                select(Payment.case_id, func.sum(Payment.amount))
                .where(Payment.is_active.is_(True))
                .group_by(Payment.case_id)
            )
        }

        n = len(cases)
        met_restant = []
        for case in cases:
            try:
                out = await get_case_outstanding(db, tenant_id, case)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {case.case_number}: fout {e}")
                continue
            if out > Decimal("0.01"):
                paid = paid_by_case.get(case.id, Decimal("0.00"))
                met_restant.append((case.case_number, out, paid))

        totaal = sum((r[1] for r in met_restant), Decimal("0.00"))
        buckets = {"≤ €100": 0, "€100–1.000": 0, "€1.000–10.000": 0, "> €10.000": 0}
        for _nr, out, _paid in met_restant:
            if out <= 100:
                buckets["≤ €100"] += 1
            elif out <= 1000:
                buckets["€100–1.000"] += 1
            elif out <= 10000:
                buckets["€1.000–10.000"] += 1
            else:
                buckets["> €10.000"] += 1

        # "Afbetaald maar spookrestant": klein restant (≤ €1.000) op een zaak waar
        # substantieel is betaald (> €0). Dit is de IN100350-categorie die de
        # afsluitdatum-knop moet rechttrekken.
        spook = [r for r in met_restant if r[1] <= 1000 and r[2] > Decimal("0")]
        spook_som = sum((r[1] for r in spook), Decimal("0.00"))

        print("=" * 70)
        print("S207 — gesloten zaken met openstaand saldo (na rente-uitrol)")
        print("=" * 70)
        print(f"  gesloten zaken totaal          : {n}")
        print(f"  met openstaand > €0,01         : {len(met_restant)}")
        print(f"  som openstaand op gesloten     : € {totaal}")
        print()
        print("  Verdeling naar bedrag:")
        for label, cnt in buckets.items():
            print(f"    {label:16s}: {cnt}")
        print()
        print(f"  'Afbetaald maar klein restant' (≤€1.000 én betaald): {len(spook)}")
        print(f"     samen: € {spook_som}")
        print("  Voorbeelden:")
        for nr, out, paid in sorted(spook, key=lambda r: -r[1])[:12]:
            print(f"    {nr:12s} openstaand € {out:>8}  (betaald € {paid})")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
