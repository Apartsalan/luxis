"""Wachters (S242): dubbelklik/2 tabs mag een betaling nooit dubbel boeken.

S240 vondst 2 (bril 'slordige gebruiker', G5): twee gelijktijdige identieke
deelbetalingen kregen allebei 201 — de UI-disable dempt alleen een nette
dubbelklik, twee tabs of een trage verbinding boekt gewoon dubbel. De poort
zit in de service-laag (`create_payment`), het gedeelde punt van álle routes
(handmatige UI, termijn-registratie, AI-agent, derdengelden) — agent-laag-
afspraak S237. Twee lagen:

1. een rij-slot op de zaak (zelfde patroon als derdengelden audit #70)
   serialiseert gelijktijdige boekingen, en
2. een dedup-venster: een identieke betaling (bedrag, datum, wijze,
   omschrijving) binnen enkele seconden na de vorige wordt geweigerd.

Bankimport en BaseNet-import boeken vanaf bron-records (twee identieke échte
overboekingen op één dag zijn daar legitiem) en slaan de dedup-poort expliciet
over via ``_skip_duplicate_guard=True`` — het rij-slot geldt daar wél.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.collections.models import Claim, InterestRate
from app.collections.schemas import PaymentCreate
from app.collections.service import create_payment
from app.shared.exceptions import BadRequestError
from tests.helpers.incasso_fixtures import create_incasso_case


async def _seed_case_with_claim(db, tenant, company, user, *, case_number):
    """Zaak + vordering €100 + rentetarief, zodat create_payment kan rekenen."""
    case = await create_incasso_case(
        db, tenant.id, company, None, user, case_number=case_number
    )
    db.add(
        InterestRate(
            id=uuid.uuid4(), rate_type="statutory", rate=Decimal("4.00"),
            effective_from=date(2024, 1, 1),
        )
    )
    db.add(
        Claim(
            id=uuid.uuid4(), tenant_id=tenant.id, case_id=case.id,
            description="Factuur", principal_amount=Decimal("100.00"),
            invoice_date=date.today(), default_date=date.today(),
        )
    )
    await db.flush()
    return case


def _payment(amount="25.00", description="Deelbetaling"):
    return PaymentCreate(
        amount=Decimal(amount),
        payment_date=date.today(),
        description=description,
        payment_method="bank",
    )


@pytest.mark.asyncio
async def test_double_submit_identical_payment_rejected(
    db, test_tenant, test_user, test_company
):
    """Tweede identieke boeking direct na de eerste → geweigerd, 1 betaling."""
    case = await _seed_case_with_claim(
        db, test_tenant, test_company, test_user, case_number="2026-09821"
    )
    await create_payment(db, test_tenant.id, case.id, _payment(), test_user.id)

    with pytest.raises(BadRequestError, match="al geboekt"):
        await create_payment(db, test_tenant.id, case.id, _payment(), test_user.id)

    payments = (
        await db.execute(
            text("SELECT count(*) FROM payments WHERE case_id = :c"),
            {"c": str(case.id)},
        )
    ).scalar()
    assert payments == 1


@pytest.mark.asyncio
async def test_concurrent_double_submit_second_rejected(
    db, test_tenant, test_user, test_company, session_factory
):
    """Echte gelijktijdigheid (de S240-reproductie: twee tabs, beide 201).

    B start terwijl A's transactie nog open staat — het dedup-venster alléén
    zou dan niets zien (A is nog niet gecommit). Het zaak-slot laat B wachten
    tot A klaar is; daarná ziet B de geboekte betaling en weigert. Zonder de
    fix boekt B na A's commit gewoon door → 2 betalingen → deze test rood.
    """
    import asyncio

    case = await _seed_case_with_claim(
        db, test_tenant, test_company, test_user, case_number="2026-09822"
    )
    await db.commit()  # setup zichtbaar maken voor de losse sessies

    sa = session_factory()
    sb = session_factory()
    try:
        # A boekt en houdt zijn transactie open (slot blijft vastgehouden).
        await create_payment(sa, test_tenant.id, case.id, _payment(), test_user.id)

        # B dient dezelfde betaling in en blokkeert op het slot...
        task = asyncio.ensure_future(
            create_payment(sb, test_tenant.id, case.id, _payment(), test_user.id)
        )
        await asyncio.sleep(0.3)
        assert not task.done(), "B had moeten wachten op het zaak-slot"

        # ...tot A commit; dan ziet B de geboekte betaling en weigert.
        await sa.commit()
        with pytest.raises(BadRequestError, match="al geboekt"):
            await asyncio.wait_for(task, timeout=5)

        payments = (
            await db.execute(
                text("SELECT count(*) FROM payments WHERE case_id = :c"),
                {"c": str(case.id)},
            )
        ).scalar()
        assert payments == 1
    finally:
        await sa.rollback()
        await sb.rollback()
        await sa.close()
        await sb.close()


@pytest.mark.asyncio
async def test_different_payment_still_books(
    db, test_tenant, test_user, test_company
):
    """Tegenproef: een ánder bedrag direct erna is een echte tweede betaling."""
    case = await _seed_case_with_claim(
        db, test_tenant, test_company, test_user, case_number="2026-09823"
    )
    await create_payment(db, test_tenant.id, case.id, _payment("25.00"), test_user.id)
    await create_payment(db, test_tenant.id, case.id, _payment("30.00"), test_user.id)

    payments = (
        await db.execute(
            text("SELECT count(*) FROM payments WHERE case_id = :c"),
            {"c": str(case.id)},
        )
    ).scalar()
    assert payments == 2


@pytest.mark.asyncio
async def test_identical_payment_after_window_still_books(
    db, test_tenant, test_user, test_company
):
    """Tegenproef: buiten het venster is een identieke betaling gewoon geldig
    (bv. tweede termijn van €25 een dag later — hier gesimuleerd door de
    eerste boeking ouder te maken)."""
    case = await _seed_case_with_claim(
        db, test_tenant, test_company, test_user, case_number="2026-09824"
    )
    await create_payment(db, test_tenant.id, case.id, _payment(), test_user.id)
    await db.execute(
        text(
            "UPDATE payments SET created_at = created_at - interval '60 seconds' "
            "WHERE case_id = :c"
        ),
        {"c": str(case.id)},
    )

    await create_payment(db, test_tenant.id, case.id, _payment(), test_user.id)

    payments = (
        await db.execute(
            text("SELECT count(*) FROM payments WHERE case_id = :c"),
            {"c": str(case.id)},
        )
    ).scalar()
    assert payments == 2


@pytest.mark.asyncio
async def test_skip_flag_allows_identical_payments(
    db, test_tenant, test_user, test_company
):
    """Bron-record-routes (bankimport/BaseNet) mogen identiek boeken: twee
    échte overboekingen van €25 op dezelfde dag zijn daar legitiem — de
    ontdubbeling gebeurt daar op het bron-record zelf (S195-les)."""
    case = await _seed_case_with_claim(
        db, test_tenant, test_company, test_user, case_number="2026-09825"
    )
    for _ in range(2):
        await create_payment(
            db, test_tenant.id, case.id, _payment(), test_user.id,
            _skip_duplicate_guard=True,
        )

    payments = (
        await db.execute(
            text("SELECT count(*) FROM payments WHERE case_id = :c"),
            {"c": str(case.id)},
        )
    ).scalar()
    assert payments == 2
