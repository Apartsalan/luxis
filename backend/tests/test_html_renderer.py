"""Tests voor server-side HTML template-renderer (incasso emails)."""

from decimal import Decimal

from app.incasso.html_renderer import (
    _extract_weerlegging,
    _fill_invoice_rows,
    render_subject,
    render_template_html,
)


_SAMPLE_TEMPLATE = """
<table>
<tr>
<td><b>Factuurnummer</b></td><td><b>Datum</b></td><td><b>Vervaldatum</b></td>
<td colspan="2"><b>Bedrag</b></td>
</tr>
<tr>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td colspan="2" style="padding:.100px .100px .100px .100px">&nbsp;</td>
</tr>
<tr>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
</tr>
<tr>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
<td style="padding:.100px .100px .100px .100px">&nbsp;</td>
</tr>
</table>
"""


def test_fill_single_invoice_uses_first_slot():
    invoices = [{"number": "F-001", "date": "01-01-2026",
                 "due_date": "15-01-2026", "amount": Decimal("1234.56")}]
    out = _fill_invoice_rows(_SAMPLE_TEMPLATE, invoices)
    assert "F-001" in out
    assert "01-01-2026" in out
    assert "1.234,56" in out


def test_fill_multiple_invoices_uses_all_slots():
    """Regressie: 5-cel rijen zonder colspan moeten ook gevuld worden."""
    invoices = [
        {"number": "F-001", "date": "01-01-2026",
         "due_date": "15-01-2026", "amount": Decimal("100.00")},
        {"number": "F-002", "date": "02-02-2026",
         "due_date": "16-02-2026", "amount": Decimal("200.00")},
        {"number": "F-003", "date": "03-03-2026",
         "due_date": "17-03-2026", "amount": Decimal("300.00")},
    ]
    out = _fill_invoice_rows(_SAMPLE_TEMPLATE, invoices)
    for inv in invoices:
        assert out.count(inv["number"]) == 1, f"{inv['number']} ontbreekt"
    assert "100,00" in out
    assert "200,00" in out
    assert "300,00" in out


def test_empty_invoice_fields_no_crash():
    invoices = [{"number": "", "date": "", "due_date": None, "amount": None}]
    out = _fill_invoice_rows(_SAMPLE_TEMPLATE, invoices)
    assert "0,00" in out


def test_no_invoices_returns_template_unchanged():
    out = _fill_invoice_rows(_SAMPLE_TEMPLATE, [])
    assert out == _SAMPLE_TEMPLATE


_LONE_COMMA_TEMPLATE = """
<html><body>
<table><tr><td>Betreft</td><td>WEDEROM SOMMATIE TOT BETALING / / </td></tr></table>
<p><br>
<span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">,<br>
<br>
Eerder heb ik u aangeschreven.</span></span></p>
</body></html>
"""

_NORMAL_GREETING_TEMPLATE = """
<html><body>
<p><span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">Geachte heer mevrouw,<br>
<br>
Eerder heb ik u aangeschreven.</span></span></p>
</body></html>
"""


def test_lone_comma_template_gets_greeting_injected():
    """Verweer beantwoorden + Aankondiging faillissement templates missen
    'Geachte heer/mevrouw' — moeten injectie krijgen voor lone-comma."""
    out = render_template_html(
        _LONE_COMMA_TEMPLATE,
        case_data={"case_number": "2026-00049"},
        debtor_data={"contact_person": "J. Jansen"},
        client_data={"name": "Test BV"},
        invoices=[],
        amounts={},
    )
    assert "Geachte heer/mevrouw J. Jansen,<br>" in out
    # Geen lone comma meer
    assert "sans-serif;\">,<br>" not in out


def test_normal_template_greeting_replaced_with_contact():
    out = render_template_html(
        _NORMAL_GREETING_TEMPLATE,
        case_data={"case_number": "2026-00049"},
        debtor_data={"contact_person": "J. Jansen"},
        client_data={"name": "Test BV"},
        invoices=[],
        amounts={},
    )
    assert "Geachte heer/mevrouw J. Jansen," in out
    assert "Geachte heer mevrouw," not in out


def test_lone_comma_template_without_contact_uses_generic():
    out = render_template_html(
        _LONE_COMMA_TEMPLATE,
        case_data={"case_number": "2026-00049"},
        debtor_data={"contact_person": ""},
        client_data={"name": "Test BV"},
        invoices=[],
        amounts={},
    )
    assert "Geachte heer/mevrouw," in out


