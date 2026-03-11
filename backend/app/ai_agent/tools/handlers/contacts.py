"""Contact (relatie) tool handlers."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.relations import service as relations_service
from app.relations.schemas import ContactCreate


async def handle_contact_lookup(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    search: str,
    contact_type: str | None = None,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    """Search for existing contacts by name, email, or KvK number."""
    contacts, total = await relations_service.list_contacts(
        db,
        tenant_id,
        page=page,
        per_page=per_page,
        contact_type=contact_type,
        search=search,
    )
    return {
        "items": [
            {
                "id": serialize(c.id),
                "contact_type": c.contact_type,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "kvk_number": c.kvk_number,
                "visit_city": c.visit_city,
                "is_active": c.is_active,
            }
            for c in contacts
        ],
        "total": total,
    }


async def handle_contact_get(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    contact_id: str,
) -> dict:
    """Get full contact details by ID."""
    contact = await relations_service.get_contact(db, tenant_id, uuid.UUID(contact_id))
    if not contact:
        return {"error": "Relatie niet gevonden"}
    return {
        "id": serialize(contact.id),
        "contact_type": contact.contact_type,
        "name": contact.name,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "kvk_number": contact.kvk_number,
        "btw_number": contact.btw_number,
        "visit_address": contact.visit_address,
        "visit_postcode": contact.visit_postcode,
        "visit_city": contact.visit_city,
        "postal_address": contact.postal_address,
        "postal_postcode": contact.postal_postcode,
        "postal_city": contact.postal_city,
        "iban": contact.iban,
        "billing_email": contact.billing_email,
        "notes": contact.notes,
        "is_active": contact.is_active,
    }


async def handle_contact_create(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    contact_type: str,
    name: str,
    email: str | None = None,
    phone: str | None = None,
    kvk_number: str | None = None,
    btw_number: str | None = None,
    visit_address: str | None = None,
    visit_postcode: str | None = None,
    visit_city: str | None = None,
) -> dict:
    """Create a new contact (person or company)."""
    data = ContactCreate(
        contact_type=contact_type,
        name=name,
        email=email,
        phone=phone,
        kvk_number=kvk_number,
        btw_number=btw_number,
        visit_address=visit_address,
        visit_postcode=visit_postcode,
        visit_city=visit_city,
    )
    contact = await relations_service.create_contact(db, tenant_id, data)
    return {
        "id": serialize(contact.id),
        "contact_type": contact.contact_type,
        "name": contact.name,
        "created": True,
    }
