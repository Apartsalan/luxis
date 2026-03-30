"""PDF text extraction using pymupdf4llm.

AI-TECH-01: Replaced pdfplumber with pymupdf4llm for better table/layout
extraction and Markdown output optimized for LLM consumption. 5-10x faster.
"""

import logging
from pathlib import Path

import pymupdf4llm

logger = logging.getLogger(__name__)

# Max pages to extract (invoices are typically 1-3 pages)
MAX_PAGES = 10
# Max characters to return (keep AI costs low)
MAX_CHARS = 5000


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF file as Markdown using pymupdf4llm.

    Returns extracted text (Markdown format), truncated to MAX_CHARS.
    Returns empty string on failure.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning("PDF file not found: %s", file_path)
        return ""

    try:
        # Get page count first to avoid requesting pages beyond the document
        import pymupdf
        doc = pymupdf.open(str(file_path))
        page_count = min(doc.page_count, MAX_PAGES)
        doc.close()

        md_text = pymupdf4llm.to_markdown(
            str(file_path),
            pages=list(range(page_count)),
            show_progress=False,
        )

        full_text = md_text.strip()

        if len(full_text) > MAX_CHARS:
            full_text = full_text[:MAX_CHARS] + "\n[... ingekort ...]"

        logger.info(
            "PDF extraction (pymupdf4llm): %s — %d chars",
            file_path.name,
            len(full_text),
        )
        return full_text

    except Exception as e:
        logger.error("PDF extraction failed for %s: %s", file_path, e)
        return ""
