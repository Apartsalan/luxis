"""Invoice (factuur) tool handlers."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.invoices import service as invoices_service
from app.invoices.schemas import InvoiceCreate


async def handle_invoice_create(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    contact_id: str,
    invoice_date: str,
    due_date: str,
    case_id: str | None = None,
    reference: str | None = None,
    notes: str | None = None,
    btw_percentage: str = "21.00",
) -> dict:
    """Create a new invoice."""
    data = InvoiceCreate(
        contact_id=uuid.UUID(contact_id),
        case_id=uuid.UUID(case_id) if case_id else None,
        invoice_date=date.fromisoformat(invoice_date),
        due_date=date.fromisoformat(due_date),
        btw_percentage=Decimal(btw_percentage),
        reference=reference,
        notes=notes,
    )
    invoice = await invoices_service.create_invoice(db, tenant_id, data)
    return {
        "id": serialize(invoice.id),
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "total": serialize(invoice.total),
        "created": True,
    }


async def handle_invoice_add_line(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    invoice_id: str,
    description: str,
    unit_price: str,
    quantity: str = "1",
    time_entry_id: str | None = None,
    expense_id: str | None = None,
) -> dict:
    """Add a line item to an invoice."""
    line = await invoices_service.add_line(
        db,
        tenant_id,
        uuid.UUID(invoice_id),
        description=description,
        quantity=Decimal(quantity),
        unit_price=Decimal(unit_price),
        time_entry_id=uuid.UUID(time_entry_id) if time_entry_id else None,
        expense_id=uuid.UUID(expense_id) if expense_id else None,
    )
    return {
        "id": serialize(line.id),
        "description": line.description,
        "quantity": serialize(line.quantity),
        "unit_price": serialize(line.unit_price),
        "line_total": serialize(line.line_total),
        "created": True,
    }


async def handle_invoice_approve(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    invoice_id: str,
) -> dict:
    """Approve a draft invoice."""
    invoice = await invoices_service.approve_invoice(db, tenant_id, uuid.UUID(invoice_id))
    return {
        "id": serialize(invoice.id),
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "approved": True,
    }


async def handle_invoice_send(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    invoice_id: str,
) -> dict:
    """Mark an invoice as sent."""
    invoice = await invoices_service.send_invoice(db, tenant_id, uuid.UUID(invoice_id))
    return {
        "id": serialize(invoice.id),
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "sent": True,
    }


async def handle_receivables_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Get receivables overview (debiteurenoverzicht)."""
    summary = await invoices_service.get_receivables(db, tenant_id)
    return serialize(summary)
