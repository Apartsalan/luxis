"""Generate 5 realistic test invoice PDFs for intake E2E testing.

Creates professional Dutch invoices with varied scenarios:
1. B2B standard (€3.200 excl. BTW)
2. B2B small amount (€850 incl. BTW)
3. B2C consumer (€450, no KvK)
4. International B2B (€12.500, German company)
5. B2B large multi-line (€25.000)

Usage:
    python scripts/generate_test_invoices.py
    # Creates PDFs in scripts/test_invoices/
"""

import os
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from weasyprint import HTML

OUTPUT_DIR = Path(__file__).parent / "test_invoices"
TODAY = date.today()


def _fmt_date(d: date) -> str:
    return d.strftime("%d-%m-%Y")


def _fmt_money(amount: Decimal) -> str:
    return f"€ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _generate_invoice_html(invoice: dict) -> str:
    """Generate HTML for a single invoice."""
    lines_html = ""
    for line in invoice["lines"]:
        lines_html += f"""
        <tr>
            <td>{line['description']}</td>
            <td class="right">{line.get('quantity', 1)}</td>
            <td class="right">{_fmt_money(line['unit_price'])}</td>
            <td class="right">{_fmt_money(line['total'])}</td>
        </tr>"""

    # BTW section
    btw_html = ""
    if invoice.get("btw_amount") and invoice["btw_amount"] > 0:
        btw_html = f"""
        <tr class="subtotal">
            <td colspan="3">Subtotaal excl. BTW</td>
            <td class="right">{_fmt_money(invoice['subtotal'])}</td>
        </tr>
        <tr>
            <td colspan="3">BTW {invoice.get('btw_pct', 21)}%</td>
            <td class="right">{_fmt_money(invoice['btw_amount'])}</td>
        </tr>"""
    else:
        btw_html = f"""
        <tr class="subtotal">
            <td colspan="3">Subtotaal</td>
            <td class="right">{_fmt_money(invoice['subtotal'])}</td>
        </tr>"""

    # KvK line
    kvk_html = ""
    if invoice["sender"].get("kvk"):
        kvk_html = f"<br>KvK: {invoice['sender']['kvk']}"

    debtor_kvk_html = ""
    if invoice["debtor"].get("kvk"):
        debtor_kvk_html = f"<br>KvK: {invoice['debtor']['kvk']}"

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 2cm 2.5cm;
    }}
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 10pt;
        color: #222;
        line-height: 1.5;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 30px;
        border-bottom: 3px solid #1a56db;
        padding-bottom: 15px;
    }}
    .logo {{
        font-size: 22pt;
        font-weight: 700;
        color: #1a56db;
    }}
    .logo-sub {{
        font-size: 9pt;
        color: #666;
        margin-top: 2px;
    }}
    .invoice-title {{
        text-align: right;
    }}
    .invoice-title h1 {{
        font-size: 28pt;
        color: #1a56db;
        margin: 0;
        font-weight: 300;
        letter-spacing: 2px;
    }}
    .invoice-number {{
        font-size: 11pt;
        color: #666;
        margin-top: 5px;
    }}
    .addresses {{
        display: flex;
        justify-content: space-between;
        margin: 25px 0 35px;
    }}
    .address-block {{
        width: 45%;
    }}
    .address-block h3 {{
        font-size: 8pt;
        text-transform: uppercase;
        color: #999;
        letter-spacing: 1px;
        margin: 0 0 8px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
    }}
    .address-block p {{
        margin: 0;
        font-size: 10pt;
    }}
    .meta {{
        display: flex;
        gap: 40px;
        margin-bottom: 30px;
        background: #f8f9fa;
        padding: 12px 18px;
        border-radius: 4px;
    }}
    .meta-item {{
        font-size: 9pt;
    }}
    .meta-label {{
        color: #999;
        text-transform: uppercase;
        font-size: 7pt;
        letter-spacing: 0.5px;
    }}
    .meta-value {{
        font-weight: 600;
        margin-top: 2px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }}
    thead th {{
        background: #1a56db;
        color: white;
        padding: 10px 12px;
        text-align: left;
        font-size: 8pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    thead th.right {{
        text-align: right;
    }}
    tbody td {{
        padding: 10px 12px;
        border-bottom: 1px solid #eee;
    }}
    .right {{
        text-align: right;
    }}
    .subtotal td {{
        border-top: 2px solid #ddd;
        font-weight: 600;
    }}
    .total td {{
        border-top: 3px solid #1a56db;
        font-weight: 700;
        font-size: 12pt;
        color: #1a56db;
        padding-top: 12px;
    }}
    .payment-info {{
        margin-top: 40px;
        background: #f8f9fa;
        padding: 18px;
        border-radius: 4px;
        border-left: 4px solid #1a56db;
    }}
    .payment-info h3 {{
        margin: 0 0 10px;
        font-size: 10pt;
        color: #1a56db;
    }}
    .payment-info p {{
        margin: 3px 0;
        font-size: 9pt;
    }}
    .footer {{
        margin-top: 50px;
        padding-top: 15px;
        border-top: 1px solid #eee;
        font-size: 8pt;
        color: #999;
        text-align: center;
    }}
</style>
</head>
<body>

<div class="header">
    <div>
        <div class="logo">{invoice['sender']['name']}</div>
        <div class="logo-sub">{invoice['sender'].get('tagline', '')}</div>
    </div>
    <div class="invoice-title">
        <h1>FACTUUR</h1>
        <div class="invoice-number">{invoice['number']}</div>
    </div>
</div>

<div class="addresses">
    <div class="address-block">
        <h3>Van</h3>
        <p>
            <strong>{invoice['sender']['name']}</strong><br>
            {invoice['sender']['address']}<br>
            {invoice['sender']['postcode']} {invoice['sender']['city']}{kvk_html}<br>
            BTW: {invoice['sender'].get('btw_nr', 'NL123456789B01')}
        </p>
    </div>
    <div class="address-block">
        <h3>Aan</h3>
        <p>
            <strong>{invoice['debtor']['name']}</strong><br>
            {invoice['debtor']['address']}<br>
            {invoice['debtor']['postcode']} {invoice['debtor']['city']}{debtor_kvk_html}
        </p>
    </div>
</div>

<div class="meta">
    <div class="meta-item">
        <div class="meta-label">Factuurdatum</div>
        <div class="meta-value">{_fmt_date(invoice['date'])}</div>
    </div>
    <div class="meta-item">
        <div class="meta-label">Vervaldatum</div>
        <div class="meta-value">{_fmt_date(invoice['due_date'])}</div>
    </div>
    <div class="meta-item">
        <div class="meta-label">Betalingstermijn</div>
        <div class="meta-value">{invoice.get('payment_term', '30 dagen')}</div>
    </div>
    <div class="meta-item">
        <div class="meta-label">Referentie</div>
        <div class="meta-value">{invoice.get('reference', '-')}</div>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th>Omschrijving</th>
            <th class="right">Aantal</th>
            <th class="right">Prijs</th>
            <th class="right">Bedrag</th>
        </tr>
    </thead>
    <tbody>
        {lines_html}
        {btw_html}
        <tr class="total">
            <td colspan="3">Totaal</td>
            <td class="right">{_fmt_money(invoice['total'])}</td>
        </tr>
    </tbody>
</table>

<div class="payment-info">
    <h3>Betaalinformatie</h3>
    <p><strong>IBAN:</strong> {invoice['sender'].get('iban', 'NL91 ABNA 0417 1643 00')}</p>
    <p><strong>T.n.v.:</strong> {invoice['sender']['name']}</p>
    <p><strong>Onder vermelding van:</strong> {invoice['number']}</p>
</div>

<div class="footer">
    {invoice['sender']['name']} &middot; {invoice['sender']['address']}, {invoice['sender']['postcode']} {invoice['sender']['city']}
    &middot; {invoice['sender'].get('email', 'info@example.nl')}
</div>

</body>
</html>"""


# =============================================================================
# Invoice definitions
# =============================================================================

def _d(s: str) -> Decimal:
    return Decimal(s)


def _line(desc: str, unit_price: str, qty: int = 1) -> dict:
    up = _d(unit_price)
    return {
        "description": desc,
        "unit_price": up,
        "quantity": qty,
        "total": (up * qty).quantize(_d("0.01"), rounding=ROUND_HALF_UP),
    }


INVOICES = [
    # 1. B2B standard — €3.200 excl. BTW
    {
        "filename": "factuur_techvision_bv.pdf",
        "number": "2026-003-TV",
        "date": TODAY - timedelta(days=60),
        "due_date": TODAY - timedelta(days=30),
        "payment_term": "30 dagen",
        "reference": "Project Digitalisering",
        "sender": {
            "name": "ICT Adviesbureau Petra",
            "tagline": "ICT-oplossingen voor het MKB",
            "address": "Herengracht 458",
            "postcode": "1017 CA",
            "city": "Amsterdam",
            "kvk": "65432198",
            "btw_nr": "NL004567891B01",
            "iban": "NL42 INGB 0006 3912 45",
            "email": "petra@ict-adviesbureau.nl",
        },
        "debtor": {
            "name": "TechVision B.V.",
            "address": "Singel 200",
            "postcode": "1012 LJ",
            "city": "Amsterdam",
            "kvk": "71456823",
        },
        "lines": [
            _line("ICT-advies en consultancy Q4 2025", "160.00", 20),
        ],
        "subtotal": _d("3200.00"),
        "btw_pct": 21,
        "btw_amount": _d("672.00"),
        "total": _d("3872.00"),
    },
    # 2. B2B small amount — €850 incl. BTW
    {
        "filename": "factuur_bakkerij_de_molen.pdf",
        "number": "F2025-412",
        "date": TODAY - timedelta(days=120),
        "due_date": TODAY - timedelta(days=90),
        "payment_term": "14 dagen",
        "reference": "Levering week 48",
        "sender": {
            "name": "Meelgroothandel Friesland B.V.",
            "tagline": "Leverancier van meel en grondstoffen",
            "address": "Zuiderweg 88",
            "postcode": "8911 AH",
            "city": "Leeuwarden",
            "kvk": "54321098",
            "btw_nr": "NL005678912B01",
            "iban": "NL55 RABO 0145 6789 12",
            "email": "verkoop@meelgroothandel.nl",
        },
        "debtor": {
            "name": "Bakkerij De Molen",
            "address": "Oudegracht 112",
            "postcode": "3511 AX",
            "city": "Utrecht",
        },
        "lines": [
            _line("Tarwebloem patent 25kg (10 zakken)", "22.50", 10),
            _line("Roggemeel volkoren 10kg (5 zakken)", "18.50", 5),
            _line("Gist vers 500g (20 stuks)", "3.75", 20),
            _line("Boter ongezouten 5kg (10 blokken)", "32.00", 10),
        ],
        "subtotal": _d("702.50"),
        "btw_pct": 9,
        "btw_amount": _d("63.23"),
        "total": _d("765.73"),
    },
    # 3. B2C consumer — €450, no KvK
    {
        "filename": "factuur_janssen_particulier.pdf",
        "number": "RK-2025-089",
        "date": TODAY - timedelta(days=90),
        "due_date": TODAY - timedelta(days=60),
        "payment_term": "14 dagen",
        "reference": "Patient 2025-089",
        "sender": {
            "name": "Tandartspraktijk Haarlem",
            "tagline": "Uw tandarts in het centrum",
            "address": "Grote Markt 15",
            "postcode": "2011 RC",
            "city": "Haarlem",
            "kvk": "76543210",
            "btw_nr": "NL006789123B01",
            "iban": "NL88 ABNA 0512 3456 78",
            "email": "info@tandartspraktijk-haarlem.nl",
        },
        "debtor": {
            "name": "K. Janssen",
            "address": "Dorpsstraat 7",
            "postcode": "2011 AB",
            "city": "Haarlem",
        },
        "lines": [
            _line("Periodieke controle", "50.00"),
            _line("Vulling composiet (2x)", "125.00", 2),
            _line("Wortelkanaalbehandeling", "150.00"),
        ],
        "subtotal": _d("450.00"),
        "btw_pct": 0,
        "btw_amount": _d("0"),
        "total": _d("450.00"),
    },
    # 4. International B2B — €12.500, German company
    {
        "filename": "factuur_mueller_gmbh.pdf",
        "number": "EU-2025-088",
        "date": TODAY - timedelta(days=70),
        "due_date": TODAY - timedelta(days=40),
        "payment_term": "30 dagen netto",
        "reference": "PO-2025-DE-4411",
        "sender": {
            "name": "Machinefabriek Nederland B.V.",
            "tagline": "Precision engineering since 1982",
            "address": "Industrielaan 22",
            "postcode": "5651 GJ",
            "city": "Eindhoven",
            "kvk": "43210987",
            "btw_nr": "NL007891234B01",
            "iban": "NL34 RABO 0298 7654 32",
            "email": "export@machinefabriek-nl.nl",
        },
        "debtor": {
            "name": "Müller GmbH",
            "address": "Industriestraße 45",
            "postcode": "40210",
            "city": "Düsseldorf",
            "kvk": "HRB 12345 (Amtsgericht Düsseldorf)",
        },
        "lines": [
            _line("CNC-gefreesd onderdeel type A (50 stuks)", "125.00", 50),
            _line("CNC-gefreesd onderdeel type B (25 stuks)", "200.00", 25),
            _line("Verpakking en verzekerde verzending DE", "250.00"),
        ],
        "subtotal": _d("11500.00"),
        "btw_pct": 0,
        "btw_amount": _d("0"),
        "total": _d("11500.00"),
    },
    # 5. B2B large multi-line — €25.000
    {
        "filename": "factuur_groothandel_nederland.pdf",
        "number": "GHN-2026-0023",
        "date": TODAY - timedelta(days=35),
        "due_date": TODAY - timedelta(days=5),
        "payment_term": "30 dagen",
        "reference": "Order KM-2026-001",
        "sender": {
            "name": "Kantoormeubelen Direct B.V.",
            "tagline": "Professionele kantoorinrichting",
            "address": "Meubelplein 8",
            "postcode": "3439 ME",
            "city": "Nieuwegein",
            "kvk": "32109876",
            "btw_nr": "NL008912345B01",
            "iban": "NL67 INGB 0007 8912 34",
            "email": "cfo@kantoormeubelen-direct.nl",
        },
        "debtor": {
            "name": "Groothandel Nederland B.V.",
            "address": "Havenweg 15-17",
            "postcode": "4825 BA",
            "city": "Breda",
            "kvk": "82345671",
        },
        "lines": [
            _line("Bureaustoelen ergonomisch (20 stuks)", "450.00", 20),
            _line("Zit-sta bureaus elektrisch (10 stuks)", "750.00", 10),
            _line("Vergadertafel groot (2 stuks)", "1200.00", 2),
            _line("Kantoorkast afsluitbaar (5 stuks)", "380.00", 5),
            _line("Bezorging en montage", "961.16"),
        ],
        "subtotal": _d("20661.16"),
        "btw_pct": 21,
        "btw_amount": _d("4338.84"),
        "total": _d("25000.00"),
    },
]


def generate_all():
    """Generate all test invoice PDFs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Test Invoice PDF Generator")
    print("=" * 60)
    print()

    for invoice in INVOICES:
        html = _generate_invoice_html(invoice)
        filepath = OUTPUT_DIR / invoice["filename"]
        HTML(string=html).write_pdf(str(filepath))
        print(
            f"  {invoice['filename']:<45s} "
            f"{_fmt_money(invoice['total']):>15s}  "
            f"({invoice['debtor']['name']})"
        )

    print()
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"  Totaal: {len(INVOICES)} PDFs gegenereerd")


if __name__ == "__main__":
    generate_all()
