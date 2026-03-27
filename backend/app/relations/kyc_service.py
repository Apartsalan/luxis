"""WWFT/KYC service — Business logic for client verification and compliance."""

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.relations.kyc_models import KycVerification
from app.relations.kyc_schemas import KycComplete, KycCreate, KycUpdate
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError, NotFoundError


async def get_kyc_for_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> KycVerification | None:
    """Get the KYC verification for a contact, or None if not started."""
    result = await db.execute(
        select(KycVerification).where(
            KycVerification.tenant_id == tenant_id,
            KycVerification.contact_id == contact_id,
        )
    )
    return result.scalar_one_or_none()


async def create_or_update_kyc(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: KycCreate,
) -> KycVerification:
    """Create a new KYC verification or update existing one for a contact.

    There is only one KYC record per contact — this upserts.
    """
    # Verify the contact exists and belongs to the tenant
    contact_result = await db.execute(
        select(Contact).where(
            Contact.id == data.contact_id,
            Contact.tenant_id == tenant_id,
        )
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise NotFoundError("Relatie niet gevonden")

    # Check if KYC already exists
    existing = await get_kyc_for_contact(db, tenant_id, data.contact_id)

    if existing:
        # Update existing record
        update_data = data.model_dump(exclude={"contact_id"}, exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing, field, value)
        existing.status = "in_behandeling"
        await db.flush()
        await db.refresh(existing)
        return existing
    else:
        # Create new record
        kyc = KycVerification(
            tenant_id=tenant_id,
            contact_id=data.contact_id,
            status="in_behandeling",
            risk_level=data.risk_level,
            risk_notes=data.risk_notes,
            id_type=data.id_type,
            id_number=data.id_number,
            id_expiry_date=data.id_expiry_date,
            id_verified_at=data.id_verified_at,
            ubo_name=data.ubo_name,
            ubo_dob=data.ubo_dob,
            ubo_nationality=data.ubo_nationality,
            ubo_percentage=data.ubo_percentage,
            ubo_verified_at=data.ubo_verified_at,
            pep_checked=data.pep_checked,
            pep_is_pep=data.pep_is_pep,
            pep_notes=data.pep_notes,
            sanctions_checked=data.sanctions_checked,
            sanctions_hit=data.sanctions_hit,
            sanctions_notes=data.sanctions_notes,
            source_of_funds=data.source_of_funds,
            source_of_funds_verified=data.source_of_funds_verified,
            next_review_date=data.next_review_date,
            notes=data.notes,
        )
        db.add(kyc)
        await db.flush()
        await db.refresh(kyc)
        return kyc


async def update_kyc(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    kyc_id: uuid.UUID,
    data: KycUpdate,
) -> KycVerification:
    """Update specific fields of a KYC verification."""
    result = await db.execute(
        select(KycVerification).where(
            KycVerification.id == kyc_id,
            KycVerification.tenant_id == tenant_id,
        )
    )
    kyc = result.scalar_one_or_none()
    if not kyc:
        raise NotFoundError("KYC verificatie niet gevonden")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kyc, field, value)

    # If fields are being filled in, move to in_behandeling
    if kyc.status == "niet_gestart" and update_data:
        kyc.status = "in_behandeling"

    await db.flush()
    await db.refresh(kyc)
    return kyc


async def complete_kyc(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    kyc_id: uuid.UUID,
    user_id: uuid.UUID,
    data: KycComplete | None = None,
) -> KycVerification:
    """Mark a KYC verification as complete.

    Validates that all required checks have been performed:
    - ID verified
    - PEP checked
    - Sanctions checked
    - Risk level assigned
    """
    result = await db.execute(
        select(KycVerification).where(
            KycVerification.id == kyc_id,
            KycVerification.tenant_id == tenant_id,
        )
    )
    kyc = result.scalar_one_or_none()
    if not kyc:
        raise NotFoundError("KYC verificatie niet gevonden")

    # Validate completeness
    errors = []
    if not kyc.id_type or not kyc.id_number:
        errors.append("Identiteitsdocument is verplicht")
    if not kyc.id_verified_at:
        errors.append("Verificatiedatum ID is verplicht")
    if not kyc.risk_level:
        errors.append("Risicoclassificatie is verplicht")
    if not kyc.pep_checked:
        errors.append("PEP-controle is verplicht")
    if not kyc.sanctions_checked:
        errors.append("Sanctielijstcontrole is verplicht")

    # For companies, UBO is required
    contact = kyc.contact
    if contact and contact.contact_type == "company":
        if not kyc.ubo_name:
            errors.append("UBO-registratie is verplicht voor bedrijven")

    if errors:
        raise BadRequestError("KYC verificatie is niet volledig: " + "; ".join(errors))

    kyc.status = "voltooid"
    kyc.verified_by_id = user_id
    kyc.verification_date = date.today()

    # Set next review in 1 year (standard) or 6 months for high risk
    if kyc.risk_level == "hoog":
        kyc.next_review_date = date.today() + timedelta(days=182)
    else:
        kyc.next_review_date = date.today() + timedelta(days=365)

    if data and data.notes:
        kyc.notes = (kyc.notes or "") + f"\n\nAfgerond: {data.notes}"

    await db.flush()
    await db.refresh(kyc)
    return kyc


