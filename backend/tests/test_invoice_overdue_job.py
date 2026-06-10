"""CONN-1: tests for the daily invoice-overdue job (process_overdue_invoices).

A sent invoice past its due date must flip to 'overdue' and notify the firm.
The job is idempotent and ignores not-yet-due, already-paid, and credit-note
invoices.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.invoices.models import Invoice
from app.invoices.service import process_overdue_invoices
from app.notifications.models import Notification
from app.notifications.service import NOTIF_INVOICE_OVERDUE
from app.relations.models import Contact


async def _contact(db: AsyncSession, tenant_id: uuid.UUID) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Klant B.V.",
        email=f"klant-{uuid.uuid4().hex[:6]}@test.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    *,
    status: str = "sent",
    due_offset_days: int = -1,
    invoice_type: str = "invoice",
) -> Invoice:
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_number=f"F2026-{uuid.uuid4().hex[:6]}",
        invoice_type=invoice_type,
        status=status,
        contact_id=contact_id,
        invoice_date=date.today() - timedelta(days=40),
        due_date=date.today() + timedelta(days=due_offset_days),
        subtotal=Decimal("500.00"),
        btw_percentage=Decimal("21.00"),
        btw_amount=Decimal("105.00"),
        total=Decimal("605.00"),
        is_active=True,
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def test_sent_invoice_past_due_becomes_overdue_and_notifies(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    contact = await _contact(db, test_tenant.id)
    invoice = await _invoice(db, test_tenant.id, contact.id, status="sent", due_offset_days=-1)

    count = await process_overdue_invoices(db, test_tenant.id)

    assert count == 1
    await db.refresh(invoice)
    assert invoice.status == "overdue"

    notifs = (
        await db.execute(
            select(Notification).where(
                Notification.tenant_id == test_tenant.id,
                Notification.type == NOTIF_INVOICE_OVERDUE,
            )
        )
    ).scalars().all()
    assert len(notifs) >= 1
    assert any(invoice.invoice_number in (n.title or "") for n in notifs)


async def test_job_is_idempotent_and_skips_non_eligible(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    contact = await _contact(db, test_tenant.id)
    overdue = await _invoice(db, test_tenant.id, contact.id, status="sent", due_offset_days=-2)
    future = await _invoice(db, test_tenant.id, contact.id, status="sent", due_offset_days=5)
    paid = await _invoice(db, test_tenant.id, contact.id, status="paid", due_offset_days=-5)
    credit_note = await _invoice(
        db, test_tenant.id, contact.id, status="sent",
        due_offset_days=-5, invoice_type="credit_note",
    )

    first = await process_overdue_invoices(db, test_tenant.id)
    assert first == 1  # only the eligible 'sent' invoice flips

    second = await process_overdue_invoices(db, test_tenant.id)
    assert second == 0  # idempotent — nothing left in 'sent' + past due

    await db.refresh(overdue)
    await db.refresh(future)
    await db.refresh(paid)
    await db.refresh(credit_note)
    assert overdue.status == "overdue"
    assert future.status == "sent"
    assert paid.status == "paid"
    assert credit_note.status == "sent"  # money the other way is never "te laat"
