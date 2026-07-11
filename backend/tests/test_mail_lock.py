"""Bouwfase-mailslot: geen enkele uitgaande mail zolang env-noodslot OF DB-vlag aan staat."""

import pytest

from app.config import settings
from app.email import service as email_service
from app.email.providers.imap_provider import ImapProvider
from app.email.providers.outlook import OutlookProvider
from app.email.service import check_outbound_lock, send_email


@pytest.fixture
def lock_on(monkeypatch):
    monkeypatch.setattr(settings, "outbound_mail_lock", True)


@pytest.fixture
def db_lock_on(monkeypatch):
    """Zet alleen de DB-vlag aan (env-noodslot blijft uit)."""
    monkeypatch.setattr(email_service, "_db_mail_locked", True)


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
