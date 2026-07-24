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

from app.ai_agent.defense_library import (
    format_examples_for_prompt,
    get_relevant_examples,
)
from app.ai_agent.kimi_client import CLAUDE_SONNET_MODEL, call_intake_ai
from app.ai_agent.models import AIDraft, DraftStatus
from app.ai_agent.pdf_extract import extract_text_from_pdf
from app.cases.files_service import get_file_path
from app.cases.models import Case, CaseFile, CaseParty
from app.collections.models import Claim, Payment
from app.email.synced_email_models import SyncedEmail
from app.invoices.models import Invoice

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
6. Verweer-bibliotheek — voorbeeldreacties op veelvoorkomende verweren van debiteuren. \
Gebruik deze als INSPIRATIE voor toon, structuur en juridische argumentatie. \
Kopieer niet letterlijk, maar pas aan op de specifieke feiten van dit dossier.

REGELS:
- Schrijf formeel maar toegankelijk Nederlands
- Verwijs naar SPECIFIEKE feiten uit de bronnen: factuurnummers, bedragen, data, artikelen uit AV, clausules uit overeenkomsten
- Als de overeenkomst (Documenten op dossier) een specifieke clausule bevat die relevant is voor deze brief, citeer die letterlijk en noem de clausule
- Verwijs naar relevante wetsartikelen waar van toepassing (art. 6:96 BW voor incassokosten, art. 6:119/119a BW voor rente)
- Eindig met een duidelijke call-to-action (betalen, reageren, bewijsstuk sturen)
- GEEN slotgroet of ondertekening — de verzendlaag voegt de kantoor-handtekening toe
  (S227: de oude instructie "Met vriendelijke groet, Kesting Legal" gaf een dubbele
  slotgroet zodra de aankleding "Hoogachtend, ..." erachter plakte)
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

# Schema hoort 1-op-1 bij de JSON-instructie in DRAFT_SYSTEM_PROMPT hierboven —
# wijzig je de prompt-velden, wijzig dan dit schema mee (S238-huisregel).
CASE_DRAFT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "tone": {"type": "string", "enum": ["formeel", "vriendelijk", "streng"]},
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["email", "factuur", "av", "overeenkomst", "wet"],
                    },
                    "reference": {"type": "string"},
                },
                "required": ["type", "reference"],
                "additionalProperties": False,
            },
        },
        "reasoning": {"type": "string"},
    },
    "required": ["subject", "body", "tone", "sources", "reasoning"],
    "additionalProperties": False,
}


def _serialize_decimal(v: Decimal | float | int | None) -> str | None:
    if v is None:
        return None
    return f"{float(v):.2f}"


