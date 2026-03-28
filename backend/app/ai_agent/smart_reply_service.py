"""Smart reply service — generates AI-powered reply suggestions for classified emails.

For each classified debtor email, generates 3 context-appropriate reply drafts
that the lawyer can review, edit, and send. Replies are never sent automatically.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.kimi_client import call_intake_ai
from app.ai_agent.models import EmailClassification
from app.ai_agent.prompts import strip_html
from app.cases.models import Case
from app.email.synced_email_models import SyncedEmail
from app.shared.exceptions import NotFoundError

logger = logging.getLogger(__name__)

SMART_REPLY_SYSTEM_PROMPT = """\
Je bent een juridisch assistent voor Kesting Legal, een Nederlands incassokantoor.
Advocaat: mr. L. Kesting. Kantoor: IJsbaanpad 9, 1076 CV Amsterdam.

Je schrijft professionele concept-antwoorden op emails van debiteuren.
Schrijf in het Nederlands, zakelijk maar correct. Gebruik "u" (formeel).

Genereer PRECIES 3 antwoord-opties met verschillende toon/aanpak:
1. Mild/meewerkend — begrip tonen, oplossing zoeken
2. Zakelijk/neutraal — feitelijk, kort, to-the-point
3. Streng/formeel — juridisch, duidelijke consequenties

Elke optie bevat:
- tone: "mild", "zakelijk", of "streng"
- subject: onderwerpregel voor het antwoord
- body: het antwoord in plain text (geen HTML)

Het antwoord moet:
- Verwijzen naar het dossiernummer
- Het openstaande bedrag noemen als relevant
- Afsluiten met "Met vriendelijke groet,\\n\\nmr. L. Kesting\\nKesting Legal"
- NIET dreigen met dagvaarding tenzij de toon "streng" is en de situatie het rechtvaardigt
- Bij betalingsbeloftes: de datum bevestigen en consequenties bij niet-betaling noemen
- Bij betwistingen: vragen om onderbouwing en aangeven dat de vordering gehandhaafd wordt
- Bij regelingsverzoeken: opties geven (accepteren, tegenvoorstel, afwijzen)

Antwoord ALLEEN met valide JSON:
[
  {"tone": "mild", "subject": "...", "body": "..."},
  {"tone": "zakelijk", "subject": "...", "body": "..."},
  {"tone": "streng", "subject": "...", "body": "..."}
]
"""


def _build_smart_reply_prompt(
    *,
    case_number: str,
    outstanding_amount: str,
    debtor_name: str,
    category: str,
    sentiment: str | None,
    email_subject: str,
    email_body: str,
    promise_date: str | None = None,
    promise_amount: str | None = None,
) -> str:
    """Build the user message for smart reply generation."""
    promise_section = ""
    if promise_date or promise_amount:
        parts = []
        if promise_date:
            parts.append(f"Beloofde datum: {promise_date}")
        if promise_amount:
            parts.append(f"Beloofd bedrag: EUR {promise_amount}")
        promise_section = f"\nBetalingsbelofte: {', '.join(parts)}\n"

    body = email_body[:2000]
    if len(email_body) > 2000:
        body += "\n[... ingekort ...]"

    return (
        f"Dossier: {case_number}\n"
        f"Openstaand bedrag: EUR {outstanding_amount}\n"
        f"Debiteur: {debtor_name}\n"
        f"Classificatie: {category}\n"
        f"Sentiment: {sentiment or 'onbekend'}\n"
        f"{promise_section}"
        f"\n--- Email van debiteur ---\n"
        f"Onderwerp: {email_subject}\n\n"
        f"{body}"
    )


async def generate_smart_replies(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    classification_id: uuid.UUID,
) -> list[dict]:
    """Generate 3 smart reply suggestions for a classified email.

    Returns list of dicts with keys: tone, subject, body
    """
    # Load classification with relationships
    result = await db.execute(
        select(EmailClassification).where(
            EmailClassification.id == classification_id,
            EmailClassification.tenant_id == tenant_id,
        )
    )
    classification = result.scalar_one_or_none()
    if not classification:
        raise NotFoundError("Classificatie niet gevonden")

    # Get email
    email = classification.synced_email
    if not email:
        raise NotFoundError("Email niet gevonden")

    # Get case
    case = classification.case
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    # Build body text
    body = email.body_text or strip_html(email.body_html or "") or ""

    # Calculate outstanding
    outstanding = case.total_principal - case.total_paid

    # Get debtor name from opposing party
    debtor_name = "Geachte heer/mevrouw"
    if case.parties:
        for party in case.parties:
            if party.role in ("debtor", "defendant", "opposing_party"):
                if party.contact:
                    debtor_name = party.contact.name
                    break

    # Build prompt
    user_message = _build_smart_reply_prompt(
        case_number=case.case_number,
        outstanding_amount=str(outstanding),
        debtor_name=debtor_name,
        category=classification.category,
        sentiment=classification.sentiment,
        email_subject=email.subject,
        email_body=body,
        promise_date=str(classification.promise_date) if classification.promise_date else None,
        promise_amount=str(classification.promise_amount) if classification.promise_amount else None,
    )

    # Call AI
    try:
        result_data, model = await call_intake_ai(
            SMART_REPLY_SYSTEM_PROMPT, user_message
        )
        logger.info("Smart replies generated using %s for classification %s", model, classification_id)
    except Exception as e:
        logger.error("Smart reply generation failed: %s", e)
        raise

    # Validate result is a list of 3 replies
    if isinstance(result_data, list):
        replies = result_data
    elif isinstance(result_data, dict) and "replies" in result_data:
        replies = result_data["replies"]
    else:
        replies = [result_data]

    validated = []
    for reply in replies[:3]:
        if isinstance(reply, dict) and "tone" in reply and "body" in reply:
            validated.append({
                "tone": reply.get("tone", "zakelijk"),
                "subject": reply.get("subject", f"Re: {email.subject}"),
                "body": reply.get("body", ""),
            })

    return validated
