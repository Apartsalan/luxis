"""S207: AV-rente (2% per maand, samengesteld) uitrollen over bestaande dossiers.

Aanleiding (demo Lisanne 13-07): IN100197 toonde €284,62 rente terwijl BaseNet
€723,31 rekent. Oorzaak: de BaseNet-import zette dossiers op wettelijke
(handels)rente; de uit de AV gelezen 2% per maand (terms_interest_*, S177) werd
alleen bij níeuwe dossiers toegepast. Bovendien rekent BaseNet maandelijks
samengesteld (rente-op-rente per maand) — bewezen met de rentespecificatie van
IN100197, zie tests/test_interest_monthly.py.

Wat dit script doet, voor cliënten met een uit de AV gelezen rentetarief en
zónder handmatige rente-override (default_interest_type):

1. Cliënt: terms_interest_compound → true (BaseNet-praktijk van de opdrachtgevers).
2. Dossiers: interest_type='contractual', contractual_rate=<AV-tarief>,
   contractual_compound=true.
3. Vorderingen: rate_basis=<AV-basis> (waar geen per-vordering tarief-override staat).
4. Betalingen: allocaties (kosten/rente/hoofdsom) chronologisch herverdeeld
   onder het nieuwe renteregime — gespiegeld aan create_payment (art. 6:44 BW).
5. Rapport: 'betaald'-zaken die onder het nieuwe regime weer een restant hebben
   (worden NIET automatisch heropend — S198: geen stille heropening).

    docker compose exec backend python -m scripts.rollout_av_rente             # dry-run
    docker compose exec backend python -m scripts.rollout_av_rente --execute
    docker compose exec backend python -m scripts.rollout_av_rente --case IN100197
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

import app.main  # noqa: F401 — registreert alle modellen
from app.cases.models import Case
from app.collections.interest import calculate_case_interest
from app.collections.models import Claim, Payment
from app.collections.nakosten import calculate_nakosten
from app.collections.payment_distribution import distribute_payment
from app.collections.service import _round2, calculate_bik
from app.database import async_session
from app.relations.models import Contact


async def _case_interest(db, case: Case, claims: list[Claim], payment_dicts, calc_date):
    claim_dicts = [
        {
            "id": str(c.id),
            "description": c.description,
            "principal_amount": c.principal_amount,
            "default_date": c.default_date,
            "rate_basis": c.rate_basis,
            "interest_rate": c.interest_rate,
        }
        for c in claims
    ]
    result = await calculate_case_interest(
        db, str(case.id), case.interest_type, case.contractual_rate,
        case.contractual_compound, claim_dicts, calc_date, payments=payment_dicts,
    )
    return result["total_interest"]


def _case_costs(case: Case, total_principal: Decimal, include_btw: bool) -> Decimal:
    # Spiegel van create_payment (collections/service.py): percentage > vast > WIK.
    if case.bik_override_percentage is not None:
        costs = _round2(total_principal * case.bik_override_percentage / Decimal("100"))
    elif case.bik_override is not None:
        costs = case.bik_override
    else:
        costs = calculate_bik(total_principal, include_btw=include_btw)["bik_inclusive"]
    return costs + calculate_nakosten(case.nakosten_type)


async def run(execute: bool, only_case: str | None) -> None:
    async with async_session() as db:
        contacts = (
            await db.execute(
                select(Contact).where(Contact.terms_interest_rate.isnot(None))
            )
        ).scalars().all()
        eligible = [c for c in contacts if not c.default_interest_type]

        print("=" * 78)
        print("S207 — AV-rente uitrol (2%/mnd samengesteld)",
              "(EXECUTE)" if execute else "(DRY RUN)")
        print("=" * 78)

        cases_updated = claims_updated = payments_updated = 0
        paid_with_rest: list[tuple[str, Decimal]] = []
        today = date.today()

        for contact in eligible:
            if execute and not contact.terms_interest_compound:
                contact.terms_interest_compound = True

            q = select(Case).where(Case.client_id == contact.id)
            if only_case:
                q = q.where(Case.case_number == only_case)
            cases = (await db.execute(q)).scalars().all()

            for case in cases:
                old = (case.interest_type, case.contractual_rate, case.contractual_compound)
                case.interest_type = "contractual"
                case.contractual_rate = contact.terms_interest_rate
                case.contractual_compound = True
                if old != ("contractual", contact.terms_interest_rate, True):
                    cases_updated += 1

                claims = (
                    await db.execute(
                        select(Claim)
                        .where(Claim.case_id == case.id, Claim.is_active.is_(True))
                        .order_by(Claim.default_date)
                    )
                ).scalars().all()
                for cl in claims:
                    if cl.interest_rate is None and cl.rate_basis != contact.terms_interest_basis:
                        cl.rate_basis = contact.terms_interest_basis
                        claims_updated += 1

                payments = (
                    await db.execute(
                        select(Payment)
                        .where(Payment.case_id == case.id, Payment.is_active.is_(True))
                        .order_by(Payment.payment_date, Payment.created_at)
                    )
                ).scalars().all()

                if payments and claims:
                    total_principal = sum(
                        (c.principal_amount for c in claims), Decimal("0")
                    )
                    include_btw = not contact.is_btw_plichtig
                    total_costs = _case_costs(case, total_principal, include_btw)
                    prior_dicts: list[dict] = []
                    prev_c = prev_i = prev_p = Decimal("0")
                    for p in payments:
                        total_interest = await _case_interest(
                            db, case, claims, prior_dicts, p.payment_date
                        )
                        dist = distribute_payment(
                            payment_amount=p.amount,
                            outstanding_costs=max(Decimal("0"), total_costs - prev_c),
                            outstanding_interest=max(Decimal("0"), total_interest - prev_i),
                            outstanding_principal=max(Decimal("0"), total_principal - prev_p),
                        )
                        changed = (
                            p.allocated_to_costs != dist["to_costs"]
                            or p.allocated_to_interest != dist["to_interest"]
                            or p.allocated_to_principal != dist["to_principal"]
                        )
                        p.allocated_to_costs = dist["to_costs"]
                        p.allocated_to_interest = dist["to_interest"]
                        p.allocated_to_principal = dist["to_principal"]
                        if changed:
                            payments_updated += 1
                        prev_c += dist["to_costs"]
                        prev_i += dist["to_interest"]
                        prev_p += dist["to_principal"]
                        prior_dicts.append(
                            {
                                "payment_date": p.payment_date,
                                "allocated_to_principal": p.allocated_to_principal,
                                "allocated_to_interest": p.allocated_to_interest,
                            }
                        )

                    # 'Betaald'-zaken met nieuw restant: rapporteren, niet heropenen.
                    if case.status == "betaald":
                        interest_now = await _case_interest(
                            db, case, claims, prior_dicts, today
                        )
                        outstanding = (
                            total_principal + interest_now + total_costs
                            - sum((p.amount for p in payments), Decimal("0"))
                        )
                        if outstanding > Decimal("0.01"):
                            paid_with_rest.append((case.case_number, _round2(outstanding)))

                if only_case and case.case_number == only_case:
                    interest_now = await _case_interest(
                        db, case, claims,
                        [
                            {
                                "payment_date": p.payment_date,
                                "allocated_to_principal": p.allocated_to_principal,
                                "allocated_to_interest": p.allocated_to_interest,
                            }
                            for p in payments
                        ],
                        today,
                    )
                    print(f"  {case.case_number}: rente per {today} = € {interest_now}")
                    for p in payments:
                        print(
                            f"    betaling {p.payment_date} € {p.amount}: "
                            f"kosten {p.allocated_to_costs} / rente {p.allocated_to_interest}"
                            f" / hoofdsom {p.allocated_to_principal}"
                        )

        if execute:
            await db.commit()
        else:
            await db.rollback()

        print("-" * 78)
        print(f"  cliënten met AV-tarief : {len(eligible)}")
        print(f"  dossiers omgezet       : {cases_updated}")
        print(f"  vorderingen op maandbasis: {claims_updated}")
        print(f"  betalingen herverdeeld : {payments_updated}")
        if paid_with_rest:
            print(f"  ⚠ 'betaald'-zaken met nieuw restant (NIET heropend): {len(paid_with_rest)}")
            for nr, bedrag in paid_with_rest:
                print(f"      {nr}: € {bedrag}")
        print(f"  {'GESCHREVEN' if execute else 'DRY RUN — niets geschreven'}")
        print("=" * 78)


def main() -> None:
    p = argparse.ArgumentParser(description="AV-rente uitrol (S207)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    p.add_argument("--case", help="Alleen dit dossiernummer (bv. IN100197)")
    args = p.parse_args()
    asyncio.run(run(execute=args.execute, only_case=args.case))


if __name__ == "__main__":
    main()
