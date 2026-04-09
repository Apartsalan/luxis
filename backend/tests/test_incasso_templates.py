"""Render tests voor de 15 Basenet-incasso templates (DF120-09).

Test per renderer:
- Render-functie produceert geldige HTML-string (geen None, >1KB)
- Zaaknummer staat in de betreft-regel
- Derdengelden IBAN + Stichting Beheer Derdengelden aanwezig (alle NL + EN)
- Correcte termijn-tekst voor het template-type
- Voor templates met placeholders: marker-tekst aanwezig
- Schuldhulp-disclaimer (alleen NL)
- Signature aanwezig (NL 'Hoogachtend' of EN 'Yours faithfully')

Context is een minimale mock dat de velden levert die alle renderers
nodig hebben. Voor fine-grained financiële tests zie
test_incasso_pipeline.py.
"""

import pytest

from app.email.incasso_templates import render_incasso_email


@pytest.fixture
def mock_context() -> dict:
    """Minimale render-context met alle velden die helpers nodig hebben."""
    return {
        "kantoor": {
            "naam": "Kesting Legal",
            "adres": "IJsbaanpad 9",
            "postcode_stad": "1076 CV Amsterdam",
            "email": "kesting@kestinglegal.nl",
            "telefoon": "06-22184090",
            "kvk": "12345678",
            "iban": "NL20 RABO 0388 5065 20",
            "btw": "NL001234567B01",
        },
        "wederpartij": {
            "naam": "Test Debiteur BV",
            "adres": "Teststraat 1",
            "postcode_stad": "1000 AA Amsterdam",
        },
        "client": {
            "naam": "Opdrachtgever BV",
            "postcode_stad": "Amsterdam",
        },
        "zaak": {
            "zaaknummer": "2026-00042",
            "referentie_regel": None,
        },
        "vandaag": "9 april 2026",
        "totaal_hoofdsom": "€ 5.000,00",
        "totaal_rente": "€ 200,00",
        "subtotaal": "€ 5.200,00",
        "bik_bedrag": "€ 625,00",
        "btw_regel_label": "BTW 21%",
        "btw_regel_bedrag": "€ 131,25",
        "totaal_verschuldigd": "€ 5.956,25",
        "betalingen_aftrek_label": "Voldaan bij klant",
        "betalingen_aftrek_bedrag": "€ 0,00",
        "betalingen_regel_label": "Reeds voldaan",
        "betalingen_regel_bedrag": "€ 0,00",
        "totaal_openstaand": "€ 5.956,25",
        "termijn_14_dagen": "23 april 2026",
        "termijn_30_dagen": "9 mei 2026",
        "btw_toelichting": " excl. BTW",
        "vorderingen": [
            {
                "beschrijving": "Factuur F001",
                "factuurnummer": "F001",
                "verzuimdatum": "1-3-2026",
                "hoofdsom": "€ 5.000,00",
            },
        ],
    }


# ── Shared assertions ────────────────────────────────────────────────────


def _assert_base_nl(html: str) -> None:
    """Basisassertions voor elke NL template."""
    assert html, "renderer returned None/empty"
    assert len(html) > 1000, f"html too small: {len(html)} bytes"
    assert "2026-00042" in html, "zaaknummer not in output"
    assert "NL20 RABO 0388 5065 20" in html, "derdengelden IBAN missing"
    assert "Stichting Beheer Derdengelden" in html, "stichting missing"
    assert "Hoogachtend" in html, "NL signature missing"
    assert "schuldenaar" in html.lower(), "schuldhulp block missing"


def _assert_base_en(html: str) -> None:
    """Basisassertions voor elke EN template."""
    assert html, "renderer returned None/empty"
    assert len(html) > 1000, f"html too small: {len(html)} bytes"
    assert "2026-00042" in html, "zaaknummer not in output"
    assert "NL20 RABO 0388 5065 20" in html, "derdengelden IBAN missing"
    assert "Stichting Beheer Derdengelden" in html, "stichting missing"
    assert "Yours faithfully" in html, "EN signature missing"


