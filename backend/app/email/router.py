"""Email module router — test endpoint, email utilities, and freestanding email sending."""

import logging
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case, CaseActivity
from app.database import get_db
from app.dependencies import get_current_user
from app.email.models import EmailLog
from app.email.schemas import SendCaseEmailRequest, SendCaseEmailResponse
from app.email.service import is_configured, send_email
from app.email.templates import _render_base
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


class TestEmailRequest(BaseModel):
    recipient_email: str = Field(
        ...,
        max_length=320,
        description="E-mailadres om de test e-mail naartoe te sturen",
    )


class TestEmailResponse(BaseModel):
    success: bool
    message: str


class EmailStatusResponse(BaseModel):
    configured: bool


@router.get("/status", response_model=EmailStatusResponse)
async def get_email_status(
    user: User = Depends(get_current_user),
) -> EmailStatusResponse:
    """Check if SMTP email is configured."""
    return EmailStatusResponse(configured=is_configured())


@router.post("/test", response_model=TestEmailResponse)
async def send_test_email(
    data: TestEmailRequest,
    user: User = Depends(get_current_user),
) -> TestEmailResponse:
    """Send a test email to verify SMTP configuration."""
    if not is_configured():
        return TestEmailResponse(
            success=False,
            message="SMTP is niet geconfigureerd. Stel SMTP_HOST en SMTP_FROM in via de server.",
        )

    kantoor = {"naam": "Luxis", "adres": "", "postcode_stad": ""}
    content_html = (
        "<p>Dit is een test e-mail vanuit Luxis.</p>"
        "<p>Als u deze e-mail ontvangt, is de SMTP-configuratie correct.</p>"
    )
    html_body = _render_base(kantoor, content_html)

    try:
        await send_email(
            to=data.recipient_email,
            subject="Luxis — Test e-mail",
            html_body=html_body,
        )
        return TestEmailResponse(
            success=True,
            message=f"Test e-mail verzonden naar {data.recipient_email}",
        )
    except Exception as e:
        logger.error(f"Test e-mail mislukt: {e}")
        return TestEmailResponse(
            success=False,
            message=f"Verzending mislukt: {e}",
        )


# ── Freestanding Email from Case ─────────────────────────────────────────────


@router.post(
    "/cases/{case_id}/send",
    response_model=SendCaseEmailResponse,
)
async def send_case_email(
    case_id: uuid.UUID,
    data: SendCaseEmailRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a freestanding email from a case (no document attachment).

    Wraps the body in the standard HTML email template, sends via SMTP,
    creates an EmailLog entry, and logs a CaseActivity.
    """
    from app.documents.docx_service import load_tenant, _tenant_ctx

    if not is_configured():
        raise BadRequestError(
            "SMTP is niet geconfigureerd. Stel SMTP_HOST en SMTP_FROM in via de server."
        )

    # Verify case exists and belongs to tenant
    result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.tenant_id == user.tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    # Build HTML email
    tenant = await load_tenant(db, user.tenant_id)
    kantoor = _tenant_ctx(tenant)

    import html as _html
    body_html = _html.escape(data.body).replace("\n", "<br>")
    html_body = _render_base(kantoor, body_html)

    # Create email log
    email_log = EmailLog(
        tenant_id=user.tenant_id,
        case_id=case.id,
        document_id=None,
        template="freestanding",
        recipient=data.recipient_email,
        subject=data.subject,
        status="sent",
    )

    try:
        await send_email(
            to=data.recipient_email,
            subject=data.subject,
            html_body=html_body,
            cc=data.cc,
        )
    except Exception as e:
        email_log.status = "failed"
        email_log.error_message = str(e)
        logger.error(f"E-mail verzenden mislukt voor zaak {case_id}: {e}")

    db.add(email_log)
    await db.flush()
    await db.refresh(email_log)

    # Log activity on the case
    recipient_label = data.recipient_name or data.recipient_email
    activity = CaseActivity(
        tenant_id=user.tenant_id,
        case_id=case.id,
        user_id=user.id,
        activity_type="email",
        title=f"E-mail verzonden naar {recipient_label}",
        description=f"Onderwerp: {data.subject}",
    )
    db.add(activity)
    await db.flush()

    if email_log.status == "failed":
        raise BadRequestError(
            f"E-mail verzenden mislukt: {email_log.error_message}"
        )

    return SendCaseEmailResponse(
        email_log_id=str(email_log.id),
        recipient=email_log.recipient,
        subject=email_log.subject,
        status=email_log.status,
    )
