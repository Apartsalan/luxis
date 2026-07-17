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
<p>Geachte heer, mevrouw,</p>
<p>Bijgaand treft u het document <strong>{{ document_titel }}</strong> aan \
inzake zaak {{ zaaknummer }}.</p>
<p>Het document is als bijlage bij deze e-mail gevoegd.</p>"""

_doc_sent_tpl = _env.from_string(_DOCUMENT_SENT_CONTENT)


def document_sent_paragraphs(document_title: str, case_number: str) -> str:
    """Kale alinea's voor de document-verzendmail (S226-review).

    Bewust GEEN eigen wrapper, aanhef-op-naam of slotgroet meer: de verzendlaag
    (`ensure_branded_body`, afspraak S186) kleedt dit aan met de volledige
    huisstijl — Betreft-regel, witregels, handtekening + logo, schuldhulpblok.
    Aanhef = S220-lijn "Geachte heer, mevrouw,".
    """
    return _doc_sent_tpl.render(
        document_titel=document_title,
        zaaknummer=case_number,
    )
