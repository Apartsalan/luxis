"""Invoice PDF parser — extracts structured data from invoice PDFs using AI."""

import logging
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.ai_agent.invoice_prompts import (
    INVOICE_PARSE_SYSTEM_PROMPT,
    build_invoice_parse_prompt,
)
from app.ai_agent.kimi_client import call_claude_with_pdf, call_intake_ai
from app.ai_agent.pdf_extract import extract_text_from_pdf

logger = logging.getLogger(__name__)

# Fields that should be present in a valid response
EXPECTED_FIELDS = [
    "debtor_name",
    "debtor_type",
    "debtor_address",
    "debtor_postcode",
    "debtor_city",
    "debtor_kvk",
    "debtor_email",
    "creditor_name",
    "creditor_btw",
    "invoice_number",
    "invoice_date",
    "due_date",
    "principal_amount",
    "description",
]


def _validate_and_clean(raw: dict) -> dict:
    """Validate types, convert principal_amount to Decimal string, ensure all fields present."""
    result: dict = {}

    for field in EXPECTED_FIELDS:
        value = raw.get(field)
        if value is None or value == "null":
            result[field] = None
        else:
            result[field] = value

    # Ensure debtor_type is valid
    if result.get("debtor_type") not in ("company", "person", None):
        result["debtor_type"] = None

    # Convert principal_amount to precise string via Decimal
    amount = result.get("principal_amount")
    if amount is not None:
        try:
            d = Decimal(str(amount)).quantize(Decimal("0.01"))
            result["principal_amount"] = str(d)
        except (InvalidOperation, ValueError):
            result["principal_amount"] = None

    # Confidence dict — ensure it's a dict with float values
    confidence = raw.get("confidence", {})
    if not isinstance(confidence, dict):
        confidence = {}
    clean_confidence: dict[str, float] = {}
    for field in EXPECTED_FIELDS:
        val = confidence.get(field, 0.0)
        try:
            clean_confidence[field] = max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            clean_confidence[field] = 0.0
    result["confidence"] = clean_confidence

    return result


async def parse_invoice_pdf(file_content: bytes, filename: str) -> dict:
    """Parse an invoice PDF and extract structured data using AI.

    Args:
        file_content: Raw PDF bytes.
        filename: Original filename (for logging).

    Returns:
        Dict with extracted fields, confidence scores, and model name.

    Raises:
        ValueError: If PDF has no extractable text or AI parsing fails.
    """
    # Write to temp file for pdfplumber
    suffix = Path(filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(tmp_path)

        if pdf_text.strip():
            # Normal path: text-based extraction + AI parsing
            user_message = build_invoice_parse_prompt(pdf_text)
            raw_result, model_name = await call_intake_ai(
                INVOICE_PARSE_SYSTEM_PROMPT, user_message
            )
        else:
            # DF2-07: Fallback for scanned/image PDFs — send directly to Claude
            logger.info(
                "No text extracted from %s, falling back to Claude native PDF",
                filename,
            )
            raw_result = await call_claude_with_pdf(
                system_prompt=INVOICE_PARSE_SYSTEM_PROMPT,
                user_message=(
                    "Dit is een gescande factuur (afbeelding-PDF). "
                    "Analyseer de afbeelding en extraheer alle velden. "
                    "Retourneer het resultaat als JSON."
                ),
                pdf_path=tmp_path,
            )
            model_name = "claude-native-pdf"

        # Validate and clean the result
        cleaned = _validate_and_clean(raw_result)
        cleaned["model"] = model_name

        logger.info(
            "Invoice parse: %s — model=%s, debtor=%s, amount=%s",
            filename,
            model_name,
            cleaned.get("debtor_name"),
            cleaned.get("principal_amount"),
        )

        return cleaned

    finally:
        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass
