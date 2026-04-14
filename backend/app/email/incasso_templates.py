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
            f'<td style="padding:4px 6px;">{v.get("factuurdatum", v["verzuimdatum"])}</td>'
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


def _stuiting_blok(ctx: dict) -> str:
    """Stuiting vordering blok (art. 3:317 BW)."""
    return (
        "<p><strong>Stuiting vordering</strong><br>"
        "Ik stel u hierbij op de hoogte dat de vordering wordt gestuit "
        "conform artikel 3:317 BW. Het recht op nakoming wordt hiermee "
        "ondubbelzinnig voorbehouden.</p>"
    )


def _stuiting_blok_en(ctx: dict) -> str:
    """English interruption of claim (art. 3:317 Dutch Civil Code)."""
    return (
        "<p><strong>Interruption of the claim</strong><br>"
        "I hereby inform you that the claim is interrupted in "
        "accordance with Article 3:317 of the Dutch Civil Code. The "
        "right to performance is thereby unambiguously reserved.</p>"
    )


def _betaling_instructie_en(ctx: dict, days: int = 2) -> str:
    """English payment instruction — derdengelden IBAN + reference."""
    return (
        f"<p>I hereby demand that you transfer the total outstanding "
        f"amount of {ctx['totaal_openstaand']} <strong>WITHIN {days} "
        "DAYS FROM TODAY</strong> to the third-party account of my "
        "office:</p>"
        "<p>IBAN: NL20 RABO 0388 5065 20<br>"
        "Account holder: Stichting Beheer Derdengelden Kesting Legal<br>"
        f"Reference: {ctx['zaak']['zaaknummer']}</p>"
        "<p><strong>Important:</strong> You must include the correct "
        "case number when making the payment. Please note that only "
        "full payment via the specified method will halt the "
        "collection procedure.</p>"
    )