async def _gather_case_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    audience: str = "debtor",
) -> dict:
    """Gather full case context for AI draft generation.

    `audience` bepaalt of de debiteur-gerichte kennislaag mee mag: "debtor" (default) =
    volledige context incl. verweer-bibliotheek + geleerde voorbeelden; "client" = update
    aan de OPDRACHTGEVER, waarbij die twee worden overgeslagen (ze spreken de debiteur aan).
    """
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

    # Client AV (terms) — S173: via de gedeelde resolver (geversioneerde ContactTerms),
    # niet meer de sinds S168 lege legacy `terms_file_path`-kolom. Zelfde AV die het
    # incasso-pad al gebruikte, zodat dit pad dezelfde spelregels ziet.
    from app.ai_agent.knowledge_context import resolve_case_terms

    terms_text_full, _ = await resolve_case_terms(db, tenant_id, case)
    terms_text = terms_text_full or ""

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
    max_files = 5
    max_chars_per_file = 2000
    for cf in case_files[:max_files]:
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
                    "excerpt": text[:max_chars_per_file],
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

    # DF120-10 / S174: categorie + verweer-type van de LAATSTE inkomende mail (gedeelde
    # helper) — bepaalt of de verweer-bibliotheek + geleerde voorbeelden meegaan en welk
    # type voorrang krijgt. Op `email_date`, niet op `EmailClassification.created_at`
    # (onbetrouwbaar na de BaseNet-import), en alleen de allernieuwste inkomende mail telt
    # (was hier de created_at-bug uit de S173-review).
    from app.ai_agent.knowledge_context import last_inbound_defense

    last_classification_category, last_defense_type = await last_inbound_defense(
        db, tenant_id, case_id
    )

    # Build context dict
    context = {
        "case_number": case.case_number,
        "status": case.status,
        "case_type": case.case_type,
        "debtor_type": case.debtor_type,
        "description": case.description,
        "last_classification_category": last_classification_category,
        "opposing_party": None,
        "client": None,
        "emails": [],
        "claims": [],
        "payments": [],
        "total_principal": _serialize_decimal(
            sum((c.principal_amount for c in claims), Decimal("0"))
        ),
        "total_paid": _serialize_decimal(sum((p.amount for p in payments), Decimal("0"))),
        "terms_text": terms_text or None,
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

    # Shadow-learning: haal Lisanne's eigen eerdere antwoorden in deze categorie op en
    # zet ze klaar voor de prompt (naast de hand-bibliotheek). Lege string als er nog
    # geen voorbeelden zijn → de prompt valt dan terug op de hand-bibliotheek.
    # S174: bij een update aan de OPDRACHTGEVER (audience="client") overslaan — die
    # voorbeelden zijn debiteur-gericht ("U heeft gesteld…"); ze horen niet in een uitleg
    # aan de cliënt en zouden anders ook use_count onterecht ophogen.
    if audience == "client":
        context["learned_examples_text"] = ""
        context["knowledge_rules_text"] = ""
    else:
        from app.ai_agent.knowledge_rules import build_knowledge_rules_text
        from app.ai_agent.learned_answers import build_learned_examples_text

        context["learned_examples_text"] = await build_learned_examples_text(
            db,
            tenant_id,
            context.get("last_classification_category"),
            defense_type=last_defense_type,
        )
        # Curated kennisregels (S248) — harde poort tegen debtor_type in de service.
        context["knowledge_rules_text"] = await build_knowledge_rules_text(
            db, tenant_id, last_defense_type, context.get("debtor_type"),
        )

    return context


def _build_draft_prompt(
    context: dict, instruction: str | None = None, audience: str = "debtor"
) -> str:
    """Build the user message for draft generation.

    `audience="client"` laat de debiteur-gerichte verweer-bibliotheek weg (de geleerde
    voorbeelden zitten dan al niet in de context, zie `_gather_case_context`).
    """
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
        parts.append("\n--- Algemene Voorwaarden cliënt ---")
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

    # DF120-10: Defense library — add relevant examples for verweer/betwisting.
    # Bij een update aan de opdrachtgever (audience="client") overslaan: die voorbeelden
    # zijn debiteur-gericht en horen niet in een cliënt-uitleg (S174).
    category = context.get("last_classification_category")
    if audience != "client" and category in ("juridisch_verweer", "betwisting"):
        examples = get_relevant_examples(category=category)
        defense_text = format_examples_for_prompt(examples)
        if defense_text:
            parts.append(f"\n{defense_text}")

    # Shadow-learning: Lisanne's eigen eerdere antwoorden (in deze categorie),
    # klaargezet in de context door _gather_case_context. Komt NAAST de
    # hand-bibliotheek — die blijft de basis zolang er weinig geleerde voorbeelden zijn.
    learned_text = context.get("learned_examples_text")
    if learned_text:
        parts.append(f"\n{learned_text}")

    # Curated juridische kennisregels (S248) — al gefilterd op verweer-type + debtor_type
    # in _gather_case_context (leeg bij audience="client" of geen toepasbare regel).
    knowledge_rules_text = context.get("knowledge_rules_text")
    if knowledge_rules_text:
        parts.append(f"\n{knowledge_rules_text}")

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
    audience: str = "debtor",
) -> dict:
    """Generate an AI draft email for a case.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        case_id: Case UUID
        instruction: Optional user instruction for the AI
        audience: "debtor" (default, volledige verweer-context) of "client" (update aan de
            opdrachtgever — verweer-bibliotheek + geleerde voorbeelden worden overgeslagen)

    Returns:
        Dict with subject, body, tone, sources, reasoning
    """
    context = await _gather_case_context(db, tenant_id, case_id, audience=audience)
    user_message = _build_draft_prompt(context, instruction, audience=audience)

    logger.info(
        "Generating AI draft for case %s (%d chars context)",
        context["case_number"],
        len(user_message),
    )

    result, model = await call_intake_ai(
        DRAFT_SYSTEM_PROMPT,
        user_message,
        schema=CASE_DRAFT_SCHEMA,
        purpose="compose_draft",
        model=CLAUDE_SONNET_MODEL,
    )

    logger.info("AI draft generated for %s via %s", context["case_number"], model)

    # S227 — zelfde wachter als de unified route: een eigen model-groet + de
    # aankleed-handtekening van de verzendlaag = dubbele slotgroet.
    from app.ai_agent.unified_draft_service import _strip_trailing_closing

    return {
        "subject": result.get("subject", ""),
        "body": _strip_trailing_closing((result.get("body") or "").strip()),
        "tone": result.get("tone", "formeel"),
        "sources": result.get("sources", []),
        "reasoning": result.get("reasoning", ""),
        "model": model,
        "case_number": context["case_number"],
    }


async def generate_and_persist_draft(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    instruction: str | None = None,
    classification_id: uuid.UUID | None = None,
) -> AIDraft:
    """Generate an AI draft and persist it in the database.

    Returns the saved AIDraft record. Idempotent per classification_id:
    if a draft already exists for the given classification, returns it.
    """
    if classification_id:
        existing = await db.execute(
            select(AIDraft).where(
                AIDraft.classification_id == classification_id,
                AIDraft.tenant_id == tenant_id,
            )
        )
        found = existing.scalar_one_or_none()
        if found:
            logger.info("Draft already exists for classification %s — skipping", classification_id)
            return found

    result = await generate_draft(db, tenant_id, case_id, instruction)

    draft = AIDraft(
        tenant_id=tenant_id,
        case_id=case_id,
        classification_id=classification_id,
        subject=result.get("subject", ""),
        body=result.get("body", ""),
        tone=result.get("tone", "formeel"),
        sources=result.get("sources"),
        reasoning=result.get("reasoning"),
        status=DraftStatus.GENERATED,
        model_used=result.get("model"),
        instruction=instruction,
    )
    db.add(draft)
    await db.flush()
    await db.refresh(draft)

    logger.info("Persisted AI draft %s for case %s", draft.id, result.get("case_number"))
    return draft


