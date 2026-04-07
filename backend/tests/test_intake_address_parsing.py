"""Tests for invoice parser address-block detection and post-processing.

These tests cover Lisanne's complaint from the demo on 2026-04-07: when uploading
a factuur to create a dossier, only the postcode came through — the street name was
missing. The fix is in `invoice_parser._post_process()` which now backfills empty
visit-address fields from detected address blocks (using the line above the postcode).
"""

from app.ai_agent.invoice_parser import (
    _detect_address_blocks,
    _post_process,
    _STREET_RE,
)


# ─── Street regex unit tests ───────────────────────────────────────────────


def test_street_regex_matches_simple_street():
    text = "Hoofdstraat 12"
    m = _STREET_RE.search(text)
    assert m is not None
    assert m.group("street").strip() == "Hoofdstraat 12"


def test_street_regex_matches_street_with_letter_suffix():
    text = "Van Houtenlaan 7B"
    m = _STREET_RE.search(text)
    assert m is not None
    assert "Van Houtenlaan 7B" in m.group("street")


def test_street_regex_matches_multi_word_street():
    text = "Prinses Beatrixlaan 614"
    m = _STREET_RE.search(text)
    assert m is not None
    assert "Prinses Beatrixlaan 614" in m.group("street")


def test_street_regex_does_not_match_postcode_line():
    text = "1234 AB Amsterdam"
    m = _STREET_RE.search(text)
    # Should not match — starts with digits, no street letters before number
    assert m is None or "Amsterdam" not in (m.group("street") or "")


# ─── Address block detection ───────────────────────────────────────────────


def test_detect_address_block_with_street_above_postcode():
    pdf_text = """\
Factuur

Acme B.V.
Hoofdstraat 12
1234 AB Amsterdam

Bedrag: € 1.500,00
"""
    blocks = _detect_address_blocks(pdf_text)
    assert len(blocks) >= 1
    debtor_block = blocks[0]
    assert "Acme" in debtor_block["name"]
    assert debtor_block["postcode"] == "1234 AB"
    assert debtor_block["city"] == "Amsterdam"
    # The key fix: street should be detected
    assert debtor_block["street"] is not None
    assert "Hoofdstraat 12" in debtor_block["street"]


def test_detect_address_block_postbus_only_no_street():
    pdf_text = """\
Acme B.V.
Postbus 123 1234 AB Amsterdam
"""
    blocks = _detect_address_blocks(pdf_text)
    assert len(blocks) >= 1
    # Postbus block: no visit street
    block = blocks[0]
    assert block.get("postbus") is not None


# ─── Post-process: fill empty visit-address from blocks ────────────────────


def test_post_process_fills_empty_visit_address_from_block():
    """Lisanne's bug: AI returned only postcode + city, not the street.
    Post-process should fill debtor_address from the detected street."""
    pdf_text = """\
Factuur 2026-001

Acme B.V.
Hoofdstraat 12
1234 AB Amsterdam

Totaal: € 1.500,00
"""
    ai_result = {
        "debtor_name": "Acme B.V.",
        "debtor_type": "company",
        "debtor_address": None,  # AI missed it
        "debtor_postcode": "1234 AB",
        "debtor_city": "Amsterdam",
        "creditor_name": "Kesting Legal",
    }
    blocks = _detect_address_blocks(pdf_text)
    fixed = _post_process(ai_result, pdf_text, blocks)
    assert fixed["debtor_address"] is not None
    assert "Hoofdstraat 12" in fixed["debtor_address"]
    assert fixed["debtor_postcode"] == "1234 AB"
    assert fixed["debtor_city"] == "Amsterdam"


def test_post_process_does_not_overwrite_existing_visit_address():
    """If AI got it right, post-process must not clobber the value."""
    pdf_text = """\
Acme B.V.
Hoofdstraat 12
1234 AB Amsterdam
"""
    ai_result = {
        "debtor_name": "Acme B.V.",
        "debtor_type": "company",
        "debtor_address": "Reeds Goed Adres 5",
        "debtor_postcode": "1234 AB",
        "debtor_city": "Amsterdam",
        "creditor_name": "Kesting Legal",
    }
    blocks = _detect_address_blocks(pdf_text)
    fixed = _post_process(ai_result, pdf_text, blocks)
    # Existing value preserved
    assert fixed["debtor_address"] == "Reeds Goed Adres 5"


def test_post_process_skips_creditor_blocks():
    """When matching debtor against blocks, the creditor block must be skipped."""
    pdf_text = """\
Kesting Legal
Juridischelaan 1
1011 AA Amsterdam

Acme B.V.
Hoofdstraat 12
1234 AB Amsterdam
"""
    ai_result = {
        "debtor_name": "Acme B.V.",
        "debtor_type": "company",
        "debtor_address": None,
        "debtor_postcode": None,
        "debtor_city": None,
        "creditor_name": "Kesting Legal",
    }
    blocks = _detect_address_blocks(pdf_text)
    fixed = _post_process(ai_result, pdf_text, blocks)
    # Should pick Acme block, not Kesting
    assert fixed["debtor_address"] is not None
    assert "Hoofdstraat" in fixed["debtor_address"]
    assert fixed["debtor_city"] == "Amsterdam"
    # Verify it's not the creditor's address
    assert "Juridischelaan" not in (fixed["debtor_address"] or "")
