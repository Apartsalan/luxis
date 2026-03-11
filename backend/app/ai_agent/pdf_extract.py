"""PDF text extraction using pdfplumber.

Extracts text from PDF attachments for invoice/claim data extraction.
"""

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)

# Max pages to extract (invoices are typically 1-3 pages)
MAX_PAGES = 10
# Max characters to return (keep AI costs low)
MAX_CHARS = 5000


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF file using pdfplumber.

    Returns extracted text, truncated to MAX_CHARS.
    Returns empty string on failure.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning("PDF file not found: %s", file_path)
        return ""

    try:
        text_parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages[:MAX_PAGES]):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n\n".join(text_parts).strip()

        if len(full_text) > MAX_CHARS:
            full_text = full_text[:MAX_CHARS] + "\n[... ingekort ...]"

        logger.info(
            "PDF extraction: %s — %d pages, %d chars",
            file_path.name,
            len(text_parts),
            len(full_text),
        )
        return full_text

    except Exception as e:
        logger.error("PDF extraction failed for %s: %s", file_path, e)
        return ""
