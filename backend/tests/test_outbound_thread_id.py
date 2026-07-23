"""S234 — write_outbound_log zet provider_thread_id op de uitgaande SyncedEmail.

Vondst S233: uitgaande mails kregen nooit een draad-kenmerk, waardoor het
antwoord-zijpaneel de eigen verstuurde mails nooit in de draad kon tonen. De
verstuurde mail moet op dezelfde draad groeperen als het gesprek:
- antwoord (References-wortel meegegeven) → die wortel;
- verse mail zonder antwoord-context → het eigen message-id (mail is zelf de
  wortel), net als de inkomende-sync (thread_id = References[0] else message_id).
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.email.oauth_models import EmailAccount
from app.email.send_service import write_outbound_log
from app.email.synced_email_models import SyncedEmail


@pytest_asyncio.fixture
async def account(db: AsyncSession, test_tenant: Tenant, test_user: User) -> EmailAccount:
    acc = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="imap",
        email_address="incasso@kestinglegal.nl",
        access_token_enc=b"x",
        refresh_token_enc=b"y",
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return acc


async def _log(db, tenant, user, account, **kw) -> SyncedEmail:
    await write_outbound_log(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        to=["debiteur@example.com"],
        subject="Re: Vraag over dossier",
        body_html="<p>hoi</p>",
        account=account,
        used_provider=True,
        status="sent",
        **kw,
    )
    synced = (
        await db.execute(
            select(SyncedEmail).where(
                SyncedEmail.provider_message_id == kw["provider_message_id"]
            )
        )
    ).scalar_one()
    return synced


@pytest.mark.asyncio
async def test_reply_stores_thread_root(db, test_tenant, test_user, account):
    """Antwoord: de meegegeven References-wortel wordt de draad, niet het eigen id."""
    synced = await _log(
        db,
        test_tenant,
        test_user,
        account,
        provider_message_id="<own-reply-123@kestinglegal.nl>",
        provider_thread_id="<root-abc@mail.gmail.com>",
    )
    assert synced.provider_thread_id == "<root-abc@mail.gmail.com>"
    assert synced.direction == "outbound"


@pytest.mark.asyncio
async def test_fresh_mail_defaults_thread_to_own_message_id(
    db, test_tenant, test_user, account
):
    """Verse mail zonder antwoord-context: de mail is zelf de wortel."""
    synced = await _log(
        db,
        test_tenant,
        test_user,
        account,
        provider_message_id="<fresh-999@kestinglegal.nl>",
        provider_thread_id=None,
    )
    assert synced.provider_thread_id == "<fresh-999@kestinglegal.nl>"


@pytest.mark.asyncio
async def test_send_as_office_address_recorded_as_sender(
    db, test_tenant, test_user, account
):
    """S242 (demo-vondst Arsalan): 'Verzenden als' kantooradres → het dossier
    moet het adres tonen dat écht op de mail stond (incasso@), niet de
    vervoerende mailbox (seidony@). Voorheen werd altijd het accountadres
    vastgelegd — verwarrend en fout in de correspondentie-weergave."""
    account.email_address = "seidony@kestinglegal.nl"
    await db.flush()
    synced = await _log(
        db,
        test_tenant,
        test_user,
        account,
        provider_message_id="<sendas-1@kestinglegal.nl>",
        effective_from="incasso@kestinglegal.nl",
    )
    assert synced.from_email == "incasso@kestinglegal.nl"


@pytest.mark.asyncio
async def test_plain_send_records_account_address(
    db, test_tenant, test_user, account
):
    """Tegenproef: geen 'verzenden als' (effective_from None) → accountadres."""
    synced = await _log(
        db,
        test_tenant,
        test_user,
        account,
        provider_message_id="<plain-1@kestinglegal.nl>",
        effective_from=None,
    )
    assert synced.from_email == "incasso@kestinglegal.nl"
