"""S246 — wachters voor 'Verstuur later' (skill breed-testen).

Eén wachter per foutSOORT, niet per geval:

* inplannen mag NIET nu versturen (en direct versturen mag niet stiekem plannen)
* de bezorger stuurt alleen wat rijp is
* een mail kan NOOIT dubbel de deur uit (claim-vangrail)
* annuleren voorkomt verzending
* een moment in het verleden wordt geweigerd; tijdzone wordt correct omgerekend
* mislukken → status 'failed' + melding, en GEEN automatische herhaling
* de AI-concept-nazorg draait pas ná de échte verzending, niet bij het inplannen
* een ander kantoor ziet noch annuleert deze mails

De provider-send wordt gemockt (geen echte mail): we toetsen de bedrading en de
afbakening, niet de verzending zelf.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case
from app.email.oauth_models import EmailAccount
from app.email.scheduled_models import (
    STATUS_CANCELLED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_SENT,
    ScheduledEmail,
)
from app.notifications.models import Notification
from app.relations.models import Contact


async def _case(db, tenant_id, number="2026-96001"):
    contact = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company", name="Cliënt"
    )
    db.add(contact)
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number=number, case_type="incasso",
        status="nieuw", debtor_type="b2b", client_id=contact.id, date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


async def _account(db, tenant_id, user_id):
    db.add(EmailAccount(
        id=uuid.uuid4(), tenant_id=tenant_id, user_id=user_id,
        provider="outlook", email_address="kantoor@test.nl",
        access_token_enc=b"x", refresh_token_enc=b"y",
    ))


def _mock_provider(message_id="provider-msg-1", boom: bool = False):
    send = AsyncMock(side_effect=RuntimeError("provider down")) if boom else AsyncMock(
        return_value=message_id
    )
    return SimpleNamespace(send_message=send)


def _send_patches(provider):
    """De drie provider-haken die de verzendmachine gebruikt."""
    return (
        patch("app.email.compose_router.resolve_office_channel",
              new_callable=AsyncMock, return_value=(None, None)),
        patch("app.email.compose_router.get_valid_access_token",
              new_callable=AsyncMock, return_value="fake-token"),
        patch("app.email.compose_router.get_provider", return_value=provider),
    )


async def _post_send(client, token, case_id, *, scheduled_at=None, **extra):
    body = {
        "to": ["debiteur@example.nl"],
        "subject": "Sommatie",
        "body_html": "<p>Gelieve te betalen.</p>",
        "case_id": str(case_id),
        "already_branded": True,
        **extra,
    }
    if scheduled_at is not None:
        body["scheduled_at"] = scheduled_at
    return await client.post(
        "/api/email/compose/send",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )


async def _rows(db, tenant_id):
    return list(
        (
            await db.execute(
                select(ScheduledEmail).where(ScheduledEmail.tenant_id == tenant_id)
            )
        ).scalars().all()
    )


async def _count(db, tenant_id) -> int:
    """Tellen i.p.v. objecten ophalen — na een teruggedraaide transactie zijn de
    objecten vervallen en zou pytest bij het tonen ervan alsnog IO doen."""
    return (
        await db.execute(
            select(func.count())
            .select_from(ScheduledEmail)
            .where(ScheduledEmail.tenant_id == tenant_id)
        )
    ).scalar_one()


# ── Inplannen ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_inplannen_verstuurt_nu_nog_niets(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De kernbelofte: met een gepland moment gaat er NU niets de deur uit."""
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    provider = _mock_provider()
    when = datetime.now(UTC) + timedelta(hours=3)
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        resp = await _post_send(client, token, case.id, scheduled_at=when.isoformat())

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scheduled"] is True
    assert body["scheduled_email_id"]
    provider.send_message.assert_not_called()  # KERN: niets verstuurd

    rows = await _rows(db, test_tenant.id)
    assert len(rows) == 1
    assert rows[0].status == STATUS_PENDING
    assert rows[0].subject == "Sommatie"
    assert rows[0].case_id == case.id
    # De payload draagt GEEN gepland moment meer — anders zou de bezorger hem
    # opnieuw inplannen i.p.v. versturen (oneindige lus).
    assert "scheduled_at" not in rows[0].payload


@pytest.mark.asyncio
async def test_direct_versturen_plant_niets_in(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Spiegelwachter: zónder gepland moment blijft het oude gedrag exact."""
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        resp = await _post_send(client, token, case.id)

    assert resp.status_code == 200, resp.text
    assert resp.json()["scheduled"] is False
    provider.send_message.assert_called_once()  # gewoon direct verstuurd
    assert await _count(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_moment_in_verleden_wordt_geweigerd(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()
    # Ids vastpakken vóór het verzoek: een geweigerd verzoek draait de transactie
    # terug, waardoor de fixture-objecten vervallen en uitlezen alsnog IO doet.
    tenant_id, case_id = test_tenant.id, case.id

    token = create_access_token(str(test_user.id), str(tenant_id))
    when = datetime.now(UTC) - timedelta(hours=1)
    resp = await _post_send(client, token, case_id, scheduled_at=when.isoformat())

    assert resp.status_code == 400
    assert "verleden" in resp.json()["detail"].lower()
    assert await _count(db, tenant_id) == 0


@pytest.mark.asyncio
async def test_nederlandse_tijd_wordt_correct_naar_utc_omgerekend(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De server draait op UTC, Lisanne kiest Nederlandse tijd.

    Zomertijd = UTC+2, dus 'morgen 09:00' in Nederland is 07:00 UTC. Zonder deze
    omrekening zou een incassomail twee uur te vroeg of te laat weggaan.
    """
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    morgen = (datetime.now(UTC) + timedelta(days=1)).date()
    nl_negen_uur = f"{morgen.isoformat()}T09:00:00+02:00"

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        resp = await _post_send(client, token, case.id, scheduled_at=nl_negen_uur)
    assert resp.status_code == 200, resp.text

    rows = await _rows(db, test_tenant.id)
    opgeslagen = rows[0].scheduled_at.astimezone(UTC)
    assert (opgeslagen.hour, opgeslagen.minute) == (7, 0)


@pytest.mark.asyncio
async def test_dagenbrief_gate_blokkeert_ook_bij_inplannen(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De wettelijke waarborg mag niet te omzeilen zijn door 'later' te kiezen —
    en Lisanne hoort het meteen, niet pas als de mail de volgende dag faalt."""
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()
    tenant_id, case_id = test_tenant.id, case.id  # zie opmerking hierboven

    token = create_access_token(str(test_user.id), str(tenant_id))
    when = datetime.now(UTC) + timedelta(hours=2)
    with patch(
        "app.collections.compliance.check_dagenbrief_gate_for_case",
        new_callable=AsyncMock, return_value="14-dagenbrief ontbreekt",
    ):
        resp = await _post_send(client, token, case_id, scheduled_at=when.isoformat())

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "DAGENBRIEF_GATE"
    assert await _count(db, tenant_id) == 0


# ── Bezorgen ─────────────────────────────────────────────────────────────────


async def _dispatch(session_factory):
    """Draai de minuut-taak tegen de testdatabase."""
    from app.email.scheduled_service import send_due_scheduled_emails

    with patch("app.database.async_session", session_factory):
        await send_due_scheduled_emails()


async def _queue_row(db, tenant_id, user_id, case_id, *, when, **extra) -> ScheduledEmail:
    row = ScheduledEmail(
        tenant_id=tenant_id, created_by_id=user_id, case_id=case_id,
        scheduled_at=when, status=STATUS_PENDING,
        payload={
            "to": ["debiteur@example.nl"], "subject": "Sommatie",
            "body_html": "<p>Gelieve te betalen.</p>",
            "case_id": str(case_id), "already_branded": True,
        },
        subject="Sommatie", recipients="debiteur@example.nl", **extra,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@pytest.mark.asyncio
async def test_rijpe_mail_gaat_weg_toekomstige_blijft_staan(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    rijp = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                            when=datetime.now(UTC) - timedelta(minutes=1))
    later = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                             when=datetime.now(UTC) + timedelta(days=1))

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)

    provider.send_message.assert_called_once()
    await db.refresh(rijp)
    await db.refresh(later)
    assert rijp.status == STATUS_SENT
    assert rijp.sent_at is not None
    assert later.status == STATUS_PENDING  # niet rijp → niet aangeraakt


@pytest.mark.asyncio
async def test_mail_kan_nooit_dubbel_de_deur_uit(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Twee bezorgrondes over dezelfde rij mogen samen één verzending opleveren."""
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) - timedelta(minutes=1))

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)
        await _dispatch(session_factory)

    assert provider.send_message.call_count == 1
    await db.refresh(row)
    assert row.status == STATUS_SENT
    assert row.attempts == 1


