"""S220 punt 5 — gedeelde onderwerp-bouwer."""

from app.email.subject import build_email_subject


def test_full_subject():
    assert (
        build_email_subject(
            client_name="LegalWork B.V.",
            debtor_name="Bayar Transport VOF",
            letter_type="Eerste sommatie",
            case_number="2026-00613",
        )
        == "LegalWork B.V. / Bayar Transport VOF — Eerste sommatie — 2026-00613"
    )


def test_missing_client_and_debtor_drops_prefix():
    assert (
        build_email_subject(
            client_name=None, debtor_name="  ", letter_type="Tweede sommatie",
            case_number="2026-00001",
        )
        == "Tweede sommatie — 2026-00001"
    )


def test_only_debtor():
    assert (
        build_email_subject(
            client_name="", debtor_name="Jansen", letter_type="Aanmaning",
            case_number="IN100007",
        )
        == "Jansen — Aanmaning — IN100007"
    )
