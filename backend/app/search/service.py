"""Search module service — Global search across cases, contacts, and documents."""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseFile
from app.relations.models import Contact
from app.search.schemas import SearchResultItem


async def global_search(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    limit: int = 10,
) -> list[SearchResultItem]:
    """Search across cases, contacts, and documents.

    Returns up to `limit` results total, balanced across types
    (max ~5 per type to ensure variety).
    """
    search_term = f"%{query}%"
    per_type_limit = max(limit // 3, 3)  # At least 3 per type
    results: list[SearchResultItem] = []

    # ── Search Cases ────────────────────────────────────────────────────
    case_query = (
        select(Case)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            or_(
                Case.case_number.ilike(search_term),
                Case.description.ilike(search_term),
                Case.reference.ilike(search_term),
                Case.client.has(Contact.name.ilike(search_term)),
                Case.opposing_party.has(Contact.name.ilike(search_term)),
            ),
        )
        .order_by(Case.updated_at.desc())
        .limit(per_type_limit)
    )
    case_result = await db.execute(case_query)
    cases = list(case_result.scalars().all())

    for c in cases:
        client_name = c.client.name if c.client else ""
        subtitle_parts = [client_name]
        if c.status:
            subtitle_parts.append(c.status.replace("_", " ").title())
        results.append(
            SearchResultItem(
                id=str(c.id),
                type="case",
                title=f"{c.case_number} — {client_name}",
                subtitle=" · ".join(filter(None, subtitle_parts)),
                href=f"/zaken/{c.id}",
            )
        )

    # ── Search Contacts ─────────────────────────────────────────────────
    contact_query = (
        select(Contact)
        .where(
            Contact.tenant_id == tenant_id,
            Contact.is_active == True,  # noqa: E712
            or_(
                Contact.name.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.kvk_number.ilike(search_term),
                Contact.phone.ilike(search_term),
                Contact.first_name.ilike(search_term),
                Contact.last_name.ilike(search_term),
            ),
        )
        .order_by(Contact.updated_at.desc())
        .limit(per_type_limit)
    )
    contact_result = await db.execute(contact_query)
    contacts = list(contact_result.scalars().all())

    for ct in contacts:
        type_label = "Bedrijf" if ct.contact_type == "company" else "Persoon"
        subtitle_parts = [type_label]
        if ct.email:
            subtitle_parts.append(ct.email)
        if ct.kvk_number:
            subtitle_parts.append(f"KvK {ct.kvk_number}")
        results.append(
            SearchResultItem(
                id=str(ct.id),
                type="contact",
                title=ct.name,
                subtitle=" · ".join(subtitle_parts),
                href=f"/relaties/{ct.id}",
            )
        )

    # ── Search Documents (uploaded files) ───────────────────────────────
    doc_query = (
        select(CaseFile)
        .where(
            CaseFile.tenant_id == tenant_id,
            CaseFile.is_active == True,  # noqa: E712
            or_(
                CaseFile.original_filename.ilike(search_term),
                CaseFile.description.ilike(search_term),
            ),
        )
        .order_by(CaseFile.created_at.desc())
        .limit(per_type_limit)
    )
    doc_result = await db.execute(doc_query)
    documents = list(doc_result.scalars().all())

    for doc in documents:
        subtitle_parts = [doc.content_type.split("/")[-1].upper()]
        if doc.description:
            subtitle_parts.append(doc.description[:60])
        results.append(
            SearchResultItem(
                id=str(doc.id),
                type="document",
                title=doc.original_filename,
                subtitle=" · ".join(subtitle_parts),
                href=f"/zaken/{doc.case_id}",
            )
        )

    # Sort: cases first, then contacts, then documents
    type_order = {"case": 0, "contact": 1, "document": 2}
    results.sort(key=lambda r: type_order.get(r.type, 3))

    return results[:limit]
