"""Generate .docx templates for the incasso document generation module.

Run once to create template files:
    python templates/_generate_templates.py

Uses docxtpl Jinja2 syntax:
  {{ variable }}           — simple substitution
  {%tr for x in list %}    — table row loop (start of row)
  {%tr endfor %}           — end of table row loop (own row, removed after render)
"""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

TEMPLATES_DIR = Path(__file__).parent


def _hdr(cell, text):
    """Style a table header cell."""
    p = cell.paragraphs[0]
    p.text = ""
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(10)


def _cel(cell, text, bold=False, right=False):
    """Style a table data cell."""
    p = cell.paragraphs[0]
    p.text = ""
    if right:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Calibri"
    r.font.size = Pt(10)


def _p(doc, text, bold=False, size=Pt(11), color=None):
    """Add a styled paragraph."""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Calibri"
    r.font.size = size
    if color:
        r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(4)
    return p


def _margins(doc):
    for s in doc.sections:
        s.top_margin = Cm(2.5)
        s.bottom_margin = Cm(2)
        s.left_margin = Cm(2.5)
        s.right_margin = Cm(2.5)


def _add_claims_table(doc):
    """Add a claims table with {%tr %} row loop.

    docxtpl replaces the ENTIRE <w:tr> containing {%tr} with just the Jinja2
    directive. So {%tr for %} and {%tr endfor %} must each be in their OWN
    row, separate from the data row.

    Structure:
      Row 0: Header (Omschrijving, Factuurnummer, Verzuimdatum, Hoofdsom)
      Row 1: {%tr for v in vorderingen %} — tag-only row, removed by docxtpl
      Row 2: Data row ({{ v.beschrijving }}, {{ v.factuurnummer }}, etc.)
      Row 3: {%tr endfor %} — tag-only row, removed by docxtpl
    """
    t = doc.add_table(rows=4, cols=4)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, h in enumerate(["Omschrijving", "Factuurnummer", "Verzuimdatum", "Hoofdsom"]):
        _hdr(t.rows[0].cells[i], h)

    # For-loop opening tag (own row — gets replaced by {% for %} directive)
    t.rows[1].cells[0].text = "{%tr for v in vorderingen %}"

    # Data row (loop body — this row gets repeated for each item)
    r2 = t.rows[2]
    _cel(r2.cells[0], "{{ v.beschrijving }}")
    _cel(r2.cells[1], "{{ v.factuurnummer }}")
    _cel(r2.cells[2], "{{ v.verzuimdatum }}")
    _cel(r2.cells[3], "{{ v.hoofdsom }}", right=True)

    # End-loop tag (own row — gets replaced by {% endfor %} directive)
    t.rows[3].cells[0].text = "{%tr endfor %}"

    return t


def _add_summary_2col(doc, rows_data):
    """Add a 2-column summary table with label/value pairs."""
    t = doc.add_table(rows=len(rows_data), cols=2)
    t.style = "Table Grid"
    for i, (label, value, bold) in enumerate(rows_data):
        _cel(t.rows[i].cells[0], label, bold=bold)
        _cel(t.rows[i].cells[1], value, bold=bold, right=True)
    return t


# ═══════════════════════════════════════════════════════════════════════════════
# 14-DAGENBRIEF (art. 6:96 lid 6 BW)
# ═══════════════════════════════════════════════════════════════════════════════


