"""AI Agent service — email classification, review, and execution logic."""

import json
import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import anthropic
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai_agent.models import (
    ACTION_LABELS,
    CATEGORY_LABELS,
    ClassificationCategory,
    ClassificationStatus,
    EmailClassification,
    ResponseTemplate,
    SuggestedAction,
)
from app.ai_agent.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    build_classification_prompt,
    strip_html,
)
from app.auth.models import Tenant
from app.cases.models import Case, CaseActivity
from app.config import settings
from app.email.send_service import send_with_attachment
from app.email.synced_email_models import SyncedEmail
from app.workflow.models import WorkflowTask

_jinja_env = SandboxedEnvironment()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AI call (isolated — easy to mock in tests)
# ---------------------------------------------------------------------------

async def _call_classification_ai(user_message: str) -> dict:
    """Call the Anthropic API to classify a debtor email.

    Returns the parsed JSON dict from the AI response.
    Raises ValueError if the response is not valid JSON.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=CLASSIFICATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()

    # Parse JSON — the prompt instructs the model to return pure JSON
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        if "```" in raw_text:
            json_part = raw_text.split("```")[1]
            if json_part.startswith("json"):
                json_part = json_part[4:]
            return json.loads(json_part.strip())
        raise ValueError(f"AI returned invalid JSON: {raw_text[:200]}")


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

async def classify_email(
    db: AsyncSession,
    synced_email_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> EmailClassification | None:
    """Classify a single inbound email. Idempotent — skips if already classified.

    Returns the EmailClassification or None if skipped.
    """
    # Check if already classified
    existing = await db.execute(
        select(EmailClassification).where(
            EmailClassification.synced_email_id == synced_email_id,
            EmailClassification.tenant_id == tenant_id,
        )
    )
    if existing.scalar_one_or_none():
        logger.info("Email %s already classified — skipping", synced_email_id)
        return None

    # Load the email with its case
    result = await db.execute(
        select(SyncedEmail)
        .options(
            selectinload(SyncedEmail.case)
            .selectinload(Case.opposing_party),
            selectinload(SyncedEmail.case)
            .selectinload(Case.incasso_step),
        )
        .where(
            SyncedEmail.id == synced_email_id,
            SyncedEmail.tenant_id == tenant_id,
        )
    )
    email = result.scalar_one_or_none()
    if not email or not email.case:
        logger.warning(
            "Email %s not found or has no case — skipping classification",
            synced_email_id,
        )
        return None

    case = email.case

    # Get email body (prefer plain text, fall back to stripped HTML)
    body = email.body_text or strip_html(email.body_html) or ""
    logger.info(
        "Email %s body extraction: body_text=%d chars, body_html=%d chars, "
        "stripped_body=%d chars",
        synced_email_id,
        len(email.body_text or ""),
        len(email.body_html or ""),
        len(body),
    )
    if not body.strip():
        logger.warning(
            "Email %s has empty body after extraction — skipping",
            synced_email_id,
        )
        return None  # Empty email — nothing to classify

    # Get the last outbound email on this case for context
    last_outbound = await db.execute(
        select(SyncedEmail)
        .where(
            SyncedEmail.case_id == case.id,
            SyncedEmail.direction == "outbound",
            SyncedEmail.tenant_id == tenant_id,
        )
        .order_by(SyncedEmail.email_date.desc())
        .limit(1)
    )
    last_out = last_outbound.scalar_one_or_none()

    # Build the prompt with case context
    outstanding = Decimal(str(case.total_principal)) - Decimal(
        str(case.total_paid)
    )
    opposing_name = (
        case.opposing_party.name if case.opposing_party else "Onbekend"
    )
    step_name = case.incasso_step.name if case.incasso_step else None

    user_message = build_classification_prompt(
        case_number=case.case_number,
        pipeline_step_name=step_name,
        outstanding_amount=str(outstanding),
        opposing_party_name=opposing_name,
        last_outbound_subject=last_out.subject if last_out else None,
        last_outbound_date=(
            last_out.email_date.strftime("%d-%m-%Y") if last_out else None
        ),
        email_subject=email.subject,
        email_from_name=email.from_name,
        email_from_email=email.from_email,
        email_date=email.email_date.strftime("%d-%m-%Y %H:%M"),
        email_body=body,
    )

    # Call the AI
    try:
        ai_result = await _call_classification_ai(user_message)
    except Exception as e:
        logger.error(
            "AI classification failed for email %s: %s",
            synced_email_id,
            e,
        )
        return None

    # Validate category
    valid_categories = {c.value for c in ClassificationCategory}
    category = ai_result.get("category", "niet_gerelateerd")
    if category not in valid_categories:
        category = "niet_gerelateerd"

    # Validate action
    valid_actions = {a.value for a in SuggestedAction}
    action = ai_result.get("suggested_action", "no_action")
    if action not in valid_actions:
        action = "no_action"

    classification = EmailClassification(
        tenant_id=tenant_id,
        synced_email_id=synced_email_id,
        case_id=case.id,
        category=category,
        confidence=min(max(float(ai_result.get("confidence", 0.5)), 0.0), 1.0),
        reasoning=ai_result.get("reasoning", ""),
        suggested_action=action,
        suggested_template_key=ai_result.get("suggested_template_key"),
        suggested_reminder_days=ai_result.get("suggested_reminder_days"),
        status=ClassificationStatus.PENDING,
    )
    db.add(classification)
    await db.flush()
    await db.refresh(classification)

    logger.info(
        "Classified email %s → %s (%.0f%%) action=%s",
        synced_email_id,
        category,
        classification.confidence * 100,
        action,
    )
    return classification


async def classify_new_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Classify all unclassified inbound emails on incasso cases.

    Returns the number of newly classified emails.
    """
    # Find inbound emails on incasso cases that haven't been classified yet
    already_classified = (
        select(EmailClassification.synced_email_id)
        .where(EmailClassification.tenant_id == tenant_id)
    )

    result = await db.execute(
        select(SyncedEmail.id)
        .join(Case, SyncedEmail.case_id == Case.id)
        .where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.direction == "inbound",
            SyncedEmail.case_id.isnot(None),
            SyncedEmail.is_dismissed.is_(False),
            Case.case_type == "incasso",
            SyncedEmail.id.notin_(already_classified),
        )
        .order_by(SyncedEmail.email_date.asc())
        .limit(20)  # Process max 20 per batch to limit API costs
    )
    email_ids = list(result.scalars().all())

    classified_count = 0
    for email_id in email_ids:
        classification = await classify_email(db, email_id, tenant_id)
        if classification:
            classified_count += 1

    return classified_count