# ── Herschreven templates (Batch 2) ──────────────────────────────────────


def test_render_sommatie_eerste_av(mock_context):
    """L13 — eerste sommatie met AV-clausule, 3 dagen."""
    html = render_incasso_email("sommatie", mock_context)
    _assert_base_nl(html)
    assert "3 DAGEN NA HEDEN" in html
    assert "Algemene Voorwaarden" in html
    assert "SOMMATIE TOT BETALING" in html
    assert "Test Debiteur BV" in html


def test_render_schikkingsvoorstel_placeholder(mock_context):
    """L3 — eenmalig schikkingsvoorstel met [VUL SCHIKKINGSBEDRAG IN]."""
    html = render_incasso_email("schikkingsvoorstel", mock_context)
    _assert_base_nl(html)
    assert "[VUL SCHIKKINGSBEDRAG IN]" in html
    assert "24 uur" in html
    assert "EENMALIG SCHIKKINGSVOORSTEL" in html


def test_render_vaststellingsovereenkomst_placeholders(mock_context):
    """L2 — VSO: totaalbedrag auto (= totaal_openstaand), termijnen handmatig."""
    html = render_incasso_email("vaststellingsovereenkomst", mock_context)
    _assert_base_nl(html)
    # Totaalbedrag wordt automatisch gevuld met totaal_openstaand (default
    # voor 95% van de VSO's — Lisanne kan overschrijven bij onderhandeling)
    assert "€ 5.956,25" in html  # = totaal_openstaand uit mock_context
    # Alleen termijnen blijven handmatig (geen deterministische default)
    assert "[VUL TERMIJNEN IN" in html
    # Auto-fill mag er niet meer zijn
    assert "[VUL TOTAALBEDRAG" not in html
    assert "2 x 24 uur" in html
    assert "Vaststellingsovereenkomst" in html


def test_render_faillissement_dreigbrief(mock_context):
    """L7 — faillissement dreigbrief met 2 dagen + verwijzing naar bijlage."""
    html = render_incasso_email("faillissement_dreigbrief", mock_context)
    _assert_base_nl(html)
    assert "2 DAGEN NA HEDEN" in html
    assert "verzoekschrift" in html.lower()
    assert "in de bijlage" in html
    assert "VERZOEKSCHRIFT FAILLISSEMENT" in html


# ── Nieuwe NL templates (Batch 3) ────────────────────────────────────────


def test_render_sommatie_na_reactie(mock_context):
    """L1 — sommatie nadat debiteur heeft gereageerd."""
    html = render_incasso_email("sommatie_na_reactie", mock_context)
    _assert_base_nl(html)
    assert "2 DAGEN NA HEDEN" in html
    assert "U heeft gereageerd" in html
    assert "Betalingsregeling" in html


def test_render_sommatie_eerste_opgave(mock_context):
    """L4 — eerste opgave vordering direct na overdracht."""
    html = render_incasso_email("sommatie_eerste_opgave", mock_context)
    _assert_base_nl(html)
    assert "per omgaand" in html
    assert "6:44 BW" in html


def test_render_niet_voldaan_regeling(mock_context):
    """L5 — opeising na breuk vaststellingsovereenkomst."""
    html = render_incasso_email("niet_voldaan_regeling", mock_context)
    _assert_base_nl(html)
    assert "2 DAGEN NA HEDEN" in html
    assert "vaststellingsovereenkomst" in html.lower()
    assert "NIET VOLDAAN AAN REGELING" in html


def test_render_sommatie_laatste_voor_fai(mock_context):
    """L8 — laatste sommatie vóór verzoekschrift faillissement."""
    html = render_incasso_email("sommatie_laatste_voor_fai", mock_context)
    _assert_base_nl(html)
    assert "2 DAGEN NA HEDEN" in html
    assert "verzoekschrift" in html.lower()
    assert "reeds begonnen" in html
    assert "LAATSTE MOGELIJKHEID" in html


