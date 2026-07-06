"""Gedeelde AV-resolver (S173).

Eén plek die per dossier de juiste versie van de Algemene Voorwaarden (AV) van de
cliënt oplevert. De logica is letterlijk geliftet uit `incasso/automation_service.py`
(dat pad was al correct: geversioneerde `ContactTerms` met selectie op factuurdatum),
zodat álle AI-conceptpaden dezelfde AV zien — voorheen zag alleen het incasso-pad de
geversioneerde AV, de compose-dialog niets en `draft_service` alleen de sinds S168 lege
legacy-kolom.

Bewust NIET gebundeld met geleerde voorbeelden + verweer-bibliotheek: die hebben al hun
eigen gedeelde functies (`learned_answers.build_learned_examples_text`,
`defense_library.get_relevant_examples` + `format_examples_for_prompt`) met per-caller
verschillende gating. Alleen de AV-selectie was echt gedupliceerd/kapot.
"""

import logging
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.cases.models import Case

logger = logging.getLogger(__name__)


def _extract_pdf_text(path: str, max_chars: int = 50000) -> str | None:
    """Extract text from PDF at given path. Returns None bij fouten of leeg.

    Verplaatst uit automation_service (S173). pymupdf, want dat is de extractor die
    het incasso-pad al gebruikte; bewust NIET de pymupdf4llm-variant uit
    `pdf_extract.py` (die capt op 5000 chars / 10 pagina's — te weinig voor een AV).
    """
    try:
        import pymupdf
    except ImportError:
        logger.warning("pymupdf niet beschikbaar — AV-text extractie uitgeschakeld")
        return None
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        logger.warning(f"AV PDF kan niet geopend worden ({path}): {e}")
        return None
    try:
        parts: list[str] = []
        total = 0
        for page in doc:
            text = page.get_text("text") or ""
            parts.append(text)
            total += len(text)
            if total >= max_chars:
                break
        result = "\n".join(parts).strip()
        return result[:max_chars] if result else None
    finally:
        doc.close()


async def _first_invoice_date(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID
) -> date | None:
    """Datum van de vroegste factuur op het dossier — voor de AV-versiekeuze."""
    from app.collections.models import Claim

    rows = (
        await db.execute(
            select(Claim.invoice_date).where(
                Claim.tenant_id == tenant_id,
                Claim.case_id == case_id,
                Claim.invoice_date.is_not(None),
            )
        )
    ).scalars().all()
    return min(rows) if rows else None


async def last_inbound_defense_category(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> str | None:
    """Categorie van de LAATSTE inkomende mail op dit dossier — of None.

    Bepaalt of de verweer-kennis (AV + bibliotheek + geleerde voorbeelden) mee de prompt
    in gaat wanneer er geen expliciete bron-classificatie is (next_step/free_compose, of
    een reply zonder eigen classificatie). Gedeeld door álle 3 de draft-paden.

    Twee harde regels (Fable-review S173 + besluit S174):
    1. Sorteer inkomende mails op `SyncedEmail.email_date`, NOOIT op
       `EmailClassification.created_at`: na de BaseNet-bulkimport (S168) klonteren de
       created_at-waarden rond het importmoment, dus dat koos een willekeurige/oude
       classificatie die vervolgens besliste of er 50k+ kennis werd geïnjecteerd.
    2. Alleen de ALLERNIEUWSTE inkomende mail telt. Is die niet geclassificeerd, dan
       geven we None terug (geen kennis injecteren) — we plakken géén oude verweer-context
       op een dossier dat inmiddels een verse, ongeclassificeerde mail heeft.
    """
    from app.ai_agent.models import EmailClassification
    from app.email.synced_email_models import SyncedEmail

    newest_inbound_id = (
        await db.execute(
            select(SyncedEmail.id)
            .where(
                SyncedEmail.tenant_id == tenant_id,
                SyncedEmail.case_id == case_id,
                SyncedEmail.direction == "inbound",
            )
            .order_by(SyncedEmail.email_date.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if newest_inbound_id is None:
        return None
    return (
        await db.execute(
            select(EmailClassification.category).where(
                EmailClassification.tenant_id == tenant_id,
                EmailClassification.synced_email_id == newest_inbound_id,
            )
        )
    ).scalar_one_or_none()


async def resolve_case_terms(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: "Case",
    *,
    target_date: date | None = None,
    max_chars: int = 50000,
) -> tuple[str | None, str | None]:
    """Bepaal AV-tekst + AV-PDF-pad voor de cliënt van dit dossier.

    Versie-keuze (S140), overgenomen uit automation_service:
    1. `case.contact_terms_id` expliciet gezet → die versie.
    2. Smart-default: versie geldig bij `target_date` (default: datum eerste factuur).
    3. Fallback: `contact.terms_file_path` (legacy single-file kolom).

    Returnt `(av_text, av_pdf_path)`; beide None als er geen AV is. Het PDF-pad wordt
    apart teruggegeven omdat het incasso-pad de AV ook native als PDF meestuurt.

    ponytail: haalt de cliënt-Contact zelf op i.p.v. te leunen op een eager-loaded
    relatie, zodat elke caller (met of zonder geladen relatie) hem veilig kan aanroepen —
    één extra indexed lookup, verwaarloosbaar.
    """
    from app.relations.models import Contact, ContactTerms
    from app.relations.service import list_contact_terms, select_terms_for_date

    client_id = getattr(case, "client_id", None)
    if not client_id:
        return None, None
    client_contact = (
        await db.execute(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.id == client_id)
        )
    ).scalar_one_or_none()
    if client_contact is None:
        return None, None

    terms_path: str | None = None
    chosen_label: str | None = None

    if case.contact_terms_id is not None:
        terms_row = (
            await db.execute(
                select(ContactTerms).where(
                    ContactTerms.tenant_id == tenant_id,
                    ContactTerms.id == case.contact_terms_id,
                )
            )
        ).scalar_one_or_none()
        if terms_row is not None:
            terms_path = terms_row.file_path
            chosen_label = terms_row.label or "(geen label)"
    else:
        # Smart-default: kies versie op basis van eerste factuur-datum.
        if target_date is None:
            target_date = await _first_invoice_date(db, tenant_id, case.id)
        versions = await list_contact_terms(db, tenant_id, client_contact.id)
        chosen = select_terms_for_date(versions, target_date)
        if chosen is not None:
            terms_path = chosen.file_path
            chosen_label = chosen.label or "(geen label)"

    # Fallback voor cliënten zonder versie-rij: legacy single-file kolom.
    if not terms_path and client_contact.terms_file_path:
        terms_path = client_contact.terms_file_path
        chosen_label = "legacy single-file"

    if not terms_path:
        return None, None

    av_text = _extract_pdf_text(terms_path, max_chars=max_chars)
    if av_text:
        logger.info(
            "AV geladen voor case %s / %s (versie='%s', %d chars)",
            getattr(case, "case_number", case.id),
            client_contact.name,
            chosen_label,
            len(av_text),
        )
    return av_text, terms_path
