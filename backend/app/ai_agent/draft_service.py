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
from app.cases.models import Case, CaseParty
from app.collections.models import Claim, Payment
from app.email.models import SyncedEmail
from app.relations.models import Contact

logger = logging.getLogger(__name__)


DRAFT_SYSTEM_PROMPT = """\
Je bent een AI-assistent voor een Nederlands incassokantoor (Kesting Legal).
Je schrijft concept-berichten (emails) namens de advocaat op basis van de dossiercontext.

REGELS:
- Schrijf formeel maar toegankelijk Nederlands
- Verwijs naar specifieke feiten uit het dossier (factuurnummer, bedrag, datum)
- Verwijs naar relevante wetsartikelen waar van toepassing
- Als er Algemene Voorwaarden (AV) zijn: verwijs naar relevante artikelen
- Eindig met een duidelijke call-to-action (betalen, reageren, bewijsstuk sturen)
- Gebruik de ondertekening: "Met vriendelijke groet,\\n\\nKesting Legal"
- Het bericht moet KLAAR zijn om te versturen — geen placeholders

BRONVERMELDING:
- Verwijs in het bericht naar de bronnen die je hebt gebruikt
- Gebruik voetnoten of inline referenties: [Email van DD-MM-YYYY], [Factuur #XXX], [Art. X AV]
- Bij wettelijke verwijzingen: noem het artikel (bijv. Art. 6:96 BW)

Antwoord ALLEEN met valide JSON:
{
  "subject": "<email onderwerp>",
  "body": "<volledige email body in plain text>",
  "tone": "<formeel|vriendelijk|streng>",
  "sources": [
    {"type": "<email|factuur|av|wet>", "reference": "<korte beschrijving>"}
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
        select(Claim)
        .where(Claim.case_id == case_id, Claim.tenant_id == tenant_id)
    )
    claims = claim_result.scalars().all()

    # Payments
    payment_result = await db.execute(
        select(Payment)
        .where(Payment.case_id == case_id, Payment.tenant_id == tenant_id)
    )
    payments = payment_result.scalars().all()

    # Client AV (terms)
    terms_text = ""
    if case.client_id:
        client_result = await db.execute(
            select(Contact).where(Contact.id == case.client_id)
        )
        client = client_result.scalar_one_or_none()
        if client and client.terms_file_path:
            terms_text = extract_text_from_pdf(client.terms_file_path)

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
        "total_principal": _serialize_decimal(sum((c.principal_amount for c in claims), Decimal("0"))),
        "total_paid": _serialize_decimal(sum((p.amount for p in payments), Decimal("0"))),
        "terms_text": terms_text[:3000] if terms_text else None,
    }

    # Parties
    for party in (case.parties or []):
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
        context["emails"].append({
            "date": str(e.email_date)[:10] if e.email_date else None,
            "direction": e.direction,
            "from": e.from_email,
            "subject": e.subject,
            "snippet": (e.snippet or "")[:200],
        })

    # Claims
    for c in claims:
        context["claims"].append({
            "description": c.description,
            "principal": _serialize_decimal(c.principal_amount),
            "invoice_number": c.invoice_number,
            "invoice_date": str(c.invoice_date) if c.invoice_date else None,
            "default_date": str(c.default_date) if c.default_date else None,
        })

    # Payments
    for p in payments:
        context["payments"].append({
            "amount": _serialize_decimal(p.amount),
            "date": str(p.payment_date) if p.payment_date else None,
            "description": p.description,
        })

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
            parts.append(f"{direction} {e.get('date', '?')}: {e.get('subject', '(geen onderwerp)')}")
            if e.get("snippet"):
                parts.append(f"  {e['snippet']}")

    # Terms
    if context.get("terms_text"):
        parts.append("\n--- Algemene Voorwaarden (excerpt) ---")
        parts.append(context["terms_text"])

    # User instruction
    if instruction:
        parts.append(f"\n--- Instructie ---\n{instruction}")
    else:
        parts.append("\n--- Instructie ---\nSchrijf een passend concept-bericht op basis van de huidige dossierstatus en de laatste correspondentie.")

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
