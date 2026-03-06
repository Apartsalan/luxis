"""Email templates — Jinja2 HTML templates for transactional emails.

Each template function returns (subject, html_body) for use with email.service.send_email.
Templates are defined as Jinja2 strings rendered with case/document context.
"""

from jinja2 import Environment, StrictUndefined
from markupsafe import Markup

_env = Environment(undefined=StrictUndefined, autoescape=True)

# ── Base HTML wrapper ─────────────────────────────────────────────────────

_BASE_HTML = """\
<!DOCTYPE html>
<html lang="nl">
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #1a1a1a; \
line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 24px;">
    <strong style="font-size: 18px;">{{ kantoor_naam }}</strong>
  </div>
  {{ content }}
  <div style="border-top: 1px solid #e5e7eb; margin-top: 32px; padding-top: 12px; \
font-size: 12px; color: #6b7280;">
    <p>{{ kantoor_naam }}{% if kantoor_adres %} &middot; {{ kantoor_adres }}{% endif %}\
{% if kantoor_postcode_stad %} &middot; {{ kantoor_postcode_stad }}{% endif %}</p>
    <p>Dit bericht is automatisch verzonden. Antwoord niet op deze e-mail.</p>
  </div>
</body>
</html>"""

_base_tpl = _env.from_string(_BASE_HTML)


def _render_base(kantoor: dict, content_html: str) -> str:
    """Wrap content in the base email layout."""
    return _base_tpl.render(
        kantoor_naam=kantoor.get("naam", ""),
        kantoor_adres=kantoor.get("adres", ""),
        kantoor_postcode_stad=kantoor.get("postcode_stad", ""),
        content=Markup(content_html),
    )


# ── Template: document verzonden ──────────────────────────────────────────

_DOCUMENT_SENT_CONTENT = """\
<p>Geachte {{ aanhef }},</p>
<p>Bijgaand treft u het document <strong>{{ document_titel }}</strong> aan \
inzake zaak {{ zaaknummer }}.</p>
<p>Het document is als bijlage bij deze e-mail gevoegd.</p>
<p>Met vriendelijke groet,<br>{{ kantoor_naam }}</p>"""

_doc_sent_tpl = _env.from_string(_DOCUMENT_SENT_CONTENT)


def document_sent(
    *,
    kantoor: dict,
    recipient_name: str,
    document_title: str,
    case_number: str,
) -> tuple[str, str]:
    """Email template for sending a document (aanmaning, sommatie, etc.).

    Returns:
        (subject, html_body)
    """
    subject = f"{document_title} — {case_number}"
    content = _doc_sent_tpl.render(
        aanhef=recipient_name or "heer/mevrouw",
        document_titel=document_title,
        zaaknummer=case_number,
        kantoor_naam=kantoor.get("naam", ""),
    )
    html_body = _render_base(kantoor, content)
    return subject, html_body


# ── Template: deadline herinnering ────────────────────────────────────────

_DEADLINE_REMINDER_CONTENT = """\
<p>Geachte {{ aanhef }},</p>
<p>Hierbij herinneren wij u aan de openstaande termijn voor zaak \
<strong>{{ zaaknummer }}</strong>.</p>
<p>De deadline van <strong>{{ deadline }}</strong> nadert. \
Wij verzoeken u vriendelijk om tijdig actie te ondernemen.</p>
<p>Met vriendelijke groet,<br>{{ kantoor_naam }}</p>"""

_deadline_tpl = _env.from_string(_DEADLINE_REMINDER_CONTENT)


def deadline_reminder(
    *,
    kantoor: dict,
    recipient_name: str,
    case_number: str,
    deadline: str,
) -> tuple[str, str]:
    """Email template for a deadline reminder.

    Returns:
        (subject, html_body)
    """
    subject = f"Herinnering deadline — {case_number}"
    content = _deadline_tpl.render(
        aanhef=recipient_name or "heer/mevrouw",
        zaaknummer=case_number,
        deadline=deadline,
        kantoor_naam=kantoor.get("naam", ""),
    )
    html_body = _render_base(kantoor, content)
    return subject, html_body


# ── Template: betalingsbevestiging ────────────────────────────────────────

_PAYMENT_CONFIRMATION_CONTENT = """\
<p>Geachte {{ aanhef }},</p>
<p>Wij bevestigen de ontvangst van uw betaling van <strong>{{ bedrag }}</strong> \
voor zaak <strong>{{ zaaknummer }}</strong>.</p>
{% if restant %}
<p>Het resterende openstaande bedrag is <strong>{{ restant }}</strong>.</p>
{% else %}
<p>Hiermee is het volledige bedrag voldaan.</p>
{% endif %}
<p>Met vriendelijke groet,<br>{{ kantoor_naam }}</p>"""

_payment_tpl = _env.from_string(_PAYMENT_CONFIRMATION_CONTENT)


def payment_confirmation(
    *,
    kantoor: dict,
    recipient_name: str,
    case_number: str,
    amount: str,
    remaining: str | None = None,
) -> tuple[str, str]:
    """Email template for a payment confirmation.

    Returns:
        (subject, html_body)
    """
    subject = f"Betalingsbevestiging — {case_number}"
    content = _payment_tpl.render(
        aanhef=recipient_name or "heer/mevrouw",
        zaaknummer=case_number,
        bedrag=amount,
        restant=remaining,
        kantoor_naam=kantoor.get("naam", ""),
    )
    html_body = _render_base(kantoor, content)
    return subject, html_body


# ── Template: status wijziging ────────────────────────────────────────────

_STATUS_CHANGE_CONTENT = """\
<p>Geachte {{ aanhef }},</p>
<p>De status van zaak <strong>{{ zaaknummer }}</strong> is gewijzigd \
van <em>{{ oude_status }}</em> naar <em>{{ nieuwe_status }}</em>.</p>
{% if toelichting %}
<p>{{ toelichting }}</p>
{% endif %}
<p>Met vriendelijke groet,<br>{{ kantoor_naam }}</p>"""

_status_tpl = _env.from_string(_STATUS_CHANGE_CONTENT)


def status_change(
    *,
    kantoor: dict,
    recipient_name: str,
    case_number: str,
    old_status: str,
    new_status: str,
    note: str | None = None,
) -> tuple[str, str]:
    """Email template for a case status change notification.

    Returns:
        (subject, html_body)
    """
    subject = f"Statuswijziging — {case_number}"
    content = _status_tpl.render(
        aanhef=recipient_name or "heer/mevrouw",
        zaaknummer=case_number,
        oude_status=old_status,
        nieuwe_status=new_status,
        toelichting=note,
        kantoor_naam=kantoor.get("naam", ""),
    )
    html_body = _render_base(kantoor, content)
    return subject, html_body
