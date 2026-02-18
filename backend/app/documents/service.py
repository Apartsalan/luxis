"""Documents module service — HTML template management and document generation.

DEPRECATED: This module uses the legacy HTML/Jinja2 template system.
New document generation should use docx_service.py (DOCX templates) instead.

The HTML template CRUD functions (list/get/create/update/delete) and the
generate_document function are retained for backwards compatibility but
should not be used for new features.
"""

import uuid
from datetime import date
from decimal import Decimal

from jinja2 import BaseLoader, Environment, StrictUndefined
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.collections.service import (
    get_financial_summary,
    list_claims,
    list_payments,
)
from app.collections.wik import calculate_bik
from app.documents.models import DocumentTemplate, GeneratedDocument
from app.documents.schemas import (
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    GenerateDocumentRequest,
)
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError, NotFoundError

# Jinja2 environment for template rendering
jinja_env = Environment(
    loader=BaseLoader(),
    undefined=StrictUndefined,
    autoescape=True,
)


# ── Custom Jinja2 Filters ───────────────────────────────────────────────────

def _format_currency(value) -> str:
    """Format a Decimal/float as Dutch currency: EUR 1.234,56."""
    if value is None:
        return "EUR 0,00"
    d = Decimal(str(value))
    # Format with 2 decimal places
    formatted = f"{d:,.2f}"
    # Convert to Dutch format: 1,234.56 -> 1.234,56
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {formatted}"


def _format_date_nl(value) -> str:
    """Format a date as Dutch format: 17 februari 2026."""
    if value is None:
        return ""
    months = [
        "", "januari", "februari", "maart", "april", "mei", "juni",
        "juli", "augustus", "september", "oktober", "november", "december",
    ]
    if isinstance(value, str):
        # Parse ISO date string
        parts = value.split("-")
        return f"{int(parts[2])} {months[int(parts[1])]} {parts[0]}"
    return f"{value.day} {months[value.month]} {value.year}"


jinja_env.filters["currency"] = _format_currency
jinja_env.filters["datum"] = _format_date_nl


# ── Template CRUD (DEPRECATED — use docx_service.py for new documents) ──────


async def list_templates(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_type: str | None = None,
) -> list[DocumentTemplate]:
    """List all active templates, optionally filtered by type."""
    query = select(DocumentTemplate).where(
        DocumentTemplate.tenant_id == tenant_id,
        DocumentTemplate.is_active.is_(True),
    ).order_by(DocumentTemplate.name)

    if template_type:
        query = query.where(DocumentTemplate.template_type == template_type)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
) -> DocumentTemplate:
    """Get a template by ID."""
    result = await db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.id == template_id,
            DocumentTemplate.tenant_id == tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise NotFoundError("Sjabloon niet gevonden")
    return template


async def create_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: DocumentTemplateCreate,
) -> DocumentTemplate:
    """Create a new document template."""
    # Validate the Jinja2 template syntax
    try:
        jinja_env.parse(data.content)
    except Exception as e:
        raise BadRequestError(
            f"Ongeldig sjabloon: {e}"
        )

    template = DocumentTemplate(
        tenant_id=tenant_id,
        **data.model_dump(),
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


async def update_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
    data: DocumentTemplateUpdate,
) -> DocumentTemplate:
    """Update a document template."""
    template = await get_template(db, tenant_id, template_id)

    update_data = data.model_dump(exclude_unset=True)

    # Validate new content if provided
    if "content" in update_data and update_data["content"] is not None:
        try:
            jinja_env.parse(update_data["content"])
        except Exception as e:
            raise BadRequestError(
                f"Ongeldig sjabloon: {e}"
            )

    for field, value in update_data.items():
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return template


async def delete_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
) -> None:
    """Soft-delete a document template."""
    template = await get_template(db, tenant_id, template_id)
    template.is_active = False
    await db.flush()


# ── Document Generation (DEPRECATED — use docx_service.render_docx) ─────────


