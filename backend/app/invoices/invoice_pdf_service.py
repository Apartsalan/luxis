"""Invoice PDF rendering — generates professional A4 PDF invoices via WeasyPrint.

Uses Jinja2 HTML template + WeasyPrint for pixel-perfect PDF output.
All financial values are pre-formatted as Dutch currency strings.
"""

import logging
import uuid
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import jinja2
import weasyprint
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.docx_service import (
    _contact_ctx,
    _fmt_currency,
    _fmt_date,
    _tenant_ctx,
    load_tenant,
)
from app.invoices.models import Invoice

from weasyprint import default_url_fetcher

logger = logging.getLogger(__name__)


def _safe_url_fetcher(url: str, timeout: int = 10, ssl_context=None):
    """URL fetcher that blocks external requests to prevent SSRF."""
    if url.startswith("file://") or url.startswith("data:"):
        return default_url_fetcher(url, timeout=timeout, ssl_context=ssl_context)
    logger.warning("WeasyPrint blocked external URL: %s", url)
    return {"string": "", "mime_type": "text/plain"}

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
    tenant = await load_tenant(db, tenant_id)

    # Build line items context (DF2-03: include per-line BTW)
    regels = [
        {
            "nummer": line.line_number,
            "omschrijving": line.description,
            "aantal": _fmt_quantity(line.quantity),
            "tarief": _fmt_currency(line.unit_price),
            "bedrag": _fmt_currency(line.line_total),
            "btw_pct": line.btw_percentage,
        }
        for line in invoice.lines
    ]

    # Calculate payment term in days
    days_until_due = (invoice.due_date - invoice.invoice_date).days
    if days_until_due < 1:
        days_until_due = 30  # fallback

    # DF2-03: BTW groups — group lines by rate, calculate per-group totals
    btw_group_totals: dict[Decimal, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for line in invoice.lines:
        btw_group_totals[line.btw_percentage] += line.line_total

    btw_groups = []
    for pct in sorted(btw_group_totals.keys()):
        group_subtotal = btw_group_totals[pct]
        group_btw = (group_subtotal * pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        pct_label = f"{int(pct)}%" if pct == pct.to_integral_value() else f"{pct}%"
        btw_groups.append(
            {
                "tarief": pct_label,
                "subtotaal": _fmt_currency(group_subtotal),
                "btw_bedrag": _fmt_currency(group_btw),
            }
        )

    # Smart label: single rate = simple, multiple rates = breakdown
    has_mixed_rates = len(btw_groups) > 1
    if not has_mixed_rates and btw_groups:
        btw_label = f"BTW ({btw_groups[0]['tarief']})"
    else:
        btw_label = "BTW"

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
        "btw_groups": btw_groups,
        "has_mixed_rates": has_mixed_rates,
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
        url_fetcher=_safe_url_fetcher,
    ).write_pdf()

    filename = f"{invoice.invoice_number}.pdf"
    logger.info("Invoice PDF generated: %s (%d bytes)", filename, len(pdf_bytes))

    return pdf_bytes, filename
