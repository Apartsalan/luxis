"""Email module schemas — request/response models for email endpoints."""

from pydantic import BaseModel, Field


class SendCaseEmailRequest(BaseModel):
    """Request body for sending a freestanding email from a case."""

    recipient_email: str = Field(
        ...,
        max_length=320,
        description="E-mailadres van de ontvanger",
    )
    recipient_name: str | None = Field(
        default=None,
        max_length=200,
        description="Naam van de ontvanger (voor aanhef)",
    )
    cc: list[str] | None = Field(
        default=None,
        description="Lijst van CC e-mailadressen",
    )
    subject: str = Field(
        ...,
        max_length=500,
        description="Onderwerp van de e-mail",
    )
    body: str = Field(
        ...,
        max_length=50000,
        description="Inhoud van de e-mail (platte tekst, wordt omgezet naar HTML)",
    )


class SendCaseEmailResponse(BaseModel):
    """Response after sending a freestanding email."""

    email_log_id: str
    recipient: str
    subject: str
    status: str