async def get_kyc_status_for_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> dict:
    """Get a lightweight KYC status summary for a contact.

    Returns dict with: has_kyc, status, is_compliant, risk_level
    """
    kyc = await get_kyc_for_contact(db, tenant_id, contact_id)

    if not kyc:
        return {
            "has_kyc": False,
            "status": "niet_gestart",
            "is_compliant": False,
            "risk_level": None,
            "next_review_date": None,
            "is_overdue": False,
        }

    is_overdue = kyc.next_review_date is not None and kyc.next_review_date < date.today()

    return {
        "has_kyc": True,
        "status": kyc.status,
        "is_compliant": kyc.status == "voltooid" and not is_overdue,
        "risk_level": kyc.risk_level,
        "next_review_date": str(kyc.next_review_date) if kyc.next_review_date else None,
        "is_overdue": is_overdue,
    }


async def get_kyc_dashboard(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict:
    """Get KYC dashboard data: overdue reviews, incomplete verifications, etc."""
    today = date.today()

    # Count contacts without KYC (only active contacts that are clients in active cases)
    from app.cases.models import Case

    # Get unique client IDs from active cases
    client_ids_query = (
        select(Case.client_id)
        .where(Case.tenant_id == tenant_id, Case.is_active == True)  # noqa: E712
        .distinct()
    )
    client_ids_result = await db.execute(client_ids_query)
    active_client_ids = {row[0] for row in client_ids_result.all()}

    # Get KYC status for these clients
    kyc_query = select(KycVerification).where(
        KycVerification.tenant_id == tenant_id,
        (
            KycVerification.contact_id.in_(active_client_ids)
            if active_client_ids
            else KycVerification.contact_id == None  # noqa: E711
        ),
    )
    kyc_result = await db.execute(kyc_query)
    kyc_records = {kyc.contact_id: kyc for kyc in kyc_result.scalars().all()}

    # Build dashboard items
    without_kyc = []
    incomplete = []
    overdue = []
    upcoming_reviews = []

    for client_id in active_client_ids:
        # Get contact name
        contact_result = await db.execute(select(Contact).where(Contact.id == client_id))
        contact = contact_result.scalar_one_or_none()
        if not contact:
            continue

        kyc = kyc_records.get(client_id)

        if not kyc:
            without_kyc.append(
                {
                    "contact_id": str(client_id),
                    "contact_name": contact.name,
                    "contact_type": contact.contact_type,
                    "kyc_status": "niet_gestart",
                }
            )
        elif kyc.status == "in_behandeling":
            incomplete.append(
                {
                    "contact_id": str(client_id),
                    "contact_name": contact.name,
                    "contact_type": contact.contact_type,
                    "kyc_status": "in_behandeling",
                }
            )
        elif kyc.status == "voltooid" and kyc.next_review_date:
            if kyc.next_review_date < today:
                overdue.append(
                    {
                        "contact_id": str(client_id),
                        "contact_name": contact.name,
                        "contact_type": contact.contact_type,
                        "kyc_status": "verlopen",
                        "next_review_date": str(kyc.next_review_date),
                        "days_overdue": (today - kyc.next_review_date).days,
                    }
                )
            elif kyc.next_review_date <= today + timedelta(days=30):
                upcoming_reviews.append(
                    {
                        "contact_id": str(client_id),
                        "contact_name": contact.name,
                        "contact_type": contact.contact_type,
                        "kyc_status": "voltooid",
                        "next_review_date": str(kyc.next_review_date),
                        "days_until_review": (kyc.next_review_date - today).days,
                    }
                )

    return {
        "without_kyc": without_kyc,
        "without_kyc_count": len(without_kyc),
        "incomplete": incomplete,
        "incomplete_count": len(incomplete),
        "overdue": overdue,
        "overdue_count": len(overdue),
        "upcoming_reviews": upcoming_reviews,
        "upcoming_reviews_count": len(upcoming_reviews),
        "total_issues": len(without_kyc) + len(incomplete) + len(overdue),
    }
