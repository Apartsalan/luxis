"""Tests voor server-side HTML template-renderer (incasso emails)."""

from decimal import Decimal

from app.incasso.html_renderer import _fill_invoice_rows


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
