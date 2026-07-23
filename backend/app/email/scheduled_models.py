"""ScheduledEmail model — de wachtrij achter 'Verstuur later' (S246).

Lisanne werkt 's avonds maar incassomail hoort op nette tijden de deur uit. Een
geplande mail gaat NIET nu weg maar belandt hier; de minuut-bezorger
(`app.email.scheduled_service.send_due_scheduled_emails`) draait op het geplande
moment exact dezelfde verzendfunctie als de knop `Versturen` — zelfde afzender,
opmaak, bijlagen, vastlegging en doorschuiven.

De volledige verzendopdracht staat als JSON in `payload` (een `ComposeRequest`).
Bewust de RUWE opdracht, niet het uitgewerkte resultaat: bijlagen worden pas op
het verzendmoment van schijf gehaald en het renteoverzicht pas dan gebouwd — net
als bij een directe verzending.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import TenantBase

# Statussen. 'sending' is de claim-status: de bezorger zet hem vóór de
# provider-aanroep, zodat een tweede bezorger dezelfde rij nooit oppakt.
STATUS_PENDING = "pending"
STATUS_SENDING = "sending"
STATUS_SENT = "sent"
STATUS_CANCELLED = "cancelled"
STATUS_FAILED = "failed"


class ScheduledEmail(TenantBase):
    """Eén ingeplande uitgaande mail."""

    __tablename__ = "scheduled_emails"

    # Wie hem inplande — krijgt de melding als de verzending mislukt.
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    # Dossier (optioneel: een vrije mail hoeft geen dossier te hebben).
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True, index=True
    )

    # Wanneer hij weg moet. ALTIJD in UTC opgeslagen; de voorkant rekent om naar
    # Nederlandse tijd (en terug bij het inplannen).
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=STATUS_PENDING, index=True
    )

    # De volledige ComposeRequest als JSON — de bezorger bouwt hem hieruit terug.
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Uitgelicht voor de lijstweergave, zodat die niet door de payload hoeft.
    subject: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    recipients: Mapped[str] = mapped_column(String(1000), nullable=False, default="")

    # AI-concept-nazorg (concept afvinken + review-taak sluiten + stap door).
    # Mag pas draaien als de mail ÉCHT weg is — daarom hier bewaard i.p.v.
    # direct bij het inplannen uitgevoerd.
    advance_draft_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    # Pogingen + laatste fout. Bewust GEEN automatische herhaling: een incassomail
    # twee keer versturen is erger dan een dag te laat. Bij een fout: status
    # 'failed' + melding, en een mens beslist.
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Wanneer de bezorger hem claimde resp. daadwerkelijk verstuurde.
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
