"""Relations module service — Business logic for contacts and links."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.relations.models import Contact, ContactLink
from app.relations.schemas import ContactCreate, ContactLinkCreate, ContactUpdate
from app.shared.exceptions import ConflictError, NotFoundError

# ── Contact CRUD ─────────────────────────────────────────────────────────────


async def list_contacts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    contact_type: str | None = None,
    search: str | None = None,
    is_active: bool = True,
) -> tuple[list[Contact], int]:
    """List contacts with optional filtering and pagination.

    Returns: (contacts, total_count)
    """
    query = select(Contact).where(
        Contact.tenant_id == tenant_id,
        Contact.is_active == is_active,
    )

    if contact_type:
        query = query.where(Contact.contact_type == contact_type)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Contact.name.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.kvk_number.ilike(search_term),
                Contact.phone.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Apply pagination
    query = query.order_by(Contact.name).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    contacts = list(result.scalars().all())

    return contacts, total


async def get_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> Contact:
    """Get a single contact by ID. Raises NotFoundError if not found."""
    result = await db.execute(
        select(Contact)
        .where(
            Contact.id == contact_id,
            Contact.tenant_id == tenant_id,
        )
        .options(
            selectinload(Contact.company_links).selectinload(ContactLink.company),
            selectinload(Contact.person_links).selectinload(ContactLink.person),
        )
        .execution_options(populate_existing=True)
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise NotFoundError("Contact niet gevonden")
    return contact


async def create_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: ContactCreate,
) -> Contact:
    """Create a new contact."""
    contact = Contact(
        tenant_id=tenant_id,
        **data.model_dump(),
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return contact


async def update_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    data: ContactUpdate,
) -> Contact:
    """Update an existing contact. Only updates fields that are provided."""
    contact = await get_contact(db, tenant_id, contact_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    await db.flush()
    await db.refresh(contact)
    return contact


async def delete_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> None:
    """Soft-delete a contact by setting is_active=False."""
    contact = await get_contact(db, tenant_id, contact_id)
    contact.is_active = False
    await db.flush()


# ── Contact Links ────────────────────────────────────────────────────────────


async def create_contact_link(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: ContactLinkCreate,
) -> ContactLink:
    """Link a person to a company."""
    # Verify both contacts exist and belong to the tenant
    person = await get_contact(db, tenant_id, data.person_id)
    company = await get_contact(db, tenant_id, data.company_id)

    if person.contact_type != "person":
        raise ConflictError("person_id moet verwijzen naar een persoon")
    if company.contact_type != "company":
        raise ConflictError("company_id moet verwijzen naar een bedrijf")

    # Check if link already exists
    existing = await db.execute(
        select(ContactLink).where(
            ContactLink.tenant_id == tenant_id,
            ContactLink.person_id == data.person_id,
            ContactLink.company_id == data.company_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Deze koppeling bestaat al")

    link = ContactLink(
        tenant_id=tenant_id,
        person_id=data.person_id,
        company_id=data.company_id,
        role_at_company=data.role_at_company,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def delete_contact_link(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    link_id: uuid.UUID,
) -> None:
    """Remove a person-company link."""
    result = await db.execute(
        select(ContactLink).where(
            ContactLink.id == link_id,
            ContactLink.tenant_id == tenant_id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError("Koppeling niet gevonden")

    await db.delete(link)
    await db.flush()


# ── Conflict Check ───────────────────────────────────────────────────────────


async def conflict_check(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    search_query: str,
) -> list[Contact]:
    """Search for potential conflicts by name, KvK number, or email.

    Used before creating a new case to check if the opposing party
    is already a client (or vice versa).
    """
    search_term = f"%{search_query}%"
    result = await db.execute(
        select(Contact)
        .where(
            Contact.tenant_id == tenant_id,
            Contact.is_active.is_(True),
            or_(
                Contact.name.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.kvk_number.ilike(search_term),
                Contact.first_name.ilike(search_term),
                Contact.last_name.ilike(search_term),
            ),
        )
        .order_by(Contact.name)
    )
    return list(result.scalars().all())
