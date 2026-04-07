"""AI-UX-09/13/14: AI concept-berichten met volledige dossiercontext + bronvermelding.

Generates draft email responses based on full case context:
- All synced emails (in/out)
- Case activities and notes
- Claims and payment status
- Client's terms & conditions (AV)
- Last classification result
"""

import logging
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai_agent.kimi_client import call_intake_ai
from app.ai_agent.pdf_extract import extract_text_from_pdf
from app.cases.files_service import get_file_path
from app.cases.models import Case, CaseFile, CaseParty
from app.collections.models import Claim, Payment
from app.email.synced_email_models import SyncedEmail
from app.invoices.models import Invoice
from app.relations.models import Contact

logger = logging.getLogger(__name__)


DRAFT_SYSTEM_PROMPT = """\
Je bent een AI-assistent voor een Nederlands incassokantoor (Kesting Legal).
Je schrijft concept-berichten (emails) namens de advocaat op basis van de dossiercontext.

JE BESCHIKT OVER DE VOLGENDE BRONNEN:
1. Vorderingen (claims) — wat de schuldenaar moet betalen, met factuurnummer en verzuimdatum
2. Facturen op het dossier — wat reeds gefactureerd is en de status
3. Recente correspondentie — eerdere e-mails in dit dossier
4. Algemene Voorwaarden van de cliënt — verwijs naar specifieke artikelen waar relevant
5. Documenten op het dossier — overeenkomsten, contracten, bewijsstukken (PDF excerpts)

REGELS:
- Schrijf formeel maar toegankelijk Nederlands
- Verwijs naar SPECIFIEKE feiten uit de bronnen: factuurnummers, bedragen, data, artikelen uit AV, clausules uit overeenkomsten
- Als de overeenkomst (Documenten op dossier) een specifieke clausule bevat die relevant is voor deze brief, citeer die letterlijk en noem de clausule
- Verwijs naar relevante wetsartikelen waar van toepassing (art. 6:96 BW voor incassokosten, art. 6:119/119a BW voor rente)
- Eindig met een duidelijke call-to-action (betalen, reageren, bewijsstuk sturen)
- Gebruik de ondertekening: "Met vriendelijke groet,\\n\\nKesting Legal"
- Het bericht moet KLAAR zijn om te versturen — geen placeholders, geen TODO's

BRONVERMELDING (sources array):
- Geef voor ELKE bron die je daadwerkelijk hebt gebruikt een entry op
- type = "email" | "factuur" | "av" | "overeenkomst" | "wet"
- reference = korte beschrijving (bijv. "Factuur F2026-001", "Art. 5.2 AV", "Overeenkomst d.d. 12-03-2024")

Antwoord ALLEEN met valide JSON:
{
  "subject": "<email onderwerp>",
  "body": "<volledige email body in plain text>",
  "tone": "<formeel|vriendelijk|streng>",
  "sources": [
    {"type": "<email|factuur|av|overeenkomst|wet>", "reference": "<korte beschrijving>"}
  ],
  "reasoning": "<1-2 zinnen waarom je dit bericht hebt geschreven>"
}
"""


def _serialize_decimal(v: Decimal | float | int | None) -> str | None:
    if v is None:
        return None
    return f"{float(v):.2f}"


