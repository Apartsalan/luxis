"""Gedeelde helper: renteoverzicht als PDF-bijlage bij de 14-dagenbrief/eerste
sommatie (S211).

Gebruikt door zowel het batch-verzendpad (`incasso.service`) als de
'Uitvoeren'-knop (`ai_agent.followup_service`), zodat de regel niet uit elkaar
loopt. De verzendbeslissing (`should_attach_rente_bijlage`) leest ALLEEN het
opgeslagen rechtsvorm-veld — deze helper raakt de KvK nooit aan.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.collections.compliance import (
    RENTE_BIJLAGE_TEMPLATE_TYPES,
    should_attach_rente_bijlage,
)
from app.documents.docx_service import render_docx
from app.documents.models import GeneratedDocument
from app.documents.pdf_service import docx_to_pdf

logger = logging.getLogger(__name__)


def wants_rente_bijlage(case, step) -> bool:
    """Verdient deze stap (14-dagenbrief/eerste sommatie) voor deze zaak een
    renteoverzicht-bijlage? Puur op de opgeslagen velden — geen render, geen KvK.
    Bruikbaar voor preview zonder de PDF te bouwen.
    """
    if getattr(step, "template_type", None) not in RENTE_BIJLAGE_TEMPLATE_TYPES:
        return False
    return should_attach_rente_bijlage(
        getattr(case, "opposing_party", None), getattr(case, "debtor_type", None)
    )


async def build_rente_bijlage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case,
    step,
    user_id: uuid.UUID,
) -> list[tuple[str, bytes, str]]:
    """Render het renteoverzicht als PDF-bijlage als deze stap er een verdient én
    de wederpartij privé aansprakelijk is. Slaat het overzicht ook op als
    GeneratedDocument zodat het in het dossier terugkomt. Retourneert de
    attachments-lijst voor `send_with_attachment` ([] als er geen bijlage hoeft).
    """
    if not wants_rente_bijlage(case, step):
        return []

    docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
        db, tenant_id, case, "renteoverzicht"
    )
    pdf_bytes = await docx_to_pdf(docx_bytes)
    pdf_filename = filename.replace(".docx", ".pdf")

    doc = GeneratedDocument(
        tenant_id=tenant_id,
        case_id=case.id,
        generated_by_id=user_id,
        title=f"Renteoverzicht - {case.case_number}",
        document_type=tpl_type,
        template_type=tpl_type,
        template_snapshot=tpl_snapshot,
    )
    db.add(doc)
    await db.flush()

    return [(pdf_filename, pdf_bytes, "pdf")]
