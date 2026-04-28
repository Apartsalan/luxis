"""Orchestrator — the brain that connects all Luxis modules.

Listens to events from the event bus and triggers automated actions:
- Email classified → auto-generate draft for Lisanne to review
- Payment received → update case, draft notification
- Step changed → prepare documents

HARD RULE: Never auto-send responses to inbound emails.
AI prepares everything, Lisanne approves and sends.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.events import EMAIL_CLASSIFIED, EventBus, event_bus
from app.ai_agent.models import CATEGORY_LABELS, ClassificationCategory

logger = logging.getLogger(__name__)

# Categories that require a draft response to the debtor
DRAFT_CATEGORIES = {
    ClassificationCategory.BELOFTE_TOT_BETALING,
    ClassificationCategory.BETWISTING,
    ClassificationCategory.BETALINGSREGELING_VERZOEK,
    ClassificationCategory.BEWEERT_BETAALD,
    ClassificationCategory.ONVERMOGEN,
    ClassificationCategory.JURIDISCH_VERWEER,
}

# Category-specific instructions for draft generation
CATEGORY_INSTRUCTIONS: dict[str, str] = {
    ClassificationCategory.BELOFTE_TOT_BETALING: (
        "Bevestig de betaalbelofte van de debiteur. Vermeld het beloofde bedrag en datum "
        "indien bekend. Benadruk dat bij uitblijven van betaling de incassoprocedure wordt voortgezet."
    ),
    ClassificationCategory.BETWISTING: (
        "Bevestig ontvangst van de betwisting. Vraag om onderbouwing indien niet verstrekt. "
        "Handhaaf de vordering en verwijs naar relevante overeenkomst/factuur/AV."
    ),
    ClassificationCategory.BETALINGSREGELING_VERZOEK: (
        "Bevestig ontvangst van het verzoek tot betalingsregeling. "
        "Geef aan dat het voorstel wordt beoordeeld. Vraag om concreet voorstel "
        "(bedrag per maand, eerste betaaldatum) indien niet verstrekt."
    ),
    ClassificationCategory.BEWEERT_BETAALD: (
        "Geef aan dat de betaling niet is ontvangen. "
        "Vraag om betalingsbewijs (bankafschrift of transactiebevestiging) binnen 5 werkdagen. "
        "Vermeld dat bij uitblijven de incassoprocedure wordt voortgezet."
    ),
    ClassificationCategory.ONVERMOGEN: (
        "Bevestig ontvangst. Geef aan dat betalingsonmacht geen grond is om de vordering "
        "te beëindigen. Stel voor om samen naar een oplossing te kijken (betalingsregeling)."
    ),
    ClassificationCategory.JURIDISCH_VERWEER: (
        "Bevestig ontvangst van het juridisch verweer. Geef aan dat de advocaat de stellingen "
        "beoordeelt. Vermeld dat de incassoprocedure niet wordt opgeschort tenzij anders bericht."
    ),
}


async def handle_email_classified(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    classification_id: uuid.UUID,
    case_id: uuid.UUID,
    category: str,
    confidence: float,
    synced_email_id: uuid.UUID,
) -> None:
    """React to a newly classified email.

    For categories that need a response: auto-generate a draft and create a notification.
    Draft is saved to DB (fixes BUG-70). Never auto-sends.
    """
    category_label = CATEGORY_LABELS.get(category, category)

    if category not in DRAFT_CATEGORIES:
        logger.info(
            "Orchestrator: category %s needs no draft — skipping (case %s)",
            category_label,
            case_id,
        )
        return

    instruction = CATEGORY_INSTRUCTIONS.get(category)

    logger.info(
        "Orchestrator: generating draft for %s on case %s (classification %s)",
        category_label,
        case_id,
        classification_id,
    )

    try:
        from sqlalchemy import select

        from app.ai_agent.draft_service import generate_and_persist_draft

        draft = await generate_and_persist_draft(
            db=db,
            tenant_id=tenant_id,
            case_id=case_id,
            instruction=instruction,
            classification_id=classification_id,
        )

        # Create notification for all active users in this tenant
        from app.auth.models import User
        from app.notifications.schemas import NotificationCreate
        from app.notifications.service import create_notification_if_not_exists

        users_result = await db.execute(
            select(User).where(User.tenant_id == tenant_id, User.is_active.is_(True))
        )
        for user in users_result.scalars().all():
            await create_notification_if_not_exists(
                db, tenant_id, user.id,
                NotificationCreate(
                    type="ai_draft_ready",
                    title=f"AI concept klaar — {category_label}",
                    message=f"Concept-antwoord gegenereerd. Categorie: {category_label}.",
                    case_id=case_id,
                ),
            )

        # Log in case activity
        from app.cases.models import CaseActivity

        activity = CaseActivity(
            tenant_id=tenant_id,
            case_id=case_id,
            activity_type="orchestrator",
            title=f"AI concept gegenereerd: {category_label}",
            description=(
                f"Automatisch concept-antwoord gegenereerd na classificatie.\n"
                f"Categorie: {category_label}\n"
                f"Toon: {draft.tone}\n"
                f"Status: wacht op goedkeuring"
            ),
        )
        db.add(activity)

        logger.info("Orchestrator: draft %s created for case %s", draft.id, case_id)

    except Exception:
        logger.exception(
            "Orchestrator: failed to generate draft for classification %s",
            classification_id,
        )


def register_handlers(bus: EventBus | None = None) -> None:
    """Register all orchestrator handlers on the event bus."""
    target = bus or event_bus
    target.on(EMAIL_CLASSIFIED, handle_email_classified)
    logger.info("Orchestrator: all handlers registered")
