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


# De dreigbrief belooft in de tekst "een kopie van het verzoekschrift treft u in
# de bijlage aan" — dan moet die kopie er op élke route ook echt bij (S225-vondst:
# de batch stuurde hem zonder; besluit Arsalan 17/7: automatisch meesturen).
VERZOEKSCHRIFT_BIJLAGE_TEMPLATE_TYPES = {"faillissement_dreigbrief"}


async def _render_pdf_bijlage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case,
    user_id: uuid.UUID,
    template_key: str,
    doc_title: str,
) -> tuple[str, bytes, str]:
    """Render één DOCX-sjabloon naar een PDF-bijlage + GeneratedDocument-spoor."""
    docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
        db, tenant_id, case, template_key
    )
    pdf_bytes = await docx_to_pdf(docx_bytes)
    pdf_filename = filename.replace(".docx", ".pdf")

    doc = GeneratedDocument(
        tenant_id=tenant_id,
        case_id=case.id,
        generated_by_id=user_id,
        title=f"{doc_title} - {case.case_number}",
        document_type=tpl_type,
        template_type=tpl_type,
        template_snapshot=tpl_snapshot,
    )
    db.add(doc)
    await db.flush()

    return (pdf_filename, pdf_bytes, "pdf")


async def build_rente_bijlage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case,
    step,
    user_id: uuid.UUID,
) -> list[tuple[str, bytes, str]]:
    """Bouw de brieftype-gebonden PDF-bijlagen voor een verzendactie.

    - Renteoverzicht bij 14-dagenbrief/eerste sommatie voor een privé
      aansprakelijke wederpartij (`wants_rente_bijlage`).
    - Concept-verzoekschrift bij de faillissementsdreigbrief (de brieftekst
      belooft die bijlage expliciet).

    Slaat elke bijlage ook op als GeneratedDocument zodat hij in het dossier
    terugkomt. Retourneert de attachments-lijst voor `send_with_attachment`
    ([] als er geen bijlage hoeft).
    """
    attachments: list[tuple[str, bytes, str]] = []

    if wants_rente_bijlage(case, step):
        attachments.append(
            await _render_pdf_bijlage(
                db, tenant_id, case, user_id, "renteoverzicht", "Renteoverzicht"
            )
        )

    if getattr(step, "template_type", None) in VERZOEKSCHRIFT_BIJLAGE_TEMPLATE_TYPES:
        attachments.append(
            await _render_pdf_bijlage(
                db,
                tenant_id,
                case,
                user_id,
                "verzoekschrift_faillissement",
                "Concept-verzoekschrift faillissement",
            )
        )

    return attachments
