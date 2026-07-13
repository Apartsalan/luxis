"""S207c: consumentenzaken (b2c) terug van AV-rente naar wettelijke rente.

Aanleiding (vervolgsessie 13-07, akkoord Arsalan): de AV-uitrol zette óók 79
consumentenzaken op contractuele rente 2%/mnd. Rechters toetsen bij consumenten
ambtshalve op oneerlijke bedingen (Richtlijn 93/13); contractuele rente vanaf
±1%/mnd wordt vrijwel altijd vernietigd en dan vervalt zelfs de wettelijke
rente. Veilige route: consumenten op wettelijke rente (art. 6:119 BW).

Per zaak (debtor_type='b2c', interest_type='contractual'):
1. interest_type → 'statutory', contractual_rate → NULL.
2. Betalingen: allocaties (kosten/rente/hoofdsom) chronologisch herverdeeld
   onder wettelijke rente — zelfde werkwijze als rollout_av_rente.py.
3. Vorderingen met een eigen tarief-override worden gemeld (niet aangeraakt).

    docker compose exec backend python -m scripts.revert_b2c_rente            # dry-run
    docker compose exec backend python -m scripts.revert_b2c_rente --execute
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


async def run(execute: bool) -> None:
    async with async_session() as db:
        cases = (
            await db.execute(
                select(Case)
                .where(Case.debtor_type == "b2c", Case.interest_type == "contractual")
                .order_by(Case.case_number)
            )
        ).scalars().all()

        print("=" * 78)
        print("S207c — consumentenzaken terug naar wettelijke rente",
              "(EXECUTE)" if execute else "(DRY RUN)")
        print("=" * 78)

        payments_updated = 0
        overrides: list[str] = []
        rente_delta: list[tuple[str, Decimal, Decimal]] = []
        today = date.today()

        for case in cases:
            claims = (
                await db.execute(
                    select(Claim)
                    .where(Claim.case_id == case.id, Claim.is_active.is_(True))
                    .order_by(Claim.default_date)
                )
            ).scalars().all()
            payments = (
                await db.execute(
                    select(Payment)
                    .where(Payment.case_id == case.id, Payment.is_active.is_(True))
                    .order_by(Payment.payment_date, Payment.created_at)
                )
            ).scalars().all()

            peildatum = case.interest_freeze_date or today

            rente_oud = (
                await _case_interest(db, case, claims, [
                    {
                        "payment_date": p.payment_date,
                        "allocated_to_principal": p.allocated_to_principal,
                        "allocated_to_interest": p.allocated_to_interest,
                    }
                    for p in payments
                ], peildatum)
                if claims else Decimal("0")
            )

            case.interest_type = "statutory"
            case.contractual_rate = None

            for cl in claims:
                if cl.interest_rate is not None:
                    overrides.append(f"{case.case_number}: vordering met eigen tarief {cl.interest_rate}")

            if payments and claims:
                contact_btw = None
                if case.client_id is not None:
                    contact_btw = (
                        await db.execute(
                            select(Contact.is_btw_plichtig).where(Contact.id == case.client_id)
                        )
                    ).scalar_one_or_none()
                include_btw = contact_btw is False
                total_principal = sum((c.principal_amount for c in claims), Decimal("0"))
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

            rente_nieuw = (
                await _case_interest(db, case, claims, [
                    {
                        "payment_date": p.payment_date,
                        "allocated_to_principal": p.allocated_to_principal,
                        "allocated_to_interest": p.allocated_to_interest,
                    }
                    for p in payments
                ], peildatum)
                if claims else Decimal("0")
            )
            rente_delta.append((case.case_number, rente_oud, rente_nieuw))

        if execute:
            await db.commit()
        else:
            await db.rollback()

        som_oud = sum((d[1] for d in rente_delta), Decimal("0"))
        som_nieuw = sum((d[2] for d in rente_delta), Decimal("0"))
        print(f"  consumentenzaken omgezet  : {len(cases)}")
        print(f"  betalingen herverdeeld    : {payments_updated}")
        print(f"  rente-som oud (2%/mnd)    : € {som_oud}")
        print(f"  rente-som nieuw (wettelijk): € {som_nieuw}")
        print(f"  verschil                  : € {som_oud - som_nieuw}")
        if overrides:
            print(f"  ⚠ vorderingen met eigen tarief-override (NIET aangeraakt): {len(overrides)}")
            for o in overrides:
                print(f"      {o}")
        print()
        print("  Grootste verschillen:")
        for nr, oud, nieuw in sorted(rente_delta, key=lambda d: -(d[1] - d[2]))[:10]:
            print(f"    {nr:12s} € {oud:>10} → € {nieuw:>10}")
        print(f"  {'GESCHREVEN' if execute else 'DRY RUN — niets geschreven'}")
        print("=" * 78)


def main() -> None:
    p = argparse.ArgumentParser(description="Consumentenzaken naar wettelijke rente (S207c)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    args = p.parse_args()
    asyncio.run(run(execute=args.execute))


if __name__ == "__main__":
    main()
