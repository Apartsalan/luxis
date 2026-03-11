"""Collections (incasso) tool handlers — claims, payments, financial summary."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.collections import service as collections_service
from app.collections.schemas import ClaimCreate, PaymentCreate


async def handle_claim_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
) -> dict:
    """List all claims (vorderingen) on a case."""
    claims = await collections_service.list_claims(db, tenant_id, uuid.UUID(case_id))
    return {
        "items": [
            {
                "id": serialize(c.id),
                "description": c.description,
                "principal_amount": serialize(c.principal_amount),
                "default_date": serialize(c.default_date),
                "invoice_number": c.invoice_number,
                "invoice_date": serialize(c.invoice_date),
                "is_active": c.is_active,
            }
            for c in claims
        ],
        "count": len(claims),
    }


async def handle_claim_create(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    description: str,
    principal_amount: str,
    default_date: str,
    invoice_number: str | None = None,
    invoice_date: str | None = None,
) -> dict:
    """Create a new claim on a case."""
    data = ClaimCreate(
        description=description,
        principal_amount=Decimal(principal_amount),
        default_date=date.fromisoformat(default_date),
        invoice_number=invoice_number,
        invoice_date=date.fromisoformat(invoice_date) if invoice_date else None,
    )
    claim = await collections_service.create_claim(db, tenant_id, uuid.UUID(case_id), data)
    return {
        "id": serialize(claim.id),
        "description": claim.description,
        "principal_amount": serialize(claim.principal_amount),
        "default_date": serialize(claim.default_date),
        "created": True,
    }


async def handle_payment_register(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    amount: str,
    payment_date: str,
    description: str | None = None,
    payment_method: str | None = None,
) -> dict:
    """Register a payment on a case (applies art. 6:44 BW distribution)."""
    data = PaymentCreate(
        amount=Decimal(amount),
        payment_date=date.fromisoformat(payment_date),
        description=description,
        payment_method=payment_method,
    )
    payment = await collections_service.create_payment(
        db, tenant_id, uuid.UUID(case_id), data, user_id,
    )
    return {
        "id": serialize(payment.id),
        "amount": serialize(payment.amount),
        "payment_date": serialize(payment.payment_date),
        "allocated_to_costs": serialize(payment.allocated_to_costs),
        "allocated_to_interest": serialize(payment.allocated_to_interest),
        "allocated_to_principal": serialize(payment.allocated_to_principal),
        "created": True,
    }


async def handle_payment_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
) -> dict:
    """List all payments on a case."""
    payments = await collections_service.list_payments(db, tenant_id, uuid.UUID(case_id))
    return {
        "items": [
            {
                "id": serialize(p.id),
                "amount": serialize(p.amount),
                "payment_date": serialize(p.payment_date),
                "description": p.description,
                "payment_method": p.payment_method,
                "allocated_to_costs": serialize(p.allocated_to_costs),
                "allocated_to_interest": serialize(p.allocated_to_interest),
                "allocated_to_principal": serialize(p.allocated_to_principal),
            }
            for p in payments
        ],
        "count": len(payments),
    }


async def handle_financial_summary(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    calc_date: str | None = None,
) -> dict:
    """Get complete financial summary for a case (principal, interest, BIK, payments)."""
    summary = await collections_service.get_financial_summary(
        db,
        tenant_id,
        uuid.UUID(case_id),
        calc_date=date.fromisoformat(calc_date) if calc_date else None,
    )
    return serialize(summary)
