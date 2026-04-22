"""Render 5 kritieke brieven met realistische context en productie-currency format.

Doel: visueel verifieren of de audit-bevindingen kloppen.
- "na dagtekening" i.p.v. "na ontvangst" (finding #4)
- BIK zonder BTW (finding #5)
- "EUR 1.234,56" i.p.v. "€ 1.234,56" (finding template #6)
- Dubbel valutasymbool in tabellen
- IBAN rendering in 14-dagenbrief

Output: docs/audits/rendered-samples/*.html
Open in browser om resultaat te zien.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.email.incasso_templates import render_incasso_email  # noqa: E402


def fmt_currency_production(value: Decimal) -> str:
    """Zelfde als backend/app/documents/docx_service.py:161 — productie format."""
    d = Decimal(str(value))
    formatted = f"{d:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {formatted}"


def build_context(*, use_production_currency: bool, include_btw: bool) -> dict:
    """Realistisch scenario:
    - Consument debiteur Jan de Vries
    - Hoofdsom € 3.500 (over de eerste 2 WIK-tiers)
    - 6 maanden verzuim, ~€ 93 rente wettelijk
    - BIK: 15% over 2500 + 10% over 1000 = 375 + 100 = 475 (excl BTW)
    - Als include_btw=True: +21% = EUR 574,75 (voor niet-BTW-plichtige cliënt)
    """
    hoofdsom = Decimal("3500.00")
    rente = Decimal("93.50")
    bik_excl = Decimal("475.00")
    btw = Decimal("99.75") if include_btw else Decimal("0.00")
    bik_incl = bik_excl + btw
    totaal = hoofdsom + rente + bik_incl

    fmt = fmt_currency_production if use_production_currency else _fmt_with_euro

    return {
        "kantoor": {
            "naam": "Kesting Legal",
            "adres": "IJsbaanpad 9",
            "postcode_stad": "1076 CV Amsterdam",
            "email": "lisanne@kestinglegal.nl",
            "telefoon": "06-22184090",
            "kvk": "12345678",
            "iban": "NL20 RABO 0388 5065 20",
            "btw": "NL001234567B01",
        },
        "wederpartij": {
            "naam": "Jan de Vries",
            "adres": "Hoofdstraat 12",
            "postcode_stad": "1234 AB Utrecht",
        },
        "client": {
            "naam": "Bakkerij Van Dijk VOF",
            "postcode_stad": "Utrecht",
        },
        "zaak": {
            "zaaknummer": "2026-00042",
            "referentie_regel": None,
        },
        "vandaag": "22 april 2026",
        "totaal_hoofdsom": fmt(hoofdsom),
        "totaal_rente": fmt(rente),
        "subtotaal": fmt(hoofdsom + rente),
        "bik_bedrag": fmt(bik_excl),
        "btw_regel_label": "BTW 21% over BIK" if include_btw else "BTW",
        "btw_regel_bedrag": fmt(btw),
        "totaal_verschuldigd": fmt(totaal),
        "betalingen_aftrek_label": "Voldaan bij klant",
        "betalingen_aftrek_bedrag": fmt(Decimal("0")),
        "betalingen_regel_label": "Reeds voldaan",
        "betalingen_regel_bedrag": fmt(Decimal("0")),
        "totaal_openstaand": fmt(totaal),
        "termijn_14_dagen": "6 mei 2026",
        "termijn_30_dagen": "22 mei 2026",
        "btw_toelichting": " incl. BTW" if include_btw else " excl. BTW",
        "vorderingen": [
            {
                "beschrijving": "Factuur 2025-1128 (brood + taart bestelling)",
                "factuurnummer": "2025-1128",
                "verzuimdatum": "22-10-2025",
                "hoofdsom": fmt(hoofdsom),
            },
        ],
    }


def _fmt_with_euro(value: Decimal) -> str:
    """Zoals de tests (met € symbool) — NIET productie."""
    d = Decimal(str(value))
    formatted = f"{d:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {formatted}"


def wrap_html(title: str, inner: str, note: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ background:#f3f4f6; margin:0; padding:40px; font-family: -apple-system, sans-serif; }}
  .audit-note {{ max-width:780px; margin:0 auto 24px; padding:16px 20px; background:#fef3c7;
                 border-left:4px solid #f59e0b; border-radius:6px; font-size:13px; }}
  .letter-wrap {{ max-width:780px; margin:0 auto; background:white; box-shadow:0 4px 12px rgba(0,0,0,0.08); }}
</style>
</head>
<body>
  {"<div class='audit-note'><strong>Audit note:</strong> " + note + "</div>" if note else ""}
  <div class="letter-wrap">
    {inner}
  </div>
</body>
</html>
"""


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "docs" / "audits" / "rendered-samples"
    out_dir.mkdir(parents=True, exist_ok=True)

    templates = [
        ("herinnering", "Herinnering"),
        ("aanmaning", "Aanmaning"),
        ("14_dagenbrief", "14-dagenbrief (art. 6:96 lid 6 BW)"),
        ("sommatie", "Sommatie"),
        ("tweede_sommatie", "Tweede sommatie"),
    ]

    # Scenario A: Productie format (EUR-tekst) + BIK ZONDER BTW (huidige default productie)
    ctx_prod = build_context(use_production_currency=True, include_btw=False)
    # Scenario B: Met € symbool + BIK MET BTW (hoe het zou moeten zijn voor niet-BTW-plichtige client)
    ctx_correct = build_context(use_production_currency=False, include_btw=True)

    index_rows = []
    for key, label in templates:
        # Productie rendering
        html_prod = render_incasso_email(key, ctx_prod)
        path_prod = out_dir / f"{key}__PRODUCTIE.html"
        path_prod.write_text(
            wrap_html(
                f"{label} — PRODUCTIE",
                html_prod or "<p>(template returned None)</p>",
                note=(
                    "Dit is wat er NU uit Luxis komt voor een niet-BTW-plichtige client "
                    "(Bakkerij VOF). Let op: valuta als 'EUR 1.234,56', geen 21% BTW op BIK. "
                    "14-dagenbrief: zoek 'dagtekening' vs 'ontvangst' — beide komen voor!"
                ),
            ),
            encoding="utf-8",
        )

        # Correcte rendering
        html_corr = render_incasso_email(key, ctx_correct)
        path_corr = out_dir / f"{key}__CORRECT.html"
        path_corr.write_text(
            wrap_html(
                f"{label} — HOE HET ZOU MOETEN",
                html_corr or "<p>(template returned None)</p>",
                note=(
                    "Zelfde brief, maar met € symbool en BIK + 21% BTW zoals wettelijk "
                    "verschuldigd voor een niet-BTW-plichtige client. Dit is hoe een "
                    "professionele incassobrief eruit hoort te zien."
                ),
            ),
            encoding="utf-8",
        )

        index_rows.append(
            f"<tr><td>{label}</td>"
            f"<td><a href='{path_prod.name}'>PRODUCTIE</a></td>"
            f"<td><a href='{path_corr.name}'>CORRECT</a></td></tr>"
        )

    # Index
    index_html = f"""<!DOCTYPE html>
<html lang="nl"><head><meta charset="utf-8"><title>Luxis Audit — Rendered Samples</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width:900px; margin:40px auto; padding:20px; }}
h1 {{ color:#1e293b; }}
table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
th, td {{ padding:12px; text-align:left; border-bottom:1px solid #e5e7eb; }}
th {{ background:#f9fafb; }}
a {{ color:#0284c7; text-decoration:none; font-weight:500; }}
a:hover {{ text-decoration:underline; }}
.checklist {{ background:#fef3c7; border-left:4px solid #f59e0b; padding:16px 20px;
              margin:20px 0; border-radius:6px; }}
.checklist h3 {{ margin-top:0; }}
code {{ background:#e5e7eb; padding:2px 6px; border-radius:3px; font-size:13px; }}
</style></head><body>
<h1>Luxis Audit — Gerendererde brieven</h1>
<p>Scenario: consument <strong>Jan de Vries</strong> heeft €3.500 schuld bij <strong>Bakkerij Van Dijk VOF</strong>
(niet-BTW-plichtige VOF). 6 maanden verzuim, ~€ 93 rente, BIK zou €475 excl moeten zijn, +€99,75 BTW = €574,75 incl.
Totaal verschuldigd (correct) = € 4.168,25.</p>

<div class="checklist">
  <h3>Waar naar kijken in de PRODUCTIE-versies:</h3>
  <ol>
    <li><strong>Valuta</strong>: staat er "EUR 3.500,00" of "€ 3.500,00"? Productie = "EUR".</li>
    <li><strong>14-dagenbrief</strong>: open het bestand, zoek naar <code>dagtekening</code> — staat er één keer "na ontvangst" (correct) en één keer "na dagtekening" (fout)?</li>
    <li><strong>BIK-bedrag</strong>: staat er €475 (zonder BTW) of €574,75 (met BTW)? Productie = €475. Maar voor een VOF/consument/stichting MOET het €574,75 zijn.</li>
    <li><strong>Totaal</strong>: productie telt €3.500 + €93 + €475 = €4.068. Correct = €4.168 (€100 verschil = de ontbrekende BTW).</li>
    <li><strong>Vorderingen-tabel</strong>: dubbel euro-symbool? (<code>€ EUR 3.500,00</code>?)</li>
  </ol>
</div>

<table>
  <thead><tr><th>Brief</th><th>Wat nu uit Luxis komt</th><th>Hoe het hoort</th></tr></thead>
  <tbody>
    {"".join(index_rows)}
  </tbody>
</table>
<p style="margin-top:30px;color:#6b7280;font-size:13px;">
Gerendererd op {ctx_prod["vandaag"]} · bron: <code>scripts/render_audit_samples.py</code>
</p>
</body></html>
"""
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    print(f"\n[OK] {len(templates)} templates gerendererd (x2 = {len(templates) * 2} bestanden)")
    print(f"[OUTPUT] {out_dir}")
    print(f"[OPEN]   file:///{out_dir.as_posix()}/index.html")


if __name__ == "__main__":
    main()
