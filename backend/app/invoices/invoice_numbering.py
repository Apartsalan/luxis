"""Invoice number generation helpers."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.invoices.models import Invoice


async def next_invoice_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next invoice number: F{year}-{seq:05d}."""
    year = date.today().year
    prefix = f"F{year}-"

    result = await db.execute(
        select(func.max(Invoice.invoice_number))
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_number.like(f"{prefix}%"),
        )
    )
    max_number = result.scalar_one()
    if max_number:
        seq = int(max_number.replace(prefix, "")) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"


async def next_credit_note_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next credit note number: CN{year}-{seq:05d}."""
    year = date.today().year
    prefix = f"CN{year}-"

    result = await db.execute(
        select(func.max(Invoice.invoice_number))
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_number.like(f"{prefix}%"),
        )
    )
    max_number = result.scalar_one()
    if max_number:
        seq = int(max_number.replace(prefix, "")) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"


async def next_voorschotnota_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next voorschotnota number: VN{year}-{seq:05d}."""
    year = date.today().year
    prefix = f"VN{year}-"

    result = await db.execute(
        select(func.max(Invoice.invoice_number))
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_number.like(f"{prefix}%"),
        )
    )
    max_number = result.scalar_one()
    if max_number:
        seq = int(max_number.replace(prefix, "")) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"