async def _gather_case_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> dict:
    """Gather full case context for AI draft generation."""
    # Case with parties
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id, Case.tenant_id == tenant_id)
        .options(selectinload(Case.parties).selectinload(CaseParty.contact))
    )
    case = result.scalar_one_or_none()
    if not case:
        raise ValueError("Dossier niet gevonden")

    # Recent emails (last 10)
    email_result = await db.execute(
        select(SyncedEmail)
        .where(SyncedEmail.case_id == case_id, SyncedEmail.tenant_id == tenant_id)
        .order_by(SyncedEmail.email_date.desc())
        .limit(10)
    )
    emails = email_result.scalars().all()

    # Claims
    claim_result = await db.execute(
        select(Claim).where(Claim.case_id == case_id, Claim.tenant_id == tenant_id)
    )
    claims = claim_result.scalars().all()

    # Payments
    payment_result = await db.execute(
        select(Payment).where(Payment.case_id == case_id, Payment.tenant_id == tenant_id)
    )
    payments = payment_result.scalars().all()

    # Client AV (terms)
    terms_text = ""
    if case.client_id:
        client_result = await db.execute(select(Contact).where(Contact.id == case.client_id))
        client = client_result.scalar_one_or_none()
        if client and client.terms_file_path:
            terms_text = extract_text_from_pdf(client.terms_file_path)

    # DF117-03 (Lisanne demo 2026-04-07): include uploaded case files (contracts,
    # overeenkomsten, deurwaardersrapporten, etc.) so the AI can reference them
    # when composing a message. Each file is read with the same PDF extractor
    # that already handles the AV; non-PDFs are skipped silently.
    case_file_excerpts: list[dict] = []
    case_files_result = await db.execute(
        select(CaseFile)
        .where(
            CaseFile.case_id == case_id,
            CaseFile.tenant_id == tenant_id,
            CaseFile.is_active.is_(True),
        )
        .order_by(CaseFile.created_at.desc())
    )
    case_files = list(case_files_result.scalars().all())
    # Hard cap: at most 5 files, ~2000 chars each, to keep prompt size sane
    MAX_FILES = 5
    MAX_CHARS_PER_FILE = 2000
    for cf in case_files[:MAX_FILES]:
        if not cf.content_type or "pdf" not in cf.content_type.lower():
            continue
        try:
            file_path = get_file_path(cf)
            if not file_path.exists():
                continue
            text = extract_text_from_pdf(file_path)
            if not text:
                continue
            case_file_excerpts.append(
                {
                    "filename": cf.original_filename,
                    "description": cf.description,
                    "direction": cf.document_direction,
                    "excerpt": text[:MAX_CHARS_PER_FILE],
                }
            )
        except Exception as e:
            logger.warning("Could not extract case file %s: %s", cf.id, e)

    # DF117-03: also include the most recent invoices on the case so the AI
    # knows what was billed and when. This complements the claims data which
    # only covers the underlying receivables.
    invoices_result = await db.execute(
        select(Invoice)
        .where(
            Invoice.case_id == case_id,
            Invoice.tenant_id == tenant_id,
            Invoice.is_active.is_(True),
        )
        .order_by(Invoice.invoice_date.desc())
        .limit(10)
    )
    case_invoices = list(invoices_result.scalars().all())

    # Build context dict
    context = {
        "case_number": case.case_number,
        "status": case.status,
        "case_type": case.case_type,
        "debtor_type": case.debtor_type,
        "description": case.description,
        "opposing_party": None,
        "client": None,
        "emails": [],
        "claims": [],
        "payments": [],
        "total_principal": _serialize_decimal(
            sum((c.principal_amount for c in claims), Decimal("0"))
        ),
        "total_paid": _serialize_decimal(sum((p.amount for p in payments), Decimal("0"))),
        "terms_text": terms_text[:3000] if terms_text else None,
        "case_files": case_file_excerpts,
        "invoices": [
            {
                "invoice_number": inv.invoice_number,
                "invoice_type": inv.invoice_type or "invoice",
                "status": inv.status,
                "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
                "due_date": str(inv.due_date) if inv.due_date else None,
                "total": _serialize_decimal(inv.total),
            }
            for inv in case_invoices
        ],
    }

    # Parties
    for party in case.parties or []:
        if party.role == "opposing_party" and party.contact:
            context["opposing_party"] = {
                "name": party.contact.name,
                "email": party.contact.email,
                "type": party.contact.contact_type,
            }
        elif party.role == "client" and party.contact:
            context["client"] = {
                "name": party.contact.name,
                "email": party.contact.email,
            }

    # Fallback for client/opposing from case fields
    if not context["client"] and hasattr(case, "client") and case.client:
        context["client"] = {"name": case.client.name, "email": getattr(case.client, "email", None)}
    if not context["opposing_party"] and hasattr(case, "opposing_party") and case.opposing_party:
        context["opposing_party"] = {
            "name": case.opposing_party.name,
            "email": getattr(case.opposing_party, "email", None),
            "type": getattr(case.opposing_party, "contact_type", None),
        }

    # Emails
    for e in emails:
        context["emails"].append(
            {
                "date": str(e.email_date)[:10] if e.email_date else None,
                "direction": e.direction,
                "from": e.from_email,
                "subject": e.subject,
                "snippet": (e.snippet or "")[:200],
            }
        )

    # Claims
    for c in claims:
        context["claims"].append(
            {
                "description": c.description,
                "principal": _serialize_decimal(c.principal_amount),
                "invoice_number": c.invoice_number,
                "invoice_date": str(c.invoice_date) if c.invoice_date else None,
                "default_date": str(c.default_date) if c.default_date else None,
            }
        )

    # Payments
    for p in payments:
        context["payments"].append(
            {
                "amount": _serialize_decimal(p.amount),
                "date": str(p.payment_date) if p.payment_date else None,
                "description": p.description,
            }
        )

    return context