_XXX_TEMPLATE = """
<html><body>
<p>Hierbij voorzie ik u van een inhoudelijke reactie, waarin ik uw stellingen weerleg.&nbsp;<br>
<br>
XXX<br>
<br>
Indien ondanks deze correspondentie betaling uitblijft, ben ik genoodzaakt het incassotraject voort te zetten.</p>
<p>totaalbedrag van <strong>€&nbsp;</strong> uiterlijk binnen 3 dagen.</p>
</body></html>
"""


def test_extract_weerlegging_finds_text_between_markers():
    ai_body = (
        "Hierbij voorzie ik u van een inhoudelijke reactie, waarin ik uw stellingen weerleg.\n\n"
        "U heeft gesteld dat het abonnement is opgezegd.\n\n"
        "Indien ondanks deze correspondentie betaling uitblijft."
    )
    out = _extract_weerlegging(ai_body)
    assert out == "U heeft gesteld dat het abonnement is opgezegd."


def test_extract_weerlegging_returns_none_without_markers():
    assert _extract_weerlegging("just some random text") is None
    assert _extract_weerlegging("") is None


def test_xxx_placeholder_replaced_with_ai_weerlegging():
    ai_body = (
        "stellingen weerleg.\n\nU heeft gesteld dat het abonnement is opgezegd. "
        "Cliënte heeft geen tijdige opzegging ontvangen.\n\n"
        "Indien ondanks deze correspondentie betaling uitblijft."
    )
    out = render_template_html(
        _XXX_TEMPLATE,
        case_data={"case_number": "2026-00049"},
        debtor_data={"contact_person": "Test"},
        client_data={"name": "BV"},
        invoices=[],
        amounts={"te_voldoen": Decimal("1687.36")},
        ai_body=ai_body,
    )
    assert "XXX" not in out
    assert "abonnement is opgezegd" in out


def test_xxx_unchanged_when_no_ai_body():
    out = render_template_html(
        _XXX_TEMPLATE,
        case_data={"case_number": "2026-00049"},
        debtor_data={"contact_person": "Test"},
        client_data={"name": "BV"},
        invoices=[],
        amounts={"te_voldoen": Decimal("1687.36")},
    )
    assert "XXX" in out


def test_totaalbedrag_amount_filled():
    out = render_template_html(
        _XXX_TEMPLATE,
        case_data={"case_number": "2026-00049"},
        debtor_data={"contact_person": "Test"},
        client_data={"name": "BV"},
        invoices=[],
        amounts={"te_voldoen": Decimal("1687.36")},
    )
    assert "1.687,36" in out
    assert "totaalbedrag van <strong>€&nbsp;</strong>" not in out


def test_render_subject_fills_placeholders():
    """Bij kenmerk == case_number → enkel slot (geen dubbele vermelding)."""
    out = render_subject(
        "REACTIE OP UW VERWEER / / ",
        case_number="2026-00049",
        kenmerk="2026-00049",
    )
    assert out == "REACTIE OP UW VERWEER / 2026-00049"


def test_render_subject_kenmerk_empty_only_case_number():
    """Bij kenmerk leeg → alleen case_number slot."""
    out = render_subject(
        "EERSTE SOMMATIE / / ",
        case_number="2026-00049",
        kenmerk="",
    )
    assert out == "EERSTE SOMMATIE / 2026-00049"


def test_render_subject_with_kenmerk():
    out = render_subject(
        "SOMMATIE TOT BETALING / / ",
        case_number="2026-00049",
        kenmerk="REF-123",
    )
    assert out == "SOMMATIE TOT BETALING / REF-123 / 2026-00049"


def test_render_subject_handles_double_space():
    out = render_subject(
        "TWEEDE SOMMATIE /  / ",
        case_number="2026-00049",
        kenmerk="REF-123",
    )
    assert out == "TWEEDE SOMMATIE / REF-123 / 2026-00049"


def test_render_subject_empty_returns_empty():
    assert render_subject("", case_number="X", kenmerk="X") == ""


def test_more_invoices_than_slots_truncates():
    """4 facturen, template heeft 3 slots → eerste 3 gevuld, 4e overgeslagen."""
    invoices = [
        {"number": f"F-{i:03d}", "date": "01-01-2026",
         "due_date": "15-01-2026", "amount": Decimal("100.00")}
        for i in range(1, 5)
    ]
    out = _fill_invoice_rows(_SAMPLE_TEMPLATE, invoices)
    assert "F-001" in out
    assert "F-002" in out
    assert "F-003" in out
    assert "F-004" not in out
