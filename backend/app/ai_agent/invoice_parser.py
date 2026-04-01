"""Invoice PDF parser — extracts structured data from invoice PDFs using AI.

Pipeline:
1. Extract text from PDF (pdfplumber/pymupdf)
2. Pre-process: detect address blocks with regex, label them for the AI
3. AI extraction (Gemini Flash → Kimi → Haiku fallback)
4. Post-process: validate + auto-correct common AI mistakes
"""

import logging
import re
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

# ── Dutch postcode pattern: 4 digits + 2 uppercase letters ──────────────────
_POSTCODE_RE = re.compile(r"\b(\d{4}\s?[A-Z]{2})\b")
# ── Email pattern ──
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# ── T.a.v. / Ter attentie van pattern ──
_TAV_RE = re.compile(r"(?:T\.?a\.?v\.?|Ter attentie van)\s+(.+?)(?:\s+Postbus|\s+\d{4}\s?[A-Z]{2}|\n|$)", re.IGNORECASE)
# ── Postbus pattern ──
_POSTBUS_RE = re.compile(r"Postbus\s+\d+", re.IGNORECASE)
# ── Address block: name line(s) before T.a.v./Postbus/postcode ──
_ADDRESS_BLOCK_RE = re.compile(
    r"(?P<name>[^\n]{3,}?)\s+"
    r"(?:T\.?a\.?v\.?\s+(?P<tav>[^\n]*?)\s+)?"
    r"(?:(?P<postbus>Postbus\s+\d+)\s+)?"
    r"(?P<postcode>\d{4}\s?[A-Z]{2})\s+"
    r"(?P<city>[A-Z' -]{2,})",
    re.IGNORECASE,
)


def _detect_address_blocks(text: str) -> list[dict]:
    """Detect structured address blocks in Dutch invoice text.

    Returns list of dicts with keys: name, tav, postbus, postcode, city, raw.
    """
    blocks = []
    for m in _ADDRESS_BLOCK_RE.finditer(text):
        name = m.group("name").strip()
        # Skip if name is just a label like "PERSOONLIJK & VERTROUWELIJK"
        if len(name) < 3 or name.upper() in ("PERSOONLIJK & VERTROUWELIJK", "VERTROUWELIJK"):
            continue
        # Skip if name looks like an email
        if "@" in name:
            continue
        blocks.append({
            "name": name,
            "tav": m.group("tav").strip() if m.group("tav") else None,
            "postbus": m.group("postbus") if m.group("postbus") else None,
            "postcode": m.group("postcode"),
            "city": m.group("city").strip(),
            "raw": m.group(0),
        })
    return blocks


def _enrich_prompt_with_blocks(pdf_text: str, blocks: list[dict]) -> str:
    """Add detected address blocks as structured hints to the prompt."""
    if not blocks:
        return pdf_text

    hints = "\n\n--- GEDETECTEERDE ADRESBLOKKEN (gebruik deze om debiteur en crediteur te identificeren) ---\n"
    for i, b in enumerate(blocks, 1):
        hints += f"\nBlok {i}:\n"
        hints += f"  Naam: {b['name']}\n"
        if b["tav"]:
            hints += f"  T.a.v.: {b['tav']}\n"
        if b["postbus"]:
            hints += f"  Postadres: {b['postbus']}\n"
        hints += f"  Postcode: {b['postcode']}\n"
        hints += f"  Plaats: {b['city']}\n"

    hints += "\nDe eerste naam in het adresblok is het bedrijf/de persoon, NIET het email-adres.\n"
    hints += "Het adresblok met 'T.a.v.' of 'Postbus' is vrijwel altijd de ONTVANGER (debiteur).\n"
    hints += "Het andere blok (vaak met KvK/BTW) is de AFZENDER (crediteur).\n"

    return pdf_text + hints


