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


def _signature(ctx: dict, english: bool = False) -> str:
    """Lisanne's full signature block — matches BaseNet style exactly."""
    k = ctx["kantoor"]
    if english:
        return (
            "Yours faithfully,<br><br>"
            "<strong>Mevr. mr. L. Kesting</strong><br>"
            "DEBT COLLECTION ATTORNEY<br><br>"
            f"{k['adres']}<br>"
            f"{k['postcode_stad']}<br>"
            f"E: {k['email']}<br>"
            "W: www.kestinglegal.nl"
        )
    return (
        "Hoogachtend,<br><br>"
        "<strong>Mevr. mr. L. Kesting</strong><br>"
        "INCASSO ADVOCAAT | DEBT COLLECTION ATTORNEY<br><br>"
        f"{k['adres']}<br>"
        f"{k['postcode_stad']}<br>"
        f"E: {k['email']}<br>"
        "W: www.kestinglegal.nl"
    )


def _schuldhulp_disclaimer(ctx: dict) -> str:
    """Wettelijk verplicht schuldhulpblok + disclaimer — matches BaseNet."""
    return (
        '<p style="font-size:11px;color:#6b7280;margin-top:24px;'
        'border-top:1px solid #e5e7eb;padding-top:16px;">'
        "Heeft u financi&euml;le zorgen en ziet u geen uitweg meer? "
        "Wij informeren u graag over uw rechten als schuldenaar: "
        '<a href="https://kestinglegal.nl/debiteuren" '
        'style="color:#c4a44c;">kestinglegal.nl/debiteuren</a>. '
        "Voor schuldhulpverlening kunt u terecht bij uw gemeente. "
        "Heeft u dringend emotionele steun nodig? Bel dan gratis "
        "en anoniem met Stichting 113 Zelfmoordpreventie via "
        "0800-0113 of kijk op "
        '<a href="http://www.113.nl" style="color:#c4a44c;">'
        "www.113.nl</a>.</p>"
        '<p style="font-size:10px;color:#9ca3af;margin-top:12px;">'
        "Disclaimer - De informatie verzonden met dit e-mailbericht "
        "is uitsluitend bestemd voor de geadresseerde(n) en kan "
        "persoonlijke of vertrouwelijke informatie bevatten, "
        "beschermd door een beroepsgeheim. Gebruik van deze "
        "informatie door anderen dan de geadresseerde(n) en "
        "gebruik door hen die niet gerechtigd zijn van deze "
        "informatie kennis te nemen, is verboden. Indien u niet "
        "de geadresseerde bent of niet gerechtigd bent tot "
        "kennisneming, is openbaarmaking, vermenigvuldiging, "
        "verspreiding en/of verstrekking van deze informatie "
        "aan derden niet toegestaan en wordt u verzocht dit "
        "bericht terug te sturen en het origineel te vernietigen."
        "</p>"
    )


