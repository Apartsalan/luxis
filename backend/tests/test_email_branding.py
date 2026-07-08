"""Huisstijl-aankleding van uitgaande mail (S186).

Alles wat vanuit de incasso-mailbox vertrekt draagt de sjabloon-opmaak
(handtekening + logo + schuldhulpblok); alleen de tekst verschilt. Al-opgemaakte
HTML (incasso-template, AI-concept) wordt niet dubbel aangekleed.
"""

import pytest

from app.email.incasso_templates import is_branded, render_plain_branded


def test_is_branded_detecteert_opgemaakt_en_kaal():
    assert is_branded("<p>Gewoon wat tekst</p>") is False
    assert is_branded('<table><tr><td>Betreft:</td></tr></table>') is True
    assert is_branded("<!DOCTYPE html><html><body>...</body></html>") is True


def _ctx() -> dict:
    return {
        "kantoor": {
            "naam": "Kesting Legal B.V.",
            "adres": "Teststraat 1",
            "postcode_stad": "1000 AA Amsterdam",
        },
        "wederpartij": {"naam": "Debiteur B.V."},
        "zaak": {"referentie_regel": "", "type": "incasso"},
        "vandaag": "08-07-2026",
    }


def test_render_plain_branded_voegt_handtekening_en_schuldhulp_toe():
    html = render_plain_branded(_ctx(), betreft="Betaling IN100019", content_html="<p>Uw reactie.</p>")
    # eigen tekst blijft
    assert "Uw reactie." in html
    # handtekening
    assert "L. Kesting" in html
    # schuldhulpblok (wettelijke onderkant)
    assert "schuldenaar" in html.lower()
    assert "113" in html
    # betreft-regel
    assert "Betaling IN100019" in html


def test_render_plain_branded_zet_citaat_onderaan():
    quote = '<div class="quote">Op 1 juli schreef X: hallo</div>'
    html = render_plain_branded(
        _ctx(), betreft="Re: iets", content_html="<p>Mijn antwoord.</p>", quoted_html=quote
    )
    # het citaat staat NA de handtekening/disclaimer (helemaal onderaan)
    assert html.index("Mijn antwoord.") < html.index("L. Kesting") < html.index("Op 1 juli schreef X")


@pytest.mark.asyncio
async def test_ensure_branded_body_force_kleedt_altijd_aan(monkeypatch):
    """force=True kleedt aan, ook als de body zelf 'Betreft:' bevat (geciteerd antwoord)."""
    import app.email.send_service as send_service

    async def fake_ctx(db, tenant_id, case=None):
        return _ctx()

    monkeypatch.setattr(send_service, "build_branding_context", fake_ctx)

    quoted_reply = "<p>Mijn antwoord.</p><div>Op 1 juli schreef X — Betreft: oud</div>"
    out = await send_service.ensure_branded_body(
        None, None, subject="Re: x", body_html=quoted_reply, force=True
    )
    assert "L. Kesting" in out  # aangekleed ondanks 'Betreft:' in het citaat


@pytest.mark.asyncio
async def test_ensure_branded_body_laat_opgemaakt_met_rust(monkeypatch):
    import app.email.send_service as send_service

    async def fake_ctx(db, tenant_id, case=None):
        return _ctx()

    monkeypatch.setattr(send_service, "build_branding_context", fake_ctx)

    already = "<!DOCTYPE html><html><body>al opgemaakt</body></html>"
    out = await send_service.ensure_branded_body(
        None, None, subject="x", body_html=already, force=False
    )
    assert out == already  # niet aangeraakt