def create_14_dagenbrief():
    doc = Document()
    _margins(doc)

    # Sender
    _p(doc, "{{ client.naam }}", bold=True)
    _p(doc, "{{ client.adres }}")
    _p(doc, "{{ client.postcode_stad }}")
    _p(doc, "")

    # Recipient
    _p(doc, "{{ wederpartij.naam }}", bold=True)
    _p(doc, "{{ wederpartij.adres }}")
    _p(doc, "{{ wederpartij.postcode_stad }}")
    _p(doc, "")

    _p(doc, "{{ vandaag }}")
    _p(doc, "")

    _p(doc, "Betreft: Ingebrekestelling en aanmaning tot betaling", bold=True)
    _p(doc, "Ons kenmerk: {{ zaak.zaaknummer }}")
    _p(doc, "{{ zaak.referentie_regel }}")
    _p(doc, "")

    _p(doc, "Geachte heer/mevrouw,")
    _p(doc, "")
    _p(doc,
        "Namens onze cli\u00ebnt, {{ client.naam }}, sommeer ik u hierbij tot betaling "
        "van het hieronder gespecificeerde bedrag. Ondanks eerdere verzoeken is betaling "
        "tot op heden uitgebleven.")

    doc.add_heading("Specificatie vordering(en)", level=2)
    _add_claims_table(doc)
    _p(doc, "")

    _add_summary_2col(doc, [
        ("Totaal hoofdsom", "{{ totaal_hoofdsom }}", True),
        ("Wettelijke rente t/m {{ vandaag }}", "{{ totaal_rente }}", False),
        ("Buitengerechtelijke incassokosten (BIK)", "{{ bik_bedrag }}", False),
        ("{{ btw_regel_label }}", "{{ btw_regel_bedrag }}", False),
        ("Totaal verschuldigd", "{{ totaal_verschuldigd }}", True),
    ])
    _p(doc, "")

    doc.add_heading("Wettelijke mededeling (art. 6:96 lid 6 BW)", level=2)
    _p(doc,
        "Hierbij wordt u gesommeerd het verschuldigde bedrag van "
        "{{ totaal_hoofdsom }} "
        "binnen veertien dagen na ontvangst van deze brief te voldoen "
        "op het rekeningnummer van onze cli\u00ebnt.")
    _p(doc,
        "Indien betaling binnen deze termijn uitblijft, bent u naast de hoofdsom "
        "tevens de buitengerechtelijke incassokosten verschuldigd ter hoogte van "
        "{{ bik_bedrag }}{{ btw_toelichting }}, "
        "alsmede de wettelijke rente vanaf de verzuimdatum.")
    _p(doc, "")
    _p(doc,
        "Ik verzoek u het totaal verschuldigde bedrag van "
        "{{ totaal_verschuldigd }} "
        "binnen veertien dagen na dagtekening van deze brief over te maken.")
    _p(doc,
        "Bij gebreke van tijdige betaling zullen wij zonder nadere aankondiging "
        "rechtsmaatregelen treffen, waarvan de kosten eveneens voor uw rekening komen.")
    _p(doc, "")
    _p(doc, "Hoogachtend,")
    _p(doc, "")
    _p(doc, "________________________")
    _p(doc, "Namens {{ client.naam }}")
    _p(doc, "")
    _p(doc, "Zaaknummer: {{ zaak.zaaknummer }} | Datum: {{ vandaag }}",
       size=Pt(9), color=RGBColor(0x88, 0x88, 0x88))

    doc.save(str(TEMPLATES_DIR / "14_dagenbrief.docx"))
    print("  14_dagenbrief.docx")


# ═══════════════════════════════════════════════════════════════════════════════
# SOMMATIE
# ═══════════════════════════════════════════════════════════════════════════════