# ---------------------------------------------------------------------------
# Review (approve / reject)
# ---------------------------------------------------------------------------

async def approve_classification(
    db: AsyncSession,
    classification_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    note: str | None = None,
) -> EmailClassification | None:
    """Approve a pending classification."""
    result = await db.execute(
        select(EmailClassification).where(
            EmailClassification.id == classification_id,
            EmailClassification.tenant_id == tenant_id,
            EmailClassification.status == ClassificationStatus.PENDING,
        )
    )
    classification = result.scalar_one_or_none()
    if not classification:
        return None

    classification.status = ClassificationStatus.APPROVED
    classification.reviewed_by_id = user_id
    classification.reviewed_at = datetime.now(UTC)
    classification.review_note = note

    await db.flush()
    return classification


async def reject_classification(
    db: AsyncSession,
    classification_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    note: str | None = None,
) -> EmailClassification | None:
    """Reject a pending classification."""
    result = await db.execute(
        select(EmailClassification).where(
            EmailClassification.id == classification_id,
            EmailClassification.tenant_id == tenant_id,
            EmailClassification.status == ClassificationStatus.PENDING,
        )
    )
    classification = result.scalar_one_or_none()
    if not classification:
        return None

    classification.status = ClassificationStatus.REJECTED
    classification.reviewed_by_id = user_id
    classification.reviewed_at = datetime.now(UTC)
    classification.review_note = note

    await db.flush()
    return classification


# ---------------------------------------------------------------------------
# Execute approved classification
# ---------------------------------------------------------------------------

