"""Unit tests voor veilige tekstextractie van dossierstukken."""

import fitz

from app.search.extract import extract_text


def test_extract_text_from_pdf() -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Doorzoekbare overeenkomst")
    content = document.tobytes()
    document.close()

    assert "Doorzoekbare overeenkomst" in extract_text(content, "application/pdf")


def test_extract_text_ignores_unsupported_excel() -> None:
    assert extract_text(b"x", "application/vnd.ms-excel") is None


def test_extract_text_handles_corrupt_pdf() -> None:
    assert extract_text(b"geen geldige pdf", "application/pdf") is None