def _betalingsregeling_en_blok(ctx: dict) -> str:
    """English payment arrangement block."""
    return (
        "<p><strong>Payment arrangement</strong><br>"
        "If, at this stage of the collection process, you wish to "
        "propose a payment arrangement, please reply to this e-mail "
        "within the stated deadline. Please note: proposing a payment "
        "arrangement does not create any rights.</p>"
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
        "IBAN NL20 RABO 0388 5065 20 t.n.v. Stichting Beheer "
        "Derdengelden Kesting Legal, "
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
        "IBAN NL20 RABO 0388 5065 20 t.n.v. Stichting Beheer "
        "Derdengelden Kesting Legal, "
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
        "IBAN NL20 RABO 0388 5065 20 t.n.v. Stichting Beheer "
        "Derdengelden Kesting Legal, "
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

    Totaalbedrag = automatisch `totaal_openstaand` (default voor 95% van
    de VSO's — matcht het volledige openstaand saldo). Lisanne kan dit
    overschrijven in de compose-editor bij een gereduceerd onderhandeld
    bedrag.

    Placeholder `[VUL TERMIJNEN IN]` blijft handmatig — komt uit
    onderhandeling met debiteur, geen deterministische default.
    Exact 6 genummerde clausules (Basenet-versie).
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
        f"<li>Partijen stellen de vordering in onderhavig dossier "
        f"op een bedrag van <strong>{ctx['totaal_openstaand']}</strong> "
        "inclusief rente en kosten.</li>"
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


# ── Template: Sommatie na reactie debiteur (Basenet L1) ────────────────


def _render_sommatie_na_reactie(ctx: dict) -> str:
    """Sommatie na inhoudelijke reactie van debiteur (Basenet L1).

    Gebruikt nadat debiteur gereageerd heeft op een eerdere brief. Lisanne
    heeft de reactie met cliënte besproken en reageert terug met sommatie.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        f"<p>Eerder schreef ik u aan inzake de onbetaald gelaten "
        f"vordering van mijn cli&euml;nte {ctx['client']['naam']}. "
        "De vordering is aan mijn kantoor overgedragen ter incasso.</p>"
        "<p>U heeft gereageerd waarna ik uw reactie met cli&euml;nte "
        "heb besproken. Hieronder treft u mijn antwoord aan.</p>"
        "<p><strong>Sommatie</strong><br>"
        "De verplichting tot betaling staat dan ook vast. Ik sommeer "
        "u een laatste maal.</p>"
    )
    body += _heading("Vordering")
    body += (
        "<p>Thans bent u verschuldigd het openstaande saldo als volgt "
        "gespecificeerd:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += "<p><strong>Te betalen</strong></p>"
    body += _betaling_instructie(ctx, termijn="2 DAGEN")
    body += _betalingsregeling_blok(ctx)
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


# ── Template: Sommatie eerste opgave (Basenet L4) ──────────────────────


def _render_sommatie_eerste_opgave(ctx: dict) -> str:
    """Eerste opgave van de vordering na overdracht (Basenet L4).

    Gebruikt bij het eerste contactmoment, direct na overdracht van
    cliënt. Verwijst expliciet naar art. 6:44 BW bij deelbetalingen.
    Termijn: per omgaand.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        f"<p>Hierbij doe ik u een opgave van de vordering die "
        f"cli&euml;nte {ctx['client']['naam']} ter incasso uit handen "
        "heeft gegeven aan mijn kantoor. De (gehele) vordering is nog "
        "niet voldaan. Indien er deelbetalingen zijn gedaan, dan zijn "
        "deze betalingen ex art. 6:44 BW afgeboekt.</p>"
        "<p>De vordering bedraagt thans:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += (
        "<p>Het restant verschuldigde dient <strong>per omgaand</strong> "
        "bijgeschreven te zijn op de derdengeldenrekening van mijn "
        "kantoor IBAN: NL20 RABO 0388 5065 20 t.n.v. Stichting Beheer "
        f"Derdengelden Kesting Legal onder vermelding van het kenmerk "
        f"{zn}.</p>"
        "<p>Een betaalbewijs zie ik wel per omgaand tegemoet.</p>"
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


# ── Template: Niet voldaan aan regeling — sommatie (Basenet L5) ────────


def _render_niet_voldaan_regeling(ctx: dict) -> str:
    """Sommatie na breuk vaststellingsovereenkomst (Basenet L5).

    Debiteur heeft eerder een regeling getroffen maar komt deze niet na
    → opeising volledig saldo met 2-dagen termijn.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Inzake het bovengenoemde dossier heb ik eerder een "
        "vaststellingsovereenkomst met u vastgelegd.</p>"
        "<p><strong>Opeising saldo</strong><br>"
        "U heeft zich niet gehouden aan de gemaakte afspraken, "
        "waardoor &mdash; conform de bepalingen van de overeenkomst "
        "&mdash; verzuim is ingetreden zonder dat daarvoor een "
        "ingebrekestelling noodzakelijk is. Hierbij eis ik het "
        "volledige verschuldigde bedrag bij u op. Het openstaande "
        f"saldo bedraagt tot op heden {ctx['totaal_openstaand']}.</p>"
        "<p><strong>Sommatie</strong><br>"
        f"Ik sommeer u hierbij om het totaalbedrag van "
        f"{ctx['totaal_openstaand']} <strong>BINNEN 2 DAGEN NA "
        "HEDEN</strong> over te maken naar IBAN: NL20 RABO 0388 5065 "
        "20 ten name van Stichting Beheer Derdengelden Kesting Legal "
        f"onder vermelding van het kenmerk {zn}.</p>"
        "<p><strong>Aanzegging rechtsmaatregelen</strong><br>"
        "Indien betaling van het bovengenoemde bedrag uitblijft, "
        "behoud ik mij het recht voor om zonder nadere aankondiging "
        "rechtsmaatregelen tegen u te treffen. De kosten die hiermee "
        "gemoeid zijn, zullen op u worden verhaald.</p>"
        "<p>Ik vertrouw erop dat u tijdig aan uw verplichtingen "
        "voldoet.</p>"
    )
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            "<strong>NIET VOLDAAN AAN REGELING - SOMMATIE TOT "
            f"BETALING / {zn} / {ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Sommatie laatste mogelijkheid vóór faillissement (L8) ────


def _render_sommatie_laatste_voor_fai(ctx: dict) -> str:
    """Laatste sommatie vóór indiening faillissement (Basenet L8).

    Verzoekschrift is al in voorbereiding. 2 dagen termijn. Géén
    concept-verzoekschrift bijlage — die volgt in faillissement_dreigbrief.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Eerder heb ik u aangeschreven betreffende de openstaande "
        "vordering van mijn cli&euml;nt. Deze vordering is ter incasso "
        "aan mijn kantoor overgedragen.</p>"
        "<p>Ondanks meerdere sommaties heeft u nog niet (geheel) aan "
        "uw betalingsverplichting voldaan. Zoals reeds aangegeven heb "
        "ik wegens het uitblijven van betaling, cli&euml;nte "
        "geadviseerd uw faillissement aan te vragen.</p>"
        "<p>Met het opstellen van het verzoekschrift ben ik reeds "
        "begonnen. Zodra het verzoekschrift is opgesteld en ingediend, "
        "is de faillissementsprocedure aanhangig.</p>"
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
        "IBAN: NL20 RABO 0388 5065 20 ten name van Stichting Beheer "
        "Derdengelden Kesting Legal onder vermelding van het kenmerk "
        f"{zn}.</p>"
        "<p>Let op: U dient bij betaling het juiste dossiernummer te "
        "vermelden. Ik wijs u erop dat alleen betaling van het "
        "volledige bedrag op de hiervoor aangegeven wijze ervoor "
        "zorgt dat de incassoprocedure wordt gestopt.</p>"
        "<p><strong>Bij uitblijven van betaling</strong><br>"
        "Indien betaling wederom uitblijft, zal ik &mdash; zoals "
        "reeds aangekondigd &mdash; het verzoekschrift strekkende "
        "tot faillietverklaring indienen bij de rechtbank. Voor "
        "alle door cli&euml;nt geleden en nog te lijden schade, "
        "waaronder begrepen de proces- en advocaatkosten, houd ik "
        "u reeds aansprakelijk.</p>"
    )
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            "<strong>SOMMATIE TOT BETALING (LAATSTE MOGELIJKHEID) "
            f"/ {zn} / {ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Wederom sommatie — inhoudelijk verweer (Basenet L11) ─────


def _render_wederom_sommatie_inhoudelijk(ctx: dict) -> str:
    """Wederom sommatie met inhoudelijke reactie op verweer (Basenet L11).

    Placeholder `[HIER INHOUDELIJKE REACTIE OP VERWEER INVULLEN]` wordt
    door Lisanne handmatig overschreven in de contentEditable body vóór
    verzenden. Bevat stuitingsblok (art. 3:317 BW).
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Eerder heb ik u aangeschreven betreffende de openstaande "
        "vordering van mijn cli&euml;nt. Deze vordering is ter incasso "
        "aan mijn kantoor overgedragen. Tot op heden heeft u nog niet "
        "(geheel) aan uw betalingsverplichting voldaan.</p>"
        "<p>Hierbij voorzie ik u van een inhoudelijke reactie, waarin "
        "ik uw stellingen weerleg.</p>"
        '<p><mark style="background:#fef3c7;padding:4px 8px;'
        'display:inline-block;">[HIER INHOUDELIJKE REACTIE OP '
        "VERWEER INVULLEN]</mark></p>"
        "<p>Indien ondanks deze correspondentie betaling uitblijft, "
        "ben ik genoodzaakt het incassotraject voort te zetten.</p>"
    )
    body += _heading("Vordering")
    body += "<p>Het openstaande saldo is als volgt gespecificeerd:</p>"
    body += _vordering_table_basenet(ctx)
    body += (
        "<p><strong>Laatste sommatie</strong><br>"
        f"Hierbij sommeer ik u andermaal het bovengenoemd totaalbedrag "
        f"van {ctx['totaal_openstaand']} uiterlijk binnen een termijn "
        "van <strong>3 dagen na heden</strong> te hebben bijgeschreven "
        "op de derdengeldenrekening van mijn kantoor IBAN: NL20 RABO "
        "0388 5065 20 t.n.v. Stichting Beheer Derdengelden Kesting "
        f"Legal onder vermelding van het kenmerk {zn}.</p>"
        "<p>Let op: U dient bij betaling het juiste dossiernummer te "
        "vermelden. Ik wijs u erop dat alleen betaling van het "
        "volledige bedrag op de hiervoor aangegeven wijze ervoor "
        "zorgt dat de incassoprocedure wordt gestopt.</p>"
        "<p><strong>Bij uitblijven van betaling</strong><br>"
        "Indien betaling wederom uitblijft, zal ik mijn cli&euml;nte "
        "moeten adviseren om uw faillissement aan te vragen. "
        "Daarnaast houd ik u namens cli&euml;nte aansprakelijk voor "
        "alle reeds geleden en nog te lijden schade, waaronder "
        "begrepen &mdash; maar niet uitsluitend &mdash; proces- en "
        "advocaatkosten.</p>"
    )
    body += _stuiting_blok(ctx)
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            "<strong>WEDEROM SOMMATIE TOT BETALING / "
            f"{zn} / {ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Wederom sommatie — kort (Basenet L12) ────────────────────


def _render_wederom_sommatie_kort(ctx: dict) -> str:
    """Wederom sommatie zonder inhoudelijke reactie (Basenet L12).

    Korte variant zonder verweer-blok. 3 dagen + stuiting.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Eerder heb ik u aangeschreven betreffende de openstaande "
        "vordering van mijn cli&euml;nt. Deze vordering is ter incasso "
        "aan mijn kantoor overgedragen. Tot op heden heeft u nog niet "
        "(geheel) aan uw betalingsverplichting voldaan. Hierdoor ben "
        "ik genoodzaakt het incassotraject voort te zetten.</p>"
    )
    body += _heading("Vordering")
    body += "<p>Het openstaande saldo is als volgt gespecificeerd:</p>"
    body += _vordering_table_basenet(ctx)
    body += (
        "<p><strong>Laatste sommatie</strong><br>"
        f"Hierbij sommeer ik u andermaal het bovengenoemd totaalbedrag "
        f"van {ctx['totaal_openstaand']} uiterlijk binnen een termijn "
        "van <strong>3 dagen na heden</strong> te hebben bijgeschreven "
        "op de derdengeldenrekening van mijn kantoor IBAN: NL20 RABO "
        "0388 5065 20 t.n.v. Stichting Beheer Derdengelden Kesting "
        f"Legal onder vermelding van het kenmerk {zn} in de "
        "onderwerpregel.</p>"
        "<p>Let op: U dient bij betaling het juiste dossiernummer te "
        "vermelden. Ik wijs u erop dat alleen betaling van het "
        "volledige bedrag op de hiervoor aangegeven wijze ervoor "
        "zorgt dat de incassoprocedure wordt gestopt.</p>"
        "<p><strong>Bij uitblijven van betaling</strong><br>"
        "Indien betaling wederom uitblijft, zal ik mijn cli&euml;nte "
        "moeten adviseren om uw faillissement aan te vragen. "
        "Daarnaast houd ik u namens cli&euml;nte aansprakelijk voor "
        "alle reeds geleden en nog te lijden schade, waaronder "
        "begrepen &mdash; maar niet uitsluitend &mdash; proces- en "
        "advocaatkosten.</p>"
    )
    body += _stuiting_blok(ctx)
    body += _schuldhulp_disclaimer(ctx)
    return _render_branded(
        ctx,
        betreft=(
            "<strong>WEDEROM SOMMATIE TOT BETALING / "
            f"{zn} / {ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx),
    )


# ── Template: Sommatie met drukte-notitie (Basenet L15) ────────────────


def _render_sommatie_drukte(ctx: dict) -> str:
    """Eerste sommatie met 'drukte in praktijk' notitie (Basenet L15).

    Zelfde basis als `_render_sommatie` (L13) + extra alinea over
    email-contact en drukte.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Geachte heer, mevrouw,</p>"
        "<p>Cli&euml;nt heeft mij verzocht om onderstaande openstaande "
        "vordering bij u te incasseren. Deze vordering is ter verdere "
        "afwikkeling aan mijn kantoor overgedragen.</p>"
        "<p>Cli&euml;nt hanteert Algemene Voorwaarden, welke van "
        "toepassing zijn op alle transacties. Primair op grond van "
        "die voorwaarden en subsidiair op grond van de van toepassing "
        "zijnde wettelijke bepalingen verhaal ik onderstaand bedrag "
        "op u.</p>"
        "<p>Thans bent u het volgende verschuldigd:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += (
        "<p><strong>Sommatie tot betaling</strong></p>"
        f"<p>Ik sommeer u hierbij om het openstaande bedrag van "
        f"<strong>{ctx['totaal_openstaand']}</strong> "
        "<strong>BINNEN 3 DAGEN NA HEDEN</strong> bij te schrijven "
        "op de derdengeldenrekening van mijn kantoor IBAN NL20 RABO "
        "0388 5065 20 ten name van Stichting Beheer Derdengelden "
        f"Kesting Legal onder vermelding van het kenmerk {zn}.</p>"
        "<p>Ik wijs u erop dat alleen betaling van het volledige "
        "bedrag op de hiervoor aangegeven wijze ervoor zorgt dat de "
        "incassoprocedure wordt gestopt. Blijft betaling uit binnen "
        "de gestelde termijn, dan heeft cli&euml;nt mij reeds "
        "verzocht alle rechtsmaatregelen tegen u te nemen die nodig "
        "worden geacht. De kosten die hiermee gepaard gaan, zullen "
        "op u worden verhaald.</p>"
        "<p>Vanwege drukte in mijn praktijk vraag ik u om per e-mail "
        "contact met mij op te nemen als u vragen heeft. Dat kan via "
        "<a href=\"mailto:incasso@kestinglegal.nl\">"
        "incasso@kestinglegal.nl</a> onder vermelding van uw "
        "dossiernummer in de onderwerpregel.</p>"
        "<p>Ik vertrouw erop dat u de ernst van de situatie inziet "
        "en tijdig tot betaling overgaat.</p>"
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


# ── Template: English — first demand for payment (Basenet L14) ────────


def _render_demand_for_payment_eerste(ctx: dict) -> str:
    """English first demand for payment (Basenet L14).

    Eerste sommatie in Engels, kort formaat, 3 dagen termijn. Voor
    internationale debiteuren bij eerste contact.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Dear sir/madam,</p>"
        f"<p>My client has requested me to collect the outstanding "
        f"claim listed below from {ctx['wederpartij']['naam']}. This "
        "claim has been transferred to my office for further "
        "processing.</p>"
        "<p>You currently owe the following amount:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += "<p><strong>Demand for payment</strong></p>"
    body += _betaling_instructie_en(ctx, days=3)
    body += (
        "<p>Please be advised that only full payment via the "
        "specified method will ensure that the collection procedure "
        "is halted. Should you fail to make payment within the given "
        "deadline, my client has already instructed me to take all "
        "necessary legal measures against you. Any costs incurred in "
        "this process will be recovered from you.</p>"
        "<p>I trust you acknowledge the seriousness of this matter "
        "and will proceed with payment in a timely manner.</p>"
    )
    return _render_branded(
        ctx,
        betreft=(
            f"<strong>DEMAND FOR PAYMENT / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx, english=True),
    )


# ── Template: English — demand with interruption + arrangement (L10) ──


def _render_demand_for_payment_uitgebreid(ctx: dict) -> str:
    """English demand with interruption + payment arrangement (Basenet L10).

    Uitgebreide variant: 3 dagen termijn, stuiting art. 3:317 BW, en
    payment arrangement blok. Voor situaties waar interruption of the
    statute of limitations nodig is.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Dear sir/madam,</p>"
        f"<p>Previously, I contacted you regarding my client's "
        f"outstanding claim against {ctx['wederpartij']['naam']}. This "
        "claim has been transferred to my office for collection. To "
        "date, you have not yet fully complied with your payment "
        "obligation. As a result, I am compelled to continue the "
        "collection process.</p>"
        "<p>The outstanding balance is specified as follows:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += "<p><strong>Demand for payment</strong></p>"
    body += _betaling_instructie_en(ctx, days=3)
    body += (
        "<p><strong>Consequences of non-payment</strong><br>"
        "If payment remains outstanding, I will have to advise my "
        "client to initiate bankruptcy proceedings against you. "
        "Additionally, on behalf of my client, I hold you liable for "
        "all damages incurred and to be incurred, including &mdash; "
        "but not limited to &mdash; legal and attorney fees.</p>"
    )
    body += _stuiting_blok_en(ctx)
    body += _betalingsregeling_en_blok(ctx)
    return _render_branded(
        ctx,
        betreft=(
            f"<strong>DEMAND FOR PAYMENT / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx, english=True),
    )


# ── Template: English — last chance (bankruptcy pending) (L9) ─────────


def _render_demand_for_payment_laatste(ctx: dict) -> str:
    """English last chance demand — bankruptcy petition pending (L9).

    2 dagen termijn. Verzoekschrift is al in voorbereiding.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Dear sir/madam,</p>"
        "<p>Previously, I contacted you regarding my client's "
        "outstanding claim. This claim has been transferred to my "
        "office for collection.</p>"
        "<p>Despite multiple reminders, you have not yet fully "
        "complied with your payment obligation. As previously stated, "
        "due to non-payment, I have advised my client to file for "
        "your bankruptcy.</p>"
        "<p>I have already begun drafting the petition. Once the "
        "petition is finalized and submitted, the bankruptcy "
        "proceedings will be initiated.</p>"
        "<p>The outstanding balance is specified as follows:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += "<p><strong>Amount to be paid</strong></p>"
    body += _betaling_instructie_en(ctx, days=2)
    body += (
        "<p><strong>Consequences of non-payment</strong><br>"
        "If payment remains outstanding, I will &mdash; as previously "
        "announced &mdash; proceed with filing the bankruptcy "
        "petition with the court. You have already been held liable "
        "for all damages incurred and yet to be incurred by my "
        "client, including legal and attorney fees.</p>"
        "<p>I trust that you recognize the seriousness of the "
        "situation and will proceed with timely payment.</p>"
    )
    return _render_branded(
        ctx,
        betreft=(
            f"<strong>DEMAND FOR PAYMENT / {zn} / "
            f"{ctx['wederpartij']['naam']}</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx, english=True),
    )


# ── Template: English — bankruptcy petition attached (L6) ─────────────


def _render_demand_for_payment_fai(ctx: dict) -> str:
    """English demand with bankruptcy petition attached (Basenet L6).

    Zelfde moment als `faillissement_dreigbrief` maar in Engels. 2 dagen
    termijn. Concept verzoekschrift PDF moet handmatig als bijlage
    toegevoegd worden via 'Uit sjablonen-bibliotheek'.
    """
    zn = ctx["zaak"]["zaaknummer"]
    body = (
        "<p>Dear sir/madam,</p>"
        "<p>In this matter, I have repeatedly and formally demanded "
        "payment on behalf of my client. To date, you have neither "
        "made payment nor provided a substantive response. You are "
        "therefore in default.</p>"
        "<p>My client has expressly instructed me to prepare and "
        "file a petition for bankruptcy with the competent court. "
        "<strong>A copy of the petition is attached.</strong></p>"
        "<p><strong>Claim</strong></p>"
        "<p>The outstanding balance is specified as follows:</p>"
    )
    body += _vordering_table_basenet(ctx)
    body += "<p><strong>Amount to be paid</strong></p>"
    body += _betaling_instructie_en(ctx, days=2)
    body += (
        "<p><strong>Consequences of non-payment</strong><br>"
        "If payment remains outstanding, I will &mdash; as previously "
        "announced &mdash; proceed with filing the bankruptcy "
        "petition with the court. You have already been held liable "
        "for all damages incurred and yet to be incurred by my "
        "client, including legal and attorney fees.</p>"
        "<p>I trust that you recognize the seriousness of the "
        "situation and will proceed with timely payment.</p>"
    )
    return _render_branded(
        ctx,
        betreft=(
            f"<strong>DEMAND FOR PAYMENT / {zn} / "
            f"{ctx['wederpartij']['naam']} / BANKRUPTCY</strong>"
        ),
        content_html=body,
        afsluiting_html=_signature(ctx, english=True),
    )


# ── Public API ───────────────────────────────────────────────────────────

_RENDERERS: dict[str, callable] = {
    "aanmaning": _render_aanmaning,
    "sommatie": _render_sommatie,
    "sommatie_na_reactie": _render_sommatie_na_reactie,
    "sommatie_eerste_opgave": _render_sommatie_eerste_opgave,
    "sommatie_drukte": _render_sommatie_drukte,
    "tweede_sommatie": _render_tweede_sommatie,
    "14_dagenbrief": _render_14_dagenbrief,
    "herinnering": _render_herinnering,
    "niet_voldaan_regeling": _render_niet_voldaan_regeling,
    "wederom_sommatie_inhoudelijk": _render_wederom_sommatie_inhoudelijk,
    "wederom_sommatie_kort": _render_wederom_sommatie_kort,
    "sommatie_laatste_voor_fai": _render_sommatie_laatste_voor_fai,
    "reactie_9_3": _render_reactie_9_3,
    "reactie_20_4": _render_reactie_20_4,
    "schikkingsvoorstel": _render_schikkingsvoorstel,
    "engelse_sommatie": _render_engelse_sommatie,
    "demand_for_payment_eerste": _render_demand_for_payment_eerste,
    "demand_for_payment_uitgebreid": _render_demand_for_payment_uitgebreid,
    "demand_for_payment_laatste": _render_demand_for_payment_laatste,
    "demand_for_payment_fai": _render_demand_for_payment_fai,
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
