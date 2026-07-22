"""Search module service — Global search across cases, contacts, and documents."""

import uuid

from sqlalchemy import Text, and_, bindparam, cast, func, literal, or_, select
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseFile
from app.collections.models import Claim
from app.email.synced_email_models import SyncedEmail
from app.invoices.models import Invoice
from app.relations.models import Contact
from app.search.schemas import SearchResultItem


async def global_search(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    limit: int = 10,
) -> list[SearchResultItem]:
    """Search across cases, contacts, documents, invoices, and emails.

    Returns up to `limit` results total, balanced across types
    (a few per type to ensure variety).
    """
    query = query.strip()
    if not query:
        return []

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
                # S239: vindbaar op het factuurnummer van een vordering — dat
                # is wat de debiteur aan de telefoon noemt.
                Case.id.in_(
                    select(Claim.case_id).where(
                        Claim.tenant_id == tenant_id,
                        Claim.is_active == True,  # noqa: E712
                        Claim.invoice_number.ilike(search_term),
                    )
                ),
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
    doc_fts_param = bindparam("doc_fts_query", type_=Text)
    doc_ts_query = func.websearch_to_tsquery(
        cast(literal("dutch"), REGCONFIG), doc_fts_param
    )
    doc_fts_match = CaseFile.search_vector.op("@@")(doc_ts_query)
    doc_rank = func.ts_rank(CaseFile.search_vector, doc_ts_query)
    doc_query = (
        select(
            CaseFile.id,
            CaseFile.case_id,
            CaseFile.original_filename,
            CaseFile.content_type,
            CaseFile.description,
            doc_fts_match.label("fts_match"),
        )
        .where(
            CaseFile.tenant_id == tenant_id,
            CaseFile.is_active == True,  # noqa: E712
            or_(
                CaseFile.original_filename.ilike(search_term),
                CaseFile.description.ilike(search_term),
                doc_fts_match,
            ),
        )
        .order_by(doc_rank.desc(), CaseFile.created_at.desc())
        .limit(per_type_limit)
    )
    documents = list((await db.execute(doc_query, {"doc_fts_query": query})).all())

    doc_fts_ids = [doc.id for doc in documents if doc.fts_match]
    document_headlines: dict[uuid.UUID, str] = {}
    if doc_fts_ids:
        headline_query = select(
            CaseFile.id,
            func.ts_headline(
                cast(literal("dutch"), REGCONFIG),
                func.left(CaseFile.extracted_text, 5000),
                doc_ts_query,
                literal("MaxWords=14, MinWords=6"),
            ).label("headline"),
        ).where(
            CaseFile.tenant_id == tenant_id,
            CaseFile.id.in_(doc_fts_ids),
            doc_fts_match,
        )
        document_headlines = {
            row.id: row.headline or ""
            for row in (
                await db.execute(headline_query, {"doc_fts_query": query})
            ).all()
        }

    for doc in documents:
        if doc.fts_match:
            subtitle = document_headlines.get(doc.id, "")
        else:
            subtitle_parts = [doc.content_type.split("/")[-1].upper()]
            if doc.description:
                subtitle_parts.append(doc.description[:60])
            subtitle = " · ".join(subtitle_parts)
        results.append(
            SearchResultItem(
                id=str(doc.id),
                type="document",
                title=doc.original_filename,
                subtitle=subtitle,
                href=f"/zaken/{doc.case_id}",
            )
        )

    # ── Search Invoices (CONN-11) ──────────────────────────────────────
    invoice_query = (
        select(Invoice)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.is_active == True,  # noqa: E712
            or_(
                Invoice.invoice_number.ilike(search_term),
                Invoice.reference.ilike(search_term),
            ),
        )
        .order_by(Invoice.invoice_date.desc())
        .limit(per_type_limit)
    )
    invoice_result = await db.execute(invoice_query)
    invoices = list(invoice_result.scalars().all())

    for inv in invoices:
        subtitle_parts = []
        if inv.contact:
            subtitle_parts.append(inv.contact.name)
        subtitle_parts.append(inv.status.replace("_", " ").title())
        subtitle_parts.append(f"€ {inv.total}")
        results.append(
            SearchResultItem(
                id=str(inv.id),
                type="invoice",
                title=inv.invoice_number,
                subtitle=" · ".join(filter(None, subtitle_parts)),
                href=f"/facturen/{inv.id}",
            )
        )

    # ── Search Emails (CONN-11) ────────────────────────────────────────
    email_fts_param = bindparam("email_fts_query", type_=Text)
    email_ts_query = func.websearch_to_tsquery(
        cast(literal("dutch"), REGCONFIG), email_fts_param
    )
    email_fts_match = SyncedEmail.search_vector.op("@@")(email_ts_query)
    email_rank = func.ts_rank(SyncedEmail.search_vector, email_ts_query)
    email_query = (
        select(
            SyncedEmail.id,
            SyncedEmail.case_id,
            SyncedEmail.subject,
            SyncedEmail.from_email,
            SyncedEmail.from_name,
            SyncedEmail.email_date,
            Case.case_number,
            email_fts_match.label("fts_match"),
        )
        .outerjoin(
            Case,
            and_(
                Case.id == SyncedEmail.case_id,
                Case.tenant_id == tenant_id,
            ),
        )
        .where(
            SyncedEmail.tenant_id == tenant_id,
            or_(
                SyncedEmail.subject.ilike(search_term),
                SyncedEmail.from_email.ilike(search_term),
                SyncedEmail.from_name.ilike(search_term),
                email_fts_match,
            ),
        )
        .order_by(email_rank.desc(), SyncedEmail.email_date.desc())
        .limit(per_type_limit)
    )
    emails = list((await db.execute(email_query, {"email_fts_query": query})).all())

    email_fts_ids = [email.id for email in emails if email.fts_match]
    email_headlines: dict[uuid.UUID, str] = {}
    if email_fts_ids:
        headline_query = select(
            SyncedEmail.id,
            func.ts_headline(
                cast(literal("dutch"), REGCONFIG),
                func.left(SyncedEmail.body_text, 5000),
                email_ts_query,
                literal("MaxWords=14, MinWords=6"),
            ).label("headline"),
        ).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.id.in_(email_fts_ids),
            email_fts_match,
        )
        email_headlines = {
            row.id: row.headline
            for row in (
                await db.execute(headline_query, {"email_fts_query": query})
            ).all()
        }

    for em in emails:
        if em.fts_match:
            subtitle = email_headlines.get(em.id, "")
        else:
            sender = em.from_name or em.from_email
            subtitle_parts = [sender] if sender else []
            if em.case_number:
                subtitle_parts.append(em.case_number)
            subtitle = " · ".join(filter(None, subtitle_parts))
        href = (
            f"/zaken/{em.case_id}?tab=correspondentie"
            if em.case_id
            else "/correspondentie"
        )
        results.append(
            SearchResultItem(
                id=str(em.id),
                type="email",
                title=(em.subject or "(geen onderwerp)")[:120],
                subtitle=subtitle,
                href=href,
            )
        )

    # Sort by type priority: cases, contacts, invoices, documents, emails
    type_order = {
        "case": 0,
        "contact": 1,
        "invoice": 2,
        "document": 3,
        "email": 4,
    }
    results.sort(key=lambda r: type_order.get(r.type, 5))

    return results[:limit]
