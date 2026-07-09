"""Tests voor IMAP/SMTP-verzending (S186) — versturen áls incasso@ via BaseNet.

De echte SMTP-verbinding wordt gemonkeypatcht; we controleren dat het bericht
correct wordt opgebouwd (afzender, ontvangers, CC, bijlage, Message-ID) en dat
de juiste SMTP-parameters worden doorgegeven.
"""

import aiosmtplib
import pytest

import app.email.providers.imap_provider as imap_provider_module
from app.email.oauth_service import imap_smtp_kwargs
from app.email.providers.base import OutgoingAttachment
from app.email.providers.imap_provider import ImapProvider


@pytest.fixture
def no_sent_append(monkeypatch):
    """Schakel de Verzonden-kopie (IMAP APPEND) uit; vang de aanroep op."""
    calls: list = []

    def fake_append(host, port, username, password, raw):
        calls.append({"host": host, "username": username, "raw": raw})

    monkeypatch.setattr(imap_provider_module, "_append_to_sent", fake_append)
    return calls


@pytest.mark.asyncio
async def test_imap_send_builds_message_and_smtp_params(monkeypatch, no_sent_append):
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

    # Kopie gaat naar de Verzonden-map via de IMAP-tegenhanger van de SMTP-host.
    assert len(no_sent_append) == 1
    assert no_sent_append[0]["host"] == "imap.basenet.nl"
    assert no_sent_append[0]["username"] == "incasso@kestinglegal.nl"


@pytest.mark.asyncio
async def test_imap_send_survives_failing_sent_append(monkeypatch):
    """De Verzonden-kopie mag de verzending nooit laten falen."""

    async def fake_send(msg, **kwargs):
        pass

    def broken_append(*args):
        raise ConnectionError("IMAP down")

    monkeypatch.setattr(aiosmtplib, "send", fake_send)
    monkeypatch.setattr(imap_provider_module, "_append_to_sent", broken_append)

    message_id = await ImapProvider().send_message(
        "pw",
        to=["a@example.com"],
        subject="x",
        body_html="<p>x</p>",
        smtp_host="smtp.basenet.nl",
        smtp_port=587,
        username="incasso@kestinglegal.nl",
    )
    assert message_id  # verzending geslaagd ondanks kapotte Verzonden-kopie


@pytest.mark.asyncio
async def test_imap_send_sets_thread_headers(monkeypatch, no_sent_append):
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
async def test_imap_reply_references_start_at_thread_root(monkeypatch, no_sent_append):
    """Antwoord middenin een keten: References begint bij de wortel, niet de
    directe voorganger — zo deelt het verzonden antwoord dezelfde thread_id als
    de rest van het gesprek."""
    captured: dict = {}

    async def fake_send(msg, **kwargs):
        captured["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    await ImapProvider().send_message(
        "pw",
        to=["a@example.com"],
        subject="Re: iets",
        body_html="<p>antwoord</p>",
        reply_to_message_id="<parent@basenet.nl>",
        references_root="<root@basenet.nl>",
        smtp_host="smtp.basenet.nl",
        smtp_port=587,
        username="incasso@kestinglegal.nl",
    )
    msg = captured["msg"]
    assert msg["In-Reply-To"] == "<parent@basenet.nl>"
    # Wortel eerst → References[0] = de echte draad-wortel.
    assert msg["References"] == "<root@basenet.nl> <parent@basenet.nl>"
    assert msg["References"].split()[0] == "<root@basenet.nl>"


@pytest.mark.asyncio
async def test_imap_reply_root_equals_parent_not_duplicated(monkeypatch, no_sent_append):
    """Antwoord op de wortel zelf: geen dubbele Message-ID in References."""
    captured: dict = {}

    async def fake_send(msg, **kwargs):
        captured["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    await ImapProvider().send_message(
        "pw",
        to=["a@example.com"],
        subject="Re: iets",
        body_html="<p>antwoord</p>",
        reply_to_message_id="<root@basenet.nl>",
        references_root="<root@basenet.nl>",
        smtp_host="smtp.basenet.nl",
        smtp_port=587,
        username="incasso@kestinglegal.nl",
    )
    assert captured["msg"]["References"] == "<root@basenet.nl>"


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


def _raw_email(message_id: str, in_reply_to: str = "", references: str = "") -> bytes:
    headers = [
        f"Message-ID: {message_id}",
        "From: iemand@example.com",
        "To: incasso@kestinglegal.nl",
        "Subject: test",
        "Date: Tue, 08 Jul 2026 10:00:00 +0000",
    ]
    if in_reply_to:
        headers.append(f"In-Reply-To: {in_reply_to}")
    if references:
        headers.append(f"References: {references}")
    return ("\r\n".join(headers) + "\r\n\r\nBody.\r\n").encode()


def test_thread_id_root_uses_own_message_id():
    from app.email.providers.imap_provider import _imap_message_to_email

    msg = _imap_message_to_email("1", _raw_email("<root@x>"))
    assert msg.thread_id == "<root@x>"


