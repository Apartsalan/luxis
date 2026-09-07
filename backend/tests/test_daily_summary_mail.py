"""Samenvattingsmail (S256) — de mailopbouw is een pure functie, dus hier
zonder database getest: (1) niets te melden = géén mail, (2) alles wat wacht
staat erin met dossiernummer en bedrag, te-laat eerst, (3) de link wijst naar
de werklijst, (4) bedragen in Nederlandse notatie, (5) lange lijsten worden
afgekapt met een telling — anders wordt de mail zelf de bel die niemand leest.
"""

from datetime import date
from decimal import Decimal

from app.notifications.daily_summary import MAX_ROWS, SummaryData, build_summary_html


def _brief(nr: str, urgency: str = "normal", amount: str = "100.00") -> dict:
    return {
        "case_number": nr,
        "party": "Testpartij B.V.",
        "step": "Tweede sommatie",
        "days": 44,
        "amount": Decimal(amount),
        "urgency": urgency,
        "action": "Document genereren & versturen",
    }


def test_niets_te_melden_geeft_geen_mail():
    assert build_summary_html(SummaryData(app_url="https://luxis.test")) is None


def test_alle_drie_blokken_met_dossiernummer_en_bedrag():
    data = SummaryData(
        brieven=[_brief("IN100602", "overdue", "18934.11")],
        verweer=[{"case_number": "IN100592", "party": "Verweerder", "days": 44}],
        termijnen=[
            {
                "case_number": "IN100026",
                "debtor_name": "F. van Alphen",
                "due_date": date(2026, 8, 1),
                "open": Decimal("500.00"),
            }
        ],
        app_url="https://luxis.test/",
        vandaag=date(2026, 9, 7),
    )
    html = build_summary_html(data)
    assert html is not None
    for verwacht in (
        "1 brieven wachten op jouw akkoord (1 te laat)",
        "IN100602",
        "€ 18.934,11",
        "te laat",
        "1 dossiers wachten op een antwoord op verweer",
        "IN100592",
        "1 gemiste termijnen op betalingsregelingen (€ 500,00)",
        "IN100026",
        "01-08-2026",
        'href="https://luxis.test/followup"',
        "07-09-2026",
    ):
        assert verwacht in html, verwacht


def test_lange_lijst_wordt_afgekapt_met_telling():
    data = SummaryData(brieven=[_brief(f"IN1{i:05d}") for i in range(MAX_ROWS + 7)])
    html = build_summary_html(data)
    assert html is not None
    assert html.count("Testpartij B.V.") == MAX_ROWS
    assert "… en nog 7 in de app." in html


def test_html_ontsnapt_namen_uit_de_database():
    data = SummaryData(brieven=[{**_brief("IN100001"), "party": "<script>x</script>"}])
    html = build_summary_html(data)
    assert html is not None and "<script>" not in html and "&lt;script&gt;" in html
