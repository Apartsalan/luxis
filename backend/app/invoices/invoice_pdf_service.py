"""Invoice PDF rendering — generates professional A4 PDF invoices via WeasyPrint.

Uses Jinja2 HTML template + WeasyPrint for pixel-perfect PDF output.
All financial values are pre-formatted as Dutch currency strings.
"""

import logging
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import jinja2
import weasyprint
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.docx_service import (
    _contact_ctx,
    _fmt_currency,
    _fmt_date,
    _load_tenant,
    _tenant_ctx,
)
from app.invoices.models import Invoice

logger = logging.getLogger(__name__)

# Template directory
_THIS_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = _THIS_DIR.parents[1] / "templates"
if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR = Path("/app/templates")

# Jinja2 environment for HTML templates
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def _fmt_quantity(value: Decimal) -> str:
    """Format quantity: integer if whole (2), decimal if fractional (1,50)."""
    if value == value.to_integral_value():
        return str(int(value))
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def render_invoice_pdf(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice: Invoice,
) -> tuple[bytes, str]:
    """Render an invoice as a PDF.

    Args:
        db: Database session.
        tenant_id: Current tenant ID.
        invoice: Invoice with lines eager-loaded.

    Returns:
        Tuple of (pdf_bytes, filename).
    """
    tenant = await _load_tenant(db, tenant_id)

    # Build line items context
    regels = [
        {
            "nummer": line.line_number,
            "omschrijving": line.description,
            "aantal": _fmt_quantity(line.quantity),
            "tarief": _fmt_currency(line.unit_price),
            "bedrag": _fmt_currency(line.line_total),
        }
        for line in invoice.lines
    ]

    # Calculate payment term in days
    days_until_due = (invoice.due_date - invoice.invoice_date).days
    if days_until_due < 1:
        days_until_due = 30  # fallback

    # BTW label
    btw_pct = invoice.btw_percentage
    if btw_pct == btw_pct.to_integral_value():
        btw_label = f"BTW ({int(btw_pct)}%)"
    else:
        btw_label = f"BTW ({btw_pct}%)"

    context = {
        "kantoor": _tenant_ctx(tenant),
        "klant": _contact_ctx(invoice.contact),
        "factuur": {
            "nummer": invoice.invoice_number,
            "datum": _fmt_date(invoice.invoice_date),
            "vervaldatum": _fmt_date(invoice.due_date),
            "kenmerk": invoice.reference or "",
            "zaaknummer": invoice.case.case_number if invoice.case else "",
        },
        "regels": regels,
        "subtotaal": _fmt_currency(invoice.subtotal),
        "btw_label": btw_label,
        "btw_bedrag": _fmt_currency(invoice.btw_amount),
        "totaal": _fmt_currency(invoice.total),
        "is_credit_note": invoice.invoice_type == "credit_note",
        "betaaltermijn_dagen": days_until_due,
        "notities": invoice.notes or "",
    }

    # Render HTML
    template = _jinja_env.get_template("factuur.html")
    html_string = template.render(context)

    # Convert to PDF
    pdf_bytes = weasyprint.HTML(
        string=html_string,
        base_url=str(TEMPLATES_DIR),
    ).write_pdf()

    filename = f"{invoice.invoice_number}.pdf"
    logger.info(
        "Invoice PDF generated: %s (%d bytes)", filename, len(pdf_bytes)
    )

    return pdf_bytes, filename