def _vordering_table_basenet(ctx: dict) -> str:
    """Vorderingstabel + financieel overzicht in BaseNet-stijl.

    Layout: factuurnummer | datum | vervaldatum | bedrag (per vordering)
    + samenvattingsregels (hoofdsom, rente, BIK, BTW, totaal, voldaan, te voldoen)
    """
    rows = ctx.get("vorderingen", [])
    html = (
        '<table role="presentation" width="500" cellpadding="4" '
        'cellspacing="0" style="border-collapse:collapse;font-size:13px;'
        'margin:16px 0;">'
        "<tr>"
        '<td style="padding:4px 6px;"><strong>Factuurnummer</strong></td>'
        '<td style="padding:4px 6px;"><strong>Datum</strong></td>'
        '<td style="padding:4px 6px;"><strong>Vervaldatum</strong></td>'
        '<td colspan="2" style="padding:4px 6px;">'
        "<strong>Bedrag</strong></td>"
        "</tr>"
    )
    for v in rows:
        html += (
            "<tr>"
            f'<td style="padding:4px 6px;">{v["factuurnummer"]}</td>'
            f'<td style="padding:4px 6px;">{v["verzuimdatum"]}</td>'
            f'<td style="padding:4px 6px;">{v["verzuimdatum"]}</td>'
            f'<td colspan="2" style="padding:4px 6px;">'
            f'{v["hoofdsom"]}</td>'
            "</tr>"
        )
    # Empty rows for spacing
    html += '<tr><td colspan="5">&nbsp;</td></tr>'
    # Summary rows
    summary_rows = [
        ("Hoofdsom", ctx["totaal_hoofdsom"], False),
        ("Rente", ctx["totaal_rente"], False),
        ("Hoofdsom + rente", ctx["subtotaal"], False),
        ("Incassokosten", ctx["bik_bedrag"], False),
    ]
    if ctx.get("btw_regel_label"):
        summary_rows.append(
            (ctx["btw_regel_label"], ctx["btw_regel_bedrag"], False)
        )
    summary_rows.append(("Totaal", ctx["totaal_verschuldigd"], False))
    summary_rows.append(
        ("Voldaan bij klant", ctx.get("betalingen_aftrek_bedrag", ""), False)
    )
    summary_rows.append(
        ("Door ons ontvangen", ctx.get("betalingen_aftrek_bedrag", ""), False)
    )
    summary_rows.append(("", "", False))  # empty row
    summary_rows.append(
        ("<strong>Te voldoen</strong>", f"<strong>{ctx['totaal_openstaand']}</strong>", True)
    )
    for label, value, _bold in summary_rows:
        html += (
            "<tr>"
            f'<td colspan="3" style="padding:2px 6px;">{label}</td>'
            f'<td style="padding:2px 6px;">&euro;</td>'
            f'<td style="padding:2px 6px;">{value}</td>'
            "</tr>"
        )
    html += "</table>"
    return html


def _betaling_instructie(ctx: dict, termijn: str = "2 DAGEN") -> str:
    """Betalingsinstructie blok — IBAN derdengelden + kenmerk."""
    return (
        f"<p>Hierbij sommeer ik u andermaal het bovengenoemd totaalbedrag "
        f"ad {ctx['totaal_openstaand']} <strong>UITERLIJK BINNEN "
        f"{termijn} NA HEDEN</strong> te hebben bijgeschreven op de "
        "derdengeldenrekening van mijn kantoor IBAN: NL20 RABO 0388 "
        "5065 20 t.n.v. Stichting Beheer Derdengelden Kesting Legal "
        f"onder vermelding van het kenmerk "
        f"{ctx['zaak']['zaaknummer']}.</p>"
    )