def _post_process(result: dict, pdf_text: str, blocks: list[dict]) -> dict:
    """Validate and auto-correct common AI extraction mistakes.

    Fixes:
    - debtor_name is an email address
    - debtor_type is 'person' but address block has a company name
    - debtor_name extracted from email instead of address block
    """
    debtor_name = result.get("debtor_name") or ""
    creditor_name = result.get("creditor_name") or ""

    # Fix 1: debtor_name is an email address
    if "@" in debtor_name:
        logger.warning("Post-process: debtor_name '%s' looks like email, attempting fix", debtor_name)
        # Move it to debtor_email if empty
        if not result.get("debtor_email"):
            result["debtor_email"] = debtor_name
        # Try to find the real name from address blocks
        for block in blocks:
            block_name = block["name"]
            # Skip if this block name matches the creditor
            if creditor_name and _names_match(block_name, creditor_name):
                continue
            result["debtor_name"] = block_name
            if block.get("tav"):
                result["debtor_contact_person"] = block["tav"]
            if block.get("postbus"):
                result["debtor_postal_address"] = block["postbus"]
            if block.get("postcode"):
                result["debtor_postal_postcode"] = block["postcode"]
            if block.get("city"):
                result["debtor_postal_city"] = block["city"]
            result["debtor_type"] = "company"
            logger.info("Post-process: corrected debtor_name to '%s'", block_name)
            break

    # Fix 2: debtor_type 'person' but address block has T.a.v. (implies company)
    if result.get("debtor_type") == "person" and blocks:
        for block in blocks:
            if _names_match(block["name"], debtor_name) or _names_match(block["name"], result.get("debtor_name", "")):
                if block.get("tav"):
                    result["debtor_type"] = "company"
                    if not result.get("debtor_contact_person"):
                        result["debtor_contact_person"] = block["tav"]
                    logger.info("Post-process: corrected debtor_type to 'company' (has T.a.v.)")
                    break

    # Fix 3: debtor_name doesn't match any block but a non-creditor block exists
    if result.get("debtor_name") and not any(
        _names_match(b["name"], result["debtor_name"]) for b in blocks
    ):
        # AI picked a name that's not in any address block — suspicious
        for block in blocks:
            if creditor_name and _names_match(block["name"], creditor_name):
                continue
            # This block is likely the real debtor
            old_name = result["debtor_name"]
            result["debtor_name"] = block["name"]
            result["debtor_type"] = "company"
            if block.get("tav"):
                result["debtor_contact_person"] = block["tav"]
            if block.get("postbus") and not result.get("debtor_postal_address"):
                result["debtor_postal_address"] = block["postbus"]
            if block.get("postcode") and not result.get("debtor_postal_postcode"):
                result["debtor_postal_postcode"] = block["postcode"]
            if block.get("city") and not result.get("debtor_postal_city"):
                result["debtor_postal_city"] = block["city"]
            logger.info(
                "Post-process: debtor_name '%s' not in any address block, corrected to '%s'",
                old_name, block["name"],
            )
            break

    return result


def _names_match(a: str, b: str) -> bool:
    """Fuzzy check if two names refer to the same entity."""
    if not a or not b:
        return False
    a_clean = a.lower().strip().rstrip(".")
    b_clean = b.lower().strip().rstrip(".")
    # Exact or substring match
    return a_clean == b_clean or a_clean in b_clean or b_clean in a_clean

# Fields that should be present in a valid response
EXPECTED_FIELDS = [
    "debtor_name",
    "debtor_contact_person",
    "debtor_type",
    "debtor_address",
    "debtor_postcode",
    "debtor_city",
    "debtor_postal_address",
    "debtor_postal_postcode",
    "debtor_postal_city",
    "debtor_kvk",
    "debtor_email",
    "creditor_name",
    "creditor_contact_person",
    "creditor_type",
    "creditor_address",
    "creditor_postcode",
    "creditor_city",
    "creditor_postal_address",
    "creditor_postal_postcode",
    "creditor_postal_city",
    "creditor_kvk",
    "creditor_btw",
    "creditor_email",
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

    # Ensure debtor_type and creditor_type are valid
    if result.get("debtor_type") not in ("company", "person", None):
        result["debtor_type"] = None
    if result.get("creditor_type") not in ("company", "person", None):
        result["creditor_type"] = None

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
            logger.info("PDF text for %s:\n%s", filename, pdf_text[:2000])

            # Pre-process: detect address blocks and enrich prompt
            address_blocks = _detect_address_blocks(pdf_text)
            if address_blocks:
                logger.info("Detected %d address blocks: %s", len(address_blocks),
                            [b["name"] for b in address_blocks])
            enriched_text = _enrich_prompt_with_blocks(pdf_text, address_blocks)

            user_message = build_invoice_parse_prompt(enriched_text)
            raw_result, model_name = await call_intake_ai(INVOICE_PARSE_SYSTEM_PROMPT, user_message)
            logger.info("Raw AI result for %s: %s", filename, raw_result)

            # Post-process: validate and auto-correct
            raw_result = _post_process(raw_result, pdf_text, address_blocks)
        else:
            # DF2-07: Fallback for scanned/image PDFs — send directly to Claude
            logger.info(
                "No text extracted from %s, falling back to Claude native PDF",
                filename,
            )
            try:
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
            except Exception as e:
                logger.error("Claude PDF fallback failed for %s: %s", filename, e)
                raise ValueError(
                    "Kan geen tekst uit deze PDF halen. "
                    "Probeer een PDF met selecteerbare tekst (geen scan/afbeelding)."
                ) from e

        # Validate and clean the result
        cleaned = _validate_and_clean(raw_result)
        cleaned["model"] = model_name

        logger.info(
            "Invoice parse: %s — model=%s, debtor=%s (type=%s, contact=%s), creditor=%s (type=%s), amount=%s",
            filename,
            model_name,
            cleaned.get("debtor_name"),
            cleaned.get("debtor_type"),
            cleaned.get("debtor_contact_person"),
            cleaned.get("creditor_name"),
            cleaned.get("creditor_type"),
            cleaned.get("principal_amount"),
        )

        return cleaned

    finally:
        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass
