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
    case = await _case(db, test_tenant.id)
    await _account(db, test_tenant.id, test_user.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    draft_id = uuid.uuid4()
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