def _betalingsregeling_blok(ctx: dict) -> str:
    """Betalingsregeling + dossiernummer + bij uitblijven van betaling."""
    return (
        "<p><strong>Betalingsregeling</strong><br>"
        "Indien u een betalingsregeling wilt voorstellen voor voornoemd "
        "totaalbedrag verneem ik dat graag uiterlijk binnen voornoemde "
        "termijn in reply op deze e-mail. Let op: aan het doen van een "
        "voorstel voor een betalingsregeling kunnen geen rechten "
        "ontleend worden.</p>"
        "<p>Let op dat u bij het doen van de betaling het juiste "
        "dossiernummer vermeldt, zodat uw betaling correct kan "
        "worden verwerkt en toegewezen.</p>"
        "<p><strong>Bij uitblijven van betaling</strong><br>"
        "Blijft betaling wederom uit, dan zal ik u in rechte moeten "
        "betrekken, voor welke kosten cli&euml;nte u integraal "
        "aansprakelijk houdt.</p>"
        "<p>Graag ontvang ik daarom uw betaalbewijs.</p>"
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
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: Aanmaning tot betaling</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Sommatie ───────────────────────────────────────────────────


def _render_sommatie(ctx: dict) -> str:
    """Eerste sommatie tot betaling (Basenet L13) — 3 dagen + AV.

    Standaard eerste sommatie na overdracht ter incasso. Verwijst naar
    Algemene Voorwaarden van cliënt + wettelijke/contractuele rente.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Cli&euml;nt heeft mij verzocht om onderstaande openstaande "
        "vordering bij u te incasseren. Deze vordering is ter verdere "
        "afwikkeling aan mijn kantoor overgedragen.</p>"
        "<p>Cli&euml;nt hanteert Algemene Voorwaarden, welke van toepassing "
        "zijn op alle transacties. Primair op grond van die voorwaarden en "
        "subsidiair op grond van de van toepassing zijnde wettelijke "
        "bepalingen verhaal ik onderstaand bedrag op u.</p>"
        "<p>Thans bent u het volgende verschuldigd:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += (
        "<p><strong>Sommatie tot betaling</strong></p>"
        f"<p>Ik sommeer u hierbij om het openstaande bedrag van "
        f"<strong>{ctx['totaal_openstaand']}</strong> "
        "<strong>BINNEN 3 DAGEN NA HEDEN</strong> bij te schrijven op de "
        "derdengeldenrekening van mijn kantoor IBAN NL20 RABO 0388 5065 20 "
        "ten name van Stichting Beheer Derdengelden Kesting Legal onder "
        f"vermelding van het kenmerk {zn}.</p>"
        "<p>Ik wijs u erop dat alleen betaling van het volledige bedrag op "
        "de hiervoor aangegeven wijze ervoor zorgt dat de incassoprocedure "
        "wordt gestopt. Blijft betaling uit binnen de gestelde termijn, "
        "dan heeft cli&euml;nt mij reeds verzocht alle rechtsmaatregelen "
        "tegen u te nemen die nodig worden geacht. De kosten die hiermee "
        "gepaard gaan, zullen op u worden verhaald.</p>"
        "<p><strong>Wettelijke of contractuele rente</strong><br>"
        "Omdat u niet op tijd heeft betaald, moet u ook rente betalen. "
        "Cli&euml;nt mag deze rente van u eisen op grond van de gesloten "
        "overeenkomst en van toepassing zijnde Algemene Voorwaarden. De "
        "rente loopt vanaf het moment dat u de schuld had moeten betalen "
        "(vervaldatum) tot aan het moment van algehele voldoening.</p>"
        "<p>Ik vertrouw erop dat u de ernst van de situatie inziet en "
        "tijdig tot betaling overgaat.</p>"
    )
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            f"<strong>SOMMATIE TOT BETALING / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
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
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: TWEEDE SOMMATIE &mdash; Laatste gelegenheid</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
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
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: Ingebrekestelling en aanmaning tot betaling</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
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
    body += _schuldhulp_disclaimer(ctx)
    afsluiting = (
        "Met vriendelijke groet,<br><br>"
        "<strong>Mevr. mr. L. Kesting</strong><br>"
        "INCASSO ADVOCAAT | DEBT COLLECTION ATTORNEY<br><br>"
        f"{ctx['kantoor']['adres']}<br>"
        f"{ctx['kantoor']['postcode_stad']}<br>"
        f"E: {ctx['kantoor']['email']}<br>"
        "W: www.kestinglegal.nl"
    )
    return _render_branded(
        ctx,
        betreft="<strong>Betreft: Herinnering openstaande vordering</strong>",
        content_html=body,
        afsluiting_html=afsluiting,
    )


# ── Template: Reactie art. 9.3 (intrekking incasso-opdracht) ────────────


def _render_reactie_9_3(ctx: dict) -> str:
    body = (
        "<p>,</p>"
        f"<p>Eerder schreef ik u aan inzake de onbetaald gelaten "
        f"vordering van mijn cli&euml;nte {ctx['client']['naam']}. "
        "De vordering is aan mijn kantoor overgedragen ter incasso.</p>"
        "<p>U heeft gereageerd. Hieronder treft u mijn antwoord aan.</p>"
        "<p>Cli&euml;nte heeft haar ter incasso gestelde opdracht "
        "afgewikkeld op grond van de overeengekomen voorwaarden en "
        "tarieven, meer in het bijzonder art. 9.3 van de voorwaarden, "
        "als volgt:</p>"
        '<p><em>9.3 Indien Cli&euml;nt een incasso-opdracht intrekt, '
        "buiten het Invorderingsbedrijf om een betalingsregeling treft "
        "met de Debiteur, met de Debiteur een schikking treft, het "
        "Invorderingsbedrijf zonder enig bericht laat, de betaling zelf "
        "regelt, dan wel een verdere incassobehandeling in de weg staat, "
        "is het Invorderingsbedrijf niettemin gerechtigd over de gehele "
        "haar ter incasso gestelde vordering 15% commissie, een bedrag "
        "van &euro; 25,- (exclusief BTW) aan registratiekosten en "
        "overige kosten &ndash; waaronder onder meer alle verschuldigde "
        "kosten van derden, zoals buitendienst, leges, proces- en "
        "executiekosten &ndash; in rekening te brengen.</em></p>"
        "<p>De verplichting tot betaling staat hiermee dan ook vast.</p>"
        "<p>Ik sommeer u zodoende voor een laatste maal.</p>"
    )
    body += _heading("Vordering")
    body += "<p>Het door u verschuldigde bedrag is als volgt gespecificeerd.</p>"
    body += _vordering_table_basenet(ctx)
    body += _betaling_instructie(ctx)
    body += _betalingsregeling_blok(ctx)
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=f"<strong>Betreft: {ctx['zaak']['zaaknummer']}</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Reactie art. 20.4 (eindafrekening) ───────────────────────


def _render_reactie_20_4(ctx: dict) -> str:
    body = (
        "<p>,</p>"
        f"<p>Eerder schreef ik u aan inzake de onbetaald gelaten "
        f"vordering van mijn cli&euml;nte {ctx['client']['naam']}. "
        "De vordering is aan mijn kantoor overgedragen ter incasso.</p>"
        "<p>U heeft gereageerd. Hieronder treft u mijn antwoord aan.</p>"
        "<p>Cli&euml;nte heeft haar ter incasso gestelde opdracht "
        "afgewikkeld op grond van de overeengekomen voorwaarden en "
        "tarieven, meer in het bijzonder art. 20.4 van de voorwaarden, "
        "als volgt:</p>"
        "<p><em>20.4 Indien een dossier wordt gesloten, wordt een "
        "eindafrekening gemaakt waarop aan Cli&euml;nt in rekening "
        "wordt gebracht de toegewezen incassokosten, rente, salaris "
        "gemachtigde, honorarium en kosten van derden, vermeerderd "
        "met eventuele overige toegekende vergoedingen en gemaakte "
        "kosten.</em></p>"
        "<p>De verplichting tot betaling staat hiermee dan ook vast.</p>"
        "<p>Ik sommeer u zodoende voor een laatste maal.</p>"
    )
    body += _heading("Vordering")
    body += "<p>Het door u verschuldigde bedrag is als volgt gespecificeerd.</p>"
    body += _vordering_table_basenet(ctx)
    body += _betaling_instructie(ctx)
    body += _betalingsregeling_blok(ctx)
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=f"<strong>Betreft: {ctx['zaak']['zaaknummer']}</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Eenmalig schikkingsvoorstel ───────────────────────────────


def _render_schikkingsvoorstel(ctx: dict) -> str:
    """Eenmalig schikkingsvoorstel (Basenet L3) — 24 uur termijn.

    Placeholder `[VUL SCHIKKINGSBEDRAG IN]` wordt door Lisanne handmatig
    overschreven in de contentEditable body-editor vóór verzenden.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Zoals ik u eerder liet weten heeft cli&euml;nte haar "
        "vordering aan mij uit handen gegeven.</p>"
        "<p>In onderhavige incassoprocedure is het totaal openstaande "
        "bedrag hieronder gespecificeerd:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += (
        "<p><strong>Eenmalig voorstel</strong></p>"
        "<p>Ik heb cli&euml;nte bereid gevonden om u een eenmalig "
        "voorstel te doen. Zij is bereid om de zaak te schikken "
        "tegen betaling van "
        '<mark style="background:#fef3c7;padding:2px 6px;">'
        "[VUL SCHIKKINGSBEDRAG IN]</mark> door u tegen verdere "
        "algehele finale kwijting over en weer ten aanzien van "
        "onderhavige vordering.</p>"
        "<p>Namens cli&euml;nte sommeer ik u om het voormelde "
        "bedrag <strong>binnen 24 uur na heden</strong> bij te "
        "schrijven op de derdengeldenrekening van mijn kantoor "
        "IBAN: NL20 RABO 0388 5065 20 ten name van Stichting "
        "Beheer Derdengelden Kesting Legal onder vermelding van "
        f"het kenmerk {zn}.</p>"
        "<p>Is het bedrag alsdan niet bijgeschreven, dan komt het "
        "aanbod automatisch te vervallen en kan daar zowel in als "
        "buiten rechte geen beroep meer op worden gedaan, laat "
        "staan rechten aan worden ontleend.</p>"
        "<p>Het aanbod wordt gedaan zonder enige nadelige erkenning "
        "en enkel uit proceseconomische redenen.</p>"
        "<p>Na ontvangst van betaling zal ik het dossier sluiten. "
        "Ik verzoek u mij in dat kader het betalingsbewijs toe "
        "te sturen.</p>"
    )
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            f"<strong>EENMALIG SCHIKKINGSVOORSTEL / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: English demand (9.3 + verlengd abonnement) ───────────────


