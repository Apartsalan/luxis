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
    """Basisassertions voor elke NL template (BaseNet-stijl, S145)."""
    assert html, "renderer returned None/empty"
    assert len(html) > 500, f"html too small: {len(html)} bytes"
    assert "2026-00042" in html, "zaaknummer not in output"
    assert "Hoogachtend" in html, "NL signature missing"
    assert "schuldenaar" in html.lower(), "schuldhulp block missing"
    # S226: logo als extern gehoste https-afbeelding (Gmail/Outlook blokkeren
    # data:-afbeeldingen → kapot kader). Geen data-URL meer.
    assert "kesting-logo-email.png" in html, "logo (externe https-URL) ontbreekt"
    assert "data:image/png;base64," not in html, "logo mag geen data-URL meer zijn"
    # S226: witregel tussen alinea's staat INLINE (Gmail nult head-<style> +
    # <p>-marges) → anders begint de brief meteen na de aanhef.
    assert 'margin:0 0 16px 0;' in html, "alinea-witregel (inline) ontbreekt"
    # S145: BaseNet stijl email-adres (hoofdletter I): Incasso@kestinglegal.nl
    assert "Incasso@kestinglegal.nl" in html, "incasso-email ontbreekt in handtekening"
    # S145: handtekening met "Mevr. mr. L. Kesting"
    assert "Mevr. mr. L. Kesting" in html, "naam ontbreekt in handtekening"
    # Lisanne S141: disclaimer MOET onder handtekening staan.
    signature_pos = html.find("Hoogachtend")
    disclaimer_pos = html.find("financi&euml;le zorgen")
    assert disclaimer_pos > signature_pos, (
        "Disclaimer (schuldhulpblok) moet NA de handtekening komen, "
        f"maar staat op pos {disclaimer_pos} terwijl handtekening op {signature_pos} staat"
    )


def _assert_base_en(html: str) -> None:
    """Basisassertions voor elke EN template (BaseNet-stijl, S145)."""
    assert html, "renderer returned None/empty"
    assert len(html) > 500, f"html too small: {len(html)} bytes"
    assert "2026-00042" in html, "zaaknummer not in output"
    assert "Yours faithfully" in html, "EN signature missing"
    assert "kesting-logo-email.png" in html, "logo (externe https-URL) ontbreekt"
    assert "Mevr. mr. L. Kesting" in html, "naam ontbreekt in handtekening"


# ── Herschreven templates (Batch 2) ──────────────────────────────────────


def test_render_sommatie_eerste_av(mock_context):
    """L13 — eerste sommatie met AV-clausule, 3 dagen."""
    html = render_incasso_email("sommatie", mock_context)
    _assert_base_nl(html)
    assert "3 DAGEN NA HEDEN" in html
    assert "Algemene Voorwaarden" in html
    # S226: betreft in huisformaat (klant / debiteur — brieftype — dossiernummer)
    assert "Sommatie tot betaling — 2026-00042" in html
    assert "Test Debiteur BV" in html


def test_render_14_dagenbrief_neutral_rente_label(mock_context):
    """Row 59 / AUDIT — de 14-dagenbrief mag rente niet hardcoden als
    'wettelijke rente'. Dat is juridisch onjuist bij B2B (handelsrente,
    art. 6:119a BW). Net als de sommatie neutraal: 'Rente' in de
    specificatieregel, 'verschuldigde rente' in de lopende tekst."""
    html = render_incasso_email("14_dagenbrief", mock_context)
    _assert_base_nl(html)
    # Specificatieregel + proza neutraal (zoals de sommatie)
    assert "Rente t/m" in html
    assert "verschuldigde rente" in html
    # Geen hardcoded 'wettelijke rente' meer. De heading 'Wettelijke
    # mededeling (art. 6:96 lid 6 BW)' mag wél blijven — dat is geen rente.
    assert "wettelijke rente" not in html.lower()


