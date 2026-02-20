"""Email module router — test endpoint and email utilities."""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.models import User
from app.dependencies import get_current_user
from app.email.service import is_configured, send_email
from app.email.templates import _render_base

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