def _render_engelse_sommatie(ctx: dict) -> str:
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Dear sir/madam,</p>"
        f"<p>Earlier, I wrote to you regarding the outstanding claim "
        f"of my client {ctx['client']['naam']}. This claim has been "
        "transferred to my office for collection.</p>"
        "<p>You have since responded. Please find my reply below.</p>"
        "<p>You entered into a service agreement with my client for "
        "a duration of one year, with automatic renewal for successive "
        "one-year terms, unless terminated in writing no later than "
        "three months before the end of the current term.</p>"
        "<p>My client did not receive a timely or valid notice of "
        "termination from you. Therefore, pursuant to the contractual "
        "provisions, the agreement was automatically renewed and is "
        "currently in force. You are thus obliged to pay the "
        "subscription fee for the renewed term.</p>"
        "<p>My client has previously informed you of this, yet no "
        "payment has been received to date. As this constitutes a "
        "default in payment, my client is entitled, under article 9.3 "
        "of the agreement, to settle the claim as follows:</p>"
        "<p><em>If the Client withdraws a debt collection assignment, "
        "makes a payment arrangement with the debtor without the "
        "involvement of Invorderingsbedrijf, reaches a settlement "
        "with the debtor, leaves Invorderingsbedrijf without any "
        "notification, arranges the payment itself, or stands in the "
        "way of further collection processing, Invorderingsbedrijf "
        "shall nevertheless be entitled to charge a 15% commission "
        "on the entire debt referred to it for collection, an amount "
        "of &euro;25 (exclusive of VAT) for registration costs and "
        "other costs.</em></p>"
        "<p>The payment obligation is therefore established.</p>"
        "<p>Accordingly, I hereby issue a final demand for payment.</p>"
    )
    body += _heading("Claim")
    body += "<p>You currently owe the following amount:</p>"
    body += _vordering_table_basenet(ctx)
    body += (
        f"<p>I hereby demand that you transfer the total outstanding "
        f"amount of {ctx['totaal_openstaand']} <strong>WITHIN 2 DAYS "
        "FROM TODAY</strong> to the escrow account of my office "
        "IBAN: NL20 RABO 0388 5065 20 in the name of Stichting "
        f"Beheer Derdengelden Kesting Legal, stating reference {zn}.</p>"
        "<p><strong>Payment arrangement</strong><br>"
        "If you wish to propose a payment arrangement, please reply "
        "to this e-mail within the stated deadline. Please note: "
        "proposing a payment arrangement does not create any rights.</p>"
        "<p><strong>In case of non-payment</strong><br>"
        "If payment is not received, I will have no choice but to "
        "commence legal proceedings, the costs of which will be "
        "charged to you in full.</p>"
    )
    return _render_branded(
        ctx,
        betreft=f"<strong>DEMAND FOR PAYMENT / {zn}</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx, english=True),
    )