def test_render_wederom_sommatie_inhoudelijk_placeholder(mock_context):
    """L11 — wederom sommatie met placeholder voor verweer-reactie."""
    html = render_incasso_email("wederom_sommatie_inhoudelijk", mock_context)
    _assert_base_nl(html)
    assert "[HIER INHOUDELIJKE REACTIE OP VERWEER INVULLEN]" in html
    assert "3 dagen na heden" in html
    assert "artikel 3:317 BW" in html  # stuiting
    assert "Stuiting vordering" in html


def test_render_wederom_sommatie_kort(mock_context):
    """L12 — wederom sommatie zonder verweer-blok."""
    html = render_incasso_email("wederom_sommatie_kort", mock_context)
    _assert_base_nl(html)
    assert "3 dagen na heden" in html
    assert "artikel 3:317 BW" in html
    # Mag de inhoudelijke placeholder NIET hebben
    assert "[HIER INHOUDELIJKE REACTIE" not in html


def test_render_sommatie_drukte(mock_context):
    """L15 — eerste sommatie met drukte-notitie."""
    html = render_incasso_email("sommatie_drukte", mock_context)
    _assert_base_nl(html)
    assert "3 DAGEN NA HEDEN" in html
    assert "drukte" in html.lower()
    assert "incasso@kestinglegal.nl" in html


# ── Nieuwe EN templates (Batch 4) ────────────────────────────────────────


def test_render_demand_for_payment_eerste(mock_context):
    """L14 — English first demand, 3 days."""
    html = render_incasso_email("demand_for_payment_eerste", mock_context)
    _assert_base_en(html)
    assert "3 DAYS FROM TODAY" in html
    assert "DEMAND FOR PAYMENT" in html


def test_render_demand_for_payment_uitgebreid(mock_context):
    """L10 — English demand + interruption + payment arrangement."""
    html = render_incasso_email("demand_for_payment_uitgebreid", mock_context)
    _assert_base_en(html)
    assert "3 DAYS FROM TODAY" in html
    assert "Interruption of the claim" in html
    assert "Article 3:317" in html
    assert "Payment arrangement" in html


def test_render_demand_for_payment_laatste(mock_context):
    """L9 — English last chance, petition in preparation."""
    html = render_incasso_email("demand_for_payment_laatste", mock_context)
    _assert_base_en(html)
    assert "2 DAYS FROM TODAY" in html
    assert "begun drafting the petition" in html


def test_render_demand_for_payment_fai(mock_context):
    """L6 — English demand with petition attached."""
    html = render_incasso_email("demand_for_payment_fai", mock_context)
    _assert_base_en(html)
    assert "2 DAYS FROM TODAY" in html
    assert "petition is attached" in html
    assert "BANKRUPTCY" in html


# ── _RENDERERS registratie check ─────────────────────────────────────────


def test_all_15_new_keys_registered():
    """Alle 15 Basenet-templates moeten in _RENDERERS staan."""
    from app.email.incasso_templates import _RENDERERS

    required_keys = {
        # Herschreven bestaande
        "sommatie",
        "schikkingsvoorstel",
        "vaststellingsovereenkomst",
        "faillissement_dreigbrief",
        # Nieuwe NL (Batch 3)
        "sommatie_na_reactie",
        "sommatie_eerste_opgave",
        "niet_voldaan_regeling",
        "sommatie_laatste_voor_fai",
        "wederom_sommatie_inhoudelijk",
        "wederom_sommatie_kort",
        "sommatie_drukte",
        # Nieuwe EN (Batch 4)
        "demand_for_payment_eerste",
        "demand_for_payment_uitgebreid",
        "demand_for_payment_laatste",
        "demand_for_payment_fai",
    }
    missing = required_keys - set(_RENDERERS.keys())
    assert not missing, f"Missing renderer keys: {missing}"


def test_render_unknown_returns_none(mock_context):
    """Onbekende template_type moet None returnen (fallback signal)."""
    result = render_incasso_email("does_not_exist_xyz", mock_context)
    assert result is None
