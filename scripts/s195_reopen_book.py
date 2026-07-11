"""S195 — heropen + boek de juli-betalingen die nog niet in BaseNet/Luxis zaten.

Achtergrond (Lisanne, 11 juli 2026): zij verwerkt betalingen maandelijks in BaseNet en
stort maandelijks door aan de cliënt. De export (2 juli) loopt dus een maand achter: de
betalingen die debiteuren ná de juni-verwerking deden staan nog niet in BaseNet, en zijn
daardoor niet meegekomen naar Luxis. Deze zaken zijn in BaseNet nog "Lopend".

Deze runner boekt precies die betalingen — als GEWONE betaling op de zaak (art. 6:44),
identiek aan hoe de 255 bestaande betalingen zijn geboekt (S179/S180): géén derdengelden-
boeking (dat blijft Lisanne's BaseNet-maandproces), workflow-hook UIT, gecapt op openstaand.
Zaken die in Luxis "afgesloten" staan worden eerst heropend (status -> "nieuw").

Idempotent via marker `[S195-heropen systemid=<datum>-<code>]`; --cleanup rolt terug.

Gebruik (in de backend-container):
    python scripts/s195_reopen_book.py --dry-run
    python scripts/s195_reopen_book.py --execute
    python scripts/s195_reopen_book.py --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select, text

from app.database import async_session
from app.cases.models import Case
from app.collections.models import Payment
from app.collections.schemas import PaymentCreate
from app.collections.service import create_payment_for_case, get_financial_summary

MARKER = "[S195-heropen"

# De te boeken betalingen: (zaaknr, datum, bedrag, debiteur-naam voor log).
# Bron: bankafschrift-credits die niet geboekt zijn EN horen bij een zaak die in
# BaseNet nog Lopend was. IN100097 (BaseNet "Gereed") en de niet-incasso/onbekende
# partijen zijn er BEWUST uit gelaten (besluit Arsalan 11 juli).
PAYMENTS: list[tuple[str, date, Decimal, str]] = [
    ("IN100002", date(2025, 10, 22), Decimal("6663.73"), "MK FLEX BV"),
    ("IN100197", date(2026, 7, 8), Decimal("271.38"), "Stal Sans Souci"),
    ("IN100215", date(2026, 7, 7), Decimal("250.00"), "Onderhoudsbedrijf Benjamin Rademaker"),
    ("IN100345", date(2026, 4, 1), Decimal("50.00"), "Mw S Saltik"),
    ("IN100345", date(2026, 5, 8), Decimal("50.00"), "Mw S Saltik"),
    ("IN100345", date(2026, 6, 1), Decimal("50.00"), "Mw S Saltik"),
    ("IN100345", date(2026, 7, 1), Decimal("50.00"), "Mw S Saltik"),
    ("IN100350", date(2026, 6, 25), Decimal("276.32"), "Hr JRCT Jairam"),
    ("IN100469", date(2026, 6, 2), Decimal("141.80"), "H.H.E. Henssen"),
    ("IN100476", date(2026, 6, 23), Decimal("200.00"), "KET D"),
    ("IN100480", date(2026, 6, 11), Decimal("2817.25"), "Studio The Blue Pearl"),
    ("IN100494", date(2026, 6, 16), Decimal("1036.58"), "FOX AANNEMERS KOZIJNEN"),
    ("IN100532", date(2026, 6, 10), Decimal("1026.54"), "Vosbouw"),
    ("IN100543", date(2026, 6, 18), Decimal("216.25"), "Mw SJL Cuijpers"),
    ("IN100547", date(2026, 6, 9), Decimal("14.52"), "Handelsond. Beerens B.V."),
    ("IN100553", date(2026, 6, 29), Decimal("100.00"), "Hr JPGT Janssen"),
    ("IN100568", date(2026, 6, 10), Decimal("540.69"), "Dakrenovatie Mulder"),
    ("IN100585", date(2026, 6, 11), Decimal("1428.62"), "Pirnar NL"),
]


def _marker(case_nr: str, pay_date: date) -> str:
    return f"{MARKER} systemid={pay_date.isoformat()}-{case_nr}]"


async def _load(db, tenant_id, case_nr) -> Case | None:
    res = await db.execute(
        select(Case).where(Case.tenant_id == tenant_id, Case.case_number == case_nr)
    )
    return res.scalar_one_or_none()


async def run(mode: str) -> None:
    import app.main  # noqa: F401 — registreer alle ORM-modellen (get_case selectinload's User)

    async with async_session() as db:
        tenant_id = (await db.execute(text("SELECT id FROM tenants LIMIT 1"))).scalar()

        if mode == "cleanup":
            res = await db.execute(
                select(Payment).where(Payment.description.like(f"%{MARKER}%"))
            )
            rows = list(res.scalars().all())
            for p in rows:
                p.is_active = False
            await db.commit()
            print(f"cleanup: {len(rows)} betalingen op inactief gezet")
            return

        reopened, booked, skipped = 0, 0, 0
        total = Decimal("0")
        print(f"{'zaak':10} {'datum':11} {'bedrag':>10} {'openstaand vóór':>16} "
              f"{'geboekt':>10} {'gecapt?':>8}  status")
        for case_nr, pay_date, amount, naam in PAYMENTS:
            case = await _load(db, tenant_id, case_nr)
            if case is None:
                print(f"{case_nr:10} ONTBREEKT in Luxis — overgeslagen")
                skipped += 1
                continue

            # al geboekt? (idempotent)
            exists = await db.execute(
                select(Payment.id).where(
                    Payment.tenant_id == tenant_id,
                    Payment.case_id == case.id,
                    Payment.description.like(f"%{_marker(case_nr, pay_date)}%"),
                )
            )
            if exists.first() is not None:
                print(f"{case_nr:10} {pay_date} al geboekt (marker) — overgeslagen")
                skipped += 1
                continue

            summary = await get_financial_summary(
                db, tenant_id, case.id, case.interest_type, case.contractual_rate,
                case.contractual_compound,
                bik_override=case.bik_override,
                bik_override_percentage=case.bik_override_percentage,
                include_btw_on_bik=(not case.client.is_btw_plichtig if case.client else False),
                nakosten_type=case.nakosten_type,
            )
            outstanding = summary["total_outstanding"]
            will_cap = amount > outstanding
            booked_amount = min(amount, outstanding) if will_cap else amount

            old_status = case.status
            new_status = "nieuw" if case.status == "afgesloten" else case.status

            print(f"{case_nr:10} {pay_date} {amount:>10,.2f} {outstanding:>16,.2f} "
                  f"{booked_amount:>10,.2f} {'JA' if will_cap else 'nee':>8}  "
                  f"{old_status}{' -> ' + new_status if new_status != old_status else ''}")

            if mode == "execute":
                if new_status != old_status:
                    case.status = new_status
                    reopened += 1
                desc = f"Ontvangen van {naam} (bankafschrift) {_marker(case_nr, pay_date)}"
                await create_payment_for_case(
                    db, tenant_id, case.id,
                    PaymentCreate(
                        amount=amount, payment_date=pay_date,
                        description=desc, payment_method="bank",
                    ),
                    None,
                    _skip_installment_link=True,
                    _skip_workflow_hook=True,
                    cap_to_outstanding=True,
                )
                booked += 1
                total += booked_amount

        if mode == "execute":
            await db.commit()
            print(f"\nEXECUTE klaar: {booked} betalingen geboekt (som €{total:,.2f}), "
                  f"{reopened} zaken heropend, {skipped} overgeslagen.")
        else:
            print(f"\nDRY-RUN: niets weggeschreven. {len(PAYMENTS) - skipped} te boeken, "
                  f"{skipped} al aanwezig/ontbrekend.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_const", dest="mode", const="dry")
    g.add_argument("--execute", action="store_const", dest="mode", const="execute")
    g.add_argument("--cleanup", action="store_const", dest="mode", const="cleanup")
    asyncio.run(run(ap.parse_args().mode))