async def get_drafts_for_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[AIDraft]:
    """Get all drafts for a case, newest first."""
    result = await db.execute(
        select(AIDraft)
        .where(AIDraft.case_id == case_id, AIDraft.tenant_id == tenant_id)
        .order_by(AIDraft.generated_at.desc())
    )
    return list(result.scalars().all())


async def get_draft_by_id(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    draft_id: uuid.UUID,
) -> AIDraft | None:
    """Get a single draft by ID."""
    result = await db.execute(
        select(AIDraft).where(AIDraft.id == draft_id, AIDraft.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def update_draft_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    draft_id: uuid.UUID,
    new_status: str,
    user_id: uuid.UUID | None = None,
) -> AIDraft | None:
    """Update draft status (approve, discard, sent)."""
    from datetime import UTC, datetime

    draft = await get_draft_by_id(db, tenant_id, draft_id)
    if not draft:
        return None

    draft.status = new_status
    if new_status in (DraftStatus.REVIEWED, DraftStatus.APPROVED):
        draft.reviewed_at = datetime.now(UTC)
        draft.reviewed_by_id = user_id
    elif new_status == DraftStatus.SENT:
        draft.sent_at = datetime.now(UTC)
    elif new_status == DraftStatus.DISCARDED:
        # S239 (P3-uitbreiding): een vervallen concept laat geen open
        # nakijk-taak achter op de Taken-pagina.
        await skip_review_tasks_for_drafts(db, tenant_id, [draft.id])

    await db.flush()
    return draft


async def skip_review_tasks_for_drafts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    draft_ids: list[uuid.UUID],
) -> int:
    """S239: sluit open nakijk-taken ('review_ai_draft') van vervallen concepten.

    Gedeeld door ALLE routes waar een concept DISCARDED wordt (handmatig
    weggooien, zaak sluiten, stap-wissel-opruiming). Zonder dit bleef de
    gespiegelde taak eeuwig open staan (8 spooktaken gemeten op prod, S239).
    Taakstatus wordt 'skipped' — zelfde semantiek als een afgewezen advies.
    """
    if not draft_ids:
        return 0
    from datetime import UTC, datetime

    from app.workflow.models import WorkflowTask

    # ponytail: alle open review-taken van de tenant scannen en op draft_id
    # filteren in Python — het zijn er hooguit tientallen; een JSON-query
    # per dialect is de complexiteit niet waard.
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.task_type == "review_ai_draft",
            WorkflowTask.status.in_(["pending", "due", "overdue"]),
        )
    )
    wanted = {str(d) for d in draft_ids}
    skipped = 0
    for task in result.scalars().all():
        if (task.action_config or {}).get("draft_id") in wanted:
            task.status = "skipped"
            task.completed_at = datetime.now(UTC)
            skipped += 1
    if skipped:
        await db.flush()
    return skipped


# Concepten die nog niet zijn verstuurd of weggegooid tellen als "open".
_OPEN_DRAFT_STATUSES = (
    DraftStatus.GENERATED,
    DraftStatus.REVIEWED,
    DraftStatus.APPROVED,
)


async def discard_open_drafts_on_close(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> int:
    """Zaak sluiten (betaald/afgesloten) → ELK open AI-concept vervalt (S223, P3).

    Een gesloten zaak mag geen concept laten staan dat later per ongeluk verstuurd
    wordt (IN100613 hield na sluiten 2 open concepten). Anders dan de stap-wissel-
    opruiming (`discard_stale_step_drafts`, alleen intent 'next_step' van een oude
    stap) raakt dit álle intents — ook antwoorden en vrij opgestelde concepten.
    Gedeeld door alle sluit-routes (handmatig, pijplijn-eindstap, betaling-hook).
    Retourneert het aantal weggegooide concepten.
    """
    result = await db.execute(
        select(AIDraft).where(
            AIDraft.tenant_id == tenant_id,
            AIDraft.case_id == case_id,
            AIDraft.status.in_(_OPEN_DRAFT_STATUSES),
        )
    )
    drafts = result.scalars().all()
    for draft in drafts:
        draft.status = DraftStatus.DISCARDED
    if drafts:
        # S239: nakijk-taken van deze concepten mee sluiten (P3-uitbreiding).
        await skip_review_tasks_for_drafts(db, tenant_id, [d.id for d in drafts])
        await db.flush()
    return len(drafts)


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
    # audience="client": dit bericht gaat naar de OPDRACHTGEVER, dus geen debiteur-gerichte
    # verweer-bibliotheek/geleerde voorbeelden meesturen (S174).
    return await generate_draft(db, tenant_id, case_id, instruction, audience="client")
