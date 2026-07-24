"""AI Agent router — endpoints for email classification review and execution."""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.models import ACTION_LABELS, CATEGORY_LABELS
from app.ai_agent.schemas import (
    AIDraftResponse,
    AIDraftUpdateRequest,
    ClassificationApproveRequest,
    ClassificationResponse,
    PendingCountResponse,
    ResponseTemplateResponse,
)
from app.ai_agent.service import (
    approve_classification,
    classify_email,
    execute_classification,
    get_classification_by_email,
    get_classification_by_id,
    get_classifications,
    get_pending_count,
    get_templates,
    reject_classification,
    seed_default_templates,
)
from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/ai-agent", tags=["ai-agent"])

# Max upload size: 10 MB
_MAX_INVOICE_SIZE = 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# Invoice parsing
# ---------------------------------------------------------------------------


@router.post("/parse-invoice")
async def parse_invoice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Parse a PDF invoice using AI and return extracted fields with confidence."""
    # Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alleen PDF-bestanden zijn toegestaan",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > _MAX_INVOICE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestand is te groot (max 10 MB)",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestand is leeg",
        )

    from app.ai_agent.invoice_parser import parse_invoice_pdf

    try:
        result = await parse_invoice_pdf(content, file.filename or "invoice.pdf")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _classification_to_response(c) -> ClassificationResponse:
    """Convert an EmailClassification model to a ClassificationResponse."""
    email = c.synced_email
    case = c.case
    reviewer = c.reviewed_by

    return ClassificationResponse(
        id=c.id,
        synced_email_id=c.synced_email_id,
        case_id=c.case_id,
        case_number=case.case_number if case else "",
        email_subject=email.subject if email else "",
        email_from=email.from_email if email else "",
        email_date=email.email_date if email else c.created_at,
        category=c.category,
        category_label=CATEGORY_LABELS.get(c.category, c.category),
        confidence=c.confidence,
        reasoning=c.reasoning,
        sentiment=getattr(c, "sentiment", None),
        promise_date=c.promise_date,
        promise_amount=c.promise_amount,
        suggested_action=c.suggested_action,
        suggested_action_label=ACTION_LABELS.get(c.suggested_action, c.suggested_action),
        suggested_template_key=c.suggested_template_key,
        suggested_template_name=None,  # Populated separately if needed
        suggested_reminder_days=c.suggested_reminder_days,
        status=c.status,
        reviewed_by_name=(reviewer.full_name if reviewer else None),
        reviewed_at=c.reviewed_at,
        review_note=c.review_note,
        executed_at=c.executed_at,
        execution_result=c.execution_result,
        created_at=c.created_at,
    )


# ---------------------------------------------------------------------------
# List / Get endpoints
# ---------------------------------------------------------------------------


@router.get("/classifications", response_model=list[ClassificationResponse])
async def list_classifications(
    status_filter: str | None = Query(default=None, alias="status"),
    case_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List email classifications with optional filters."""
    classifications, total = await get_classifications(
        db,
        current_user.tenant_id,
        status=status_filter,
        case_id=case_id,
        page=page,
        per_page=per_page,
    )
    return [_classification_to_response(c) for c in classifications]


