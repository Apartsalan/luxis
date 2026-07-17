"""Server-side HTML template-renderer voor incasso emails.

Het AI-model (Sonnet/Haiku) genereert alleen `subject` + plain `body`
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

from markupsafe import escape

from app.email.incasso_templates import _LOGO_URL
from app.email.subject import build_email_subject

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

    Matcht: <td>...Label...</td><td>...€...</td><td>&nbsp;</td> waarbij
    er ook <b>/<strong>/<span> wrappers tussen mogen zitten (Lisanne's
    "Te voldoen" rij gebruikt <b>).
    """
    inner_open = r"(?:<(?:span|b|strong|u)[^>]*>)*"
    inner_close = r"(?:</(?:span|b|strong|u)>)*"
    pattern = re.compile(
        r"(<td[^>]*>" + inner_open + r"\s*"
        + re.escape(label)
        + r"\s*" + inner_close + r"</td>"
        + r"\s*<td[^>]*>" + inner_open + r"\s*€\s*" + inner_close + r"</td>"
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

    Matcht twee rij-formats die in templates voorkomen:
    - 4-cell met colspan="2" op laatste cel (1e factuur-slot)
    - 5-cell zonder colspan (slot 2-N)
    Output behoudt het oorspronkelijke format zodat tabel-layout intact blijft.
    """
    if not invoices:
        return html

    # Pattern A: 4-cell met colspan="2" op laatste cel
    pattern_4cell = (
        r'<tr>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*colspan="2"[^>]*>&nbsp;</td>\s*'
        r'</tr>'
    )
    # Pattern B: 5-cell zonder colspan
    pattern_5cell = (
        r'<tr>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'<td[^>]*>&nbsp;</td>\s*'
        r'</tr>'
    )
    combined = re.compile(
        f"(?P<colspan>{pattern_4cell})|(?P<flat>{pattern_5cell})",
        re.DOTALL,
    )

    span_open = '<span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">'
    span_close = "</span></span>"
    cell_style = 'style="padding:.100px .100px .100px .100px"'

    rows_iter = iter(invoices)
    leftover_placeholders = False

    def _replace(match: re.Match[str]) -> str:
        nonlocal leftover_placeholders
        try:
            inv = next(rows_iter)
        except StopIteration:
            # DF138-23: niet meer factuur-data — markeer en strip later om
            # geen lege placeholder-rijen in de uiteindelijke mail te tonen.
            leftover_placeholders = True
            return ""
        number = inv.get("number") or ""
        date = inv.get("date") or ""
        due = inv.get("due_date") or ""
        amount = f"€ {_fmt_eur(inv.get('amount'))}"
        if match.group("colspan"):
            return (
                "<tr>"
                f'<td {cell_style}>{span_open}{number}{span_close}</td>'
                f'<td {cell_style}>{span_open}{date}{span_close}</td>'
                f'<td {cell_style}>{span_open}{due}{span_close}</td>'
                f'<td colspan="2" {cell_style}>{span_open}{amount}{span_close}</td>'
                "</tr>"
            )
        # 5-cell format: split bedrag in valuta-cel + getal-cel
        return (
            "<tr>"
            f'<td {cell_style}>{span_open}{number}{span_close}</td>'
            f'<td {cell_style}>{span_open}{date}{span_close}</td>'
            f'<td {cell_style}>{span_open}{due}{span_close}</td>'
            f'<td {cell_style}>{span_open}€{span_close}</td>'
            f'<td {cell_style}>{span_open}{_fmt_eur(inv.get("amount"))}{span_close}</td>'
            "</tr>"
        )

    html = combined.sub(_replace, html)
    # Veiligheidsnet: als templates extra lege placeholders bevatten die niet
    # door de iterator zijn vervangen, strip ze alsnog.
    if leftover_placeholders:
        html = re.sub(pattern_4cell, "", html, flags=re.DOTALL)
        html = re.sub(pattern_5cell, "", html, flags=re.DOTALL)
    return html


_TD_STYLE = "padding:2px 6px;vertical-align:top"
_TABLE_STYLE = "width:500px;border-collapse:collapse;font-family:Verdana,Geneva,sans-serif;font-size:12px"


def _normalize_table_styling(html: str) -> str:
    """Geef alle <table>/<td>-tags identieke inline styling.

    Lisanne's .eml-templates gebruiken inconsistente tabel-stijlen (1e
    sommatie heeft padding+class, andere niet). Deze functie maakt alles
    visueel hetzelfde groot en uitgelijnd.
    """
    # Wrap <table width="500"...> met uniform style. Behoud bestaande width
    # attribute, vervang/voeg inline style toe.
    def _table_repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        # Strip existing inline style + class
        attrs = re.sub(r'\s+style="[^"]*"', "", attrs)
        attrs = re.sub(r'\s+class="[^"]*"', "", attrs)
        return f'<table{attrs} style="{_TABLE_STYLE}">'

    html = re.sub(
        r'<table((?:\s+[a-z-]+="[^"]*")*?\s+width="500"(?:\s+[a-z-]+="[^"]*")*?)\s*>',
        _table_repl,
        html,
    )

    # <td> zonder style krijgt uniform padding. <td> met bestaande
    # padding:.100px... krijgt ook normalisatie (anders verschillen 1e en 2e).
    def _td_repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        # Strip existing style attr (verwijdert padding:.100px)
        attrs = re.sub(r'\s+style="[^"]*"', "", attrs)
        return f'<td{attrs} style="{_TD_STYLE}">'

    html = re.sub(r"<td((?:\s+[a-z-]+=\"[^\"]*\")*)\s*>", _td_repl, html)
    return html


def render_subject(template_subject: str, *, case_number: str, kenmerk: str) -> str:
    """Vul `SUBJECT_OVERRIDES`-template `... / / ` met kenmerk + dossiernummer.

    Templates volgen format `<TYPE> / / ` (twee slashes met dubbele spatie of
    enkele spatie). Server rendert deze altijd zelf — AI maakt soms fouten
    met de structuur (bv. contactnaam in 2e slot in plaats van dossiernummer).

    Bij kenmerk leeg OF gelijk aan case_number → alleen één slot tonen
    (voorkomt dubbele vermelding `... / 2026-00049 / 2026-00049`).
    """
    if not template_subject:
        return ""
    out = template_subject.rstrip()
    if not kenmerk or kenmerk == case_number:
        replacement = f" / {case_number}"
        inline_replacement = f"/ {case_number}"
    else:
        replacement = f" / {kenmerk} / {case_number}"
        inline_replacement = f"/ {kenmerk} / {case_number}"
    out = re.sub(r"\s*/\s*/\s*$", replacement, out)
    if "/ /" in out:
        out = out.replace("/ /", inline_replacement, 1)
    if "/  /" in out:
        out = out.replace("/  /", inline_replacement, 1)
    return out.strip()


def _extract_weerlegging(ai_body: str) -> str | None:
    """Extract de weerlegging-paragraaf uit AI's plain text body.

    De Verweer-beantwoorden template heeft een 'XXX' placeholder tussen de zin
    'stellingen weerleg.' en 'Indien ondanks deze correspondentie'. AI vult
    deze sectie in plain text — extract zodat we het ook in HTML kunnen
    plaatsen.
    """
    if not ai_body:
        return None
    start_marker = "stellingen weerleg."
    start_idx = ai_body.find(start_marker)
    if start_idx < 0:
        return None
    start = start_idx + len(start_marker)
    end_markers = ("Indien ondanks deze correspondentie", "\nVordering\n", "\nVordering\r")
    end = len(ai_body)
    for m in end_markers:
        i = ai_body.find(m, start)
        if i >= 0 and i < end:
            end = i
    text = ai_body[start:end].strip()
    return text or None


def _plain_to_html_paragraph(text: str) -> str:
    """Plain-text weerlegging → HTML met span/br matching template-stijl."""
    span_open = '<span style="font-size:12px;"><span style="font-family:Verdana,Geneva,sans-serif;">'
    span_close = "</span></span>"
    html_text = text.replace("\r\n", "\n").replace("\r", "\n")
    html_text = html_text.replace("\n", "<br>\n")
    return f"{span_open}{html_text}{span_close}"


def render_template_html(
    template_html: str,
    *,
    case_data: dict[str, Any],
    debtor_data: dict[str, Any],
    client_data: dict[str, Any],
    invoices: list[dict[str, Any]],
    amounts: dict[str, Decimal],
    ai_body: str | None = None,
    **_: Any,
) -> str:
    """Render the HTML template met dossier-data ingevuld.

    Returns het volledige HTML met placeholders vervangen. Als template leeg
    is geeft het een lege string terug.
    """
    if not template_html:
        return ""

    case_number = str(case_data.get("case_number") or "")
    raw_ref = str(case_data.get("reference") or "")
    kenmerk = raw_ref if raw_ref and raw_ref != case_number else ""
    client_name = str(client_data.get("name") or "")
    contact = debtor_data.get("contact_person") or ""
    # DF138-04: salutation bepaalt of we "heer", "mevrouw" of "heer/mevrouw"
    # gebruiken in de aanhef. Default 'unknown' → generieke aanhef zonder naam.
    salutation = (debtor_data.get("salutation") or "unknown").lower()

    html = template_html

    # S226: het logo zat in de BaseNet-stap-teksten als data:-afbeelding →
    # Gmail én Outlook blokkeren die (kapot kader). Vervang door de extern
    # gehoste https-URL, gelijk aan de code-brieven.
    html = re.sub(r'src="data:image/[^"]*"', f'src="{_LOGO_URL}"', html)

    # Betreft-regel binnen de body: BaseNet leverde "SOMMATIE TOT BETALING / /"
    # (lege slots). S226: gelijktrekken met het mail-onderwerp naar huisformaat
    # "{klant} / {debiteur} — {brieftype} — {dossiernummer}". Langste tag eerst,
    # zodat "(LAATSTE MOGELIJKHEID)" niet door de generieke variant wordt geraakt.
    # De debiteurnaam komt hier nieuw in de HTML → escapen (stored-injectie dicht).
    debtor_name = str(debtor_data.get("name") or "")
    for tag, brieftype in (
        ("SOMMATIE TOT BETALING (LAATSTE MOGELIJKHEID)",
         "Sommatie tot betaling (laatste mogelijkheid)"),
        ("SOMMATIE AANKONDIGING FAILLISSEMENT", "Sommatie aankondiging faillissement"),
        ("VERZOEKSCHRIFT FAILLISSEMENT", "Verzoekschrift faillissement"),
        ("WEDEROM SOMMATIE", "Wederom sommatie tot betaling"),
        ("TWEEDE SOMMATIE", "Tweede sommatie"),
        ("SOMMATIE TOT BETALING", "Sommatie tot betaling"),
    ):
        betreft = build_email_subject(
            client_name=str(escape(client_name)) or None,
            debtor_name=str(escape(debtor_name)) or None,
            letter_type=brieftype,
            case_number=case_number,
        )
        html = html.replace(f"{tag} / /", betreft)
        html = html.replace(f"{tag} /  /", betreft)

    # Cliëntnaam
    html = html.replace("(invullen gegevens cliënt)", client_name or "(cliënt)")
    html = html.replace("(invullen gegevens client)", client_name or "(cliënt)")

    # Aanhef: combineer salutation + contactpersoon-naam.
    # - mr  + naam → "Geachte heer Seidony"
    # - mrs + naam → "Geachte mevrouw Seidony"
    # - unknown OF geen naam → "Geachte heer/mevrouw"
    if salutation == "mr" and contact:
        greeting_text = f"Geachte heer {contact}"
    elif salutation == "mrs" and contact:
        greeting_text = f"Geachte mevrouw {contact}"
    elif contact:
        # salutation onbekend maar wel naam → toch generiek (geen gok)
        greeting_text = "Geachte heer, mevrouw"
    else:
        greeting_text = "Geachte heer, mevrouw"
    # Vervang varianten van de template-aanhef
    html = html.replace("Geachte heer mevrouw,", f"{greeting_text},")
    html = html.replace("Geachte heer mevrouw", greeting_text)
    html = html.replace("Geachte heer/mevrouw,", f"{greeting_text},")
    html = html.replace("Geachte heer/mevrouw", greeting_text)
    # Twee templates (Verweer beantwoorden + Aankondiging faillissement) bevatten
    # geen "Geachte heer/mevrouw" in de HTML body — alleen een lone `,<br>` na
    # de Betreft-tabel. Injecteer greeting voor de eerste lone-comma in een span.
    html = re.sub(
        r'(<span[^>]*>(?:\s*<span[^>]*>)?\s*),<br>',
        rf'\1{greeting_text},<br>',
        html,
        count=1,
    )

    # Kenmerk in IBAN-instructie — ALTIJD case_number gebruiken (debiteur moet
    # ergens op betalen). Externe cliënt-reference (raw_ref) zou ook kunnen maar
    # dossiernummer is veilig altijd-aanwezig en uniek.
    iban_kenmerk = kenmerk or case_number
    html = html.replace(
        "onder vermelding van het kenmerk&nbsp;",
        f"onder vermelding van het kenmerk&nbsp;{iban_kenmerk}",
    )
    html = html.replace(
        "onder vermelding van het kenmerk ",
        f"onder vermelding van het kenmerk {iban_kenmerk} ",
    )

    # Dossiernummer in onderwerpregel-instructie
    html = html.replace(
        "uw dossiernummer in de onderwerpregel",
        f"uw dossiernummer {case_number} in de onderwerpregel",
    )

    # Bedragen-tabel
    html = _fill_amount_cell(html, "Hoofdsom", _fmt_eur(amounts.get("hoofdsom")))
    # DF138-21: Rente expliciet invullen — hardcoded 0,00 in template is
    # weggehaald, server-side renderer vult nu de berekende waarde in.
    html = _fill_amount_cell(html, "Rente", _fmt_eur(amounts.get("rente")))
    html = _fill_amount_cell(html, "Hoofdsom + rente", _fmt_eur(amounts.get("hoofdsom_plus_rente")))
    html = _fill_amount_cell(html, "Incassokosten", _fmt_eur(amounts.get("incassokosten")))
    html = _fill_amount_cell(html, "BTW&nbsp;21%", _fmt_eur(amounts.get("btw")))
    html = _fill_amount_cell(html, "BTW 21%", _fmt_eur(amounts.get("btw")))
    html = _fill_amount_cell(html, "Totaal", _fmt_eur(amounts.get("totaal")))
    html = _fill_amount_cell(html, "Voldaan bij klant", _fmt_eur(amounts.get("voldaan_bij_klant")))
    html = _fill_amount_cell(html, "Door ons ontvangen", _fmt_eur(amounts.get("door_ons_ontvangen")))
    html = _fill_amount_cell(html, "Te voldoen", _fmt_eur(amounts.get("te_voldoen")))

    # Specifieke openstaand-bedrag in zin
    te_voldoen_str = _fmt_eur(amounts.get("te_voldoen"))
    html = html.replace(
        "openstaande bedrag van <strong>€&nbsp;</strong>",
        f"openstaande bedrag van <strong>€&nbsp;{te_voldoen_str}</strong>",
    )
    html = html.replace(
        "openstaande bedrag van € ",
        f"openstaande bedrag van € {te_voldoen_str} ",
    )
    # Sommatie-zin: "totaalbedrag van € uiterlijk binnen ..." mist bedrag.
    # Templates gebruiken &nbsp; tussen 'van' en '€' en tussen '€' en het lege
    # bedrag-veld. Match beide varianten (met en zonder &nbsp;).
    _ws = r"(?:\s|&nbsp;)+"
    html = re.sub(
        rf"totaalbedrag van{_ws}<strong>€&nbsp;</strong>",
        f"totaalbedrag van <strong>€&nbsp;{te_voldoen_str}</strong>",
        html,
    )
    html = re.sub(
        rf"totaalbedrag van{_ws}€{_ws}(uiterlijk|binnen)",
        rf"totaalbedrag van&nbsp;€&nbsp;{te_voldoen_str} \1",
        html,
    )

    # XXX-placeholder in Verweer beantwoorden template: vervang met AI weerlegging
    if ai_body and "XXX" in html:
        weerlegging = _extract_weerlegging(ai_body)
        if weerlegging:
            weerlegging_html = _plain_to_html_paragraph(weerlegging)
            html = html.replace("XXX<br>", weerlegging_html + "<br>", 1)
            if "XXX" in html:
                html = html.replace("XXX", weerlegging_html, 1)

    # Factuur-rijen
    html = _fill_invoice_rows(html, invoices)

    # Normaliseer tabel-styling voor alle templates (1e/2e/3e sommatie etc.)
    html = _normalize_table_styling(html)

    return html
