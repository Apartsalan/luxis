"""HTML email templates for incasso brieven — sent as email body (not attachment).

Each template mirrors the corresponding DOCX template text exactly, wrapped in
a branded Kesting Legal email layout.  Uses the same Jinja2 context dict produced
by documents.docx_service.build_base_context().

Supported template types: aanmaning, sommatie, tweede_sommatie, 14_dagenbrief,
herinnering.  All others return None → caller falls back to PDF attachment.
"""

from jinja2 import Environment, StrictUndefined
from markupsafe import Markup

_env = Environment(undefined=StrictUndefined, autoescape=True)

# ── Branded base layout ──────────────────────────────────────────────────

_BASE_EMAIL = """\
<!DOCTYPE html>
<html lang="nl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background-color:#ffffff;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" \
style="background-color:#ffffff;">
<tr><td align="center" style="padding:0;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" \
style="max-width:600px;width:100%;font-family:Arial,Helvetica,sans-serif;\
color:#1a1a1a;line-height:1.6;font-size:14px;">

<!-- Header -->
<tr><td style="padding:24px 32px 16px 32px;border-bottom:3px solid #c4a44c;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>
<td style="vertical-align:middle;">
<img src="https://kestinglegal.nl/logo.png" alt="Kesting Legal" \
style="max-width:180px;height:auto;display:block;" />
</td>
</tr>
</table>
</td></tr>

<!-- Kantoor address block -->
<tr><td style="padding:24px 32px 0 32px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" \
style="font-size:13px;color:#4b5563;">
<tr><td>
<strong>{{ kantoor.naam }}</strong><br>
{{ kantoor.adres }}<br>
{{ kantoor.postcode_stad }}<br>
{% if kantoor.telefoon %}Tel: {{ kantoor.telefoon }}<br>{% endif %}
</td></tr>
</table>
</td></tr>

<!-- Recipient address block -->
<tr><td style="padding:20px 32px 0 32px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" \
style="font-size:14px;">
<tr><td>
<strong>{{ wederpartij.naam }}</strong><br>
{% if wederpartij.adres %}{{ wederpartij.adres }}<br>{% endif %}
{% if wederpartij.postcode_stad %}{{ wederpartij.postcode_stad }}{% endif %}
</td></tr>
</table>
</td></tr>

<!-- Date + reference -->
<tr><td style="padding:20px 32px 0 32px;font-size:14px;">
{{ vandaag }}<br><br>
{{ betreft_regel }}<br>
Ons kenmerk: {{ zaak.zaaknummer }}
{% if zaak.referentie_regel %}<br>{{ zaak.referentie_regel }}{% endif %}
</td></tr>

<!-- Body content -->
<tr><td style="padding:20px 32px 0 32px;">
{{ content }}
</td></tr>

<!-- Signature -->
<tr><td style="padding:24px 32px 0 32px;font-size:14px;">
{{ afsluiting }}
</td></tr>

<!-- Footer -->
<tr><td style="padding:24px 32px 32px 32px;border-top:1px solid #e5e7eb;\
margin-top:24px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" \
style="font-size:12px;color:#6b7280;">
<tr><td>
<strong>{{ kantoor.naam }}</strong><br>
{{ kantoor.adres }}{% if kantoor.postcode_stad %} &middot; \
{{ kantoor.postcode_stad }}{% endif %}<br>
{% if kantoor.telefoon %}Tel: {{ kantoor.telefoon }}{% endif %}\
{% if kantoor.telefoon and kantoor.email %} &middot; {% endif %}\
{% if kantoor.email %}{{ kantoor.email }}{% endif %}
{% if kantoor.kvk %}<br>KvK: {{ kantoor.kvk }}{% endif %}
{% if kantoor.iban %}<br>IBAN: {{ kantoor.iban }}{% endif %}
</td></tr>
</table>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

_base_tpl = _env.from_string(_BASE_EMAIL)


def _render_branded(context: dict, betreft: str, content_html: str, afsluiting_html: str) -> str:
    """Wrap brief content in the branded email layout."""
    return _base_tpl.render(
        kantoor=context["kantoor"],
        wederpartij=context["wederpartij"],
        zaak=context["zaak"],
        vandaag=context["vandaag"],
        betreft_regel=Markup(betreft),
        content=Markup(content_html),
        afsluiting=Markup(afsluiting_html),
    )


# ── Shared HTML fragments ────────────────────────────────────────────────


def _claims_table(context: dict) -> str:
    """Render vorderingen table (4 columns)."""
    rows = context.get("vorderingen", [])
    if not rows:
        return ""
    html = (
        '<table role="presentation" width="100%" cellpadding="6" cellspacing="0" '
        'style="border-collapse:collapse;font-size:13px;margin:16px 0;">'
        "<tr>"
        '<th style="text-align:left;border-bottom:2px solid #1e293b;'
        'padding:8px 6px;">Omschrijving</th>'
        '<th style="text-align:left;border-bottom:2px solid #1e293b;'
        'padding:8px 6px;">Factuurnummer</th>'
        '<th style="text-align:left;border-bottom:2px solid #1e293b;'
        'padding:8px 6px;">Verzuimdatum</th>'
        '<th style="text-align:right;border-bottom:2px solid #1e293b;'
        'padding:8px 6px;">Hoofdsom</th>'
        "</tr>"
    )
    for v in rows:
        html += (
            "<tr>"
            f'<td style="padding:6px;border-bottom:1px solid #e5e7eb;">{v["beschrijving"]}</td>'
            f'<td style="padding:6px;border-bottom:1px solid #e5e7eb;">{v["factuurnummer"]}</td>'
            f'<td style="padding:6px;border-bottom:1px solid #e5e7eb;">{v["verzuimdatum"]}</td>'
            '<td style="padding:6px;border-bottom:1px solid #e5e7eb;'
            f'text-align:right;">{v["hoofdsom"]}</td>'
            "</tr>"
        )
    html += "</table>"
    return html


def _summary_row(label: str, value: str, bold: bool = False) -> str:
    """Single row for the financial summary table."""
    if not label and not value:
        return ""
    weight = "font-weight:bold;" if bold else ""
    return (
        "<tr>"
        f'<td style="padding:4px 6px;{weight}">{label}</td>'
        f'<td style="padding:4px 6px;text-align:right;{weight}">{value}</td>'
        "</tr>"
    )


def _financial_summary(context: dict, include_payments: bool = True) -> str:
    """Render the 2-column financial summary table."""
    html = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;font-size:13px;margin:16px 0;'
        'border-top:2px solid #1e293b;">'
    )
    html += _summary_row("Hoofdsom", context["totaal_hoofdsom"], bold=True)
    html += _summary_row(f"Rente t/m {context['vandaag']}", context["totaal_rente"])
    html += _summary_row("Buitengerechtelijke incassokosten (BIK)", context["bik_bedrag"])
    html += _summary_row(context["btw_regel_label"], context["btw_regel_bedrag"])
    html += _summary_row("Totaal verschuldigd", context["totaal_verschuldigd"], bold=True)
    if include_payments:
        html += _summary_row(
            context["betalingen_aftrek_label"], context["betalingen_aftrek_bedrag"]
        )
        html += _summary_row("Totaal openstaand", context["totaal_openstaand"], bold=True)
    html += "</table>"
    return html


def _financial_summary_compact(context: dict) -> str:
    """Compact summary: only hoofdsom + rente + openstaand."""
    html = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;font-size:13px;margin:16px 0;'
        'border-top:2px solid #1e293b;">'
    )
    html += _summary_row("Hoofdsom", context["totaal_hoofdsom"], bold=True)
    html += _summary_row(f"Rente t/m {context['vandaag']}", context["totaal_rente"])
    html += _summary_row("Totaal openstaand", context["totaal_openstaand"], bold=True)
    html += "</table>"
    return html


def _heading(text: str) -> str:
    return (
        f'<p style="font-size:15px;font-weight:bold;color:#1e293b;margin:20px 0 8px 0;">{text}</p>'
    )


# ── Template: Aanmaning ──────────────────────────────────────────────────


def _render_aanmaning(ctx: dict) -> str:
    body = (
        "<p>Geachte heer/mevrouw,</p>"
        f"<p>Ondanks onze eerdere herinnering constateren wij dat de "
        f"vordering(en) van onze cli&euml;nt {ctx['client']['naam']} "
        f"nog steeds niet zijn voldaan.</p>"
    )
    body += _heading("Specificatie")
    body += _claims_table(ctx)
    body += _financial_summary(ctx, include_payments=True)
    body += (
        f"<p>Wij sommeren u het bedrag van <strong>{ctx['totaal_openstaand']}"
        f"</strong> uiterlijk {ctx['termijn_14_dagen']} te voldoen op "
        f"IBAN {ctx['kantoor']['iban']} t.n.v. {ctx['kantoor']['naam']}, "
        f"onder vermelding van zaaknummer {ctx['zaak']['zaaknummer']}.</p>"
        "<p>Bij gebreke van tijdige betaling zullen wij zonder nadere "
        "aankondiging rechtsmaatregelen treffen.</p>"
    )
    afsluiting = f"Hoogachtend,<br><br>{ctx['kantoor']['naam']}"
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: Aanmaning tot betaling</strong>",
        content_html=body,
        afsluiting_html=afsluiting,
    )


# ── Template: Sommatie ───────────────────────────────────────────────────


def _render_sommatie(ctx: dict) -> str:
    body = (
        "<p>Geachte heer/mevrouw,</p>"
        f"<p>Tot mij heeft zich gewend {ctx['client']['naam']} met het "
        f"verzoek u te sommeren tot betaling van het hierna te noemen bedrag. "
        f"Tot op heden is betaling, ondanks eerdere aanmaningen, uitgebleven.</p>"
    )
    body += _heading("Specificatie vordering")
    body += _claims_table(ctx)
    # Sommatie uses betalingen_regel (inline deduction in summary)
    summary = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;font-size:13px;margin:16px 0;'
        'border-top:2px solid #1e293b;">'
    )
    summary += _summary_row("Hoofdsom", ctx["totaal_hoofdsom"], bold=True)
    summary += _summary_row(f"Wettelijke rente t/m {ctx['vandaag']}", ctx["totaal_rente"])
    summary += _summary_row("Buitengerechtelijke incassokosten", ctx["bik_bedrag"])
    summary += _summary_row(ctx["btw_regel_label"], ctx["btw_regel_bedrag"])
    summary += _summary_row(ctx["betalingen_regel_label"], ctx["betalingen_regel_bedrag"])
    summary += _summary_row("Totaal thans verschuldigd", ctx["totaal_openstaand"], bold=True)
    summary += "</table>"
    body += summary

    body += _heading("Sommatie")
    body += (
        f"<p>Ik sommeer u hierbij om het verschuldigde bedrag van "
        f"<strong>{ctx['totaal_openstaand']}</strong> binnen acht (8) dagen "
        f"na dagtekening van deze brief over te maken.</p>"
        "<p>Bij gebreke van tijdige en volledige betaling zal ik, zonder "
        "nadere aankondiging, overgaan tot het uitbrengen van een dagvaarding. "
        "De hieraan verbonden kosten (griffierecht, deurwaarderskosten, "
        "proceskosten) komen volledig voor uw rekening.</p>"
        "<p>Ik vertrouw erop u hiermee voldoende te hebben "
        "ge&iuml;nformeerd en zie uw betaling met spoed tegemoet.</p>"
    )
    afsluiting = f"Hoogachtend,<br><br>________________________<br>Namens {ctx['client']['naam']}"
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: SOMMATIE &mdash; Laatste aanmaning voor dagvaarding</strong>",
        content_html=body,
        afsluiting_html=afsluiting,
    )


# ── Template: Tweede Sommatie ────────────────────────────────────────────


def _render_tweede_sommatie(ctx: dict) -> str:
    body = (
        "<p>Geachte heer/mevrouw,</p>"
        f"<p>Ondanks onze eerdere sommatie heeft u nog steeds niet voldaan "
        f"aan de vordering(en) van onze cli&euml;nt {ctx['client']['naam']}. "
        f"Dit is uw laatste gelegenheid om vrijwillig te betalen.</p>"
    )
    body += _heading("Specificatie")
    body += _financial_summary(ctx, include_payments=True)
    body += (
        f"<p>Wij sommeren u &mdash; voor de laatste maal &mdash; het bedrag van "
        f"<strong>{ctx['totaal_openstaand']}</strong> uiterlijk "
        f"{ctx['termijn_14_dagen']} te voldoen op "
        f"IBAN {ctx['kantoor']['iban']} t.n.v. {ctx['kantoor']['naam']}, "
        f"onder vermelding van zaaknummer {ctx['zaak']['zaaknummer']}.</p>"
        "<p>Bij gebreke van tijdige betaling zullen wij zonder nadere "
        "aankondiging tot dagvaarding overgaan. De kosten hiervan "
        "(griffierecht, deurwaarderskosten, proceskosten) komen "
        "volledig voor uw rekening.</p>"
    )
    afsluiting = f"Hoogachtend,<br><br>{ctx['kantoor']['naam']}"
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: TWEEDE SOMMATIE &mdash; Laatste gelegenheid</strong>",
        content_html=body,
        afsluiting_html=afsluiting,
    )


# ── Template: 14-dagenbrief ──────────────────────────────────────────────


def _render_14_dagenbrief(ctx: dict) -> str:
    body = (
        "<p>Geachte heer/mevrouw,</p>"
        f"<p>Namens onze cli&euml;nt, {ctx['client']['naam']}, sommeer ik u "
        f"hierbij tot betaling van het hieronder gespecificeerde bedrag. "
        f"Ondanks eerdere verzoeken is betaling tot op heden uitgebleven.</p>"
    )
    body += _heading("Specificatie vordering(en)")
    body += _claims_table(ctx)
    # Summary without payments deduction (14-dagenbrief shows totaal_verschuldigd)
    summary = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;font-size:13px;margin:16px 0;'
        'border-top:2px solid #1e293b;">'
    )
    summary += _summary_row("Totaal hoofdsom", ctx["totaal_hoofdsom"], bold=True)
    summary += _summary_row(f"Wettelijke rente t/m {ctx['vandaag']}", ctx["totaal_rente"])
    summary += _summary_row("Buitengerechtelijke incassokosten (BIK)", ctx["bik_bedrag"])
    summary += _summary_row(ctx["btw_regel_label"], ctx["btw_regel_bedrag"])
    summary += _summary_row("Totaal verschuldigd", ctx["totaal_verschuldigd"], bold=True)
    summary += "</table>"
    body += summary

    body += _heading("Wettelijke mededeling (art. 6:96 lid 6 BW)")
    body += (
        f"<p>Hierbij wordt u gesommeerd het verschuldigde bedrag van "
        f"<strong>{ctx['totaal_hoofdsom']}</strong> binnen veertien dagen "
        f"na ontvangst van deze brief te voldoen op het rekeningnummer "
        f"van onze cli&euml;nt.</p>"
        f"<p>Indien betaling binnen deze termijn uitblijft, bent u naast "
        f"de hoofdsom tevens de buitengerechtelijke incassokosten verschuldigd "
        f"ter hoogte van <strong>{ctx['bik_bedrag']}"
        f"{ctx['btw_toelichting']}</strong>, alsmede de wettelijke rente "
        f"vanaf de verzuimdatum.</p>"
        f"<p>Ik verzoek u het totaal verschuldigde bedrag van "
        f"<strong>{ctx['totaal_verschuldigd']}</strong> binnen veertien dagen "
        f"na dagtekening van deze brief over te maken.</p>"
        "<p>Bij gebreke van tijdige betaling zullen wij zonder nadere "
        "aankondiging rechtsmaatregelen treffen, waarvan de kosten eveneens "
        "voor uw rekening komen.</p>"
    )
    afsluiting = f"Hoogachtend,<br><br>________________________<br>Namens {ctx['client']['naam']}"
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: Ingebrekestelling en aanmaning tot betaling</strong>",
        content_html=body,
        afsluiting_html=afsluiting,
    )


# ── Template: Herinnering ────────────────────────────────────────────────


def _render_herinnering(ctx: dict) -> str:
    body = (
        "<p>Geachte heer/mevrouw,</p>"
        f"<p>Wij constateren dat de onderstaande vordering(en) van onze "
        f"cli&euml;nt {ctx['client']['naam']} nog niet zijn voldaan. "
        f"Wij verzoeken u vriendelijk het openstaande bedrag binnen "
        f"14 dagen te voldoen.</p>"
    )
    body += _heading("Specificatie")
    body += _financial_summary_compact(ctx)
    body += (
        f"<p>Wij verzoeken u het bedrag van <strong>{ctx['totaal_openstaand']}"
        f"</strong> voor {ctx['termijn_14_dagen']} over te maken op "
        f"IBAN {ctx['kantoor']['iban']} t.n.v. {ctx['kantoor']['naam']}, "
        f"onder vermelding van zaaknummer {ctx['zaak']['zaaknummer']}.</p>"
    )
    afsluiting = f"Met vriendelijke groet,<br><br>{ctx['kantoor']['naam']}"
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: Herinnering openstaande vordering</strong>",
        content_html=body,
        afsluiting_html=afsluiting,
    )


# ── Public API ───────────────────────────────────────────────────────────

_RENDERERS: dict[str, callable] = {
    "aanmaning": _render_aanmaning,
    "sommatie": _render_sommatie,
    "tweede_sommatie": _render_tweede_sommatie,
    "14_dagenbrief": _render_14_dagenbrief,
    "herinnering": _render_herinnering,
}


def render_incasso_email(template_type: str, context: dict) -> str | None:
    """Render an incasso brief as branded HTML email body.

    Args:
        template_type: Template key (e.g. "aanmaning", "sommatie").
        context: Full context dict from build_base_context().

    Returns:
        HTML string for the email body, or None if template_type is not
        supported as inline email (caller should fall back to PDF attachment).
    """
    renderer = _RENDERERS.get(template_type)
    if renderer is None:
        return None
    return renderer(context)
