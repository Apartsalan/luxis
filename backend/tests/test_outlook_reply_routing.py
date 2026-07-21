"""S234 — OutlookProvider mag NIET de Graph /reply-endpoint gebruiken met een
RFC Message-ID.

Live-bug (prod): antwoorden op een via IMAP gesyncte inkomende mail faalde met
400 op `POST /me/messages/<RFC-id>/reply`. Graph's /reply verwacht het
postvak-interne message-id (AAMk...); een RFC Message-ID (`<...@...>`) — of een
mail die dít postvak nooit zag — kan daar niet langs.

Afspraak: alleen /reply bij een Graph-id (geen `<`-prefix); een RFC-id valt terug
op gewone sendMail met het (reeds "Re:") onderwerp. Luxis groepeert de draad zelf
via provider_thread_id op het uitgaande record.
"""

import httpx
import pytest

from app.email import service as email_service
from app.email.providers import outlook as outlook_mod
from app.email.providers.outlook import OutlookProvider


class _FakeResp:
    status_code = 202

    def raise_for_status(self):
        return None

    def json(self):
        return {"id": "x", "webLink": None}


class _FakeClient:
    """Vangt de POST-URL's op i.p.v. echt naar Graph te gaan."""

    calls: list[str] = []

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, **kwargs):
        _FakeClient.calls.append(url)
        return _FakeResp()


@pytest.fixture(autouse=True)
def _patch_httpx(monkeypatch):
    _FakeClient.calls = []
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    # het bouwfase-mailslot mag de test niet blokkeren
    monkeypatch.setattr(email_service, "is_mail_locked", lambda: False)
    yield


@pytest.mark.asyncio
async def test_rfc_message_id_falls_back_to_sendmail():
    """RFC-id (`<...@...>`) → gewone sendMail, NIET de /reply-endpoint."""
    provider = OutlookProvider()
    await provider.send_message(
        "token",
        to=["debiteur@example.com"],
        subject="Re: Vraag over dossier 2026-00006",
        body_html="<p>hoi</p>",
        reply_to_message_id="<CACkvTp@mail.gmail.com>",
    )
    assert _FakeClient.calls == [f"{outlook_mod.GRAPH_API_BASE}/me/sendMail"]
    assert not any("/reply" in c for c in _FakeClient.calls)


@pytest.mark.asyncio
async def test_graph_id_uses_reply_endpoint():
    """Een echt Graph-id (geen `<`) mag wél de /reply-endpoint gebruiken."""
    provider = OutlookProvider()
    graph_id = "AAMkAGI2abcdef123"
    await provider.send_message(
        "token",
        to=["debiteur@example.com"],
        subject="Re: iets",
        body_html="<p>hoi</p>",
        reply_to_message_id=graph_id,
    )
    assert _FakeClient.calls == [
        f"{outlook_mod.GRAPH_API_BASE}/me/messages/{graph_id}/reply"
    ]


@pytest.mark.asyncio
async def test_no_reply_id_uses_sendmail():
    """Verse mail zonder reply-id → sendMail."""
    provider = OutlookProvider()
    await provider.send_message(
        "token",
        to=["x@example.com"],
        subject="Nieuw",
        body_html="<p>hoi</p>",
    )
    assert _FakeClient.calls == [f"{outlook_mod.GRAPH_API_BASE}/me/sendMail"]
