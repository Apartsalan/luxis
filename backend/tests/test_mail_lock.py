"""Bouwfase-mailslot: geen enkele uitgaande mail zolang env-noodslot OF DB-vlag aan staat."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.email import service as email_service
from app.email.providers.imap_provider import ImapProvider
from app.email.providers.outlook import OutlookProvider
from app.email.service import check_outbound_lock, load_mail_lock, send_email


@pytest.fixture
def lock_on(monkeypatch):
    monkeypatch.setattr(settings, "outbound_mail_lock", True)


@pytest.fixture
def db_lock_on(monkeypatch):
    """Zet alleen de DB-vlag aan (env-noodslot blijft uit)."""
    monkeypatch.setattr(email_service, "_db_mail_locked", True)


@pytest.fixture
def restore_mail_lock():
    """Herstel de globale DB-vlag na een test die 'm via de API omzet, zodat
    andere tests (die mail versturen) niet omvallen."""
    original = email_service._db_mail_locked
    yield
    email_service._db_mail_locked = original


def test_lock_off_is_default_and_passes():
    assert settings.outbound_mail_lock is False
    assert email_service.db_mail_locked() is False
    check_outbound_lock()  # geen exceptie


def test_db_flag_blocks_even_without_env_lock(db_lock_on):
    """De UI-schakelbare DB-vlag blokkeert ook als het env-noodslot uit staat."""
    assert settings.outbound_mail_lock is False
    with pytest.raises(RuntimeError, match="op slot"):
        check_outbound_lock()


@pytest.mark.asyncio
async def test_mail_lock_toggle_via_api(
    client: AsyncClient, auth_headers: dict, restore_mail_lock
):
    """De knop werkt end-to-end: open -> mail mag; op slot -> geblokkeerd."""
    # Openen (uit)
    r = await client.put("/api/settings/mail-lock", json={"locked": False}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["db_locked"] is False
    assert r.json()["locked"] is False  # env-noodslot staat uit in tests
    check_outbound_lock()  # geen exceptie

    # Weer op slot
    r = await client.put("/api/settings/mail-lock", json={"locked": True}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["db_locked"] is True
    with pytest.raises(RuntimeError, match="op slot"):
        check_outbound_lock()


@pytest.mark.asyncio
async def test_set_mail_lock_leaves_memory_unchanged_on_failed_commit(
    db: AsyncSession, restore_mail_lock, monkeypatch
):
    """S202 L5: als de commit mislukt, mag het geheugen niet alvast zijn
    bijgewerkt — anders staat de knop 'open' in het geheugen terwijl de DB nog
    op slot staat, tot een herstart of de volgende toggle."""
    from app.email import service as email_service_module

    email_service_module._db_mail_locked = True  # startpunt: dicht

    async def _boom():
        raise RuntimeError("connection lost")

    monkeypatch.setattr(db, "commit", _boom)

    with pytest.raises(RuntimeError, match="connection lost"):
        await email_service_module.set_mail_lock(db, False)

    assert email_service_module._db_mail_locked is True  # ongewijzigd, nog dicht


@pytest.mark.asyncio
async def test_load_mail_lock_failsafe_locked_without_row(db: AsyncSession, restore_mail_lock):
    """Fail-safe: geen app_config-rij -> op slot (True), niet per ongeluk open."""
    result = await load_mail_lock(db)
    assert result is True
    assert email_service.db_mail_locked() is True


@pytest.mark.asyncio
async def test_lock_blocks_smtp_bridge(lock_on):
    with pytest.raises(RuntimeError, match="op slot"):
        await send_email(to="x@example.com", subject="t", html_body="<p>t</p>")


@pytest.mark.asyncio
async def test_lock_blocks_imap_provider(lock_on):
    with pytest.raises(RuntimeError, match="op slot"):
        await ImapProvider().send_message(
            "wachtwoord",
            to=["x@example.com"],
            subject="t",
            body_html="<p>t</p>",
            smtp_host="smtp.example.com",
            username="incasso@example.com",
        )


@pytest.mark.asyncio
async def test_lock_blocks_outlook_provider(lock_on):
    with pytest.raises(RuntimeError, match="op slot"):
        await OutlookProvider().send_message(
            "token",
            to=["x@example.com"],
            subject="t",
            body_html="<p>t</p>",
        )