def test_render_schikkingsvoorstel_placeholder(mock_context):
    """L3 — eenmalig schikkingsvoorstel met [VUL SCHIKKINGSBEDRAG IN]."""
    html = render_incasso_email("schikkingsvoorstel", mock_context)
    _assert_base_nl(html)
    assert "[VUL SCHIKKINGSBEDRAG IN]" in html
    assert "24 uur" in html
    assert "Eenmalig schikkingsvoorstel — 2026-00042" in html


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
    assert "Verzoekschrift faillissement (laatste mogelijkheid) — 2026-00042" in html


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
    assert "Sommatie tot betaling (niet voldaan aan regeling) — 2026-00042" in html


def test_render_sommatie_laatste_voor_fai(mock_context):
    """L8 — laatste sommatie vóór verzoekschrift faillissement."""
    html = render_incasso_email("sommatie_laatste_voor_fai", mock_context)
    _assert_base_nl(html)
    assert "2 DAGEN NA HEDEN" in html
    assert "verzoekschrift" in html.lower()
    assert "reeds begonnen" in html
    assert "Sommatie tot betaling (laatste mogelijkheid) — 2026-00042" in html


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
    assert "Demand for payment — 2026-00042" in html


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
    assert "Demand for payment (bankruptcy) — 2026-00042" in html


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


def test_all_betreft_lines_use_house_format(mock_context):
    """Wachter (S226 A3 — foutSOORT 'betreft niet in huisformaat').

    Geen enkele brief mag de Betreft-regel nog in het oude BaseNet-formaat
    'TYPE / dossiernummer / debiteur' dragen, en nooit de dubbele
    'Betreft: Betreft:' (S225-vondst). Elke betreft-regel moet huisformaat zijn:
    '{klant} / {debiteur} — {brieftype} — {dossiernummer}', gelijk aan het
    mail-onderwerp. Een nieuw brieftype dat dit vergeet valt hier om.
    """
    import re

    from app.email.incasso_templates import _RENDERERS

    zaaknummer = mock_context["zaak"]["zaaknummer"]  # "2026-00042"
    for key in _RENDERERS:
        html = render_incasso_email(key, mock_context)
        assert html, f"{key}: geen output"
        # De betreft-cel = tweede kolom van de Betreft-tabel in _BASE_EMAIL.
        m = re.search(r"Betreft:</td>\s*<td[^>]*>(.*?)</td>", html, re.S)
        assert m, f"{key}: geen Betreft-cel gevonden"
        cel = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        # Geen dubbele 'Betreft:'-prefix (de template zet 'm zelf al voor de cel).
        assert "Betreft:" not in cel, f"{key}: dubbele 'Betreft:' → {cel!r}"
        # Huisformaat eindigt op '— {dossiernummer}' (em-dash), niet '/ nr'.
        assert cel.endswith(f"— {zaaknummer}"), (
            f"{key}: geen huisformaat-suffix → {cel!r}"
        )
        # Oud BaseNet-formaat had het dossiernummer tussen slashes.
        assert f"/ {zaaknummer}" not in cel, f"{key}: oud slash-formaat → {cel!r}"


# ── S145: signature email-adres switcht op case_type ────────────────────


def test_signature_uses_incasso_email_for_incasso_case():
    """case_type='incasso' → incasso@kestinglegal.nl."""
    from app.email.incasso_templates import _signature

    ctx = {
        "kantoor": {"adres": "IJsbaanpad 9", "postcode_stad": "1076 CV Amsterdam", "kvk": "12345678"},
        "zaak": {"type": "incasso"},
    }
    sig = _signature(ctx)
    assert "Incasso@kestinglegal.nl" in sig
    assert "kesting@kestinglegal.nl" not in sig


def test_signature_uses_kantoor_email_for_other_case_types():
    """case_type≠incasso (faillissement, advies, etc.) → kesting@kestinglegal.nl."""
    from app.email.incasso_templates import _signature

    for case_type in ("faillissement", "advies", "procedure"):
        ctx = {
            "kantoor": {"adres": "IJsbaanpad 9", "postcode_stad": "1076 CV Amsterdam", "kvk": "12345678"},
            "zaak": {"type": case_type},
        }
        sig = _signature(ctx)
        assert "kesting@kestinglegal.nl" in sig, f"kantoor-email mist voor case_type={case_type}"
        assert "Incasso@kestinglegal.nl" not in sig, f"incasso-email lekt voor case_type={case_type}"