# ── Template: Reactie NCNP 9.3 + Disclaimer (gerechtelijk) ────────────


def _render_reactie_ncnp_9_3(ctx: dict) -> str:
    body = (
        "<p>,</p>"
        f"<p>Eerder schreef ik u aan inzake de onbetaald gelaten "
        f"vordering van mijn cli&euml;nte {ctx['client']['naam']}. "
        "De vordering is aan mijn kantoor overgedragen ter incasso.</p>"
        "<p>U heeft gereageerd en daarbij gesteld dat sprake zou zijn "
        "van een afspraak op basis van &ldquo;no cure no pay&rdquo;. "
        "Daarop het volgende.</p>"
        "<p>Bij aanvang van de gerechtelijke procedure is u per e-mail "
        "de schriftelijke opdrachtbevestiging toegezonden, waarin "
        "expliciet is vermeld dat de werkwijze van no cure no pay "
        "niet langer van toepassing is. In de overeenkomst zelf staat "
        "hierover het volgende vermeld:</p>"
        "<p><em><strong>No Cure No Pay</strong><br>"
        "De werkwijze van No Cure No Pay is uitdrukkelijk niet van "
        "toepassing in de juridische fase en vervalt met de aanvang "
        "van de juridische fase.</em></p>"
        "<p>De door cli&euml;nte gemaakte (proces)kosten zijn dan ook "
        "volledig in lijn met de gesloten overeenkomst, en zien op "
        "werkzaamheden die daadwerkelijk zijn verricht in het kader "
        "van de gerechtelijke procedure.</p>"
        "<p>Bovendien is in artikel 9.3 van de overeenkomst "
        "ondubbelzinnig bepaald dat het Invorderingsbedrijf bij "
        "tussentijdse be&euml;indiging of belemmering van het "
        "traject gerechtigd is kosten in rekening te brengen, "
        "ongeacht het resultaat:</p>"
        "<p><em>Artikel 9.3 &mdash; Indien Cli&euml;nt een "
        "incasso-opdracht intrekt, buiten het Invorderingsbedrijf om "
        "een betalingsregeling treft met de Debiteur, met de Debiteur "
        "een schikking treft, het Invorderingsbedrijf zonder enig "
        "bericht laat, de betaling zelf regelt, dan wel een verdere "
        "incassobehandeling in de weg staat, is het Invorderingsbedrijf "
        "niettemin gerechtigd over de gehele haar ter incasso gestelde "
        "vordering 15% commissie, een bedrag van &euro; 25,- "
        "(exclusief BTW) aan registratiekosten en overige kosten "
        "&ndash; in rekening te brengen.</em></p>"
        "<p>De verplichting tot betaling staat hiermee dan ook vast.</p>"
        "<p>Ik sommeer u zodoende voor een laatste maal.</p>"
    )
    body += _heading("Vordering")
    body += "<p>Het door u verschuldigde bedrag is als volgt gespecificeerd.</p>"
    body += _vordering_table_basenet(ctx)
    body += _betaling_instructie(ctx)
    body += _betalingsregeling_blok(ctx)
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=f"<strong>Betreft: {ctx['zaak']['zaaknummer']}</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Reactie verlengd abonnement + 9.3 ───────────────────────


