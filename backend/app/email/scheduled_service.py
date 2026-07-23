"""Wachtrij-logica achter 'Verstuur later' (S246).

Inplannen, opsommen, annuleren en bezorgen. De bezorger draait op het geplande
moment `perform_compose_send` — exact dezelfde machine als de knop `Versturen` —
zodat afzender, opmaak, bijlagen, vastlegging, meldingen en doorschuiven identiek
zijn aan een directe verzending.

Twee harde keuzes:

* **Nooit dubbel versturen.** Een rij wordt eerst geclaimd (`pending` → `sending`
  in één voorwaardelijke UPDATE) en pas daarna verstuurd. Een tweede bezorger
  krijgt 0 rijen terug en laat hem staan.
* **Geen automatische herhaling.** Eén incassomail twee keer versturen is erger
  dan een dag te laat. Mislukt de verzending, dan status `failed` + een melding
  voor wie hem inplande; een mens beslist wat er gebeurt.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.email.scheduled_models import (
    STATUS_CANCELLED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_SENDING,
    STATUS_SENT,
    ScheduledEmail,
)
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

# Meldingstype bij een mislukte geplande verzending.
NOTIF_SCHEDULED_EMAIL_FAILED = "scheduled_email_failed"

# Een claim die zó lang blijft hangen, is een halverwege afgebroken run (herstart,
# stroomstoring). We weten dan NIET of de provider hem verstuurd heeft → nooit
# stilzwijgend opnieuw sturen, wel melden dat het onzeker is.
STUCK_CLAIM_MINUTES = 10

# Sanity-grens: verder dan een jaar vooruit plannen is bijna altijd een typefout.
MAX_SCHEDULE_AHEAD_DAYS = 365


def _as_utc(moment: datetime) -> datetime:
    """Maak het moment tijdzone-bewust in UTC.

    De voorkant stuurt een ISO-tijd mét zone (Nederlandse tijd omgerekend). Komt er
    tóch een kale tijd binnen (een API-aanroep buiten de app om), dan lezen we die
    als UTC — de server draait op UTC.
    """
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


async def schedule_compose_email(db: AsyncSession, user, data):
    """Zet een compose-mail in de wachtrij i.p.v. hem nu te versturen.

    Draait dezelfde wettelijke controle als een directe verzending, zodat Lisanne
    's avonds meteen hoort dat iets niet mag — niet pas de volgende ochtend.
    """
    from app.email.compose_router import ComposeResponse

    when = _as_utc(data.scheduled_at)
    now = datetime.now(UTC)
    if when <= now:
        raise BadRequestError(
            "Het gekozen verzendmoment ligt in het verleden. Kies een tijdstip in de toekomst."
        )
    if when > now + timedelta(days=MAX_SCHEDULE_AHEAD_DAYS):
        raise BadRequestError(
            f"Een mail kan maximaal {MAX_SCHEDULE_AHEAD_DAYS} dagen vooruit worden ingepland."
        )

    # Zelfde 14-dagenbrief-waarborg als het directe pad (art. 6:96 lid 6 BW): alleen
    # bij een VERSE dossier-mail. Hier alleen CONTROLEREN — het onuitwisbare spoor van
    # een 'toch versturen'-override hoort bij de échte verzending, niet bij het
    # inplannen (anders staat er een override op het dossier voor een mail die
    # misschien nooit weggaat).
    is_reply_or_forward = bool(data.reply_to_message_id or data.forward_from_email_id)
    if data.case_id and not is_reply_or_forward and not data.compliance_override:
        from app.collections.compliance import check_dagenbrief_gate_for_case

        gate_reason = await check_dagenbrief_gate_for_case(db, user.tenant_id, data.case_id)
        if gate_reason is not None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=422,
                detail={"code": "DAGENBRIEF_GATE", "message": gate_reason},
            )

    # De payload is de RUWE opdracht zonder het geplande moment: de bezorger draait
    # hem straks als een gewone directe verzending (anders zou hij zichzelf opnieuw
    # inplannen). advance_draft_id gaat apart mee als kolom, niet in de payload —
    # de nazorg is geen onderdeel van de verzending zelf.
    payload = data.model_dump(mode="json", exclude={"scheduled_at", "advance_draft_id"})

    row = ScheduledEmail(
        tenant_id=user.tenant_id,
        created_by_id=user.id,
        case_id=data.case_id,
        scheduled_at=when,
        status=STATUS_PENDING,
        payload=payload,
        subject=(data.subject or "")[:500],
        recipients=", ".join(data.to)[:1000],
        advance_draft_id=data.advance_draft_id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)

    logger.info(
        "Mail ingepland (tenant=%s, case=%s, moment=%s)",
        user.tenant_id,
        data.case_id,
        when.isoformat(),
    )
    return ComposeResponse(
        success=True,
        message="E-mail ingepland",
        scheduled=True,
        scheduled_email_id=row.id,
        scheduled_at=when,
    )


async def list_scheduled_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    include_done: bool = False,
) -> list[ScheduledEmail]:
    """Geplande mails, eerstvolgende bovenaan.

    Standaard alleen wat er nog aankomt of aandacht vraagt (wachtend, bezig,
    mislukt); verstuurd/geannuleerd alleen op verzoek.
    """
    statuses = (
        [STATUS_PENDING, STATUS_SENDING, STATUS_FAILED]
        if not include_done
        else [STATUS_PENDING, STATUS_SENDING, STATUS_FAILED, STATUS_SENT, STATUS_CANCELLED]
    )
    stmt = select(ScheduledEmail).where(
        ScheduledEmail.tenant_id == tenant_id,
        ScheduledEmail.status.in_(statuses),
    )
    if case_id is not None:
        stmt = stmt.where(ScheduledEmail.case_id == case_id)
    stmt = stmt.order_by(ScheduledEmail.scheduled_at.asc())
    return list((await db.execute(stmt)).scalars().all())


async def cancel_scheduled_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    scheduled_id: uuid.UUID,
) -> ScheduledEmail:
    """Annuleer een geplande mail.

    Alleen zolang hij nog wacht. Staat hij op `sending`, dan is de bezorger al
    bezig met de provider — annuleren zou dan een valse belofte zijn (de mail kan
    net weg zijn), dus dat weigeren we expliciet.
    """
    row = (
        await db.execute(
            select(ScheduledEmail).where(
                ScheduledEmail.id == scheduled_id,
                ScheduledEmail.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Geplande e-mail niet gevonden")
    if row.status == STATUS_SENDING:
        raise BadRequestError(
            "Deze e-mail wordt op dit moment verstuurd en kan niet meer worden geannuleerd."
        )
    if row.status != STATUS_PENDING:
        raise BadRequestError("Deze e-mail wacht niet meer — annuleren kan niet.")

    row.status = STATUS_CANCELLED
    await db.flush()
    return row


async def _notify_failure(
    db: AsyncSession,
    row: ScheduledEmail,
    reason: str,
) -> None:
    """Meld aan wie de mail inplande dat hij NIET verstuurd is."""
    from app.notifications.schemas import NotificationCreate
    from app.notifications.service import create_notification

    await create_notification(
        db,
        row.tenant_id,
        row.created_by_id,
        NotificationCreate(
            type=NOTIF_SCHEDULED_EMAIL_FAILED,
            title=f"Geplande e-mail niet verstuurd: {row.subject or '(geen onderwerp)'}",
            message=(
                f"Aan {row.recipients}. {reason} "
                "De mail is NIET opnieuw geprobeerd — controleer en verstuur hem zelf."
            ),
            case_id=row.case_id,
        ),
    )


async def _claim(db: AsyncSession, row_id: uuid.UUID) -> bool:
    """Claim een rij: pending → sending. False = een ander had hem al.

    Vangrail tegen dubbel versturen, twee lagen:

    1. Statuswissel én voorwaarde zitten in ÉÉN UPDATE, dus twee gelijktijdige
       bezorgers kunnen nooit allebei dezelfde mail oppakken.
    2. De claim wordt METEEN vastgelegd (commit), vóórdat er ook maar iets naar de
       provider gaat. Zonder die commit zou een crash tussen claimen en versturen
       de rij terugdraaien naar 'wachtend' — en dan zou de volgende ronde een mail
       versturen die misschien al weg was. Nu blijft hij op 'sending' staan en
       pikt `_fail_stuck_claims` hem op als 'onzeker', nooit als 'opnieuw sturen'.
    """
    result = await db.execute(
        update(ScheduledEmail)
        .where(ScheduledEmail.id == row_id, ScheduledEmail.status == STATUS_PENDING)
        .values(
            status=STATUS_SENDING,
            claimed_at=datetime.now(UTC),
            attempts=ScheduledEmail.attempts + 1,
        )
    )
    await db.commit()
    return result.rowcount == 1


async def _send_one(session: AsyncSession, row_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """Verstuur één geplande mail. Geeft de eindstatus terug (voor de logregel)."""
    from app.auth.models import User
    from app.email.compose_router import ComposeRequest, perform_compose_send
    from app.middleware.tenant import set_tenant_context

    # Draai onder dezelfde kantoor-afscherming als een echte klik, i.p.v. als
    # superuser: een fout kan dan nooit buiten het eigen kantoor komen.
    await set_tenant_context(session, str(tenant_id))

    if not await _claim(session, row_id):
        return "overgeslagen (al geclaimd)"

    # De claim is nu vastgelegd; de kantoor-context ging mee in die commit, dus
    # opnieuw zetten voor de transactie waarin de verzending draait.
    await set_tenant_context(session, str(tenant_id))

    row = await session.get(ScheduledEmail, row_id)
    if row is None:  # pragma: no cover — geclaimd maar verdwenen
        await session.rollback()
        return "overgeslagen (verdwenen)"

    user = await session.get(User, row.created_by_id)
    if user is None:
        row.status = STATUS_FAILED
        row.last_error = "De gebruiker die deze mail inplande bestaat niet meer."
        await session.commit()
        return "mislukt (gebruiker weg)"

    try:
        data = ComposeRequest(**row.payload)
        await perform_compose_send(data, user, session)
    except Exception as exc:
        # Sessie is vervuild door de fout → eerst schoon terug, dan pas de
        # statusregel + melding schrijven (les S203/S205: nooit op een vervuilde
        # sessie doorschrijven).
        await session.rollback()
        await set_tenant_context(session, str(tenant_id))
        row = await session.get(ScheduledEmail, row_id)
        if row is not None:
            row.status = STATUS_FAILED
            row.last_error = str(exc)[:2000]
            await _notify_failure(session, row, f"Reden: {exc}")
        await session.commit()
        logger.error("Geplande mail %s mislukt: %s", row_id, exc)
        return "mislukt"

    row.status = STATUS_SENT
    row.sent_at = datetime.now(UTC)

    # Pas NU de AI-concept-nazorg: concept afvinken, review-taak sluiten, dossier
    # een stap door. Bij het inplannen mocht dit nog niet — dan zou het dossier
    # vooruitlopen op een mail die nog niet weg was.
    if row.advance_draft_id and row.case_id:
        from app.incasso.service import complete_ai_draft_after_send

        try:
            await complete_ai_draft_after_send(
                session, row.tenant_id, row.created_by_id, row.case_id, row.advance_draft_id
            )
        except Exception as exc:
            # De mail IS weg — dat mag nooit terugdraaien op een mislukte nazorg.
            # Wel melden, zodat iemand het concept handmatig afrondt.
            logger.error("Nazorg AI-concept na geplande mail %s mislukt: %s", row_id, exc)
            await _notify_failure(
                session,
                row,
                "De e-mail IS verstuurd, maar het bijbehorende concept kon niet "
                f"worden afgerond ({exc}).",
            )

    await session.commit()
    return "verstuurd"


async def _fail_stuck_claims(session: AsyncSession) -> int:
    """Zet claims die te lang hangen op 'mislukt' — mét eerlijke onzekerheid.

    Een rij die minutenlang op `sending` staat, hoort bij een run die halverwege
    is afgebroken. Of de provider de mail nog verstuurd heeft, weten we niet. We
    proberen hem daarom NOOIT automatisch opnieuw; we melden dat het onzeker is.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=STUCK_CLAIM_MINUTES)
    rows = list(
        (
            await session.execute(
                select(ScheduledEmail).where(
                    ScheduledEmail.status == STATUS_SENDING,
                    ScheduledEmail.claimed_at < cutoff,
                )
            )
        )
        .scalars()
        .all()
    )
    for row in rows:
        row.status = STATUS_FAILED
        row.last_error = (
            "De verzending is halverwege afgebroken. Het is ONZEKER of deze mail "
            "toch nog verstuurd is — controleer de map Verzonden vóór u hem opnieuw stuurt."
        )
        await _notify_failure(
            session,
            row,
            "De verzending brak halverwege af en het is ONZEKER of de mail toch "
            "is verstuurd. Controleer eerst de map Verzonden.",
        )
    if rows:
        await session.commit()
    return len(rows)


