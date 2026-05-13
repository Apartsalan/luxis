"""Relations module service — Business logic for contacts and links."""

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.relations.models import Contact, ContactLink, ContactTerms
from app.relations.schemas import (
    ContactCreate,
    ContactLinkCreate,
    ContactTermsCreate,
    ContactTermsUpdate,
    ContactUpdate,
)
from app.shared.exceptions import ConflictError, NotFoundError

# ── Contact CRUD ─────────────────────────────────────────────────────────────


_SORTABLE_CONTACT_COLUMNS = {
    "name": Contact.name,
    "contact_type": Contact.contact_type,
    "visit_city": Contact.visit_city,
    "email": Contact.email,
    "created_at": Contact.created_at,
}


async def list_contacts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    contact_type: str | None = None,
    search: str | None = None,
    is_active: bool = True,
    sort_by: str = "name",
    sort_dir: str = "asc",
) -> tuple[list[Contact], int]:
    """List contacts with optional filtering, sorting and pagination.

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

    # Sortering met whitelist — onbekende kolom valt terug op naam.
    sort_col = _SORTABLE_CONTACT_COLUMNS.get(sort_by, Contact.name)
    direction = sort_col.desc() if sort_dir == "desc" else sort_col.asc()
    # Secundaire sortering op naam zodat rijen met gelijke sorteer-waarde
    # (bv. lege plaats, identieke datum) consistent ordenen.
    query = (
        query.order_by(direction.nulls_last(), Contact.name.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

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
    """Soft-delete a contact by setting is_active=False.

    DF138-09: blokkeer delete als de relatie nog gekoppeld is aan actieve
    dossiers. Soft-delete alleen verbergt de relatie uit zoek/lijst, maar
    in een dossier blijft de partij zichtbaar via de FK — dat is verwarrend:
    de gebruiker drukt 'Verwijderen' en denkt 'het werkt niet'. Beter
    duidelijke melding teruggeven zodat eerst de koppeling wordt opgelost.
    """
    from app.cases.models import Case, CaseParty

    # Tel actieve dossiers waar deze relatie cliënt of wederpartij is
    case_link_count = await db.scalar(
        select(func.count())
        .select_from(Case)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            or_(
                Case.client_id == contact_id,
                Case.opposing_party_id == contact_id,
            ),
        )
    )
    # Plus tel actieve dossiers via CaseParty (extra partijen, bv. advocaat)
    party_link_count = await db.scalar(
        select(func.count(func.distinct(CaseParty.case_id)))
        .select_from(CaseParty)
        .join(Case, CaseParty.case_id == Case.id)
        .where(
            CaseParty.tenant_id == tenant_id,
            CaseParty.contact_id == contact_id,
            Case.is_active.is_(True),
        )
    )
    total_links = (case_link_count or 0) + (party_link_count or 0)
    if total_links > 0:
        dossier_woord = "dossier" if total_links == 1 else "dossiers"
        raise ConflictError(
            f"Deze relatie is nog gekoppeld aan {total_links} actief {dossier_woord}. "
            f"Sluit eerst het dossier of vervang de partij voordat je de relatie verwijdert."
        )

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


# ── Contact Terms (AV-versies) ───────────────────────────────────────────────


async def list_contact_terms(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> list[ContactTerms]:
    """Alle AV-versies van een cliënt, gesorteerd op valid_from desc (NULL onderaan)."""
    result = await db.execute(
        select(ContactTerms)
        .where(
            ContactTerms.tenant_id == tenant_id,
            ContactTerms.contact_id == contact_id,
        )
        .order_by(ContactTerms.valid_from.desc().nulls_last(), ContactTerms.created_at.desc())
    )
    return list(result.scalars().all())


async def get_contact_terms(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    terms_id: uuid.UUID,
) -> ContactTerms:
    """Eén AV-versie ophalen. Raises NotFoundError als niet bestaat."""
    result = await db.execute(
        select(ContactTerms).where(
            ContactTerms.id == terms_id,
            ContactTerms.tenant_id == tenant_id,
        )
    )
    terms = result.scalar_one_or_none()
    if terms is None:
        raise NotFoundError("AV-versie niet gevonden")
    return terms


async def create_contact_terms(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    file_path: str,
    file_name: str,
    metadata: ContactTermsCreate,
    uploaded_by_id: uuid.UUID | None = None,
) -> ContactTerms:
    """Maak nieuwe AV-versie. Caller is verantwoordelijk voor file-upload op disk."""
    # Verifieer dat contact bestaat (raises NotFoundError indien niet)
    await get_contact(db, tenant_id, contact_id)

    terms = ContactTerms(
        tenant_id=tenant_id,
        contact_id=contact_id,
        file_path=file_path,
        file_name=file_name,
        label=metadata.label,
        valid_from=metadata.valid_from,
        valid_to=metadata.valid_to,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(terms)
    await db.flush()
    await db.refresh(terms)
    return terms


async def update_contact_terms(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    terms_id: uuid.UUID,
    data: ContactTermsUpdate,
) -> ContactTerms:
    """Update metadata (label, geldigheid) — file zelf wijzigt niet."""
    terms = await get_contact_terms(db, tenant_id, terms_id)
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(terms, field, value)
    await db.flush()
    await db.refresh(terms)
    return terms


async def delete_contact_terms(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    terms_id: uuid.UUID,
) -> str:
    """Verwijder AV-versie + retourneert file_path zodat caller bestand kan opruimen.

    Cases die naar deze versie verwezen krijgen `contact_terms_id = NULL`
    via ON DELETE SET NULL is niet ingesteld; we doen handmatige cleanup
    door eerst alle cases bij te werken.
    """
    from app.cases.models import Case

    terms = await get_contact_terms(db, tenant_id, terms_id)
    file_path = terms.file_path

    # Cases die hiernaar wijzen → contact_terms_id leegmaken
    await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.contact_terms_id == terms_id,
        )
    )
    from sqlalchemy import update as sa_update

    await db.execute(
        sa_update(Case)
        .where(Case.tenant_id == tenant_id, Case.contact_terms_id == terms_id)
        .values(contact_terms_id=None)
    )

    await db.delete(terms)
    await db.flush()
    return file_path


def select_terms_for_date(
    versions: list[ContactTerms],
    target_date: "date | None",
) -> ContactTerms | None:
    """Kies de AV-versie die geldig is op `target_date`.

    Match-logica:
    1. valid_from <= target_date AND (valid_to IS NULL OR valid_to >= target_date)
    2. Geen match: pak versie met valid_from NULL (= "altijd geldig" / migratie)
    3. Geen match: pak meest recente versie (op valid_from desc, dan created_at desc)
    4. Geen versies: None

    `target_date` NULL → ook fallback naar "altijd geldig" of meest recente.
    """
    if not versions:
        return None

    if target_date is not None:
        for v in versions:
            if v.valid_from is None:
                continue
            if v.valid_from <= target_date and (
                v.valid_to is None or v.valid_to >= target_date
            ):
                return v

    # Fallback 1: versie met valid_from NULL (= "altijd geldig")
    null_from = next((v for v in versions if v.valid_from is None), None)
    if null_from is not None:
        return null_from

    # Fallback 2: meest recente (versions is al gesorteerd valid_from desc)
    return versions[0]


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
