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
# ── Dutch street + number line: capital-cased street name + house number ──
# Examples: "Hoofdstraat 12", "Van Houtenlaan 7B", "Prinses Beatrixlaan 614"
_STREET_RE = re.compile(
    r"^\s*(?P<street>(?:[A-Z][a-zA-ZÀ-ÿ.'\-]+\s+){1,5}"
    r"\d+\s*[A-Za-z]?(?:\s*[-/]\s*\d+\s*[A-Za-z]?)?)\s*$",
    re.MULTILINE,
)


_POSTCODE_LINE_RE = re.compile(
    r"^\s*(?P<postcode>\d{4}\s?[A-Z]{2})\s+(?P<city>[A-Z][A-Za-z' -]{1,})\s*$"
)
_POSTBUS_LINE_RE = re.compile(
    r"^\s*(?P<postbus>Postbus\s+\d+)"
    r"(?:\s+(?P<postcode>\d{4}\s?[A-Z]{2})\s+(?P<city>[A-Z][A-Za-z' -]{1,}))?\s*$",
    re.IGNORECASE,
)


def _detect_address_blocks(text: str) -> list[dict]:
    """Detect structured address blocks in Dutch invoice text using a line-based scan.

    A typical Dutch invoice address block looks like:
        Bedrijfsnaam BV          ← name
        T.a.v. Jan Jansen        ← optional tav
        Hoofdstraat 12           ← optional street + number
        Postbus 123              ← optional postbus
        1234 AB Amsterdam        ← postcode + city

    Returns list of dicts with keys: name, tav, postbus, postcode, city, street, raw.
    """
    lines = text.split("\n")
    blocks: list[dict] = []
    skip_labels = {
        "PERSOONLIJK & VERTROUWELIJK",
        "VERTROUWELIJK",
        "PERSOONLIJK",
        "FACTUUR",
        "INVOICE",
    }

    for i, line in enumerate(lines):
        m_pc = _POSTCODE_LINE_RE.match(line)
        if not m_pc:
            continue
        postcode = m_pc.group("postcode")
        city = m_pc.group("city").strip()

        # Look at up to 5 lines above for street, postbus, tav, name
        street = None
        postbus = None
        tav = None
        name = None
        # Walk upwards
        candidates: list[str] = []
        for j in range(i - 1, max(-1, i - 6), -1):
            ln = lines[j].strip()
            if not ln:
                if candidates:
                    break  # Empty line ends the block
                continue
            if ln.upper() in skip_labels:
                continue
            if "@" in ln:
                continue
            candidates.append(ln)

        # Reverse to get top-down order
        candidates.reverse()

        for cand in candidates:
            # T.a.v. line
            tav_m = re.match(r"(?:T\.?a\.?v\.?|Ter attentie van)\s+(.+)", cand, re.IGNORECASE)
            if tav_m:
                tav = tav_m.group(1).strip()
                continue
            # Postbus line
            pb_m = re.match(r"(Postbus\s+\d+)", cand, re.IGNORECASE)
            if pb_m:
                postbus = pb_m.group(1)
                continue
            # Street + number line
            st_m = _STREET_RE.match(cand)
            if st_m:
                street = st_m.group("street").strip()
                continue
            # Otherwise: candidate name (first non-tav/postbus/street line)
            if name is None:
                name = cand

        if not name:
            continue
        if name.upper() in skip_labels:
            continue

        raw_lines = candidates + [line.strip()]
        blocks.append({
            "name": name,
            "tav": tav,
            "postbus": postbus,
            "postcode": postcode,
            "city": city,
            "street": street,
            "raw": "\n".join(raw_lines),
        })

    # Also handle "Postbus + postcode + city" on the same line (postal-only blocks)
    for i, line in enumerate(lines):
        m_pb = _POSTBUS_LINE_RE.match(line)
        if not m_pb or not m_pb.group("postcode"):
            continue
        # Find name above
        name = None
        for j in range(i - 1, max(-1, i - 4), -1):
            ln = lines[j].strip()
            if not ln or ln.upper() in skip_labels or "@" in ln:
                continue
            name = ln
            break
        if not name:
            continue
        # Skip if we already have a block with this postcode
        if any(b["postcode"] == m_pb.group("postcode") and b["name"] == name for b in blocks):
            continue
        blocks.append({
            "name": name,
            "tav": None,
            "postbus": m_pb.group("postbus"),
            "postcode": m_pb.group("postcode"),
            "city": m_pb.group("city").strip() if m_pb.group("city") else "",
            "street": None,
            "raw": f"{name}\n{line.strip()}",
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
    - Empty visit address fields filled in from detected address blocks (Lisanne demo 7-4-2026:
      AI sometimes only returns postcode, missing the street).
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

    # Fix 4: empty visit-address fields — fill from the address block that matches the debtor.
    # Lisanne's complaint (demo 7-4-2026): AI returned only postcode, no street name.
    # Strategy: find a non-creditor block matching the debtor, then use its `street`
    # (detected from the line above the postcode) and postcode/city to fill any empty visit fields.
    final_debtor_name = result.get("debtor_name") or ""
    if final_debtor_name and blocks:
        for block in blocks:
            # Skip creditor blocks
            if creditor_name and _names_match(block["name"], creditor_name):
                continue
            # Only use blocks that match the debtor name
            if not _names_match(block["name"], final_debtor_name):
                continue
            # Don't pick a postbus-only block as visit address — postbus is postal, not visit
            if block.get("postbus"):
                # But still use postcode/city if visit fields are empty AND there's a street
                pass
            if not result.get("debtor_address") and block.get("street"):
                result["debtor_address"] = block["street"]
                logger.info(
                    "Post-process: filled debtor_address from block street: '%s'",
                    block["street"],
                )
            has_visit_pc = block.get("postcode") and not block.get("postbus")
            if not result.get("debtor_postcode") and has_visit_pc:
                result["debtor_postcode"] = block["postcode"]
            if not result.get("debtor_city") and has_visit_pc and block.get("city"):
                result["debtor_city"] = block["city"]
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
