"""PDF service — convert rendered DOCX documents to PDF.

Uses LibreOffice in headless mode (soffice --headless --convert-to pdf).
LibreOffice must be installed in the Docker image (libreoffice-writer).
"""

import asyncio
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


async def docx_to_pdf(docx_bytes: bytes) -> bytes:
    """Convert a DOCX byte-string to PDF using LibreOffice headless.

    Args:
        docx_bytes: The rendered .docx file as bytes.

    Returns:
        The PDF file as bytes.

    Raises:
        RuntimeError: If LibreOffice conversion fails.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "input.docx"
        input_path.write_bytes(docx_bytes)

        proc = await asyncio.create_subprocess_exec(
            "soffice",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmpdir_path),
            str(input_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace").strip()
            logger.error(f"LibreOffice conversie mislukt (exit {proc.returncode}): {error_msg}")
            raise RuntimeError(
                f"PDF-conversie mislukt. Controleer of LibreOffice is geinstalleerd. "
                f"Fout: {error_msg}"
            )

        output_path = tmpdir_path / "input.pdf"
        if not output_path.exists():
            raise RuntimeError(
                "PDF-conversie mislukt: uitvoerbestand niet gevonden. "
                "LibreOffice heeft mogelijk geen output geproduceerd."
            )

        pdf_bytes = output_path.read_bytes()
        logger.info(f"DOCX naar PDF geconverteerd ({len(docx_bytes)} → {len(pdf_bytes)} bytes)")
        return pdf_bytes


def html_to_pdf(html: str) -> bytes:
    """Convert stored document HTML to PDF via WeasyPrint.

    B1 — e-mailroute-documenten worden als HTML gearchiveerd (`content_html`),
    niet als DOCX. Voor de dossier-preview maken we daar direct een PDF van:
    exact wat er verstuurd is. Hergebruikt de SSRF-veilige URL-fetcher van de
    facturenmodule.
    """
    import weasyprint

    from app.invoices.invoice_pdf_service import _safe_url_fetcher

    return weasyprint.HTML(string=html, url_fetcher=_safe_url_fetcher).write_pdf()
