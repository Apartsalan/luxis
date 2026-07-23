"""Wachters (S240): nieuwe ongesorteerde inbound-mail → melding bij alle gebruikers.

S239-meting: 2 échte zakelijke mails lagen 9 dagen / 5 weken stil in de
ongesorteerde bak zonder enig signaal (het S237-gat). De sync meldt nu elke
nieuwe inbound-mail die nérgens aan koppelt. Kruispunt-poorten die NOOIT mogen
melden: gekoppelde mail (die heeft zijn eigen email_received-melding), bounces
(auto-dismissed), eigen-afzender-mails (S236: outbound) en het
BaseNet-importaccount (provider 'import').
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
from app.notifications.models import Notification
from app.notifications.service import NOTIF_EMAIL_UNSORTED

# ── Helpers ──────────────────────────────────────────────────────────────────


def _fake_provider_with(messages):
    provider = MagicMock()
    provider.list_messages = AsyncMock(return_value=(messages, None))
    return provider


async def _make_account(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, provider: str = "outlook"
) -> EmailAccount:
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        provider=provider,
        email_address="seidony@kestinglegal.nl",
        access_token_enc=b"fake",
        refresh_token_enc=b"fake",
    )
    db.add(account)
    await db.flush()
    return account


async def _sync(db, account, messages):
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
        # Het importaccount-pad haalt zijn 'token' uit decrypt_token
        patch("app.email.sync_service.decrypt_token", return_value="tok"),
    ):
        return await sync_emails_for_account(db, account)


async def _unsorted_notifications(db, tenant_id) -> list[Notification]:
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.type == NOTIF_EMAIL_UNSORTED,
        )
    )
    return list(result.scalars().all())


def _inbound_msg(msg_id: str = "MSG-1", subject: str = "Vraag over factuur") -> EmailMessage:
    return EmailMessage(
        provider_message_id=msg_id,
        subject=subject,
        from_email="onbekende@debiteur.nl",
        from_name="Onbekende Afzender",
        to_emails=["seidony@kestinglegal.nl"],
    )


# ── Wachters ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_new_unsorted_inbound_notifies_all_users(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Nieuwe inbound-mail zonder koppeling → melding email_unsorted."""
    account = await _make_account(db, test_tenant.id, test_user.id)
    await _sync(db, account, [_inbound_msg()])

    notifs = await _unsorted_notifications(db, test_tenant.id)
    assert len(notifs) == 1  # test-tenant heeft één actieve gebruiker
    assert notifs[0].user_id == test_user.id
    assert "Vraag over factuur" in notifs[0].title
    assert notifs[0].case_id is None


@pytest.mark.asyncio
async def test_second_sync_of_same_mail_does_not_notify_again(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Dubbele sync-run van dezelfde mail → één melding (dedupe + skip-tak)."""
    account = await _make_account(db, test_tenant.id, test_user.id)
    await _sync(db, account, [_inbound_msg()])
    await _sync(db, account, [_inbound_msg()])

    assert len(await _unsorted_notifications(db, test_tenant.id)) == 1


@pytest.mark.asyncio
async def test_linked_mail_does_not_notify_unsorted(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Mail die aan een dossier koppelt → géén ongesorteerd-melding."""
    from app.relations.models import Contact

    client = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Cliënt B.V.",
        email="client@test.nl",
    )
    db.add(client)
    await db.flush()
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-00088",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=datetime.now(UTC).date(),
        client_id=client.id,
    )
    db.add(case)
    await db.flush()

    account = await _make_account(db, test_tenant.id, test_user.id)
    msg = _inbound_msg(subject="Inzake dossier 2026-00088")
    await _sync(db, account, [msg])

    assert await _unsorted_notifications(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_bounce_does_not_notify_unsorted(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Bounce/NDR zonder koppeling → auto-dismissed, géén melding."""
    account = await _make_account(db, test_tenant.id, test_user.id)
    bounce = EmailMessage(
        provider_message_id="BOUNCE-1",
        subject="Onbestelbaar: Sommatie",
        from_email="postmaster@mail.example.com",
        from_name="Mail Delivery System",
        to_emails=["seidony@kestinglegal.nl"],
    )
    await _sync(db, account, [bounce])

    assert await _unsorted_notifications(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_own_sender_mail_does_not_notify_unsorted(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S236-kruispunt: mail namens het kantooradres is outbound → géén melding."""
    test_tenant.email = "incasso@kestinglegal.nl"
    account = await _make_account(db, test_tenant.id, test_user.id)
    own = EmailMessage(
        provider_message_id="OWN-1",
        subject="Sommatie IN100999",
        from_email="Incasso@KestingLegal.nl",
        to_emails=["debiteur@example.com"],
    )
    await _sync(db, account, [own])

    assert await _unsorted_notifications(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_import_account_does_not_notify_unsorted(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """BaseNet-importaccount (provider 'import') mag nooit melden — ook niet
    als het ooit tóch door de sync zou lopen."""
    account = await _make_account(db, test_tenant.id, test_user.id, provider="import")
    await _sync(db, account, [_inbound_msg(msg_id="IMPORT-1")])

    assert await _unsorted_notifications(db, test_tenant.id) == []