def _build_draft_prompt(context: dict, instruction: str | None = None) -> str:
    """Build the user message for draft generation."""
    parts = [f"Dossier: {context['case_number']} ({context['case_type']})"]
    parts.append(f"Status: {context['status']}")

    if context.get("opposing_party"):
        op = context["opposing_party"]
        parts.append(f"Wederpartij: {op['name']} ({op.get('type', 'onbekend')})")

    if context.get("client"):
        parts.append(f"Cliënt: {context['client']['name']}")

    if context.get("description"):
        parts.append(f"Omschrijving: {context['description']}")

    # Financial summary
    parts.append(f"\nHoofdsom: €{context.get('total_principal', '0.00')}")
    parts.append(f"Betaald: €{context.get('total_paid', '0.00')}")

    # Claims
    if context.get("claims"):
        parts.append("\n--- Vorderingen ---")
        for c in context["claims"]:
            line = f"- {c.get('description', 'Vordering')}: €{c.get('principal', '?')}"
            if c.get("invoice_number"):
                line += f" (factuur {c['invoice_number']})"
            if c.get("default_date"):
                line += f", verzuim vanaf {c['default_date']}"
            parts.append(line)

    # Recent emails
    if context.get("emails"):
        parts.append("\n--- Recente correspondentie ---")
        for e in context["emails"]:
            direction = "←" if e["direction"] == "inbound" else "→"
            subj = e.get("subject", "(geen onderwerp)")
            parts.append(f"{direction} {e.get('date', '?')}: {subj}")
            if e.get("snippet"):
                parts.append(f"  {e['snippet']}")

    # DF117-03: invoices on the case (what was actually billed)
    if context.get("invoices"):
        parts.append("\n--- Facturen op dit dossier ---")
        for inv in context["invoices"]:
            line = f"- {inv['invoice_type'].upper()} {inv['invoice_number']}"
            if inv.get("invoice_date"):
                line += f" dd. {inv['invoice_date']}"
            line += f": €{inv.get('total', '?')} ({inv['status']})"
            if inv.get("due_date"):
                line += f", vervaldatum {inv['due_date']}"
            parts.append(line)

    # Terms
    if context.get("terms_text"):
        parts.append("\n--- Algemene Voorwaarden cliënt (excerpt) ---")
        parts.append(context["terms_text"])

    # DF117-03: case files (overeenkomsten, contracten, etc.)
    if context.get("case_files"):
        parts.append("\n--- Documenten op dossier ---")
        for cf in context["case_files"]:
            header = f"\n[{cf['filename']}"
            if cf.get("description"):
                header += f" — {cf['description']}"
            if cf.get("direction"):
                header += f" ({cf['direction']})"
            header += "]"
            parts.append(header)
            parts.append(cf["excerpt"])

    # User instruction
    if instruction:
        parts.append(f"\n--- Instructie ---\n{instruction}")
    else:
        parts.append(
            "\n--- Instructie ---\n"
            "Schrijf een passend concept-bericht op basis van de huidige"
            " dossierstatus en de laatste correspondentie."
        )

    return "\n".join(parts)


async def generate_draft(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    instruction: str | None = None,
) -> dict:
    """Generate an AI draft email for a case.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        case_id: Case UUID
        instruction: Optional user instruction for the AI

    Returns:
        Dict with subject, body, tone, sources, reasoning
    """
    context = await _gather_case_context(db, tenant_id, case_id)
    user_message = _build_draft_prompt(context, instruction)

    logger.info(
        "Generating AI draft for case %s (%d chars context)",
        context["case_number"],
        len(user_message),
    )

    result, model = await call_intake_ai(DRAFT_SYSTEM_PROMPT, user_message)

    logger.info("AI draft generated for %s via %s", context["case_number"], model)

    return {
        "subject": result.get("subject", ""),
        "body": result.get("body", ""),
        "tone": result.get("tone", "formeel"),
        "sources": result.get("sources", []),
        "reasoning": result.get("reasoning", ""),
        "model": model,
        "case_number": context["case_number"],
    }


async def generate_client_update(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    trigger: str,
    details: str | None = None,
) -> dict:
    """Generate an AI draft update email to the client (opdrachtgever).

    Called automatically when a payment is received or status changes.

    Args:
        trigger: "payment" or "status_change"
        details: Extra context (e.g. "Betaling van €500 ontvangen" or "Status: sommatie → dagvaarding")
    """
    instructions = {
        "payment": (
            "Schrijf een kort update-bericht naar de OPDRACHTGEVER (cliënt, niet de debiteur). "
            "Meld dat er een betaling is ontvangen op het dossier. "
            "Vermeld het bedrag, het resterende openstaande bedrag, en wat de volgende stap is. "
            "Houd het kort en zakelijk (3-5 zinnen). "
            f"Extra details: {details or 'geen'}"
        ),
        "status_change": (
            "Schrijf een kort update-bericht naar de OPDRACHTGEVER (cliënt, niet de debiteur). "
            "Meld dat de status van het incassodossier is gewijzigd. "
            "Leg kort uit wat de nieuwe status betekent en wat de volgende stap is. "
            "Houd het kort en zakelijk (3-5 zinnen). "
            f"Extra details: {details or 'geen'}"
        ),
    }

    instruction = instructions.get(trigger, instructions["status_change"])
    return await generate_draft(db, tenant_id, case_id, instruction)