def create_sommatie():
    doc = Document()
    _margins(doc)

    _p(doc, "{{ client.naam }}", bold=True)
    _p(doc, "{{ client.adres }}")
    _p(doc, "{{ client.postcode_stad }}")
    _p(doc, "")

    _p(doc, "AANGETEKEND", bold=True, size=Pt(12))
    _p(doc, "")
    _p(doc, "{{ wederpartij.naam }}", bold=True)
    _p(doc, "{{ wederpartij.adres }}")
    _p(doc, "{{ wederpartij.postcode_stad }}")
    _p(doc, "")

    _p(doc, "{{ vandaag }}")
    _p(doc, "")

    _p(doc, "Betreft: SOMMATIE \u2014 Laatste aanmaning voor dagvaarding", bold=True)
    _p(doc, "Ons kenmerk: {{ zaak.zaaknummer }}")
    _p(doc, "{{ zaak.referentie_regel }}")
    _p(doc, "")

    _p(doc, "Geachte heer/mevrouw,")
    _p(doc, "")
    _p(doc,
        "Tot mij heeft zich gewend {{ client.naam }} met het verzoek u te sommeren "
        "tot betaling van het hierna te noemen bedrag. Tot op heden is betaling, "
        "ondanks eerdere aanmaningen, uitgebleven.")

    doc.add_heading("Specificatie vordering", level=2)
    _add_claims_table(doc)
    _p(doc, "")

    _add_summary_2col(doc, [
        ("Hoofdsom", "{{ totaal_hoofdsom }}", True),
        ("Wettelijke rente t/m {{ vandaag }}", "{{ totaal_rente }}", False),
        ("Buitengerechtelijke incassokosten", "{{ bik_bedrag }}", False),
        ("{{ btw_regel_label }}", "{{ btw_regel_bedrag }}", False),
        ("{{ betalingen_regel_label }}", "{{ betalingen_regel_bedrag }}", False),
        ("Totaal thans verschuldigd", "{{ totaal_openstaand }}", True),
    ])
    _p(doc, "")

    doc.add_heading("SOMMATIE", level=2)
    _p(doc,
        "Ik sommeer u hierbij om het verschuldigde bedrag van "
        "{{ totaal_openstaand }} "
        "binnen acht (8) dagen na dagtekening van deze brief over te maken.")
    _p(doc,
        "Bij gebreke van tijdige en volledige betaling zal ik, zonder nadere "
        "aankondiging, overgaan tot het uitbrengen van een dagvaarding. "
        "De hieraan verbonden kosten (griffierecht, deurwaarderskosten, "
        "proceskosten) komen volledig voor uw rekening.")
    _p(doc, "")
    _p(doc,
        "Ik vertrouw erop u hiermee voldoende te hebben ge\u00efnformeerd en zie uw "
        "betaling met spoed tegemoet.")
    _p(doc, "")
    _p(doc, "Hoogachtend,")
    _p(doc, "")
    _p(doc, "________________________")
    _p(doc, "Namens {{ client.naam }}")
    _p(doc, "")
    _p(doc, "Zaaknummer: {{ zaak.zaaknummer }} | Datum: {{ vandaag }}",
       size=Pt(9), color=RGBColor(0x88, 0x88, 0x88))

    doc.save(str(TEMPLATES_DIR / "sommatie.docx"))
    print("  sommatie.docx")


# ═══════════════════════════════════════════════════════════════════════════════
# RENTEOVERZICHT
# ═══════════════════════════════════════════════════════════════════════════════