@pytest.mark.asyncio
async def test_geannuleerde_mail_wordt_niet_verstuurd(
    client, db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) + timedelta(hours=2))

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.delete(
        f"/api/email/scheduled/{row.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == STATUS_CANCELLED

    # Zelfs als het moment intussen verstrijkt: geannuleerd blijft geannuleerd.
    row.scheduled_at = datetime.now(UTC) - timedelta(minutes=1)
    await db.commit()

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)

    provider.send_message.assert_not_called()
    await db.refresh(row)
    assert row.status == STATUS_CANCELLED


@pytest.mark.asyncio
async def test_mislukking_meldt_en_herhaalt_niet(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Eén incassomail twee keer sturen is erger dan een dag te laat: na een
    fout blijft het bij één poging + een melding voor wie hem inplande."""
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) - timedelta(minutes=1))

    provider = _mock_provider(boom=True)
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)
        await _dispatch(session_factory)  # tweede ronde mag NIET opnieuw proberen

    assert provider.send_message.call_count == 1
    await db.refresh(row)
    assert row.status == STATUS_FAILED
    assert row.attempts == 1
    assert row.last_error

    notifs = list(
        (
            await db.execute(
                select(Notification).where(
                    Notification.tenant_id == test_tenant.id,
                    Notification.type == "scheduled_email_failed",
                )
            )
        ).scalars().all()
    )
    assert len(notifs) == 1
    assert notifs[0].user_id == test_user.id


@pytest.mark.asyncio
async def test_ai_concept_nazorg_pas_na_echte_verzending(
    client, db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Het kruispunt: bij het INPLANNEN mag het concept niet worden afgevinkt en
    het dossier niet doorschuiven — anders loopt het dossier vooruit op een mail
    die nog in de wachtrij staat. Pas ná verzending draait de nazorg."""
    from app.ai_agent.models import AIDraft, DraftStatus

    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    # Echt concept in reviewstatus — de blinde-wachtrij-guard (S246-review)
    # blokkeert terecht op een niet-bestaand of al-verstuurd concept.
    draft = AIDraft(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        subject="Concept", body="x", status=DraftStatus.GENERATED,
    )
    db.add(draft)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    draft_id = draft.id
    when = datetime.now(UTC) + timedelta(hours=2)

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with (
        p1, p2, p3,
        patch("app.incasso.service.complete_ai_draft_after_send",
              new_callable=AsyncMock, return_value={"advanced": True}) as nazorg,
    ):
        resp = await _post_send(
            client, token, case.id,
            scheduled_at=when.isoformat(), advance_draft_id=str(draft_id),
        )
        assert resp.status_code == 200, resp.text
        nazorg.assert_not_called()  # KERN: nog niets afgevinkt bij het inplannen

    rows = await _rows(db, test_tenant.id)
    assert rows[0].advance_draft_id == draft_id
    rows[0].scheduled_at = datetime.now(UTC) - timedelta(minutes=1)
    await db.commit()

    provider2 = _mock_provider("provider-msg-2")
    q1, q2, q3 = _send_patches(provider2)
    with (
        q1, q2, q3,
        patch("app.incasso.service.complete_ai_draft_after_send",
              new_callable=AsyncMock, return_value={"advanced": True}) as nazorg,
    ):
        await _dispatch(session_factory)

    provider2.send_message.assert_called_once()
    nazorg.assert_called_once()
    assert nazorg.call_args.args[4] == draft_id  # juiste concept


# ── Blinde-wachtrij-guards (S246-review) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_betaald_dossier_blokkeert_geplande_mail(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Kruispunt: het dossier wordt betaald NA het inplannen. Bij een directe
    klik ziet een mens dat; de wachtrij is blind → guard moet blokkeren."""
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) - timedelta(minutes=1))

    case.status = "betaald"
    await db.commit()

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)

    provider.send_message.assert_not_called()  # KERN: niets de deur uit
    await db.refresh(row)
    assert row.status == STATUS_FAILED
    assert "betaald" in (row.last_error or "")

    notifs = list((await db.execute(
        select(Notification).where(Notification.type == "scheduled_email_failed")
    )).scalars().all())
    assert len(notifs) == 1


@pytest.mark.asyncio
async def test_al_verstuurd_concept_blokkeert_geplande_kopie(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Kruispunt: het AI-concept wordt ná het inplannen alsnog handmatig
    verstuurd. De geplande kopie zou een DUBBELE mail aan de debiteur zijn en
    het dossier een extra stap doorschuiven → guard moet blokkeren."""
    from app.ai_agent.models import AIDraft, DraftStatus

    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    draft = AIDraft(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        subject="Sommatie", body="x", status=DraftStatus.SENT,
    )
    db.add(draft)
    await db.commit()
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) - timedelta(minutes=1),
                           advance_draft_id=draft.id)

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)

    provider.send_message.assert_not_called()  # geen dubbele mail
    await db.refresh(row)
    assert row.status == STATUS_FAILED
    assert "al handmatig verstuurd" in (row.last_error or "")