async def execute_classification(
    db: AsyncSession,
    classification_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> EmailClassification | None:
    """Execute an approved classification action.

    For send_template / request_proof: sends the template email.
    For wait_and_remind: logs the reminder.
    For escalate / dismiss / no_action: just marks as executed.
    """
    result = await db.execute(
        select(EmailClassification)
        .options(
            selectinload(EmailClassification.synced_email),
            selectinload(EmailClassification.case)
            .selectinload(Case.opposing_party),
            selectinload(EmailClassification.case)
            .selectinload(Case.client),
        )
        .where(
            EmailClassification.id == classification_id,
            EmailClassification.tenant_id == tenant_id,
            EmailClassification.status == ClassificationStatus.APPROVED,
        )
    )
    classification = result.scalar_one_or_none()
    if not classification:
        return None

    action = classification.suggested_action
    case = classification.case
    email = classification.synced_email
    execution_notes = []

    try:
        if action in ("send_template", "request_proof"):
            template_key = classification.suggested_template_key
            if not template_key:
                execution_notes.append("Geen template geselecteerd")
            elif not email:
                execution_notes.append(
                    "Geen email gekoppeld aan classificatie"
                )
            elif not case:
                execution_notes.append(
                    "Geen zaak gekoppeld aan classificatie"
                )
            else:
                # Find the template
                tmpl_result = await db.execute(
                    select(ResponseTemplate).where(
                        ResponseTemplate.tenant_id == tenant_id,
                        ResponseTemplate.key == template_key,
                        ResponseTemplate.is_active.is_(True),
                    )
                )
                template = tmpl_result.scalar_one_or_none()
                if not template:
                    execution_notes.append(
                        f"Template '{template_key}' niet gevonden"
                    )
                else:
                    # Get tenant for kantoor context
                    tenant_result = await db.execute(
                        select(Tenant).where(Tenant.id == tenant_id)
                    )
                    tenant = tenant_result.scalar_one_or_none()

                    # Build Jinja2 context
                    wederpartij_naam = (
                        case.opposing_party.name
                        if case.opposing_party
                        else email.from_name or email.from_email
                    )
                    tmpl_context = {
                        "zaak": {"zaaknummer": case.case_number},
                        "wederpartij": {"naam": wederpartij_naam},
                        "kantoor": {
                            "naam": tenant.name if tenant else "",
                        },
                    }

                    # Render subject and body (sandboxed to prevent SSTI)
                    subject = _jinja_env.from_string(
                        template.subject_template
                    ).render(tmpl_context)
                    body_text = _jinja_env.from_string(
                        template.body_template
                    ).render(tmpl_context)
                    import html as _html
                    body_html = _html.escape(body_text).replace("\n", "<br>")

                    # Send via email provider / SMTP
                    email_log = await send_with_attachment(
                        db,
                        user_id,
                        tenant_id,
                        to=email.from_email,
                        subject=subject,
                        body_html=body_html,
                        attachments=[],
                        case_id=case.id,
                        recipient_name=wederpartij_naam,
                        sender_name=(
                            tenant.name if tenant else ""
                        ),
                    )

                    if email_log.status == "sent":
                        execution_notes.append(
                            f"Template '{template.name}' verzonden"
                            f" naar {email.from_email}"
                        )
                    else:
                        execution_notes.append(
                            f"Verzending mislukt:"
                            f" {email_log.error_message}"
                        )

        elif action == "wait_and_remind":
            days = classification.suggested_reminder_days or 7
            reminder_date = date.today() + timedelta(days=days)
            if case:
                task = WorkflowTask(
                    tenant_id=tenant_id,
                    case_id=case.id,
                    assigned_to_id=user_id,
                    task_type="check_payment",
                    title=(
                        f"Herinnering: opvolging email"
                        f" — {case.case_number}"
                    ),
                    description=(
                        f"Automatisch aangemaakt door AI classificatie.\n"
                        f"Email van: {email.from_email if email else 'onbekend'}\n"
                        f"Onderwerp: {email.subject if email else 'onbekend'}\n"
                        f"Categorie: {CATEGORY_LABELS.get(
                            classification.category,
                            classification.category,
                        )}"
                    ),
                    due_date=reminder_date,
                    status="pending",
                    action_config={
                        "source": "ai_classification",
                        "classification_id": str(classification.id),
                    },
                )
                db.add(task)
            execution_notes.append(
                f"Herinnering gepland over {days} dagen ({reminder_date})"
            )

        elif action == "escalate":
            if case:
                task = WorkflowTask(
                    tenant_id=tenant_id,
                    case_id=case.id,
                    assigned_to_id=user_id,
                    task_type="manual_review",
                    title=(
                        f"URGENT: Escalatie email beoordelen"
                        f" — {case.case_number}"
                    ),
                    description=(
                        f"Automatisch geëscaleerd door AI classificatie.\n"
                        f"Email van: {email.from_email if email else 'onbekend'}\n"
                        f"Onderwerp: {email.subject if email else 'onbekend'}\n"
                        f"Categorie: {CATEGORY_LABELS.get(
                            classification.category,
                            classification.category,
                        )}\n"
                        f"Reden: {classification.reasoning or 'niet opgegeven'}"
                    ),
                    due_date=date.today(),
                    status="pending",
                    action_config={
                        "source": "ai_classification",
                        "classification_id": str(classification.id),
                        "urgent": True,
                    },
                )
                db.add(task)
            execution_notes.append(
                "Geëscaleerd naar advocaat voor beoordeling"
            )

        elif action == "dismiss":
            if email:
                email.is_dismissed = True
            execution_notes.append("Email weggezet (niet relevant)")

        elif action == "no_action":
            execution_notes.append("Geen actie nodig")

        # Log case activity
        if case:
            category_label = CATEGORY_LABELS.get(
                classification.category, classification.category
            )
            action_label = ACTION_LABELS.get(action, action)
            activity = CaseActivity(
                tenant_id=tenant_id,
                case_id=case.id,
                user_id=user_id,
                activity_type="ai_action",
                title=f"AI actie uitgevoerd: {action_label}",
                description=(
                    f"Classificatie: {category_label}\n"
                    f"Resultaat: {'; '.join(execution_notes)}"
                ),
            )
            db.add(activity)

        classification.status = ClassificationStatus.EXECUTED
        classification.executed_at = datetime.now(UTC)
        classification.execution_result = "; ".join(execution_notes)

    except Exception as e:
        logger.error(
            "Execute classification %s failed: %s",
            classification_id, e,
        )
        classification.execution_result = f"Fout: {e}"

    await db.flush()
    return classification


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