def _render_reactie_verlengd_9_3(ctx: dict) -> str:
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        f"<p>Eerder schreef ik u aan inzake de onbetaald gelaten "
        f"vordering van mijn cli&euml;nte {ctx['client']['naam']}. "
        "De vordering is aan mijn kantoor overgedragen ter incasso.</p>"
        "<p>U heeft gereageerd. Hieronder treft u mijn antwoord aan.</p>"
        "<p>U heeft met cli&euml;nte een serviceovereenkomst gesloten "
        "voor de duur van &eacute;&eacute;n jaar, met stilzwijgende "
        "verlenging telkens voor de duur van een jaar, tenzij "
        "uiterlijk drie maanden voor het einde van de lopende termijn "
        "schriftelijk wordt opgezegd.</p>"
        "<p>Cli&euml;nte heeft van u geen tijdige of geldige opzegging "
        "ontvangen. De overeenkomst is daarmee automatisch verlengd "
        "en loopt thans door. U bent om die reden gehouden tot "
        "betaling van het abonnementstarief voor de verlengde "
        "periode.</p>"
        "<p>Nu sprake is van wanbetaling, is cli&euml;nte op grond "
        "van artikel 9.3 van de overeenkomst gerechtigd tot "
        "afrekening van de vordering als volgt:</p>"
        "<p><em>Indien Cli&euml;nt een incasso-opdracht intrekt, "
        "buiten het Invorderingsbedrijf om een betalingsregeling "
        "treft met de Debiteur, met de Debiteur een schikking treft, "
        "het Invorderingsbedrijf zonder enig bericht laat, de "
        "betaling zelf regelt, dan wel een verdere incassobehandeling "
        "in de weg staat, is het Invorderingsbedrijf niettemin "
        "gerechtigd over de gehele haar ter incasso gestelde "
        "vordering 15% commissie, een bedrag van &euro; 25,- "
        "(exclusief BTW) aan registratiekosten en overige kosten "
        "&ndash; in rekening te brengen.</em></p>"
        "<p>De betalingsverplichting staat daarmee vast.</p>"
        "<p>Ik sommeer u zodoende voor een laatste maal.</p>"
    )
    body += _heading("Vordering")
    body += "<p>Het door u verschuldigde bedrag is als volgt gespecificeerd.</p>"
    body += _vordering_table_basenet(ctx)
    body += _betaling_instructie(ctx)
    body += _betalingsregeling_blok(ctx)
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=f"<strong>Betreft: {ctx['zaak']['zaaknummer']}</strong>",
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Vaststellingsovereenkomst (betalingsregeling) ────────────