def create_renteoverzicht():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2)
        s.bottom_margin = Cm(2)
        s.left_margin = Cm(2)
        s.right_margin = Cm(2)

    doc.add_heading("Renteberekening / Specificatie", level=1)

    # Meta
    meta = doc.add_table(rows=5, cols=2)
    meta.style = "Table Grid"
    for i, (l, v) in enumerate([
        ("Zaaknummer:", "{{ zaak.zaaknummer }}"),
        ("Cli\u00ebnt:", "{{ client.naam }}"),
        ("Wederpartij:", "{{ wederpartij.naam }}"),
        ("Type rente:", "{{ rente_type_label }}"),
        ("Berekend t/m:", "{{ vandaag }}"),
    ]):
        _cel(meta.rows[i].cells[0], l, bold=True)
        _cel(meta.rows[i].cells[1], v)
    _p(doc, "")

    # Claims
    doc.add_heading("Vorderingen", level=2)
    ct = _add_claims_table(doc)

    # Totaal row (static)
    tr = ct.add_row()
    _cel(tr.cells[0], "Totaal hoofdsom", bold=True)
    tr.cells[1].text = ""
    tr.cells[2].text = ""
    _cel(tr.cells[3], "{{ totaal_hoofdsom }}", bold=True, right=True)
    _p(doc, "")

    # Interest per period
    doc.add_heading("Renteberekening per periode", level=2)

    it = doc.add_table(rows=5, cols=6)
    it.style = "Table Grid"
    it.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(["Van", "Tot", "Dagen", "Tarief", "Hoofdsom", "Rente"]):
        _hdr(it.rows[0].cells[i], h)

    # For-loop opening tag (own row)
    it.rows[1].cells[0].text = "{%tr for r in rente_regels %}"

    # Data row (loop body)
    _cel(it.rows[2].cells[0], "{{ r.van }}")
    _cel(it.rows[2].cells[1], "{{ r.tot }}")
    _cel(it.rows[2].cells[2], "{{ r.dagen }}")
    _cel(it.rows[2].cells[3], "{{ r.tarief }}")
    _cel(it.rows[2].cells[4], "{{ r.hoofdsom }}")
    _cel(it.rows[2].cells[5], "{{ r.rente }}")

    # Endfor row
    it.rows[3].cells[0].text = "{%tr endfor %}"

    # Total
    _cel(it.rows[4].cells[0], "Totaal rente", bold=True)
    for c in it.rows[4].cells[1:5]:
        c.text = ""
    _cel(it.rows[4].cells[5], "{{ totaal_rente }}", bold=True, right=True)
    _p(doc, "")

    # BIK
    doc.add_heading("Buitengerechtelijke incassokosten (BIK)", level=2)
    _add_summary_2col(doc, [
        ("BIK (excl. BTW)", "{{ bik_bedrag }}", True),
        ("{{ btw_regel_label }}", "{{ btw_regel_bedrag }}", False),
        ("{{ bik_incl_label }}", "{{ bik_incl_bedrag }}", False),
    ])
    _p(doc, "")

    # Payments
    doc.add_heading("{{ betalingen_kop }}", level=2)
    pt = doc.add_table(rows=4, cols=3)
    pt.style = "Table Grid"
    for i, h in enumerate(["Datum", "Omschrijving", "Bedrag"]):
        _hdr(pt.rows[0].cells[i], h)

    # For-loop opening tag (own row)
    pt.rows[1].cells[0].text = "{%tr for b in betalingen %}"

    # Data row (loop body)
    _cel(pt.rows[2].cells[0], "{{ b.datum }}")
    _cel(pt.rows[2].cells[1], "{{ b.beschrijving }}")
    _cel(pt.rows[2].cells[2], "{{ b.bedrag }}")

    # Endfor row
    pt.rows[3].cells[0].text = "{%tr endfor %}"
    _p(doc, "")

    # Grand total
    doc.add_heading("Totaaloverzicht", level=2)
    _add_summary_2col(doc, [
        ("Hoofdsom", "{{ totaal_hoofdsom }}", False),
        ("Rente t/m {{ vandaag }}", "{{ totaal_rente }}", False),
        ("Buitengerechtelijke incassokosten", "{{ totaal_bik }}", False),
        ("Subtotaal", "{{ subtotaal }}", True),
        ("{{ betalingen_aftrek_label }}", "{{ betalingen_aftrek_bedrag }}", False),
        ("Totaal verschuldigd", "{{ totaal_openstaand }}", True),
    ])
    _p(doc, "")

    _p(doc,
       "Berekening gegenereerd door Luxis op {{ vandaag }} | "
       "Zaaknummer: {{ zaak.zaaknummer }}",
       size=Pt(9), color=RGBColor(0x88, 0x88, 0x88))

    doc.save(str(TEMPLATES_DIR / "renteoverzicht.docx"))
    print("  renteoverzicht.docx")


if __name__ == "__main__":
    print("Generating .docx templates...")
    create_14_dagenbrief()
    create_sommatie()
    create_renteoverzicht()
    print("Done!")
