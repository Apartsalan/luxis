"""B13 — vast afzenderkanaal: pipeline-mail gaat via het kantoor-account (incasso@),
niet via de mailbox van de klikkende gebruiker. Valt terug op het gebruikersaccount
als er geen kantoor-e-mail is ingesteld."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.email.oauth_models import EmailAccount
from app.email.oauth_service import get_tenant_send_account


async def _account(
    db: AsyncSession, tenant_id, user_id, email: str, provider: str = "outlook"
) -> EmailAccount:
    acc = EmailAccount(
        tenant_id=tenant_id,
        user_id=user_id,
        provider=provider,
        email_address=email,
        access_token_enc=b"x",
        refresh_token_enc=b"x",
    )
    db.add(acc)
    await db.flush()
    return acc


@pytest.mark.asyncio
async def test_tenant_send_account_matches_office_email(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Kiest het verbonden account dat matcht met de ingestelde kantoor-e-mail,
    ook al klikte een gebruiker met een ánder account."""
    test_tenant.email = "incasso@kestinglegal.nl"
    await _account(db, test_tenant.id, test_user.id, "seidony@kestinglegal.nl")
    await _account(db, test_tenant.id, test_user.id, "incasso@kestinglegal.nl")
    await db.commit()

    acc = await get_tenant_send_account(db, test_tenant.id)
    assert acc is not None
    assert acc.email_address == "incasso@kestinglegal.nl"


@pytest.mark.asyncio
async def test_tenant_send_account_case_insensitive(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Hoofdletterverschil mag de match niet blokkeren."""
    test_tenant.email = "Incasso@KestingLegal.nl"
    await _account(db, test_tenant.id, test_user.id, "incasso@kestinglegal.nl")
    await db.commit()

    acc = await get_tenant_send_account(db, test_tenant.id)
    assert acc is not None
    assert acc.email_address == "incasso@kestinglegal.nl"


@pytest.mark.asyncio
async def test_tenant_send_account_none_without_office_email(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Geen kantoor-e-mail ingesteld → None → beller valt terug op gebruikersaccount."""
    test_tenant.email = None
    await _account(db, test_tenant.id, test_user.id, "seidony@kestinglegal.nl")
    await db.commit()

    assert await get_tenant_send_account(db, test_tenant.id) is None


@pytest.mark.asyncio
async def test_tenant_send_account_none_when_no_matching_account(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Kantoor-e-mail ingesteld maar dat account is niet verbonden → None."""
    test_tenant.email = "incasso@kestinglegal.nl"
    await _account(db, test_tenant.id, test_user.id, "seidony@kestinglegal.nl")
    await db.commit()

    assert await get_tenant_send_account(db, test_tenant.id) is None