def _render_vaststellingsovereenkomst(ctx: dict) -> str:
    """Vaststellingsovereenkomst / treffen van een regeling (Basenet L2).

    Placeholders `[VUL TOTAALBEDRAG IN]` en `[VUL TERMIJNEN IN]` worden
    door Lisanne handmatig overschreven in de contentEditable body vóór
    verzenden. Exact 6 genummerde clausules (Basenet-versie).
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        f"<p>Geachte heer, mevrouw {ctx['wederpartij']['naam']},</p>"
        f"<p>Inzake dossier {zn} heeft u in verband met uw "
        "openstaande schuld aangegeven een regeling te willen "
        "treffen. Een regeling wordt aangegaan onder voorbehoud "
        "van nadere acceptatie van cli&euml;nte, uw schuldeiser.</p>"
        "<p>In uw dossier is het mogelijk een regeling te treffen, "
        "onder de volgende voorwaarden. Om de regeling te "
        "effectueren dient u nog uw akkoord te geven in reply "
        "op deze e-mail.</p>"
        "<p><strong>Vaststellingsovereenkomst in de zin der wet"
        "</strong></p><ol>"
        "<li>Partijen stellen de vordering in onderhavig dossier "
        "op een bedrag van "
        '<mark style="background:#fef3c7;padding:2px 6px;">'
        "[VUL TOTAALBEDRAG VSO IN]</mark> inclusief rente en "
        "kosten.</li>"
        "<li>Schuldenaar zal bovengenoemd totaalbedrag voldoen "
        "door betaling in termijnen. De termijnen zijn als volgt, "
        "waarbij elke termijn uiterlijk op de vervaldatum moet "
        "zijn bijgeschreven:<br>"
        '<mark style="background:#fef3c7;padding:2px 6px;display:'
        'inline-block;margin-top:4px;">[VUL TERMIJNEN IN '
        "&mdash; bijv. &euro; 500 uiterlijk 1-5-2026; &euro; 500 "
        "uiterlijk 1-6-2026]</mark></li>"
        "<li>De betaling zal uitsluitend geschieden op IBAN: "
        "NL20 RABO 0388 5065 20 ten name van Stichting Beheer "
        f"Derdengelden Kesting Legal onder vermelding van het "
        f"kenmerk {zn}.</li>"
        "<li>Elke betaling strekt allereerst in mindering op de "
        "kosten, vervolgens de rente en aansluitend de hoofdsom.</li>"
        "<li>Indien de regeling niet stipt wordt nagekomen, "
        "vervalt de regeling in zijn geheel en is het restant "
        "zonder nadere ingebrekestelling geheel opeisbaar. In "
        "geval van verzuim geldt een contractuele rente van 2% "
        "per maand tot de dag der algehele voldoening.</li>"
        "<li>Behoudens effectuering van het bovenstaande verklaren "
        "partijen over en weer met betrekking tot onderhavige "
        "vordering niets meer van elkaar te vorderen te hebben en "
        "verlenen partijen elkaar over en weer finale kwijting. "
        "Deze overeenkomst is een vaststellingsovereenkomst in de "
        "zin van de wet. Partijen doen afstand van het recht deze "
        "overeenkomst te ontbinden of te vernietigen. Alleen "
        "nakoming kan worden gevorderd. Op de overeenkomst is "
        "Nederlands recht van toepassing.</li>"
        "</ol>"
        "<p><strong>Let op!</strong> Om deze betalingsregeling "
        "definitief te treffen dient u binnen 2 x 24 uur na heden "
        "schriftelijk uw akkoord te geven in reply op deze e-mail. "
        "Daarna is de regeling getroffen.</p>"
        "<p>Zonder uw schriftelijke bevestiging is er geen "
        "regeling getroffen.</p>"
    )
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            "<strong>Treffen van een regeling (aanbod "
            f"vaststellingsovereenkomst) / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Verzoekschrift faillissement (dreigbrief) ────────────────


def _render_faillissement_dreigbrief(ctx: dict) -> str:
    """Verzoekschrift faillissement dreigbrief (Basenet L7) — 2 dagen.

    Let op: het concept verzoekschrift moet Lisanne zelf als PDF-bijlage
    toevoegen via 'Uit sjablonen-bibliotheek' in de compose-dialog.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        f"<p>Geachte heer, mevrouw {ctx['wederpartij']['naam']},</p>"
        "<p>In onderhavige zaak heb ik u namens cli&euml;nte "
        "herhaaldelijk gesommeerd om tot betaling over te gaan. "
        "Tot op heden heeft u geen betaling verricht. Hierdoor "
        "bent u definitief in verzuim geraakt.</p>"
        "<p>Cli&euml;nte heeft mij uitdrukkelijk verzocht een "
        "verzoek tot faillietverklaring op te stellen en in te "
        "dienen bij de bevoegde rechtbank. <strong>Een kopie van "
        "het verzoekschrift treft u in de bijlage aan.</strong></p>"
    )
    body += _heading("Vordering")
    body += "<p>Het openstaande saldo is als volgt gespecificeerd:</p>"
    body += _vordering_table_basenet(ctx)
    body += (
        "<p><strong>Door u te betalen</strong></p>"
        f"<p>Hierbij sommeer ik u andermaal het bovengenoemd "
        f"totaalbedrag van {ctx['totaal_openstaand']} uiterlijk "
        "<strong>BINNEN 2 DAGEN NA HEDEN</strong> te hebben "
        "bijgeschreven op de derdengeldenrekening van mijn kantoor "
        "IBAN: NL20 RABO 0388 5065 20 ten name van Stichting "
        f"Beheer Derdengelden Kesting Legal onder vermelding van "
        f"het kenmerk {zn}.</p>"
        "<p>Let op: U dient bij betaling het juiste dossiernummer "
        "te vermelden zodat uw betaling correct kan worden "
        "gealloceerd.</p>"
        "<p><strong>Bij uitblijven van betaling</strong><br>"
        "Indien betaling wederom uitblijft, zal ik &mdash; zoals "
        "reeds aangekondigd &mdash; het verzoekschrift strekkende "
        "tot faillietverklaring indienen bij de rechtbank. De "
        "enige manier om indiening te voorkomen is door mij een "
        "betalingsbewijs toe te zenden.</p>"
    )
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            "<strong>VERZOEKSCHRIFT FAILLISSEMENT (LAATSTE "
            f"MOGELIJKHEID) / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Bevestiging betaling + sluiting dossier ──────────────────