async def get_classifications(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status: str | None = None,
    case_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[EmailClassification], int]:
    """Get classifications with optional filters, paginated."""
    query = (
        select(EmailClassification)
        .options(
            selectinload(EmailClassification.synced_email),
            selectinload(EmailClassification.case),
            selectinload(EmailClassification.reviewed_by),
        )
        .where(EmailClassification.tenant_id == tenant_id)
    )
    count_query = (
        select(func.count())
        .select_from(EmailClassification)
        .where(EmailClassification.tenant_id == tenant_id)
    )

    if status:
        query = query.where(EmailClassification.status == status)
        count_query = count_query.where(
            EmailClassification.status == status
        )
    if case_id:
        query = query.where(EmailClassification.case_id == case_id)
        count_query = count_query.where(
            EmailClassification.case_id == case_id
        )

    query = query.order_by(
        EmailClassification.created_at.desc()
    ).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    classifications = list(result.scalars().all())
    total = (await db.execute(count_query)).scalar() or 0

    return classifications, total


async def get_classification_by_id(
    db: AsyncSession,
    classification_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> EmailClassification | None:
    """Get a single classification by ID."""
    result = await db.execute(
        select(EmailClassification)
        .options(
            selectinload(EmailClassification.synced_email),
            selectinload(EmailClassification.case),
            selectinload(EmailClassification.reviewed_by),
        )
        .where(
            EmailClassification.id == classification_id,
            EmailClassification.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_classification_by_email(
    db: AsyncSession,
    synced_email_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> EmailClassification | None:
    """Get classification for a specific synced email."""
    result = await db.execute(
        select(EmailClassification)
        .options(
            selectinload(EmailClassification.synced_email),
            selectinload(EmailClassification.case),
            selectinload(EmailClassification.reviewed_by),
        )
        .where(
            EmailClassification.synced_email_id == synced_email_id,
            EmailClassification.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_pending_count(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Get number of pending classifications for a tenant."""
    result = await db.execute(
        select(func.count())
        .select_from(EmailClassification)
        .where(
            EmailClassification.tenant_id == tenant_id,
            EmailClassification.status == ClassificationStatus.PENDING,
        )
    )
    return result.scalar() or 0


async def get_templates(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[ResponseTemplate]:
    """Get all active response templates for a tenant."""
    result = await db.execute(
        select(ResponseTemplate)
        .where(
            ResponseTemplate.tenant_id == tenant_id,
            ResponseTemplate.is_active.is_(True),
        )
        .order_by(ResponseTemplate.sort_order, ResponseTemplate.name)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Seed default templates
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATES = [
    {
        "key": "bevestiging_betaalbelofte",
        "name": "Bevestiging betaalbelofte",
        "category": "belofte_tot_betaling",
        "subject_template": (
            "Bevestiging betaalafspraak — {{ zaak.zaaknummer }}"
        ),
        "body_template": (
            "Geachte {{ wederpartij.naam }},\n\n"
            "Wij bevestigen hierbij uw toezegging tot betaling "
            "inzake dossier {{ zaak.zaaknummer }}.\n\n"
            "Wij verzoeken u het openstaande bedrag binnen de "
            "afgesproken termijn te voldoen.\n\n"
            "Met vriendelijke groet,\n"
            "{{ kantoor.naam }}"
        ),
    },
    {
        "key": "ontvangst_betwisting",
        "name": "Ontvangstbevestiging betwisting",
        "category": "betwisting",
        "subject_template": (
            "Ontvangst uw reactie — {{ zaak.zaaknummer }}"
        ),
        "body_template": (
            "Geachte {{ wederpartij.naam }},\n\n"
            "Wij hebben uw reactie inzake dossier "
            "{{ zaak.zaaknummer }} in goede orde ontvangen.\n\n"
            "Uw betwisting wordt door onze advocaat beoordeeld. "
            "U ontvangt hierover nader bericht.\n\n"
            "Met vriendelijke groet,\n"
            "{{ kantoor.naam }}"
        ),
    },
    {
        "key": "ontvangst_regeling_verzoek",
        "name": "Ontvangstbevestiging betalingsregeling",
        "category": "betalingsregeling_verzoek",
        "subject_template": (
            "Ontvangst verzoek betalingsregeling — "
            "{{ zaak.zaaknummer }}"
        ),
        "body_template": (
            "Geachte {{ wederpartij.naam }},\n\n"
            "Wij hebben uw verzoek tot een betalingsregeling "
            "inzake dossier {{ zaak.zaaknummer }} ontvangen.\n\n"
            "Uw verzoek wordt beoordeeld. U ontvangt hierover "
            "zo spoedig mogelijk bericht.\n\n"
            "Met vriendelijke groet,\n"
            "{{ kantoor.naam }}"
        ),
    },
    {
        "key": "verzoek_betalingsbewijs",
        "name": "Verzoek betalingsbewijs",
        "category": "beweert_betaald",
        "subject_template": (
            "Verzoek betalingsbewijs — {{ zaak.zaaknummer }}"
        ),
        "body_template": (
            "Geachte {{ wederpartij.naam }},\n\n"
            "U geeft aan reeds betaald te hebben inzake dossier "
            "{{ zaak.zaaknummer }}. Wij hebben deze betaling "
            "helaas nog niet ontvangen.\n\n"
            "Wij verzoeken u vriendelijk om een betalingsbewijs "
            "(bankafschrift of transactiebevestiging) te "
            "overleggen zodat wij dit kunnen verifiëren.\n\n"
            "Met vriendelijke groet,\n"
            "{{ kantoor.naam }}"
        ),
    },
    {
        "key": "ontvangst_onvermogen",
        "name": "Ontvangstbevestiging onvermogen",
        "category": "onvermogen",
        "subject_template": (
            "Ontvangst uw bericht — {{ zaak.zaaknummer }}"
        ),
        "body_template": (
            "Geachte {{ wederpartij.naam }},\n\n"
            "Wij hebben uw bericht inzake dossier "
            "{{ zaak.zaaknummer }} ontvangen waarin u aangeeft "
            "niet in staat te zijn te betalen.\n\n"
            "Uw situatie wordt door onze advocaat beoordeeld. "
            "U ontvangt hierover nader bericht.\n\n"
            "Met vriendelijke groet,\n"
            "{{ kantoor.naam }}"
        ),
    },
    {
        "key": "doorverwijzing_advocaat",
        "name": "Doorverwijzing naar advocaat",
        "category": "juridisch_verweer",
        "subject_template": (
            "Uw juridische reactie — {{ zaak.zaaknummer }}"
        ),
        "body_template": (
            "Geachte {{ wederpartij.naam }},\n\n"
            "Wij hebben uw juridische reactie inzake dossier "
            "{{ zaak.zaaknummer }} ontvangen.\n\n"
            "Uw bericht is doorgestuurd naar onze behandelend "
            "advocaat. U ontvangt hierover zo spoedig mogelijk "
            "een inhoudelijke reactie.\n\n"
            "Met vriendelijke groet,\n"
            "{{ kantoor.naam }}"
        ),
    },
]


async def seed_default_templates(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Seed default response templates for a tenant. Idempotent.

    Returns the number of templates created (0 if all existed).
    """
    created = 0
    for tmpl_data in DEFAULT_TEMPLATES:
        existing = await db.execute(
            select(ResponseTemplate).where(
                ResponseTemplate.tenant_id == tenant_id,
                ResponseTemplate.key == tmpl_data["key"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        template = ResponseTemplate(
            tenant_id=tenant_id,
            key=tmpl_data["key"],
            name=tmpl_data["name"],
            category=tmpl_data["category"],
            subject_template=tmpl_data["subject_template"],
            body_template=tmpl_data["body_template"],
        )
        db.add(template)
        created += 1

    if created:
        await db.flush()
    return created
