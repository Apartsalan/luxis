"""Tests voor IMAP/SMTP-verzending (S186) — versturen áls incasso@ via BaseNet.

De echte SMTP-verbinding wordt gemonkeypatcht; we controleren dat het bericht
correct wordt opgebouwd (afzender, ontvangers, CC, bijlage, Message-ID) en dat
de juiste SMTP-parameters worden doorgegeven.
"""

import aiosmtplib
import pytest

from app.email.oauth_service import imap_smtp_kwargs
from app.email.providers.base import OutgoingAttachment
from app.email.providers.imap_provider import ImapProvider


@pytest.mark.asyncio
async def test_imap_send_builds_message_and_smtp_params(monkeypatch):
    captured: dict = {}

    async def fake_send(msg, **kwargs):
        captured["msg"] = msg
        captured["kwargs"] = kwargs

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    provider = ImapProvider()
    message_id = await provider.send_message(
        "geheim-wachtwoord",
        to=["debiteur@example.com"],
        subject="Sommatie inzake IN100019",
        body_html="<p>Gelieve te betalen.</p>",
        cc=["kopie@example.com"],
        attachments=[
            OutgoingAttachment("factuur.pdf", b"%PDF-1.4 test", "application/pdf")
        ],
        smtp_host="smtp.basenet.nl",
        smtp_port=587,
        username="incasso@kestinglegal.nl",
    )

    msg = captured["msg"]
    kwargs = captured["kwargs"]

    # Afzender = het account zelf, niet een globale test-afzender.
    assert msg["From"] == "incasso@kestinglegal.nl"
    assert msg["To"] == "debiteur@example.com"
    assert msg["Cc"] == "kopie@example.com"
    assert msg["Subject"] == "Sommatie inzake IN100019"

    # SMTP-parameters kloppen (STARTTLS + AUTH met het IMAP-wachtwoord).
    assert kwargs["hostname"] == "smtp.basenet.nl"
    assert kwargs["port"] == 587
    assert kwargs["start_tls"] is True
    assert kwargs["username"] == "incasso@kestinglegal.nl"
    assert kwargs["password"] == "geheim-wachtwoord"

    # Message-ID wordt teruggegeven en zit in de header (sync dedupliceert hierop).
    assert message_id and message_id == msg["Message-ID"]

    # Bijlage zit in het bericht.
    filenames = [p.get_filename() for p in msg.walk() if p.get_filename()]
    assert "factuur.pdf" in filenames


@pytest.mark.asyncio
async def test_imap_send_sets_thread_headers(monkeypatch):
    captured: dict = {}

    async def fake_send(msg, **kwargs):
        captured["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    await ImapProvider().send_message(
        "pw",
        to=["a@example.com"],
        subject="Re: iets",
        body_html="<p>antwoord</p>",
        reply_to_message_id="<origineel@basenet.nl>",
        smtp_host="smtp.basenet.nl",
        smtp_port=587,
        username="incasso@kestinglegal.nl",
    )
    msg = captured["msg"]
    assert msg["In-Reply-To"] == "<origineel@basenet.nl>"
    assert msg["References"] == "<origineel@basenet.nl>"


@pytest.mark.asyncio
async def test_imap_send_requires_smtp_host_and_username():
    with pytest.raises(ValueError):
        await ImapProvider().send_message(
            "pw",
            to=["a@example.com"],
            subject="x",
            body_html="<p>x</p>",
            smtp_host="",
            username="",
        )


def test_imap_smtp_kwargs_derives_basenet_host():
    class Acc:
        provider = "imap"
        scopes = "imap.basenet.nl:993"
        email_address = "incasso@kestinglegal.nl"

    assert imap_smtp_kwargs(Acc()) == {
        "smtp_host": "smtp.basenet.nl",
        "smtp_port": 587,
        "username": "incasso@kestinglegal.nl",
    }


def test_imap_smtp_kwargs_empty_for_oauth_provider():
    class Acc:
        provider = "outlook"
        scopes = ""
        email_address = "seidony@kestinglegal.nl"

    assert imap_smtp_kwargs(Acc()) == {}
