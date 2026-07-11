"""Veilige tekstextractie voor doorzoekbare dossierstukken."""

import logging

import fitz

from app.email.providers.imap_provider import _html_to_text

logger = logging.getLogger(__name__)

MAX_EXTRACTED_TEXT_LENGTH = 200_000


def extract_text(content: bytes, content_type: str) -> str | None:
    """Extraheer doorzoekbare tekst zonder uploads of backfills te laten falen."""
    try:
        if content_type == "application/pdf":
            with fitz.open(stream=content, filetype="pdf") as document:
                text = "\n".join(page.get_text() for page in document)
        elif content_type == "text/html":
            # Hergebruik dezelfde HTML-normalisatie als de e-mailprovider.
            text = _html_to_text(content.decode("utf-8", errors="replace"))
        elif content_type == "text/plain":
            text = content.decode("utf-8", errors="replace")
        else:
            return None

        # PostgreSQL-tekstvelden weigeren NUL-bytes (0x00) — sommige PDF's
        # leveren die in hun tekstlaag (backfill-run 12 juli, prod-bewezen).
        text = text.replace("\x00", "")
        return text.strip()[:MAX_EXTRACTED_TEXT_LENGTH] or None
    except Exception:
        logger.warning("Tekstextractie mislukt voor content-type %s", content_type, exc_info=True)
        return None
