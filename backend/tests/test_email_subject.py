"""S220 punt 5 — gedeelde onderwerp-bouwer."""

from app.email.subject import build_email_subject, build_reply_subject


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


# ── S223 — antwoord-onderwerp (Re: + partijen/dossiernummer) ───────────────


def test_reply_prefixes_re_and_appends_parties():
    assert (
        build_reply_subject(
            original_subject="SOMMATIE TOT BETALING / LEGALWORK - SRict",
            client_name="LegalWork B.V.",
            debtor_name="SRict B.V.",
            case_number="IN100607",
        )
        == "Re: SOMMATIE TOT BETALING / LEGALWORK - SRict — LegalWork B.V. / SRict B.V. — IN100607"
    )


def test_reply_keeps_single_re_prefix():
    # Origineel heeft al "Re:" → niet verdubbelen.
    out = build_reply_subject(
        original_subject="Re: Ik betwist",
        client_name="LegalWork B.V.", debtor_name="SRict B.V.",
        case_number="IN100607",
    )
    assert out.count("Re:") == 1
    assert out.startswith("Re: Ik betwist")


def test_reply_skips_append_when_case_number_already_present():
    # Dossiernummer staat al in het onderwerp → geen dubbele vermelding.
    out = build_reply_subject(
        original_subject="Vraag over IN100607",
        client_name="LegalWork B.V.", debtor_name="SRict B.V.",
        case_number="IN100607",
    )
    assert out == "Re: Vraag over IN100607"


def test_reply_empty_original_falls_back_to_re():
    out = build_reply_subject(
        original_subject="", client_name=None, debtor_name="SRict B.V.",
        case_number="IN100607",
    )
    assert out == "Re: — SRict B.V. — IN100607"


def test_reply_strips_basenet_tracking_tags():
    """S227 (keuze Arsalan): BaseNet-volgcodes "[IN100458_I...]" horen niet in
    het antwoord-onderwerp; de rest van het origineel blijft (Re:-draad intact)."""
    out = build_reply_subject(
        original_subject=(
            "RE: SOMMATIE TOT BETALING / LegalWork B.V. / Studio Hartzema B.V. "
            "/ IN100458 [IN100458_I63930662] [IN100458_I64036393]"
        ),
        client_name="LegalWork B.V.", debtor_name="Studio Hartzema B.V.",
        case_number="IN100458",
    )
    assert out == (
        "RE: SOMMATIE TOT BETALING / LegalWork B.V. / Studio Hartzema B.V. / IN100458"
    )
    assert "[" not in out