async def send_due_scheduled_emails() -> None:
    """Minuut-taak: verstuur alles wat rijp is.

    De zoekronde draait bewust zónder kantoor-context (achtergrondtaken draaien als
    superuser, zie app/security/rls.py) zodat álle kantoren worden bediend; elke
    mail zelf gaat daarna wél onder zijn eigen kantoor-afscherming de deur uit.
    """
    from app.database import async_session

    try:
        async with async_session() as session:
            await _fail_stuck_claims(session)

            due = list(
                (
                    await session.execute(
                        select(ScheduledEmail.id, ScheduledEmail.tenant_id)
                        .where(
                            ScheduledEmail.status == STATUS_PENDING,
                            ScheduledEmail.scheduled_at <= datetime.now(UTC),
                        )
                        .order_by(ScheduledEmail.scheduled_at.asc())
                        .limit(50)
                    )
                ).all()
            )

        if not due:
            return

        results: dict[str, int] = {}
        for row_id, tenant_id in due:
            # Eigen sessie per mail (les S205): een kapotte mail mag de andere niet
            # meesleuren via een gedeelde rollback.
            async with async_session() as session:
                try:
                    outcome = await _send_one(session, row_id, tenant_id)
                except Exception as exc:  # pragma: no cover — vangnet
                    logger.exception("Geplande mail %s: onverwachte fout", row_id)
                    outcome = f"onverwachte fout ({type(exc).__name__})"
                    await session.rollback()
            results[outcome] = results.get(outcome, 0) + 1

        logger.info(
            "Scheduler: geplande mails — %s",
            ", ".join(f"{n}× {k}" for k, n in sorted(results.items())),
        )
    except Exception:
        logger.exception("Scheduler: geplande mails versturen faalde")
        from app.workflow.scheduler import _write_heartbeat

        await _write_heartbeat("send_due_scheduled_emails", "run faalde")