@pytest.mark.asyncio
async def test_mislukte_rij_is_weg_te_halen(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Een mislukte rij mag niet eeuwig blijven staan: weghalen (→ geannuleerd)
    moet kunnen; de foutreden blijft op de rij bewaard."""
    case = await _case(db, test_tenant.id)
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) - timedelta(minutes=5))
    row.status = STATUS_FAILED
    row.last_error = "provider down"
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.delete(
        f"/api/email/scheduled/{row.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == STATUS_CANCELLED

    await db.refresh(row)
    assert row.status == STATUS_CANCELLED
    assert row.last_error == "provider down"  # reden blijft bewaard


# ── Lopende band: batch + follow-up (S246-nacht) ─────────────────────────────


async def _step(db, tenant_id, name="Eerste sommatie", template="sommatie", order=1):
    from app.incasso.models import IncassoPipelineStep

    step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name=name, sort_order=order,
        template_type=template, is_active=True,
    )
    db.add(step)
    await db.flush()
    return step


async def _case_met_stap_en_debiteur(db, tenant_id, step, number="2026-95001"):
    """Incassodossier op een stap, mét debiteur die een e-mailadres heeft."""
    client = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company", name="Cliënt"
    )
    debiteur = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company",
        name="Debiteur BV", email="debiteur@example.nl",
    )
    db.add_all([client, debiteur])
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number=number, case_type="incasso",
        status="in_behandeling", debtor_type="b2b", client_id=client.id,
        opposing_party_id=debiteur.id, date_opened=date.today(),
        incasso_step_id=step.id,
    )
    db.add(case)
    await db.flush()
    return case


@pytest.mark.asyncio
async def test_batch_inplannen_verstuurt_nu_niets(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Batch met gepland moment: nu geen brief, geen mail, geen doorschuiven —
    alleen wachtrij-rijen (één per dossier, met stap-anker)."""
    step = await _step(db, test_tenant.id)
    case = await _case_met_stap_en_debiteur(db, test_tenant.id, step)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    when = datetime.now(UTC) + timedelta(hours=8)
    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        resp = await client.post(
            "/api/incasso/batch",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "case_ids": [str(case.id)],
                "action": "generate_document",
                "send_email": True,
                "scheduled_at": when.isoformat(),
            },
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["action"] == "schedule_document_send"
    assert body["processed"] == 1
    provider.send_message.assert_not_called()  # KERN: nu niets de deur uit

    rows = await _rows(db, test_tenant.id)
    assert len(rows) == 1
    assert rows[0].kind == "batch_step"
    assert rows[0].step_id_at_schedule == step.id
    assert rows[0].case_id == case.id
    # Dossier is NIET doorgeschoven en er is GEEN document gemaakt.
    await db.refresh(case)
    assert case.incasso_step_id == step.id
    from app.documents.models import GeneratedDocument
    docs = (await db.execute(
        select(func.count()).select_from(GeneratedDocument)
        .where(GeneratedDocument.case_id == case.id)
    )).scalar_one()
    assert docs == 0


@pytest.mark.asyncio
async def test_batch_stap_gewisseld_blokkeert_verzending(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Kruispunt: het dossier wisselt van stap ná het inplannen — dan zou de
    VERKEERDE brief uitgaan. De bezorger moet blokkeren + melden."""
    stap_oud = await _step(db, test_tenant.id, "Eerste sommatie", "sommatie", 1)
    stap_nieuw = await _step(db, test_tenant.id, "Tweede sommatie", "tweede_sommatie", 2)
    case = await _case_met_stap_en_debiteur(db, test_tenant.id, stap_oud)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    row = ScheduledEmail(
        tenant_id=test_tenant.id, created_by_id=test_user.id, case_id=case.id,
        scheduled_at=datetime.now(UTC) - timedelta(minutes=1), status=STATUS_PENDING,
        kind="batch_step", step_id_at_schedule=stap_oud.id,
        payload={"auto_assign_step": False},
        subject="Stap-brief", recipients="debiteur@example.nl",
    )
    db.add(row)
    case.incasso_step_id = stap_nieuw.id  # stap wisselt buitenom
    await db.commit()

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)

    provider.send_message.assert_not_called()
    await db.refresh(row)
    assert row.status == STATUS_FAILED
    assert "andere stap" in (row.last_error or "")


@pytest.mark.asyncio
async def test_batch_dispatch_draait_de_echte_batchfunctie(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Bedrading: op het verzendmoment draait EXACT batch_execute (zelfde functie
    als de knop). Geslaagd (1 mail) → sent; niets verstuurd → failed mét reden."""
    from unittest.mock import AsyncMock as AM

    from app.incasso.schemas import BatchActionResult

    step = await _step(db, test_tenant.id)
    case = await _case_met_stap_en_debiteur(db, test_tenant.id, step)
    await db.commit()

    def rij(when_offset=-1):
        return ScheduledEmail(
            tenant_id=test_tenant.id, created_by_id=test_user.id, case_id=case.id,
            scheduled_at=datetime.now(UTC) + timedelta(minutes=when_offset),
            status=STATUS_PENDING, kind="batch_step", step_id_at_schedule=step.id,
            payload={"auto_assign_step": False},
            subject="Stap-brief", recipients="debiteur@example.nl",
        )

    ok = rij(); db.add(ok); await db.commit(); await db.refresh(ok)
    goed = BatchActionResult(action="generate_document", processed=1, skipped=0,
                             errors=[], emails_sent=1)
    with patch("app.incasso.service.batch_execute", new_callable=AM, return_value=goed) as be:
        await _dispatch(session_factory)
    be.assert_called_once()
    assert be.call_args.args[3] == [case.id]  # één dossier per rij
    await db.refresh(ok)
    assert ok.status == STATUS_SENT

    fout = rij(); db.add(fout); await db.commit(); await db.refresh(fout)
    mislukt = BatchActionResult(action="generate_document", processed=0, skipped=1,
                                errors=["2026-95001: e-mail mislukt — provider down"],
                                emails_sent=0)
    with patch("app.incasso.service.batch_execute", new_callable=AM, return_value=mislukt):
        await _dispatch(session_factory)
    await db.refresh(fout)
    assert fout.status == STATUS_FAILED
    assert "provider down" in (fout.last_error or "")


async def _aanbeveling(db, tenant_id, case, step, status="pending"):
    from app.ai_agent.followup_models import FollowupRecommendation

    rec = FollowupRecommendation(
        id=uuid.uuid4(), tenant_id=tenant_id, case_id=case.id,
        incasso_step_id=step.id, recommended_action="generate_document",
        reasoning="test", days_in_step=10, outstanding_amount=100,
        status=status,
    )
    db.add(rec)
    await db.flush()
    return rec


@pytest.mark.asyncio
async def test_followup_inplannen_keurt_goed_en_plant(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Goedkeuren gebeurt NU (besluit van vanavond), uitvoeren wacht in de
    wachtrij. Dubbel inplannen wordt geweigerd."""
    step = await _step(db, test_tenant.id)
    case = await _case_met_stap_en_debiteur(db, test_tenant.id, step)
    rec = await _aanbeveling(db, test_tenant.id, case, step)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    when = datetime.now(UTC) + timedelta(hours=8)
    resp = await client.post(
        f"/api/followup/{rec.id}/schedule-execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"scheduled_at": when.isoformat()},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["scheduled"] is True

    await db.refresh(rec)
    assert rec.status == "approved"  # goedgekeurd, NIET uitgevoerd
    rows = await _rows(db, test_tenant.id)
    assert len(rows) == 1 and rows[0].kind == "followup"

    # Nogmaals inplannen → geweigerd (anders 2× dezelfde brief morgen).
    resp2 = await client.post(
        f"/api/followup/{rec.id}/schedule-execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"scheduled_at": when.isoformat()},
    )
    assert resp2.status_code == 400
    assert "al ingepland" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_followup_verouderd_of_uitgevoerd_blokkeert(
    db: AsyncSession, session_factory, test_tenant: Tenant, test_user: User
):
    """Kruispunt: de aanbeveling is intussen al uitgevoerd (of verouderd door een
    stapwissel). De bezorger voert dan NIETS uit — echte statusmachine, geen mock."""
    step = await _step(db, test_tenant.id)
    case = await _case_met_stap_en_debiteur(db, test_tenant.id, step)
    rec = await _aanbeveling(db, test_tenant.id, case, step, status="executed")
    await db.commit()

    row = ScheduledEmail(
        tenant_id=test_tenant.id, created_by_id=test_user.id, case_id=case.id,
        scheduled_at=datetime.now(UTC) - timedelta(minutes=1), status=STATUS_PENDING,
        kind="followup", payload={"rec_id": str(rec.id)},
        subject="Follow-up", recipients="debiteur@example.nl",
    )
    db.add(row)
    await db.commit()

    provider = _mock_provider()
    p1, p2, p3 = _send_patches(provider)
    with p1, p2, p3:
        await _dispatch(session_factory)

    provider.send_message.assert_not_called()
    await db.refresh(row)
    assert row.status == STATUS_FAILED
    assert "intussen" in (row.last_error or "")


# ── Afscherming ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ander_kantoor_ziet_noch_annuleert(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Kantoor-afscherming op de wachtrij: buurkantoor ziet niets en kan niets af."""
    case = await _case(db, test_tenant.id)
    row = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                           when=datetime.now(UTC) + timedelta(hours=2))

    ander = Tenant(id=uuid.uuid4(), name="Ander Kantoor", slug="ander", kvk_number="12345678")
    db.add(ander)
    await db.flush()
    andere_user = User(
        id=uuid.uuid4(), tenant_id=ander.id, email="collega@ander.nl",
        hashed_password="x", full_name="Collega", role="advocaat", is_active=True,
    )
    db.add(andere_user)
    await db.commit()

    token = create_access_token(str(andere_user.id), str(ander.id))
    lijst = await client.get(
        "/api/email/scheduled", headers={"Authorization": f"Bearer {token}"}
    )
    assert lijst.status_code == 200
    assert lijst.json() == []

    weg = await client.delete(
        f"/api/email/scheduled/{row.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert weg.status_code == 404
    await db.refresh(row)
    assert row.status == STATUS_PENDING  # onaangeroerd


@pytest.mark.asyncio
async def test_lijst_toont_eigen_geplande_mails(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id)
    vroeg = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                             when=datetime.now(UTC) + timedelta(hours=1))
    laat = await _queue_row(db, test_tenant.id, test_user.id, case.id,
                            when=datetime.now(UTC) + timedelta(days=2))

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.get(
        f"/api/email/scheduled?case_id={case.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    ids = [r["id"] for r in resp.json()]
    assert ids == [str(vroeg.id), str(laat.id)]  # eerstvolgende bovenaan
