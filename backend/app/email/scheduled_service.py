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
    KIND_BATCH_STEP,
    KIND_FOLLOWUP,
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


def _validate_when(moment: datetime) -> datetime:
    """Gedeelde tijdcontrole voor alle inplan-routes: toekomst, niet absurd ver."""
    when = _as_utc(moment)
    now = datetime.now(UTC)
    if when <= now:
        raise BadRequestError(
            "Het gekozen verzendmoment ligt in het verleden. Kies een tijdstip in de toekomst."
        )
    if when > now + timedelta(days=MAX_SCHEDULE_AHEAD_DAYS):
        raise BadRequestError(
            f"Een mail kan maximaal {MAX_SCHEDULE_AHEAD_DAYS} dagen vooruit worden ingepland."
        )
    return when


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

    when = _validate_when(data.scheduled_at)

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

    # S246-review: de totale grootte van meegeplakte bijlagen al bij het INPLANNEN
    # bewaken (dezelfde grens als de verzending zelf hanteert) — anders hoort
    # Lisanne pas de volgende ochtend dat haar mail te zwaar was. Dossierbijlagen
    # worden pas op het verzendmoment van schijf gehaald; dit dekt de uploads.
    if data.inline_attachments:
        from app.email.compose_router import MAX_TOTAL_ATTACHMENT_SIZE

        totaal = sum((len(a.data_base64) * 3) // 4 for a in data.inline_attachments)
        if totaal > MAX_TOTAL_ATTACHMENT_SIZE:
            raise BadRequestError(
                f"De bijlagen zijn samen te groot ({totaal // (1024 * 1024)} MB, "
                f"max {MAX_TOTAL_ATTACHMENT_SIZE // (1024 * 1024)} MB)."
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


async def schedule_batch_send(
    db: AsyncSession,
    user,
    case_ids: list[uuid.UUID],
    scheduled_at: datetime,
    *,
    auto_assign_step: bool = False,
):
    """Plan de batch-stapverzending in: één wachtrij-rij per dossier.

    S246-nacht (GO Arsalan). Er wordt NU niets gemaakt of verstuurd — geen brief,
    geen document, geen doorschuiven. Op het verzendmoment draait de bezorger per
    dossier exact dezelfde batchfunctie als de knop 'Verstuur brief', dus de brief
    krijgt de rentestand van dát moment en het dossier schuift dan pas door.

    Per dossier lichte controles nú (zelfde als de batch zelf zou doen), zodat
    Lisanne 's avonds meteen hoort welke dossiers niet meekunnen: stap aanwezig,
    briefsjabloon aanwezig, e-mailadres aanwezig, 14-dagenbrief-poort.
    """
    from app.cases.models import Case
    from app.cases.schemas import TERMINAL_STATUSES
    from app.collections.compliance import check_dagenbrief_gate
    from app.incasso.schemas import BatchActionResult
    from app.incasso.service import list_pipeline_steps

    if not case_ids:
        raise BadRequestError("Geen dossiers geselecteerd")
    when = _validate_when(scheduled_at)

    steps = await list_pipeline_steps(db, user.tenant_id, active_only=True)
    step_map = {s.id: s for s in steps}

    result = await db.execute(
        select(Case).where(
            Case.tenant_id == user.tenant_id,
            Case.id.in_(case_ids),
            Case.case_type == "incasso",
            Case.is_active.is_(True),
        )
    )
    cases = list(result.scalars().all())

    ingepland = 0
    skipped = 0
    errors: list[str] = []
    for case in cases:
        step = step_map.get(case.incasso_step_id) if case.incasso_step_id else None
        if step is None:
            skipped += 1
            errors.append(f"{case.case_number}: geen pipeline stap — niet ingepland")
            continue
        if not step.template_type:
            skipped += 1
            errors.append(
                f"{case.case_number}: stap '{step.name}' gebruikt AI-concepten — niet ingepland"
            )
            continue
        if case.status in TERMINAL_STATUSES:
            skipped += 1
            errors.append(f"{case.case_number}: status '{case.status}' — niet ingepland")
            continue
        debtor_email = (
            case.opposing_party.email if case.opposing_party else None
        )
        if not debtor_email:
            skipped += 1
            errors.append(
                f"{case.case_number}: geen e-mailadres wederpartij — niet ingepland"
            )
            continue
        gate_reason = await check_dagenbrief_gate(
            db, user.tenant_id, case, step.name, case_number=case.case_number
        )
        if gate_reason is not None:
            skipped += 1
            errors.append(gate_reason)
            continue

        db.add(ScheduledEmail(
            tenant_id=user.tenant_id,
            created_by_id=user.id,
            case_id=case.id,
            scheduled_at=when,
            status=STATUS_PENDING,
            kind=KIND_BATCH_STEP,
            step_id_at_schedule=case.incasso_step_id,
            payload={"auto_assign_step": auto_assign_step},
            subject=f"Stap-brief: {step.name} — {case.case_number}"[:500],
            recipients=debtor_email[:1000],
        ))
        ingepland += 1

    await db.flush()
    logger.info(
        "Batch-verzending ingepland (tenant=%s): %d dossiers op %s, %d overgeslagen",
        user.tenant_id, ingepland, when.isoformat(), skipped,
    )
    # Zelfde antwoordvorm als de batch zelf, zodat de bestaande toast-opbouw
    # (verwerkt/overgeslagen/redenen) op de voorkant gewoon blijft werken.
    return BatchActionResult(
        action="schedule_document_send",
        processed=ingepland,
        skipped=skipped,
        errors=errors,
    )


async def schedule_followup_execute(
    db: AsyncSession,
    user,
    rec_id: uuid.UUID,
    scheduled_at: datetime,
) -> ScheduledEmail:
    """Plan een follow-up-'Uitvoeren' in.

    Het GOEDKEUREN gebeurt nú (dat is Lisannes besluit van vanavond); alleen de
    uitvoering — brief maken, versturen, doorschuiven — wacht tot het gekozen
    moment. Verandert de stap intussen buitenom, dan blokkeert
    execute_recommendation op de stap-mismatch (S247-review; de
    superseded-opruiming raakt alleen PENDING-adviezen, en dit advies staat na
    het goedkeuren op APPROVED) en meldt de bezorger het als mislukt.
    """
    from app.ai_agent.followup_models import FollowupRecommendation, RecommendationStatus
    from app.ai_agent.followup_service import approve_recommendation
    from app.cases.models import Case
    from app.incasso.models import IncassoPipelineStep

    when = _validate_when(scheduled_at)

    rec = (
        await db.execute(
            select(FollowupRecommendation).where(
                FollowupRecommendation.tenant_id == user.tenant_id,
                FollowupRecommendation.id == rec_id,
            )
        )
    ).scalar_one_or_none()
    if rec is None:
        raise NotFoundError("Aanbeveling niet gevonden")

    if rec.status == RecommendationStatus.PENDING:
        rec = await approve_recommendation(db, user.tenant_id, rec_id, user.id)
        if rec is None:  # pragma: no cover — race met een andere klik
            raise BadRequestError("Aanbeveling kon niet worden goedgekeurd")
    elif rec.status != RecommendationStatus.APPROVED:
        raise BadRequestError(
            "Deze aanbeveling is niet meer uit te voeren "
            f"(status: {rec.status})."
        )

    # Dubbel-plan-guard: één open wachtrij-rij per aanbeveling.
    bestaand = (
        await db.execute(
            select(ScheduledEmail).where(
                ScheduledEmail.tenant_id == user.tenant_id,
                ScheduledEmail.kind == KIND_FOLLOWUP,
                ScheduledEmail.status == STATUS_PENDING,
                ScheduledEmail.payload["rec_id"].astext == str(rec_id),
            )
        )
    ).scalar_one_or_none()
    if bestaand is not None:
        raise BadRequestError(
            "Deze aanbeveling staat al ingepland — annuleer eerst de bestaande planning."
        )

    case = await db.get(Case, rec.case_id)
    step = await db.get(IncassoPipelineStep, rec.incasso_step_id)
    debtor_email = (
        case.opposing_party.email if case and case.opposing_party else ""
    ) or ""

    row = ScheduledEmail(
        tenant_id=user.tenant_id,
        created_by_id=user.id,
        case_id=rec.case_id,
        scheduled_at=when,
        status=STATUS_PENDING,
        kind=KIND_FOLLOWUP,
        payload={"rec_id": str(rec_id)},
        subject=(
            f"Follow-up: {step.name if step else 'stap-brief'} — "
            f"{case.case_number if case else ''}"
        )[:500],
        recipients=debtor_email[:1000],
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


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
    # S246-review: 'failed' mag ook weg — anders blijft een mislukte rij eeuwig
    # op het dossier en de Mail-pagina staan zonder opruimknop. De foutmelding
    # blijft bewaard op de rij (last_error), alleen de status gaat naar
    # geannuleerd zodat hij uit de standaardlijst verdwijnt.
    if row.status not in (STATUS_PENDING, STATUS_FAILED):
        raise BadRequestError("Deze e-mail wacht niet meer — annuleren kan niet.")

    row.status = STATUS_CANCELLED
    await db.flush()
    return row


async def _notify_failure(
    db: AsyncSession,
    row: ScheduledEmail,
    reason: str,
    *,
    mail_sent: bool = False,
    blocked: bool = False,
) -> None:
    """Meld aan wie de mail inplande dat er iets misging.

    De staartzin hangt af van wat we zéker weten (S246/S247-review — een
    verkeerde staartzin nodigt uit tot een dúbbele mail aan de debiteur):

    * `mail_sent` — de mail is aantoonbaar weg; alleen de nazorg faalde.
    * `blocked` — een guard blokkeerde VÓÓR er iets naar de provider ging;
      er is met zekerheid niets verstuurd.
    * anders — de verzending zelf klapte; of de provider de mail nog heeft
      meegenomen is dan NIET zeker (time-out ná acceptatie bestaat), dus
      eerst de map Verzonden controleren vóór iemand hem zelf opnieuw stuurt.
    """
    from app.notifications.schemas import NotificationCreate
    from app.notifications.service import create_notification

    if mail_sent:
        titel = f"Geplande e-mail: nazorg mislukt — {row.subject or '(geen onderwerp)'}"
        staart = "De mail zelf IS verstuurd — NIET opnieuw versturen."
    elif blocked:
        titel = f"Geplande e-mail niet verstuurd: {row.subject or '(geen onderwerp)'}"
        staart = "Er is niets verstuurd; er wordt niet automatisch opnieuw geprobeerd."
    else:
        titel = f"Geplande e-mail niet verstuurd: {row.subject or '(geen onderwerp)'}"
        staart = (
            "Er wordt niet automatisch opnieuw geprobeerd. Controleer eerst de "
            "map Verzonden vóórdat u de mail zelf opnieuw verstuurt."
        )

    await create_notification(
        db,
        row.tenant_id,
        row.created_by_id,
        NotificationCreate(
            type=NOTIF_SCHEDULED_EMAIL_FAILED,
            title=titel,
            message=f"Aan {row.recipients}. {reason} {staart}",
            case_id=row.case_id,
        ),
    )


async def _pre_send_blokkade(session: AsyncSession, row: ScheduledEmail) -> str | None:
    """Redenen om een rijpe mail tóch niet te versturen. None = alles in orde.

    S246-review-vondsten (kruispunt 'de wereld veranderde na het inplannen'):

    * Het dossier is intussen betaald of afgesloten — een sommatie naar een
      debiteur die al betaald heeft is precies wat 'nette tijden' moest voorkomen.
    * Het AI-concept is intussen al handmatig verstuurd (dubbele mail aan de
      debiteur + het dossier zou een éxtra stap doorschuiven) of afgewezen
      (Lisanne wilde deze tekst juist níét versturen).
    """
    if row.case_id is not None:
        from app.cases.models import Case
        from app.cases.schemas import TERMINAL_STATUSES

        case = await session.get(Case, row.case_id)
        if case is not None and case.status in TERMINAL_STATUSES:
            return (
                f"Het dossier is intussen '{case.status}' — de geplande mail is "
                "daarom NIET verstuurd."
            )

    if row.advance_draft_id is not None:
        from app.ai_agent.draft_service import get_draft_by_id
        from app.ai_agent.models import DraftStatus

        draft = await get_draft_by_id(session, row.tenant_id, row.advance_draft_id)
        if draft is None:
            return "Het bijbehorende AI-concept bestaat niet meer — mail NIET verstuurd."
        if draft.status == DraftStatus.SENT:
            return (
                "Het AI-concept is intussen al handmatig verstuurd — de geplande "
                "kopie is NIET nogmaals verstuurd."
            )
        if draft.status == DraftStatus.DISCARDED:
            return "Het AI-concept is intussen afgewezen — mail NIET verstuurd."

    return None


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

    # S246-review — de wachtrij is blind: tussen inplannen en verzenden kan de
    # wereld veranderd zijn, en anders dan bij een directe klik kijkt er nu geen
    # mens naar het scherm. Twee guards vóór er iets de deur uit gaat:
    blokkade = await _pre_send_blokkade(session, row)
    if blokkade is not None:
        row.status = STATUS_FAILED
        row.last_error = blokkade
        await _notify_failure(session, row, blokkade, blocked=True)
        await session.commit()
        return "mislukt (blokkade)"

    try:
        if row.kind == KIND_BATCH_STEP:
            await _run_batch_step(session, row)
        elif row.kind == KIND_FOLLOWUP:
            await _run_followup(session, row)
        else:
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
                mail_sent=True,
            )

    await session.commit()
    return "verstuurd"


async def _run_batch_step(session: AsyncSession, row: ScheduledEmail) -> None:
    """Verzendmoment van een ingeplande batch-stapverzending (één dossier).

    Draait exact dezelfde batchfunctie als de knop 'Verstuur brief' — brief
    maken (rentestand van nú), versturen via het kantoorkanaal, taken afronden,
    doorschuiven. Eén extra guard vooraf: staat het dossier nog op de stap van
    het inplanmoment? Zo niet, dan zou de VERKEERDE brief uitgaan → fout.
    """
    from app.cases.models import Case
    from app.incasso.service import batch_execute

    case = await session.get(Case, row.case_id)
    if case is None:
        raise BadRequestError("Dossier bestaat niet meer — niets verstuurd.")
    if case.incasso_step_id != row.step_id_at_schedule:
        raise BadRequestError(
            "Het dossier staat intussen op een andere stap dan bij het inplannen "
            "— de geplande stap-brief is NIET verstuurd."
        )

    result = await batch_execute(
        session,
        row.tenant_id,
        row.created_by_id,
        [row.case_id],
        "generate_document",
        None,
        bool(row.payload.get("auto_assign_step", False)),
        True,  # send_email — inplannen bestaat alléén voor de verzend-variant
    )
    if result.emails_sent < 1:
        # batch_execute rapporteert redenen in errors; maak er één fout van
        # zodat status/melding het echte verhaal dragen.
        raise BadRequestError(
            "; ".join(result.errors) or "Verzending is niet gelukt (geen reden gemeld)."
        )
    if result.errors:
        # S247-review: de mail is wél weg, maar een deel van de nazorg
        # (doorschuiven, taken afronden) faalde — de directe route toont dat in
        # de toast, de wachtrij is blind. Niet stil laten verdwijnen.
        await _notify_failure(
            session,
            row,
            "Nazorg deels mislukt: " + "; ".join(result.errors) + ".",
            mail_sent=True,
        )


async def _run_followup(session: AsyncSession, row: ScheduledEmail) -> None:
    """Verzendmoment van een ingeplande follow-up-uitvoering.

    Zelfde functie als de knop 'Uitvoeren'. Geeft die None terug, dan is de
    aanbeveling intussen al uitgevoerd, afgewezen of verouderd (stap wisselde
    buitenom) — dan hoort er niets te gebeuren behalve een eerlijke melding.
    """
    from app.ai_agent.followup_service import execute_recommendation

    rec_id = uuid.UUID(row.payload["rec_id"])
    rec = await execute_recommendation(session, row.tenant_id, rec_id, row.created_by_id)
    if rec is None:
        raise BadRequestError(
            "De aanbeveling is intussen al uitgevoerd, afgewezen of verouderd "
            "— de geplande uitvoering is NIET gedraaid."
        )


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
            "is verstuurd.",
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
