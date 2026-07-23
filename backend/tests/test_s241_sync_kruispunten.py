"""S241-wachters — dossier-sync-kruispunten van de ongesorteerd-melding + het
her-koppelpad (Bril A5/A6, testronde 3).

Vondst S241-1 (foutsoort: "her-koppelen overschrijft de Negeren-beslissing"):
een door de gebruiker genegeerde ongelinkte mail werd bij een volgende sync
stil aan een dossier gekoppeld — via force_case_id (dossier-sync) én via een
dossiernummer in de tekst. De re-match respecteerde 'Negeren' al (S188c), het
inline her-koppelpad in sync_emails_for_account niet. Bounces zijn óók
dismissed maar dat is een systeemvlag — die mogen wél op dossiernummer
koppelen (bewust gedrag, tegenproef hieronder).
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.email.oauth_models import EmailAccount
from app.email.providers.base import EmailMessage
from app.email.sync_service import sync_emails_for_account
from app.email.synced_email_models import SyncedEmail
from app.notifications.models import Notification
from app.notifications.service import NOTIF_EMAIL_UNSORTED
from app.relations.models import Contact


def _fake_provider_with(messages):
    provider = MagicMock()
    provider.list_messages = AsyncMock(return_value=(messages, None))
    return provider


async def _make_account(db, tenant_id, user_id) -> EmailAccount:
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        provider="outlook",
        email_address="seidony@kestinglegal.nl",
        access_token_enc=b"fake",
        refresh_token_enc=b"fake",
    )
    db.add(account)
    await db.flush()
    return account


async def _make_case(db, tenant_id, case_number="2026-00090", email="debiteur@voorbeeld.nl"):
    client = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Cliënt B.V.",
        email="client@test.nl",
    )
    debtor = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="person",
        name="Debiteur",
        email=email,
    )
    db.add_all([client, debtor])
    await db.flush()
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=datetime.now(UTC).date(),
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    return case, debtor


async def _sync(db, account, messages, force_case_id=None):
    with (
        patch(
            "app.email.sync_service.get_provider",
            return_value=_fake_provider_with(messages),
        ),
        patch(
            "app.email.sync_service.get_valid_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch("app.email.sync_service.decrypt_token", return_value="tok"),
    ):
        return await sync_emails_for_account(db, account, force_case_id=force_case_id)


async def _unsorted_notifications(db, tenant_id):
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.type == NOTIF_EMAIL_UNSORTED,
        )
    )
    return list(result.scalars().all())


def _msg(msg_id="MSG-1", subject="Vraag", from_email="debiteur@voorbeeld.nl"):
    return EmailMessage(
        provider_message_id=msg_id,
        subject=subject,
        from_email=from_email,
        from_name="Debiteur",
        to_emails=["seidony@kestinglegal.nl"],
    )


# A5a — dossier-sync: mail zonder dossiernummer wordt force-gekoppeld → géén
# ongesorteerd-melding (wel een email_received-melding, maar daar gaat het hier niet om).
@pytest.mark.asyncio
async def test_dossier_sync_force_link_geeft_geen_ongesorteerd_melding(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case, _ = await _make_case(db, test_tenant.id)
    account = await _make_account(db, test_tenant.id, test_user.id)

    await _sync(db, account, [_msg()], force_case_id=case.id)

    row = (
        await db.execute(select(SyncedEmail).where(SyncedEmail.provider_message_id == "MSG-1"))
    ).scalar_one()
    assert row.case_id == case.id
    assert await _unsorted_notifications(db, test_tenant.id) == []


# A5b — dossier-sync: mail mét onbekend dossiernummer blijft ongelinkt → melding
# is terecht (hij ís ongesorteerd).
@pytest.mark.asyncio
async def test_dossier_sync_onbekend_dossiernummer_meldt_wel(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case, _ = await _make_case(db, test_tenant.id)
    account = await _make_account(db, test_tenant.id, test_user.id)

    await _sync(
        db,
        account,
        [_msg(subject="Inzake dossier 2099-99999")],
        force_case_id=case.id,
    )

    row = (
        await db.execute(select(SyncedEmail).where(SyncedEmail.provider_message_id == "MSG-1"))
    ).scalar_one()
    assert row.case_id is None
    assert len(await _unsorted_notifications(db, test_tenant.id)) == 1


# A5c — storm: 3 verschillende ongesorteerde mails in één sync → 3 losse meldingen
# per gebruiker (geen bundeling; titel-dedup pakt alleen identieke onderwerpen).
@pytest.mark.asyncio
async def test_drie_ongesorteerde_mails_in_een_sync_geven_drie_meldingen(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    account = await _make_account(db, test_tenant.id, test_user.id)
    msgs = [
        _msg(msg_id=f"MSG-{i}", subject=f"Onderwerp {i}", from_email=f"x{i}@onbekend.nl")
        for i in range(3)
    ]
    await _sync(db, account, msgs)

    assert len(await _unsorted_notifications(db, test_tenant.id)) == 3


# A6-diep — genegeerde ongelinkte mail + dossier-sync: het her-koppelpad voor
# bestaande ongelinkte mails checkt is_dismissed niet. Deze proef stelt vast wat
# er werkelijk gebeurt (koppeling ja/nee, en zo ja: blijft hij 'genegeerd'?).
@pytest.mark.asyncio
async def test_genegeerde_mail_wordt_bij_dossier_sync_niet_stil_gekoppeld(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case, _ = await _make_case(db, test_tenant.id)
    account = await _make_account(db, test_tenant.id, test_user.id)

    # 1e sync: mail komt binnen, blijft ongelinkt (geen dossiernummer, geen force)
    await _sync(db, account, [_msg()])
    row = (
        await db.execute(select(SyncedEmail).where(SyncedEmail.provider_message_id == "MSG-1"))
    ).scalar_one()
    assert row.case_id is None

    # Gebruiker drukt "Negeren"
    row.is_dismissed = True
    await db.flush()

    # 2e sync, nu vanuit het dossier (force_case_id): zelfde mail zit in het venster
    await _sync(db, account, [_msg()], force_case_id=case.id)

    await db.refresh(row)
    assert row.case_id is None, (
        "Genegeerde mail is bij een dossier-sync stil aan het dossier gekoppeld "
        f"(case_id={row.case_id}, is_dismissed={row.is_dismissed})"
    )


# Route 2 van dezelfde foutsoort: genegeerde mail waar later een dossiernummer
# bij zou matchen (zaak bestaat inmiddels) — Negeren blijft ook dan gelden.
@pytest.mark.asyncio
async def test_genegeerde_mail_wordt_niet_alsnog_op_dossiernummer_gekoppeld(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    account = await _make_account(db, test_tenant.id, test_user.id)

    # Mail met dossiernummer van een zaak die nog niet bestaat → ongelinkt
    await _sync(db, account, [_msg(subject="Inzake dossier 2026-00091")])
    row = (
        await db.execute(select(SyncedEmail).where(SyncedEmail.provider_message_id == "MSG-1"))
    ).scalar_one()
    assert row.case_id is None

    row.is_dismissed = True
    await db.flush()

    # Zaak bestaat inmiddels; zelfde mail komt opnieuw langs in de sync
    await _make_case(db, test_tenant.id, case_number="2026-00091")
    await _sync(db, account, [_msg(subject="Inzake dossier 2026-00091")])

    await db.refresh(row)
    assert row.case_id is None


# Tegenproef: een bounce is óók dismissed (systeemvlag) maar mag WÉL alsnog op
# dossiernummer koppelen — bewust gedrag, mag niet sneuvelen door de S241-poort.
@pytest.mark.asyncio
async def test_bounce_koppelt_wel_alsnog_op_dossiernummer(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    account = await _make_account(db, test_tenant.id, test_user.id)
    bounce = EmailMessage(
        provider_message_id="BOUNCE-1",
        subject="Onbestelbaar: Sommatie dossier 2026-00092",
        from_email="postmaster@mail.example.com",
        from_name="Mail Delivery System",
        to_emails=["seidony@kestinglegal.nl"],
    )

    # Bounce komt binnen vóór de zaak bestaat → ongelinkt + auto-dismissed
    await _sync(db, account, [bounce])
    row = (
        await db.execute(
            select(SyncedEmail).where(SyncedEmail.provider_message_id == "BOUNCE-1")
        )
    ).scalar_one()
    assert row.case_id is None
    assert row.is_dismissed is True
    assert row.is_bounce is True

    # Zaak bestaat inmiddels; volgende sync ziet dezelfde bounce
    case, _ = await _make_case(db, test_tenant.id, case_number="2026-00092")
    await _sync(db, account, [bounce])

    await db.refresh(row)
    assert row.case_id == case.id