def test_thread_id_uses_references_root_across_the_chain():
    from app.email.providers.imap_provider import _imap_message_to_email

    # Diepe reply: References = "root parent grootouder..." → wortel wint,
    # zodat hij dezelfde thread deelt als de allereerste mail.
    deep = _imap_message_to_email(
        "3", _raw_email("<c@x>", in_reply_to="<b@x>", references="<root@x> <b@x>")
    )
    assert deep.thread_id == "<root@x>"


def test_thread_id_falls_back_to_in_reply_to_without_references():
    from app.email.providers.imap_provider import _imap_message_to_email

    msg = _imap_message_to_email("2", _raw_email("<b@x>", in_reply_to="<root@x>"))
    assert msg.thread_id == "<root@x>"


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


# ── Gelezen-status (\Seen) meelezen ─────────────────────────────────────────


def test_seen_flag_present_reads_descriptor_not_body():
    from app.email.providers.imap_provider import _seen_flag_present

    # Typische imaplib-vorm: (descriptor-bytes, body-bytes), gevolgd door b')'.
    seen = [(b"1 (FLAGS (\\Seen) RFC822 {12}", b"body zonder vlag"), b")"]
    unseen = [(b"2 (FLAGS () RFC822 {12}", b"body \\Seen in tekst"), b")"]
    assert _seen_flag_present(seen) is True
    # Body noemt "\\Seen" maar de descriptor niet → als ongelezen zien.
    assert _seen_flag_present(unseen) is False


def test_imap_message_to_email_respects_is_read():
    from app.email.providers.imap_provider import _imap_message_to_email

    read = _imap_message_to_email("1", _raw_email("<a@x>"), is_read=True)
    unread = _imap_message_to_email("2", _raw_email("<b@x>"), is_read=False)
    assert read.is_read is True
    assert unread.is_read is False


# ── S188c-review-fixes: tekstversie, afzendernaam, IMAP-ontsmetting ──────────


def test_html_to_text_strips_tags_and_keeps_lines():
    from app.email.providers.imap_provider import _html_to_text

    out = _html_to_text("<p>Regel een</p><p>Regel twee</p>Drie<br>Vier")
    assert "Regel een" in out and "Regel twee" in out
    assert "Drie" in out and "Vier" in out
    assert "<" not in out and ">" not in out
    assert _html_to_text("") == ""


def test_html_to_text_placeholder_for_markup_without_text():
    from app.email.providers.imap_provider import _html_to_text

    assert _html_to_text("<div><img src='x'></div>").startswith("(deze e-mail")


def test_imap_quote_escapes_quote_and_backslash():
    from app.email.providers.imap_provider import _imap_quote

    assert _imap_quote('a"b') == 'a\\"b'
    assert _imap_quote("a\\b") == "a\\\\b"
    assert _imap_quote("<normaal@id>") == "<normaal@id>"


@pytest.mark.asyncio
async def test_imap_send_uses_display_name_and_real_text_part(monkeypatch, no_sent_append):
    """Afzender krijgt een weergavenaam en het text/plain-deel komt uit de HTML
    (niet meer de placeholder-zin)."""
    captured: dict = {}

    async def fake_send(msg, **kwargs):
        captured["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    await ImapProvider().send_message(
        "pw",
        to=["a@example.com"],
        subject="Test",
        body_html="<p>Gelieve <b>te betalen</b>.</p><p>Met groet</p>",
        from_name="Kesting Legal",
        smtp_host="smtp.basenet.nl",
        smtp_port=587,
        username="incasso@kestinglegal.nl",
    )
    msg = captured["msg"]
    assert msg["From"] == "Kesting Legal <incasso@kestinglegal.nl>"

    text_parts = [
        p.get_content() for p in msg.walk() if p.get_content_type() == "text/plain"
    ]
    joined = "\n".join(text_parts)
    assert "Gelieve te betalen." in joined
    assert "Met groet" in joined
    assert "opgemaakte (HTML) inhoud" not in joined


def test_compose_request_rejects_invalid_email():
    from pydantic import ValidationError

    from app.email.compose_router import ComposeRequest

    # Geldig adres → oké
    ComposeRequest(to=["goed@example.com"], subject="x", body_html="<p>x</p>")

    # Ongeldig adres → afgewezen
    with pytest.raises(ValidationError):
        ComposeRequest(to=["geen-adres"], subject="x", body_html="<p>x</p>")

    # Lege ontvangerslijst → afgewezen
    with pytest.raises(ValidationError):
        ComposeRequest(to=[], subject="x", body_html="<p>x</p>")

    # Ongeldig CC-adres → afgewezen
    with pytest.raises(ValidationError):
        ComposeRequest(
            to=["goed@example.com"], cc=["fout"], subject="x", body_html="<p>x</p>"
        )
