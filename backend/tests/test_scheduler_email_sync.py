"""S205 — mailsync-foutpad: één kapotte postbus mag de rest niet blokkeren.

De 5-minuten-sync deelde één sessie over alle accounts. Faalde er één (bv. een
verlopen token), dan expireerde de rollback álle geladen objecten en crashte het
volgende account op zijn eerste attribuutlezing (MissingGreenlet) — de accounts
erná synceten dan elke 5 min stil niet meer. De fix geeft elk account een eigen
sessie; deze test dwingt af dat account 2 alsnog synct als account 1 faalt.
"""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.email.oauth_models import EmailAccount
from app.workflow.scheduler import email_auto_sync


async def _account(db, tenant_id, user_id, email):
    acc = EmailAccount(
        id=uuid.uuid4(), tenant_id=tenant_id, user_id=user_id,
        provider="outlook", email_address=email,
        access_token_enc=b"x", refresh_token_enc=b"y",
    )
    db.add(acc)
    return acc


@pytest.mark.asyncio
async def test_broken_account_does_not_block_siblings(
    db: AsyncSession, test_tenant: Tenant, test_user: User, session_factory
):
    broken = await _account(db, test_tenant.id, test_user.id, "broken@example.nl")
    good = await _account(db, test_tenant.id, test_user.id, "good@example.nl")
    await db.commit()

    called: list[str] = []

    async def fake_sync(session, account, max_results=50):
        called.append(account.email_address)
        if account.email_address == "broken@example.nl":
            raise RuntimeError("token verlopen")
        return {"new": 0, "linked": 0}

    async def fake_backfill(session, tenant_id):
        return 0

    with patch("app.workflow.scheduler.async_session", session_factory), \
         patch("app.email.sync_service.sync_emails_for_account", fake_sync), \
         patch("app.ai_agent.learned_answers.backfill_learned_answers", fake_backfill):
        await email_auto_sync()

    # Beide postbussen zijn geprobeerd — de kapotte hield de goede niet tegen.
    assert "broken@example.nl" in called
    assert "good@example.nl" in called

    # Verse stand uit de DB: kapotte draagt de fout, goede is schoon.
    await db.refresh(broken)
    await db.refresh(good)
    assert broken.last_sync_error is not None
    assert "token verlopen" in broken.last_sync_error
    assert good.last_sync_error is None


# ── S221 blok 4 (B3): classificatie meteen ná de sync bij nieuwe mail ────────
# Deze trigger draaide op prod nog nooit (geen nieuwe mail sinds deploy) en had
# geen test. Twee gevallen: verse mail → classificatie meteen; geen verse mail →
# niet (geen dubbel werk met de reguliere 6-min-cyclus).


async def _run_sync_with_new(db, session_factory, *, new_count: int, has_key: bool):
    """Draai email_auto_sync met een gemockte sync die `new_count` verse mails
    teruggeeft; retourneert of ai_email_classification werd aangeroepen."""
    called = {"classify": 0}

    async def fake_sync(session, account, max_results=50):
        return {"new": new_count, "linked": 0}

    async def fake_backfill(session, tenant_id):
        return 0

    async def fake_classify():
        called["classify"] += 1

    from app.config import settings as app_settings

    with patch("app.workflow.scheduler.async_session", session_factory), \
         patch("app.email.sync_service.sync_emails_for_account", fake_sync), \
         patch("app.ai_agent.learned_answers.backfill_learned_answers", fake_backfill), \
         patch("app.workflow.scheduler.ai_email_classification", fake_classify), \
         patch.object(app_settings, "anthropic_api_key", "sk-test" if has_key else None):
        await email_auto_sync()

    return called["classify"]


@pytest.mark.asyncio
async def test_new_mail_triggers_classification(
    db: AsyncSession, test_tenant: Tenant, test_user: User, session_factory
):
    """Verse mail binnengekomen → classificatie meteen getriggerd (niet wachten
    op de losse 6-min-cyclus)."""
    await _account(db, test_tenant.id, test_user.id, "inbox@example.nl")
    await db.commit()

    calls = await _run_sync_with_new(db, session_factory, new_count=2, has_key=True)
    assert calls == 1


@pytest.mark.asyncio
async def test_no_new_mail_skips_classification(
    db: AsyncSession, test_tenant: Tenant, test_user: User, session_factory
):
    """Geen verse mail → geen extra classificatie-run (voorkomt dubbel werk)."""
    await _account(db, test_tenant.id, test_user.id, "inbox@example.nl")
    await db.commit()

    calls = await _run_sync_with_new(db, session_factory, new_count=0, has_key=True)
    assert calls == 0


@pytest.mark.asyncio
async def test_new_mail_without_key_skips_classification(
    db: AsyncSession, test_tenant: Tenant, test_user: User, session_factory
):
    """Verse mail maar geen AI-sleutel → geen classificatie (geen call zonder key)."""
    await _account(db, test_tenant.id, test_user.id, "inbox@example.nl")
    await db.commit()

    calls = await _run_sync_with_new(db, session_factory, new_count=2, has_key=False)
    assert calls == 0
