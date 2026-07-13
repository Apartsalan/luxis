"""S207c: bevriesdatum (interest_freeze_date) backfillen op gesloten zaken.

Aanleiding (demo Lisanne 13-07 + vervolgsessie): de rente-uitrol (2%/mnd
samengesteld) raakte óók de 580 gesloten zaken. Zonder bevriesdatum rekent
Luxis hun rente door tot vandaag — een afgewikkelde zaak toont dan een
groeiend (spook)saldo (IN100350). De afsluit-hooks zetten de bevriesdatum
alleen going-forward; dit script trekt de bestaande gesloten zaken recht.

Recept per zaak (status afgesloten/betaald, nog zonder bevriesdatum):
1. laatste actieve betaaldatum          → afwikkelmoment (134 zaken, gemeten)
2. anders date_closed (BaseNet pdateend) → einddatum uit de bron (67 zaken)
3. anders EXPORT_DATE (2 juli 2026)      → stand-bij-overname: deze 379 zaken
   hebben geen betaling én geen einddatum (BaseNet-archief zonder pdateend;
   de ruwe export bestaat niet meer). De rente wordt bevroren op het moment
   dat BaseNet ophield de waarheid te zijn — Luxis extrapoleert niet verder.

Rollback: het script print per zaak oud → nieuw; vóór dit script stond het
veld overal op NULL, dus terugdraaien = dezelfde selectie weer op NULL zetten.

    python /app/scripts/backfill_freeze_date.py            # dry-run + meting
    python /app/scripts/backfill_freeze_date.py --execute
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

import app.main  # noqa: F401 — registreert alle ORM-modellen
from app.cases.models import Case
from app.collections.models import Payment
from app.collections.service import get_financial_summary
from app.database import async_session
from app.relations.models import Contact

CLOSED = ("afgesloten", "betaald")
EXPORT_DATE = date(2026, 7, 2)  # BaseNet-exportdatum (overnamemoment)


async def _outstanding_at(db, tenant_id, case: Case, calc_date: date | None) -> Decimal:
    """Spiegel van get_case_outstanding, maar met een expliciete peildatum."""
    include_btw_on_bik = False
    if case.client_id is not None:
        is_btw_plichtig = (
            await db.execute(
                select(Contact.is_btw_plichtig).where(Contact.id == case.client_id)
            )
        ).scalar_one_or_none()
        include_btw_on_bik = is_btw_plichtig is False

    summary = await get_financial_summary(
        db, tenant_id, case.id,
        case.interest_type, case.contractual_rate, case.contractual_compound,
        calc_date=calc_date,
        bik_override=case.bik_override,
        bik_override_percentage=case.bik_override_percentage,
        include_btw_on_bik=include_btw_on_bik,
        nakosten_type=case.nakosten_type,
    )
    return summary.get("total_outstanding", Decimal("0"))


async def run(execute: bool) -> None:
    async with async_session() as db:
        tenant_id = (await db.execute(select(Case.tenant_id).limit(1))).scalar()
        cases = (
            await db.execute(
                select(Case)
                .where(
                    Case.status.in_(CLOSED),
                    Case.interest_freeze_date.is_(None),
                )
                .order_by(Case.case_number)
            )
        ).scalars().all()

        last_pay_by_case = {
            row[0]: row[1]
            for row in await db.execute(
                select(Payment.case_id, func.max(Payment.payment_date))
                .where(Payment.is_active.is_(True))
                .group_by(Payment.case_id)
            )
        }

        print("=" * 78)
        print("S207c — bevriesdatum-backfill op gesloten zaken",
              "(EXECUTE)" if execute else "(DRY RUN)")
        print("=" * 78)

        bron_telling = {"betaaldatum": 0, "date_closed": 0, "exportdatum": 0}
        som_voor = som_na = Decimal("0.00")
        fouten = 0
        movers: list[tuple[str, str, date, Decimal, Decimal]] = []

        for case in cases:
            last_pay = last_pay_by_case.get(case.id)
            if last_pay is not None:
                freeze, bron = last_pay, "betaaldatum"
            elif case.date_closed is not None:
                freeze, bron = case.date_closed, "date_closed"
            else:
                freeze, bron = EXPORT_DATE, "exportdatum"
            bron_telling[bron] += 1

            try:
                voor = await _outstanding_at(db, tenant_id, case, date.today())
                na = await _outstanding_at(db, tenant_id, case, freeze)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {case.case_number}: rekenfout, overgeslagen: {e}")
                fouten += 1
                continue

            som_voor += voor
            som_na += na
            movers.append((case.case_number, bron, freeze, voor, na))

            if execute:
                case.interest_freeze_date = freeze

        if execute:
            await db.commit()
        else:
            await db.rollback()

        print(f"  zaken zonder bevriesdatum : {len(cases)}")
        for bron, n in bron_telling.items():
            print(f"    anker {bron:12s}: {n}")
        print(f"  rekenfouten (overgeslagen): {fouten}")
        print(f"  openstaand vóór (vandaag) : € {som_voor}")
        print(f"  openstaand ná (bevroren)  : € {som_na}")
        print(f"  verschuiving              : € {som_voor - som_na}")
        print()
        print("  Grootste verschuivingen:")
        for nr, bron, fr, voor, na in sorted(movers, key=lambda m: -(m[3] - m[4]))[:15]:
            print(f"    {nr:12s} {bron:12s} → {fr}  € {voor:>12} → € {na:>12}")
        if execute:
            print()
            print("  Volledige lijst (zaak / anker / bevriesdatum):")
            for nr, bron, fr, _voor, _na in movers:
                print(f"    {nr:12s} {bron:12s} {fr}")
        print(f"  {'GESCHREVEN' if execute else 'DRY RUN — niets geschreven'}")
        print("=" * 78)


def main() -> None:
    p = argparse.ArgumentParser(description="Bevriesdatum-backfill (S207c)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    args = p.parse_args()
    asyncio.run(run(execute=args.execute))


if __name__ == "__main__":
    main()
