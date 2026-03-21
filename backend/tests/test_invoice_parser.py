"""Tests for invoice PDF parsing."""

import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_agent.invoice_parser import _validate_and_clean, parse_invoice_pdf
from app.ai_agent.invoice_prompts import (
    INVOICE_PARSE_SYSTEM_PROMPT,
    build_invoice_parse_prompt,
)


# ── Unit tests: prompt builder ────────────────────────────────────────────


def test_build_invoice_parse_prompt_basic():
    result = build_invoice_parse_prompt("Invoice #123\nTotal: €500.00")
    assert "Invoice #123" in result
    assert "Total: €500.00" in result
    assert "Factuur (PDF)" in result


def test_build_invoice_parse_prompt_truncation():
    long_text = "x" * 6000
    result = build_invoice_parse_prompt(long_text)
    assert len(result) < 6000
    assert "[... ingekort ...]" in result


def test_system_prompt_has_required_fields():
    assert "debtor_name" in INVOICE_PARSE_SYSTEM_PROMPT
    assert "creditor_name" in INVOICE_PARSE_SYSTEM_PROMPT
    assert "principal_amount" in INVOICE_PARSE_SYSTEM_PROMPT
    assert "confidence" in INVOICE_PARSE_SYSTEM_PROMPT


# ── Unit tests: validation ────────────────────────────────────────────────


SAMPLE_AI_RESPONSE = {
    "debtor_name": "Acme B.V.",
    "debtor_type": "company",
    "debtor_address": "Keizersgracht 100",
    "debtor_postcode": "1015 AA",
    "debtor_city": "Amsterdam",
    "debtor_kvk": "12345678",
    "debtor_email": "info@acme.nl",
    "creditor_name": "Kesting Legal",
    "creditor_btw": "NL123456789B01",
    "invoice_number": "2025-001",
    "invoice_date": "2025-01-15",
    "due_date": "2025-02-15",
    "principal_amount": 1500.50,
    "description": "Juridische dienstverlening",
    "confidence": {
        "debtor_name": 0.95,
        "debtor_type": 0.9,
        "debtor_address": 0.85,
        "debtor_postcode": 0.85,
        "debtor_city": 0.85,
        "debtor_kvk": 0.8,
        "debtor_email": 0.7,
        "creditor_name": 0.95,
        "creditor_btw": 0.9,
        "invoice_number": 0.95,
        "invoice_date": 0.95,
        "due_date": 0.9,
        "principal_amount": 0.95,
        "description": 0.8,
    },
}


def test_validate_and_clean_basic():
    result = _validate_and_clean(SAMPLE_AI_RESPONSE)
    assert result["debtor_name"] == "Acme B.V."
    assert result["debtor_type"] == "company"
    assert result["principal_amount"] == "1500.50"
    assert result["confidence"]["debtor_name"] == 0.95


def test_validate_and_clean_decimal_precision():
    raw = {**SAMPLE_AI_RESPONSE, "principal_amount": 1234.567}
    result = _validate_and_clean(raw)
    # Should be rounded to 2 decimal places
    assert result["principal_amount"] == "1234.57"


def test_validate_and_clean_invalid_amount():
    raw = {**SAMPLE_AI_RESPONSE, "principal_amount": "not-a-number"}
    result = _validate_and_clean(raw)
    assert result["principal_amount"] is None


def test_validate_and_clean_null_fields():
    raw = {**SAMPLE_AI_RESPONSE, "debtor_kvk": None, "debtor_email": "null"}
    result = _validate_and_clean(raw)
    assert result["debtor_kvk"] is None
    assert result["debtor_email"] is None


def test_validate_and_clean_invalid_debtor_type():
    raw = {**SAMPLE_AI_RESPONSE, "debtor_type": "invalid"}
    result = _validate_and_clean(raw)
    assert result["debtor_type"] is None


def test_validate_and_clean_missing_confidence():
    raw = {**SAMPLE_AI_RESPONSE}
    del raw["confidence"]
    result = _validate_and_clean(raw)
    assert result["confidence"]["debtor_name"] == 0.0


def test_validate_and_clean_confidence_clamped():
    raw = {
        **SAMPLE_AI_RESPONSE,
        "confidence": {**SAMPLE_AI_RESPONSE["confidence"], "debtor_name": 1.5},
    }
    result = _validate_and_clean(raw)
    assert result["confidence"]["debtor_name"] == 1.0


# ── Integration tests: parse_invoice_pdf ──────────────────────────────────


@pytest.mark.asyncio
async def test_parse_invoice_pdf_success():
    with (
        patch(
            "app.ai_agent.invoice_parser.extract_text_from_pdf",
            return_value="Invoice #123\nTotal: €1500.50",
        ),
        patch(
            "app.ai_agent.invoice_parser.call_intake_ai",
            new_callable=AsyncMock,
            return_value=(SAMPLE_AI_RESPONSE, "kimi-2.5"),
        ),
    ):
        result = await parse_invoice_pdf(b"fake-pdf-bytes", "test.pdf")
        assert result["debtor_name"] == "Acme B.V."
        assert result["principal_amount"] == "1500.50"
        assert result["model"] == "kimi-2.5"
        assert "confidence" in result


@pytest.mark.asyncio
async def test_parse_invoice_pdf_empty_text():
    with patch(
        "app.ai_agent.invoice_parser.extract_text_from_pdf",
        return_value="",
    ):
        with pytest.raises(ValueError, match="Geen tekst gevonden"):
            await parse_invoice_pdf(b"fake-pdf-bytes", "empty.pdf")


@pytest.mark.asyncio
async def test_parse_invoice_pdf_ai_failure():
    with (
        patch(
            "app.ai_agent.invoice_parser.extract_text_from_pdf",
            return_value="Some text",
        ),
        patch(
            "app.ai_agent.invoice_parser.call_intake_ai",
            new_callable=AsyncMock,
            side_effect=ValueError("All AI providers failed"),
        ),
    ):
        with pytest.raises(ValueError, match="All AI providers failed"):
            await parse_invoice_pdf(b"fake-pdf-bytes", "test.pdf")