def _render_bevestiging_sluiting(ctx: dict) -> str:
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        f"<p>Hierbij bevestig ik de ontvangst van uw betaling "
        f"inzake dossier {zn}.</p>"
        "<p>Met deze betaling is het openstaande saldo volledig "
        "voldaan. Het dossier wordt hiermee gesloten.</p>"
        "<p>Mocht u in de toekomst vragen hebben over deze zaak, "
        "dan kunt u contact opnemen onder vermelding van "
        "bovengenoemd dossiernummer.</p>"
    )
    return _render_branded(
        ctx,
        betreft=(
            "<strong>Bevestiging betaling en sluiting dossier / "
            f"{zn}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Public API ───────────────────────────────────────────────────────────

_RENDERERS: dict[str, callable] = {
    "aanmaning": _render_aanmaning,
    "sommatie": _render_sommatie,
    "tweede_sommatie": _render_tweede_sommatie,
    "14_dagenbrief": _render_14_dagenbrief,
    "herinnering": _render_herinnering,
    "reactie_9_3": _render_reactie_9_3,
    "reactie_20_4": _render_reactie_20_4,
    "schikkingsvoorstel": _render_schikkingsvoorstel,
    "engelse_sommatie": _render_engelse_sommatie,
    "reactie_ncnp_9_3": _render_reactie_ncnp_9_3,
    "reactie_verlengd_9_3": _render_reactie_verlengd_9_3,
    "vaststellingsovereenkomst": _render_vaststellingsovereenkomst,
    "faillissement_dreigbrief": _render_faillissement_dreigbrief,
    "bevestiging_sluiting": _render_bevestiging_sluiting,
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
