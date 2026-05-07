"""Server-side HTML template-renderer voor incasso emails.

Het AI-model (Sonnet/Gemini/Haiku) genereert alleen `subject` + plain `body`
(betrouwbaar, kort). De HTML-versie van de email wordt server-side opgebouwd
op basis van het template (`IncassoPipelineStep.email_body_template_html`)
plus dossier-context.

Aanpak: simpele regex-replacements voor de meest voorkomende placeholders
in Lisanne's .eml-sjablonen. Dit is robuuster dan AI vragen om volledig
HTML terug te geven (kostbaar, foutgevoelig, hit token-limits).
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


def _fmt_eur(value: Decimal | float | int | None) -> str:
    """Format als '1.687,36' (Nederlands, geen € teken)."""
    if value is None:
        return "0,00"
    d = Decimal(str(value)).quantize(Decimal("0.01"))
    s = f"{d:,.2f}"
    # 1,687.36 (US) → 1.687,36 (NL)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fill_amount_cell(html: str, label: str, amount_str: str) -> str:
    """Vervang lege bedrag-cel naast `label` met het bedrag.

    Matcht: <td>...Label</td><td>...€</td><td>&nbsp;</td>
    """
    pattern = re.compile(
        r"(<td[^>]*>(?:<span[^>]*>)*\s*"
        + re.escape(label)
        + r"\s*(?:</span>)*</td>"
        + r"\s*<td[^>]*>(?:<span[^>]*>)*€(?:</span>)*</td>"
        + r"\s*<td[^>]*>)(?:&nbsp;|\s*)(</td>)",
        re.DOTALL,
    )
    replacement = (
        r'\1<span style="font-size:12px;">'
        r'<span style="font-family:Verdana,Geneva,sans-serif;">'
        + amount_str
        + r"</span></span>\2"
    )
    return pattern.sub(replacement, html, count=1)


def _fill_invoice_rows(html: str, invoices: list[dict[str, Any]]) -> str:
    """Vul lege factuur-rijen met factuurdata.

    Lisanne's template bevat na de header (Factuurnummer | Datum | Vervaldatum |
    Bedrag) een aantal lege <tr>-rijen voor factuurregels. We vullen ze in
    volgorde met de eerste N facturen.
    """
    if not invoices:
        return html

    # Find the table after "Factuurnummer" header and replace empty rows
    # Pattern: <tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
    empty_row_pattern = re.compile(
        r'(<tr>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*colspan="2"[^>]*>&nbsp;</td>\s*'
        r'</tr>)',
        re.DOTALL,
    )

    # Vervang de eerste N lege rijen met factuur-data
    rows_iter = iter(invoices)
    def _replace(match: re.Match[str]) -> str:
        try:
            inv = next(rows_iter)
        except StopIteration:
            return match.group(0)
        return (
            "<tr>"
            f'<td style="padding:.100px .100px .100px .100px"><span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">{inv.get("number") or ""}</span></span></td>'
            f'<td style="padding:.100px .100px .100px .100px"><span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">{inv.get("date") or ""}</span></span></td>'
            f'<td style="padding:.100px .100px .100px .100px"><span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">{inv.get("due_date") or ""}</span></span></td>'
            f'<td colspan="2" style="padding:.100px .100px .100px .100px"><span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">€ {_fmt_eur(inv.get("amount"))}</span></span></td>'
            "</tr>"
        )

    return empty_row_pattern.sub(_replace, html)


def render_template_html(
    template_html: str,
    *,
    case_data: dict[str, Any],
    debtor_data: dict[str, Any],
    client_data: dict[str, Any],
    invoices: list[dict[str, Any]],
    amounts: dict[str, Decimal],
    **_: Any,
) -> str:
    """Render the HTML template met dossier-data ingevuld.

    Returns het volledige HTML met placeholders vervangen. Als template leeg
    is geeft het een lege string terug.
    """
    if not template_html:
        return ""

    case_number = str(case_data.get("case_number") or "")
    kenmerk = str(case_data.get("reference") or case_number)
    client_name = str(client_data.get("name") or "")
    contact = debtor_data.get("contact_person") or ""

    html = template_html

    # Subject-regel binnen body: "SOMMATIE TOT BETALING / /" → "SOMMATIE TOT BETALING / kenmerk / dossiernummer"
    # (Lisanne's templates hebben " / / " met spaties tussen slashes)
    for tag in ("SOMMATIE TOT BETALING", "TWEEDE SOMMATIE", "WEDEROM SOMMATIE",
                "SOMMATIE AANKONDIGING FAILLISSEMENT", "VERZOEKSCHRIFT FAILLISSEMENT",
                "SOMMATIE TOT BETALING (LAATSTE MOGELIJKHEID)"):
        # Generieke patronen met of zonder spaties tussen slashes
        html = html.replace(f"{tag} / /", f"{tag} / {kenmerk} / {case_number}")
        html = html.replace(f"{tag} /  /", f"{tag} / {kenmerk} / {case_number}")

    # Cliëntnaam
    html = html.replace("(invullen gegevens cliënt)", client_name or "(cliënt)")
    html = html.replace("(invullen gegevens client)", client_name or "(cliënt)")

    # Aanhef met contactpersoon-naam (alleen als bekend)
    if contact:
        html = html.replace("Geachte heer mevrouw,", f"Geachte heer/mevrouw {contact},")
        html = html.replace("Geachte heer mevrouw", f"Geachte heer/mevrouw {contact}")

    # Kenmerk in IBAN-instructie
    html = html.replace(
        "onder vermelding van het kenmerk&nbsp;",
        f"onder vermelding van het kenmerk&nbsp;{kenmerk}",
    )
    html = html.replace(
        "onder vermelding van het kenmerk ",
        f"onder vermelding van het kenmerk {kenmerk} ",
    )

    # Dossiernummer in onderwerpregel-instructie
    html = html.replace(
        "uw dossiernummer in de onderwerpregel",
        f"uw dossiernummer {case_number} in de onderwerpregel",
    )

    # Bedragen-tabel
    html = _fill_amount_cell(html, "Hoofdsom", _fmt_eur(amounts.get("hoofdsom")))
    html = _fill_amount_cell(html, "Hoofdsom + rente", _fmt_eur(amounts.get("hoofdsom_plus_rente")))
    html = _fill_amount_cell(html, "Incassokosten", _fmt_eur(amounts.get("incassokosten")))
    html = _fill_amount_cell(html, "BTW&nbsp;21%", _fmt_eur(amounts.get("btw")))
    html = _fill_amount_cell(html, "BTW 21%", _fmt_eur(amounts.get("btw")))
    html = _fill_amount_cell(html, "Totaal", _fmt_eur(amounts.get("totaal")))
    html = _fill_amount_cell(html, "Voldaan bij klant", _fmt_eur(amounts.get("voldaan_bij_klant")))
    html = _fill_amount_cell(html, "Door ons ontvangen", _fmt_eur(amounts.get("door_ons_ontvangen")))
    html = _fill_amount_cell(html, "Te voldoen", _fmt_eur(amounts.get("te_voldoen")))

    # Specifieke openstaand-bedrag in zin
    html = html.replace(
        "openstaande bedrag van <strong>€&nbsp;</strong>",
        f"openstaande bedrag van <strong>€&nbsp;{_fmt_eur(amounts.get('te_voldoen'))}</strong>",
    )
    html = html.replace(
        "openstaande bedrag van € ",
        f"openstaande bedrag van € {_fmt_eur(amounts.get('te_voldoen'))} ",
    )

    # Factuur-rijen
    html = _fill_invoice_rows(html, invoices)

    return html
