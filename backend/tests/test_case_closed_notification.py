"""Wachter (S235): automatisch afsluiten na volledige betaling laat een melding achter.

Keuze Arsalan (22-7): het afsluiten zelf blijft automatisch, maar er komt een
zichtbare melding "Dossier volledig betaald en afgesloten — wil je de cliënt
factureren?". Deze wachter eist:
- ná auto-afsluiten bestaat precies één case_closed_invoice-melding (per gebruiker);
- géén melding als de zaak niet volledig betaald is (hook sluit dan ook niet).
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.collections.models import Claim
from app.notifications.models import Notification
from app.notifications.service import NOTIF_CASE_CLOSED_INVOICE
from app.workflow.hooks import on_payment_received
from tests.helpers.incasso_fixtures import create_incasso_case


async def _count_notifications(db, tenant_id, case_id) -> int:
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.case_id == case_id,
            Notification.type == NOTIF_CASE_CLOSED_INVOICE,
        )
    )
    return len(list(result.scalars().all()))


@pytest.mark.asyncio
async def test_autoclose_creates_exactly_one_notification(
    db, test_tenant, test_user, test_company
):
    """€0 openstaand → hook sluit de zaak én laat precies één melding achter."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09501"
    )

    result = await on_payment_received(db, test_tenant.id, case.id, Decimal("100.00"))
    assert result is not None  # hook sloot de zaak
    assert case.status == "betaald"

    assert await _count_notifications(db, test_tenant.id, case.id) == 1

    # Dubbele hook-run (bv. dubbele betaling-boeking) → dedup, geen tweede melding.
    # De zaak is nu terminaal dus de hook doet niets meer; de melding blijft één.
    await on_payment_received(db, test_tenant.id, case.id, Decimal("0.01"))
    assert await _count_notifications(db, test_tenant.id, case.id) == 1


@pytest.mark.asyncio
async def test_no_notification_when_not_fully_paid(
    db, test_tenant, test_user, test_company
):
    """Openstaand saldo → hook sluit niet en er komt géén melding."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09502"
    )
    db.add(
        Claim(
            id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
            description="Factuur", principal_amount=Decimal("1000.00"),
            invoice_date=date.today(), default_date=date.today(),
        )
    )
    await db.flush()

    result = await on_payment_received(db, test_tenant.id, case.id, Decimal("100.00"))
    assert result is None  # niet volledig betaald → geen afsluiting

    assert await _count_notifications(db, test_tenant.id, case.id) == 0
