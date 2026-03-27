"""Invoice number generation helpers.

Uses SELECT ... FOR UPDATE to prevent race conditions when two concurrent
requests generate invoice numbers simultaneously.
"""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.invoices.models import Invoice


async def _next_number(db: AsyncSession, tenant_id: uuid.UUID, prefix: str) -> str:
    """Generate the next sequential number for a given prefix.

    Uses FOR UPDATE to lock the row with the highest number, preventing
    two concurrent transactions from reading the same MAX value.
    """
    result = await db.execute(
        select(Invoice.invoice_number)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_number.like(f"{prefix}%"),
        )
        .order_by(Invoice.invoice_number.desc())
        .limit(1)
        .with_for_update()
    )
    max_number = result.scalar_one_or_none()
    if max_number:
        seq = int(max_number.replace(prefix, "")) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"


async def next_invoice_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next invoice number: F{year}-{seq:05d}."""
    prefix = f"F{date.today().year}-"
    return await _next_number(db, tenant_id, prefix)


async def next_credit_note_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next credit note number: CN{year}-{seq:05d}."""
    prefix = f"CN{date.today().year}-"
    return await _next_number(db, tenant_id, prefix)


async def next_voorschotnota_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next voorschotnota number: VN{year}-{seq:05d}."""
    prefix = f"VN{date.today().year}-"
    return await _next_number(db, tenant_id, prefix)