@router.get(
    "/classifications/{classification_id}",
    response_model=ClassificationResponse,
)
async def get_classification(
    classification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single classification by ID."""
    c = await get_classification_by_id(db, classification_id, current_user.tenant_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classificatie niet gevonden",
        )
    return _classification_to_response(c)


@router.get(
    "/email/{synced_email_id}/classification",
    response_model=ClassificationResponse | None,
)
async def get_email_classification(
    synced_email_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the classification for a specific synced email (if any)."""
    c = await get_classification_by_email(db, synced_email_id, current_user.tenant_id)
    if not c:
        return None
    return _classification_to_response(c)


@router.get("/pending-count", response_model=PendingCountResponse)
async def pending_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get number of pending classifications for the current tenant."""
    count = await get_pending_count(db, current_user.tenant_id)
    return PendingCountResponse(count=count)


@router.get("/templates", response_model=list[ResponseTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active response templates."""
    templates = await get_templates(db, current_user.tenant_id)
    return templates


# ---------------------------------------------------------------------------
# Action endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/classify/{synced_email_id}",
    response_model=ClassificationResponse | None,
)
async def classify_single_email(
    synced_email_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger classification for a specific email."""
    c = await classify_email(db, synced_email_id, current_user.tenant_id)
    if not c:
        return None
    await db.commit()
    # Refresh to load relationships
    refreshed = await get_classification_by_id(db, c.id, current_user.tenant_id)
    return _classification_to_response(refreshed) if refreshed else None


@router.post(
    "/classifications/{classification_id}/approve",
    response_model=ClassificationResponse,
)
async def approve(
    classification_id: uuid.UUID,
    body: ClassificationApproveRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending classification."""
    note = body.note if body else None
    c = await approve_classification(
        db, classification_id, current_user.tenant_id, current_user.id, note
    )
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classificatie niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    refreshed = await get_classification_by_id(db, c.id, current_user.tenant_id)
    return _classification_to_response(refreshed)


@router.post(
    "/classifications/{classification_id}/reject",
    response_model=ClassificationResponse,
)
async def reject(
    classification_id: uuid.UUID,
    body: ClassificationApproveRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending classification."""
    note = body.note if body else None
    c = await reject_classification(
        db, classification_id, current_user.tenant_id, current_user.id, note
    )
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classificatie niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    refreshed = await get_classification_by_id(db, c.id, current_user.tenant_id)
    return _classification_to_response(refreshed)


@router.post(
    "/classifications/{classification_id}/execute",
    response_model=ClassificationResponse,
)
async def execute(
    classification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an approved classification action."""
    c = await execute_classification(db, classification_id, current_user.tenant_id, current_user.id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classificatie niet gevonden of niet in status 'approved'",
        )
    await db.commit()
    refreshed = await get_classification_by_id(db, c.id, current_user.tenant_id)
    return _classification_to_response(refreshed)


@router.post(
    "/classifications/{classification_id}/approve-and-execute",
    response_model=ClassificationResponse,
)
async def approve_and_execute(
    classification_id: uuid.UUID,
    body: ClassificationApproveRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve and immediately execute a classification in one step."""
    note = body.note if body else None
    c = await approve_classification(
        db, classification_id, current_user.tenant_id, current_user.id, note
    )
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classificatie niet gevonden of niet in status 'pending'",
        )
    c = await execute_classification(db, classification_id, current_user.tenant_id, current_user.id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Classificatie goedgekeurd maar uitvoeren mislukt",
        )
    await db.commit()
    refreshed = await get_classification_by_id(db, c.id, current_user.tenant_id)
    return _classification_to_response(refreshed)


# ---------------------------------------------------------------------------
# Client update draft (AUDIT-22)
# ---------------------------------------------------------------------------


@router.post("/client-update/{case_id}")
async def generate_client_update_draft(
    case_id: uuid.UUID,
    trigger: str = Query(default="status_change", pattern="^(payment|status_change)$"),
    details: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI draft update email to the client (opdrachtgever).

    Trigger types:
    - payment: notification that a payment was received
    - status_change: notification that the case status changed
    """
    from app.ai_agent.draft_service import generate_client_update

    return await generate_client_update(
        db, current_user.tenant_id, case_id, trigger, details
    )


# ---------------------------------------------------------------------------
# Seed templates
# ---------------------------------------------------------------------------


@router.post(
    "/templates/seed",
    status_code=status.HTTP_201_CREATED,
)
async def seed_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seed default response templates for the current tenant. Idempotent."""
    created = await seed_default_templates(db, current_user.tenant_id)
    await db.commit()
    return {"created": created}


# ── AI-UX-09/13/14: Draft read endpoints ────────────────────────────────────


def _draft_to_response(d) -> AIDraftResponse:
    """Convert an AIDraft model to an AIDraftResponse."""
    return AIDraftResponse(
        id=d.id,
        case_id=d.case_id,
        case_number=d.case.case_number if d.case else "",
        classification_id=d.classification_id,
        subject=d.subject,
        body=d.body,
        body_html=d.body_html,
        tone=d.tone,
        sources=d.sources,
        reasoning=d.reasoning,
        status=d.status,
        generated_at=d.generated_at,
        reviewed_at=d.reviewed_at,
        reviewed_by_name=(d.reviewed_by.full_name if d.reviewed_by else None),
        sent_at=d.sent_at,
        model_used=d.model_used,
        instruction=d.instruction,
        attach_invoices=bool(getattr(d, "attach_invoices", False)),
        created_at=d.created_at,
    )


# CLEAN-AI-01 (S148): POST /draft/{case_id} verwijderd — vervangen door
# POST /api/ai/draft (UnifiedDraftService). De automatische draft-generatie loopt
# via generate_and_persist_draft (ai_agent/orchestrator.py) die AIDraft persisteert
# en de ai_draft_ready notificatie voor de CaseActionFeed afvuurt.


@router.get("/drafts/case/{case_id}", response_model=list[AIDraftResponse])
async def list_drafts_for_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all AI drafts for a case, newest first."""
    from app.ai_agent.draft_service import get_drafts_for_case

    drafts = await get_drafts_for_case(db, current_user.tenant_id, case_id)
    return [_draft_to_response(d) for d in drafts]


@router.get("/drafts/{draft_id}", response_model=AIDraftResponse)
async def get_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single AI draft by ID."""
    from app.ai_agent.draft_service import get_draft_by_id

    draft = await get_draft_by_id(db, current_user.tenant_id, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Concept niet gevonden")
    return _draft_to_response(draft)


@router.patch("/drafts/{draft_id}", response_model=AIDraftResponse)
async def update_draft(
    draft_id: uuid.UUID,
    data: AIDraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a draft's status (approve, discard, mark as sent)."""
    from app.ai_agent.draft_service import update_draft_status

    if not data.status:
        raise HTTPException(status_code=400, detail="Status is verplicht")

    draft = await update_draft_status(
        db, current_user.tenant_id, draft_id, data.status, current_user.id
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Concept niet gevonden")
    await db.commit()
    return _draft_to_response(draft)


# CLEAN-AI-01 (S148): GET /classifications/{id}/smart-replies + smart_reply_service
# verwijderd. Reageren op een geclassificeerde mail loopt nu via de CaseActionFeed
# ClassificationDoneCard ('Antwoord opstellen' CTA) → Correspondentie.


# ---------------------------------------------------------------------------
# Shadow-learning (S168): leren van de eigen verzonden antwoorden
# ---------------------------------------------------------------------------


@router.post("/learning/backfill")
async def learning_backfill(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Vul de leer-voorbeelden uit bestaande verzonden antwoorden (idempotent).

    Eenmalig + periodiek te draaien zodat de agent leert van het echte werk. Geeft
    het aantal NIEUW toegevoegde voorbeelden terug.
    """
    from app.ai_agent.learned_answers import backfill_learned_answers

    added = await backfill_learned_answers(db, current_user.tenant_id)
    await db.commit()
    return {"added": added}


@router.get("/learning/stats")
async def learning_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Kwaliteits-dashboard: edit-rate (AI-versie vs. verzonden) + leer-statistieken."""
    from app.ai_agent.learned_answers import get_learning_stats

    return await get_learning_stats(db, current_user.tenant_id)


class ApproveCandidateRequest(BaseModel):
    """Goedkeuring van een verweer-kandidaat: de bevestigde geanonimiseerde tekst."""

    anonymized_body: str
    defense_type: str | None = None


@router.get("/learning/candidates")
async def learning_candidates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Kandidaat-antwoorden die op beoordeling wachten (voor het 'Slim leren'-dashboard)."""
    from app.ai_agent.learned_answers import (
        candidates_source_context,
        list_candidates,
    )

    rows = await list_candidates(db, current_user.tenant_id)
    ctx = await candidates_source_context(db, current_user.tenant_id, rows)
    return [
        {
            "id": str(r.id),
            "category": r.category,
            "defense_type": r.defense_type,
            "body": r.body,
            "anonymized_body": r.anonymized_body,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            **ctx.get(r.id, {}),
        }
        for r in rows
    ]


@router.post("/learning/candidates/{candidate_id}/approve")
async def learning_approve_candidate(
    candidate_id: uuid.UUID,
    payload: ApproveCandidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Keur een kandidaat goed — pas hierna voedt de (geanonimiseerde) tekst de AI."""
    from app.ai_agent.learned_answers import approve_candidate

    row = await approve_candidate(
        db,
        current_user.tenant_id,
        candidate_id,
        anonymized_body=payload.anonymized_body,
        defense_type=payload.defense_type,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Kandidaat niet gevonden")
    await db.commit()
    return {"id": str(row.id), "status": row.status}


@router.post("/learning/candidates/{candidate_id}/reject")
async def learning_reject_candidate(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Wijs een kandidaat af — die voedt de AI nooit."""
    from app.ai_agent.learned_answers import reject_candidate

    ok = await reject_candidate(db, current_user.tenant_id, candidate_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Kandidaat niet gevonden")
    await db.commit()
    return {"ok": True}


class BulkCandidateRequest(BaseModel):
    """Bulk-actie: de id's van de kandidaten die in één keer verwerkt mogen worden."""

    ids: list[uuid.UUID]


@router.post("/learning/candidates/reject-bulk")
async def learning_reject_candidates_bulk(
    payload: BulkCandidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Wijs meerdere kandidaten tegelijk af (ruis in bulk opruimen)."""
    from app.ai_agent.learned_answers import reject_candidates_bulk

    rejected = await reject_candidates_bulk(db, current_user.tenant_id, payload.ids)
    await db.commit()
    return {"rejected": rejected}


@router.post("/learning/candidates/approve-bulk")
async def learning_approve_candidates_bulk(
    payload: BulkCandidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Keur meerdere kandidaten tegelijk goed — met hun eigen tekst + voor-gelabeld type."""
    from app.ai_agent.learned_answers import approve_candidates_bulk

    approved = await approve_candidates_bulk(db, current_user.tenant_id, payload.ids)
    await db.commit()
    return {"approved": approved}


# ── Juridische kennisregels (S248) — curated kennis met harde toepasbaarheids-poort ──


class KnowledgeRuleRequest(BaseModel):
    """Een juridische kennisregel (aanmaken of bewerken)."""

    defense_type: str
    applies_to: str
    title: str
    rebuttal_body: str
    claim_description: str | None = None
    legal_basis: str | None = None


def _serialize_rule(r) -> dict:
    return {
        "id": str(r.id),
        "defense_type": r.defense_type,
        "applies_to": r.applies_to,
        "title": r.title,
        "claim_description": r.claim_description,
        "rebuttal_body": r.rebuttal_body,
        "legal_basis": r.legal_basis,
        "status": r.status,
        "is_active": r.is_active,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/learning/rules")
async def learning_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alle juridische kennisregels (kandidaat + goedgekeurd + afgewezen)."""
    from app.ai_agent.knowledge_rules import list_rules

    rows = await list_rules(db, current_user.tenant_id)
    return [_serialize_rule(r) for r in rows]


@router.post("/learning/rules")
async def learning_create_rule(
    payload: KnowledgeRuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Maak een nieuwe kennisregel aan (als kandidaat — voedt de AI pas na goedkeuring)."""
    from app.ai_agent.knowledge_rules import create_rule, validate_rule_fields

    err = validate_rule_fields(
        defense_type=payload.defense_type,
        applies_to=payload.applies_to,
        title=payload.title,
        rebuttal_body=payload.rebuttal_body,
    )
    if err:
        raise HTTPException(status_code=422, detail=err)
    row = await create_rule(
        db,
        current_user.tenant_id,
        defense_type=payload.defense_type,
        applies_to=payload.applies_to,
        title=payload.title,
        rebuttal_body=payload.rebuttal_body,
        claim_description=payload.claim_description,
        legal_basis=payload.legal_basis,
    )
    await db.commit()
    return _serialize_rule(row)


@router.put("/learning/rules/{rule_id}")
async def learning_update_rule(
    rule_id: uuid.UUID,
    payload: KnowledgeRuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bewerk de inhoud van een kennisregel (raakt de goedkeur-status niet)."""
    from app.ai_agent.knowledge_rules import update_rule, validate_rule_fields

    err = validate_rule_fields(
        defense_type=payload.defense_type,
        applies_to=payload.applies_to,
        title=payload.title,
        rebuttal_body=payload.rebuttal_body,
    )
    if err:
        raise HTTPException(status_code=422, detail=err)
    row = await update_rule(
        db,
        current_user.tenant_id,
        rule_id,
        defense_type=payload.defense_type,
        applies_to=payload.applies_to,
        title=payload.title,
        rebuttal_body=payload.rebuttal_body,
        claim_description=payload.claim_description,
        legal_basis=payload.legal_basis,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Kennisregel niet gevonden")
    await db.commit()
    return _serialize_rule(row)


@router.post("/learning/rules/{rule_id}/approve")
async def learning_approve_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Keur een kennisregel goed — pas hierna gebruikt de AI hem."""
    from app.ai_agent.knowledge_rules import approve_rule

    row = await approve_rule(db, current_user.tenant_id, rule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Kennisregel niet gevonden")
    await db.commit()
    return {"id": str(row.id), "status": row.status}


@router.post("/learning/rules/{rule_id}/reject")
async def learning_reject_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Wijs een kennisregel af / trek een goedkeuring in — voedt de AI nooit meer."""
    from app.ai_agent.knowledge_rules import reject_rule

    ok = await reject_rule(db, current_user.tenant_id, rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Kennisregel niet gevonden")
    await db.commit()
    return {"ok": True}


@router.delete("/learning/rules/{rule_id}")
async def learning_delete_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verwijder een kennisregel definitief."""
    from app.ai_agent.knowledge_rules import delete_rule

    ok = await delete_rule(db, current_user.tenant_id, rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Kennisregel niet gevonden")
    await db.commit()
    return {"ok": True}