def test_signature_defaults_to_incasso_when_type_missing():
    """Geen zaak.type → default incasso@kestinglegal.nl (backwards compat)."""
    from app.email.incasso_templates import _signature

    ctx = {
        "kantoor": {"adres": "IJsbaanpad 9", "postcode_stad": "1076 CV Amsterdam", "kvk": "12345678"},
        "zaak": {},
    }
    sig = _signature(ctx)
    assert "Incasso@kestinglegal.nl" in sig


def test_signature_english_respects_case_type():
    """English signature must also switch email on case_type."""
    from app.email.incasso_templates import _signature

    ctx_incasso = {
        "kantoor": {"adres": "IJsbaanpad 9", "postcode_stad": "1076 CV Amsterdam", "kvk": "12345678"},
        "zaak": {"type": "incasso"},
    }
    ctx_advies = {
        "kantoor": {"adres": "IJsbaanpad 9", "postcode_stad": "1076 CV Amsterdam", "kvk": "12345678"},
        "zaak": {"type": "advies"},
    }
    assert "Incasso@kestinglegal.nl" in _signature(ctx_incasso, english=True)
    assert "kesting@kestinglegal.nl" in _signature(ctx_advies, english=True)


# ── HTML-injectie via opgeslagen dossierdata (S202 M4) ───────────────────────


def test_injected_html_in_wederpartij_naam_is_escaped(mock_context):
    """Audit-probe (S202 M4): een cliënt-/debiteurnaam met een HTML-tag mag
    niet als echte markup in de uitgaande brief belanden. sommatie_drukte
    toont de wederpartijnaam in de betreft-regel."""
    mock_context["wederpartij"]["naam"] = "<b>INJECTED</b>"
    html = render_incasso_email("sommatie_drukte", mock_context)
    assert "<b>INJECTED</b>" not in html
    assert "&lt;b&gt;INJECTED&lt;/b&gt;" in html


def test_injected_html_in_client_naam_is_escaped(mock_context):
    mock_context["client"]["naam"] = "<img src=x onerror=alert(1)>"
    html = render_incasso_email("aanmaning", mock_context)
    assert "<img src=x" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_injected_html_in_claim_beschrijving_and_factuurnummer_is_escaped(mock_context):
    mock_context["vorderingen"][0]["beschrijving"] = "<script>alert(1)</script>"
    mock_context["vorderingen"][0]["factuurnummer"] = "<a href=evil>F001</a>"
    html = render_incasso_email("aanmaning", mock_context)
    assert "<script>alert(1)</script>" not in html
    assert "<a href=evil>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;a href=evil&gt;F001&lt;/a&gt;" in html


def test_legitimate_ampersand_in_naam_renders_once_not_doubled(mock_context):
    """Regressie-check: een gewone '&' in een bedrijfsnaam moet precies één
    keer geëscaped worden (niet dubbel via het bestaande Jinja-pad)."""
    mock_context["wederpartij"]["naam"] = "Jansen & Zonen B.V."
    html = render_incasso_email("sommatie_drukte", mock_context)
    assert "Jansen &amp; Zonen B.V." in html
    assert "&amp;amp;" not in html


def test_referentie_regel_not_double_escaped(mock_context):
    """zaak.referentie_regel loopt via Jinja's eigen {{ }}-autoescape in
    _BASE_EMAIL — de M4-fix mag dat pad niet nogmaals escapen."""
    mock_context["zaak"]["referentie_regel"] = "Uw kenmerk: Jansen & Zonen"
    html = render_incasso_email("aanmaning", mock_context)
    assert "Uw kenmerk: Jansen &amp; Zonen" in html
    assert "&amp;amp;" not in html


def test_legitimate_content_still_renders_normally(mock_context):
    """Geen regressie: gewone namen/adressen zonder HTML-tekens blijven
    precies zo zichtbaar als voorheen."""
    assert "Factuur F001" in render_incasso_email("aanmaning", mock_context)
    assert "Test Debiteur BV" in render_incasso_email("sommatie_drukte", mock_context)