async def _build_template_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    extra_context: dict | None = None,
) -> dict:
    """Build the full context dictionary for template rendering.

    Available variables in templates:
      - zaak: case data (case_number, case_type, status, etc.)
      - client: client contact data
      - wederpartij: opposing party data (may be None)
      - vorderingen: list of claims
      - betalingen: list of payments
      - financieel: financial summary (totals, interest, BIK)
      - bik: BIK calculation details
      - vandaag: today's date
    """
    today = date.today()

    # Get client contact
    client = case.client

    # Get opposing party
    wederpartij = case.opposing_party

    # Get claims
    claims = await list_claims(db, tenant_id, case.id)

    # Get payments
    payments = await list_payments(db, tenant_id, case.id)

    # Get financial summary
    financieel = await get_financial_summary(
        db=db,
        tenant_id=tenant_id,
        case_id=case.id,
        interest_type=case.interest_type,
        contractual_rate=(
            Decimal(str(case.contractual_rate))
            if case.contractual_rate
            else None
        ),
        contractual_compound=case.contractual_compound,
        calc_date=today,
    )

    # Calculate BIK
    total_principal = sum(
        c.principal_amount for c in claims
    )
    bik = calculate_bik(total_principal)

    # Build context
    context = {
        "zaak": {
            "zaaknummer": case.case_number,
            "zaaktype": case.case_type,
            "status": case.status,
            "beschrijving": case.description or "",
            "referentie": case.reference or "",
            "rente_type": case.interest_type,
            "datum_geopend": case.date_opened,
            "datum_gesloten": case.date_closed,
        },
        "client": _contact_to_dict(client) if client else {},
        "wederpartij": (
            _contact_to_dict(wederpartij) if wederpartij else {}
        ),
        "vorderingen": [
            {
                "beschrijving": c.description,
                "hoofdsom": c.principal_amount,
                "verzuimdatum": c.default_date,
                "factuurnummer": c.invoice_number or "",
                "factuurdatum": c.invoice_date,
            }
            for c in claims
        ],
        "betalingen": [
            {
                "bedrag": p.amount,
                "datum": p.payment_date,
                "beschrijving": p.description or "",
            }
            for p in payments
        ],
        "financieel": financieel,
        "bik": bik,
        "vandaag": today,
    }

    # Merge extra context
    if extra_context:
        context.update(extra_context)

    return context


def _contact_to_dict(contact: Contact) -> dict:
    """Convert a Contact model to a template-friendly dict."""
    return {
        "naam": contact.name,
        "voornaam": contact.first_name or "",
        "achternaam": contact.last_name or "",
        "email": contact.email or "",
        "telefoon": contact.phone or "",
        "type": contact.contact_type,
        "kvk": contact.kvk_number or "",
        "btw": contact.btw_number or "",
        "adres": contact.visit_address or "",
        "postcode": contact.visit_postcode or "",
        "stad": contact.visit_city or "",
    }


async def generate_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: GenerateDocumentRequest,
) -> GeneratedDocument:
    """DEPRECATED: Generate an HTML document from a template for a case.

    Use docx_service.render_docx() for new document generation instead.

    1. Loads the template
    2. Loads the case + related data
    3. Renders the template with Jinja2
    4. Stores the result as a GeneratedDocument
    """
    # Get the template
    template = await get_template(db, tenant_id, data.template_id)

    # Get the case
    result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.tenant_id == tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    # Build context
    context = await _build_template_context(
        db, tenant_id, case, data.extra_context
    )

    # Render template
    try:
        jinja_template = jinja_env.from_string(template.content)
        rendered_html = jinja_template.render(**context)
    except Exception as e:
        raise BadRequestError(
            f"Fout bij renderen sjabloon: {e}"
        )

    # Determine title
    title = data.title or f"{template.name} - {case.case_number}"

    # Create the generated document
    doc = GeneratedDocument(
        tenant_id=tenant_id,
        case_id=case_id,
        template_id=template.id,
        generated_by_id=user_id,
        title=title,
        document_type=template.template_type,
        content_html=rendered_html,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


# ── Generated Document CRUD ──────────────────────────────────────────────────


async def list_generated_documents(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[GeneratedDocument]:
    """List all generated documents for a case."""
    result = await db.execute(
        select(GeneratedDocument).where(
            GeneratedDocument.tenant_id == tenant_id,
            GeneratedDocument.case_id == case_id,
            GeneratedDocument.is_active.is_(True),
        ).order_by(GeneratedDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def get_generated_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
) -> GeneratedDocument:
    """Get a generated document by ID."""
    result = await db.execute(
        select(GeneratedDocument).where(
            GeneratedDocument.id == document_id,
            GeneratedDocument.tenant_id == tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise NotFoundError("Document niet gevonden")
    return doc


async def delete_generated_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    """Soft-delete a generated document."""
    doc = await get_generated_document(db, tenant_id, document_id)
    doc.is_active = False
    await db.flush()
