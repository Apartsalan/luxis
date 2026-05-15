"""Tests voor _to_html_entities — fix voor mojibake in outbound mails (S145).

Microsoft Graph API genereert outgoing emails met Content-Type charset=
Windows-1252. De UTF-8 body bytes worden door de ontvanger's mailclient
als Windows-1252 gedecodeerd, wat mojibake produceert (€ → â,¬, ë → Ã«).
HTML-entity escaping van non-ASCII chars omzeilt het probleem.
"""

from app.email.providers.outlook import _to_html_entities


def test_euro_sign_becomes_entity():
    assert _to_html_entities("€ 211,75") == "&#8364; 211,75"


def test_diacritics_become_entities():
    out = _to_html_entities("cliënte cliëntèl")
    assert "ë" not in out
    assert "è" not in out
    assert "&#235;" in out  # ë
    assert "&#232;" in out  # è


def test_em_dash_becomes_entity():
    out = _to_html_entities("Disclaimer — De informatie")
    assert "—" not in out
    assert "&#8212;" in out


def test_ascii_unchanged():
    src = "<p>Hello, world! 0123456789 @#$%^&*()_+-=[]{};:'\",.<>?/</p>"
    assert _to_html_entities(src) == src


def test_html_entities_already_present_pass_through():
    # &amp; and &#8364; are pure ASCII — should not double-encode
    src = "<p>Already &amp; encoded &#8364; here</p>"
    assert _to_html_entities(src) == src


def test_empty_input():
    assert _to_html_entities("") == ""
    assert _to_html_entities(None) == ""  # type: ignore[arg-type]


def test_full_kesting_legal_signature_is_safe():
    """Sanity: full BaseNet-style signature with €/ë/é renders pure ASCII."""
    sig = (
        "Hoogachtend,<br><br>"
        "<strong>Mevr. mr. L. Kesting</strong><br>"
        "INCASSO ADVOCAAT | DEBT COLLECTION ATTORNEY<br><br>"
        "Kesting Legal B.V.<br>"
        "IJsbaanpad 9<br>"
        "1076 CV Amsterdam<br>"
        "E: Incasso@kestinglegal.nl<br>"
        "Heeft u financiële zorgen?<br>"
        "Te voldoen: € 285,44"
    )
    out = _to_html_entities(sig)
    # ASCII-only after escape
    assert out.encode("ascii")  # raises if any non-ASCII remains
    # Original entities/HTML stay intact
    assert "<strong>" in out
    assert "Kesting Legal" in out
    # Euro + ë escaped
    assert "&#8364;" in out
    assert "&#235;" in out
