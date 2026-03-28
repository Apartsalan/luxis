"""Docx template rendering service — generates Word documents from .docx templates.

Uses docxtpl to render Jinja2 tags inside Word templates.
Templates live in the project-root templates/ directory.

All financial values are pre-formatted as Dutch currency strings before
being passed to the template, so the templates contain no formatting logic.
"""

import io
import uuid
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from docxtpl import DocxTemplate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.service import (
    get_financial_summary,
    list_claims,
    list_payments,
)
from app.collections.wik import calculate_bik
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError, NotFoundError

# Templates directory: project_root/templates/
# In Docker (dev): mounted at /app/templates via docker-compose.dev.yml
# Fallback: relative to this file (../../templates from backend/app/documents/)
_THIS_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = _THIS_DIR.parents[2] / "templates"
if not TEMPLATES_DIR.exists():
    # Docker production layout: /app/templates
    TEMPLATES_DIR = Path("/app/templates")

# Available template types and their file names
TEMPLATE_FILES = {
    "14_dagenbrief": "14_dagenbrief.docx",
    "sommatie": "sommatie.docx",
    "renteoverzicht": "renteoverzicht.docx",
    "herinnering": "herinnering.docx",
    "aanmaning": "aanmaning.docx",
    "tweede_sommatie": "tweede_sommatie.docx",
    "dagvaarding": "dagvaarding.docx",
}

INTEREST_TYPE_LABELS = {
    "statutory": "Wettelijke rente (art. 6:119 BW)",
    "commercial": "Handelsrente (art. 6:119a BW)",
    "government": "Overheidsrente (art. 6:119b BW)",
    "contractual": "Contractuele rente",
}

DEBTOR_TYPE_LABELS = {
    "b2b": "Zakelijk (B2B)",
    "b2c": "Particulier (B2C)",
}

CASE_TYPE_LABELS = {
    "incasso": "Incasso",
    "dossier": "Dossier",
    "advies": "Advies",
}

# Merge field definitions — used by the /merge-fields endpoint
# Each category has a label and a list of (field_key, nl_label) tuples.
MERGE_FIELD_DEFINITIONS: dict[str, dict] = {
    "kantoor": {
        "label": "Kantoor",
        "fields": [
            ("kantoor.naam", "Kantoornaam"),
            ("kantoor.adres", "Adres"),
            ("kantoor.postcode_stad", "Postcode + Stad"),
            ("kantoor.kvk", "KVK-nummer"),
            ("kantoor.btw", "BTW-nummer"),
            ("kantoor.iban", "IBAN"),
            ("kantoor.telefoon", "Telefoonnummer"),
            ("kantoor.email", "E-mailadres"),
        ],
    },
    "zaak": {
        "label": "Zaak",
        "fields": [
            ("zaak.zaaknummer", "Zaaknummer"),
            ("zaak.type", "Zaaktype"),
            ("zaak.type_label", "Zaaktype (label)"),
            ("zaak.status", "Status"),
            ("zaak.debtor_type", "Debiteurtype (b2b/b2c)"),
            ("zaak.debtor_type_label", "Debiteurtype (label)"),
            ("zaak.referentie_regel", "Referentieregel"),
            ("zaak.omschrijving", "Omschrijving"),
            ("zaak.datum_geopend", "Datum geopend"),
        ],
    },
    "client": {
        "label": "Client (opdrachtgever)",
        "fields": [
            ("client.naam", "Naam"),
            ("client.adres", "Adres"),
            ("client.postcode_stad", "Postcode + Stad"),
            ("client.email", "E-mailadres"),
            ("client.telefoon", "Telefoonnummer"),
            ("client.kvk", "KVK-nummer"),
        ],
    },
    "wederpartij": {
        "label": "Wederpartij (debiteur)",
        "fields": [
            ("wederpartij.naam", "Naam"),
            ("wederpartij.adres", "Adres"),
            ("wederpartij.postcode_stad", "Postcode + Stad"),
            ("wederpartij.email", "E-mailadres"),
            ("wederpartij.telefoon", "Telefoonnummer"),
            ("wederpartij.kvk", "KVK-nummer"),
        ],
    },
    "financieel": {
        "label": "Financieel",
        "fields": [
            ("totaal_hoofdsom", "Totaal hoofdsom"),
            ("totaal_rente", "Totaal rente"),
            ("rente_type_label", "Type rente (label)"),
            ("bik_bedrag", "BIK bedrag (excl. BTW)"),
            ("btw_regel_label", "BTW-regel label"),
            ("btw_regel_bedrag", "BTW-regel bedrag"),
            ("totaal_bik", "Totaal BIK (incl. BTW)"),
            ("totaal_verschuldigd", "Totaal verschuldigd"),
            ("totaal_openstaand", "Totaal openstaand"),
            ("subtotaal", "Subtotaal"),
        ],
    },
    "datum": {
        "label": "Datums",
        "fields": [
            ("vandaag", "Datum vandaag"),
            ("termijn_14_dagen", "Termijn 14 dagen"),
            ("termijn_30_dagen", "Termijn 30 dagen"),
        ],
    },
    "lijsten": {
        "label": "Lijsten (voor tabellen)",
        "fields": [
            ("vorderingen[]", "Vorderingen (beschrijving, factuurnummer, verzuimdatum, hoofdsom)"),
            ("betalingen[]", "Betalingen (datum, beschrijving, bedrag)"),
            ("rente_regels[]", "Renteperiodes (van, tot, dagen, tarief, hoofdsom, rente)"),
        ],
    },
}


# ── Formatting helpers ─────────────────────────────────────────────────────


def _fmt_currency(value: Decimal | int | float | None) -> str:
    """Format value as Dutch currency: EUR 1.234,56."""
    if value is None:
        return "EUR 0,00"
    d = Decimal(str(value))
    formatted = f"{d:,.2f}"
    # 1,234.56 → 1.234,56
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"EUR {formatted}"


def _fmt_date(value: date | str | None) -> str:
    """Format date as Dutch: 17 februari 2026."""
    if value is None:
        return ""
    months = [
        "",
        "januari",
        "februari",
        "maart",
        "april",
        "mei",
        "juni",
        "juli",
        "augustus",
        "september",
        "oktober",
        "november",
        "december",
    ]
    if isinstance(value, str):
        parts = value.split("-")
        return f"{int(parts[2])} {months[int(parts[1])]} {parts[0]}"
    return f"{value.day} {months[value.month]} {value.year}"


def _fmt_pct(value: Decimal | float | None) -> str:
    """Format percentage: 6,00%."""
    if value is None:
        return "0,00%"
    d = Decimal(str(value))
    return f"{d:,.2f}%".replace(".", ",")


def _contact_ctx(contact: Contact | None) -> dict:
    """Build template context dict for a contact."""
    if contact is None:
        return {
            "naam": "",
            "adres": "",
            "postcode_stad": "",
            "email": "",
            "telefoon": "",
            "kvk": "",
        }
    postcode = contact.visit_postcode or ""
    stad = contact.visit_city or ""
    postcode_stad = f"{postcode} {stad}".strip() if postcode or stad else ""
    return {
        "naam": contact.name or "",
        "adres": contact.visit_address or "",
        "postcode_stad": postcode_stad,
        "email": contact.email or "",
        "telefoon": contact.phone or "",
        "kvk": contact.kvk_number or "",
    }


def _tenant_ctx(tenant: Tenant | None) -> dict:
    """Build template context dict for the tenant (kantoor)."""
    if tenant is None:
        return {
            "naam": "",
            "adres": "",
            "postcode_stad": "",
            "kvk": "",
            "btw": "",
            "iban": "",
            "telefoon": "",
            "email": "",
        }
    postcode = tenant.postal_code or ""
    stad = tenant.city or ""
    postcode_stad = f"{postcode} {stad}".strip() if postcode or stad else ""
    return {
        "naam": tenant.name or "",
        "adres": tenant.address or "",
        "postcode_stad": postcode_stad,
        "kvk": tenant.kvk_number or "",
        "btw": tenant.btw_number or "",
        "iban": tenant.iban or "",
        "telefoon": tenant.phone or "",
        "email": tenant.email or "",
    }


# ── Context builders per template type ─────────────────────────────────────


async def load_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
    """Load the tenant for kantoor merge fields."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def build_base_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
) -> dict:
    """Build the shared context used by all templates.

    Public so that incasso email templates can reuse the same context data.
    """
    today = date.today()

    # Load tenant for kantoor fields
    tenant = await load_tenant(db, tenant_id)

    claims = await list_claims(db, tenant_id, case.id)
    payments = await list_payments(db, tenant_id, case.id)

    financieel = await get_financial_summary(
        db=db,
        tenant_id=tenant_id,
        case_id=case.id,
        interest_type=case.interest_type,
        contractual_rate=(Decimal(str(case.contractual_rate)) if case.contractual_rate else None),
        contractual_compound=case.contractual_compound,
        calc_date=today,
    )

    total_principal = sum(c.principal_amount for c in claims)
    bik = calculate_bik(total_principal)

    # Pre-format claims for template
    vorderingen = [
        {
            "beschrijving": c.description,
            "factuurnummer": c.invoice_number or "",
            "verzuimdatum": _fmt_date(c.default_date),
            "hoofdsom": _fmt_currency(c.principal_amount),
        }
        for c in claims
    ]

    # Pre-format payments
    betalingen_list = [
        {
            "datum": _fmt_date(p.payment_date),
            "beschrijving": p.description or "",
            "bedrag": _fmt_currency(p.amount),
        }
        for p in payments
    ]

    # Reference line (only if present)
    ref_regel = f"Uw kenmerk: {case.reference}" if case.reference else ""

    # Interest type label (available in all templates)
    rente_type_label = INTEREST_TYPE_LABELS.get(case.interest_type, case.interest_type)

    # BTW conditional fields
    has_btw = bik["btw_amount"] > 0
    btw_regel_label = "BTW over BIK (21%)" if has_btw else ""
    btw_regel_bedrag = _fmt_currency(bik["btw_amount"]) if has_btw else ""
    btw_toelichting = (
        f" (vermeerderd met {_fmt_currency(bik['btw_amount'])} BTW)" if has_btw else ""
    )

    # Payments conditional fields
    total_paid = financieel["total_paid"]
    has_payments = total_paid > 0
    betalingen_regel_label = "Af: reeds ontvangen betalingen" if has_payments else ""
    betalingen_regel_bedrag = f"-{_fmt_currency(total_paid)}" if has_payments else ""

    return {
        # Kantoor (tenant)
        "kantoor": _tenant_ctx(tenant),
        # Zaak — extended with type, status, debtor_type, datum_geopend
        "zaak": {
            "zaaknummer": case.case_number,
            "type": case.case_type,
            "type_label": CASE_TYPE_LABELS.get(case.case_type, case.case_type),
            "status": case.status,
            "debtor_type": getattr(case, "debtor_type", "b2b"),
            "debtor_type_label": DEBTOR_TYPE_LABELS.get(
                getattr(case, "debtor_type", "b2b"), "Zakelijk (B2B)"
            ),
            "referentie_regel": ref_regel,
            "omschrijving": case.description or "",
            "datum_geopend": _fmt_date(case.date_opened),
        },
        # Contacts
        "client": _contact_ctx(case.client),
        "wederpartij": _contact_ctx(case.opposing_party),
        # Dates
        "vandaag": _fmt_date(today),
        # Art. 6:96 lid 6 BW: 14 dagen na ontvangst (dag NA ontvangst, +1 voor postbezorging)
        "termijn_14_dagen": _fmt_date(today + timedelta(days=15)),
        "termijn_30_dagen": _fmt_date(today + timedelta(days=30)),
        # Financial — interest type label now in base context
        "rente_type_label": rente_type_label,
        # Lists
        "vorderingen": vorderingen,
        "betalingen": betalingen_list,
        # Financial totals
        "totaal_hoofdsom": _fmt_currency(financieel["total_principal"]),
        "totaal_rente": _fmt_currency(financieel["total_interest"]),
        "bik_bedrag": _fmt_currency(bik["bik_exclusive"]),
        "btw_regel_label": btw_regel_label,
        "btw_regel_bedrag": btw_regel_bedrag,
        "btw_toelichting": btw_toelichting,
        "totaal_bik": _fmt_currency(financieel["total_bik"]),
        "totaal_verschuldigd": _fmt_currency(financieel["grand_total"]),
        "totaal_openstaand": _fmt_currency(financieel["total_outstanding"]),
        "subtotaal": _fmt_currency(financieel["grand_total"]),
        "betalingen_regel_label": betalingen_regel_label,
        "betalingen_regel_bedrag": betalingen_regel_bedrag,
        "betalingen_aftrek_label": ("Af: ontvangen betalingen" if has_payments else ""),
        "betalingen_aftrek_bedrag": (f"-{_fmt_currency(total_paid)}" if has_payments else ""),
        # Raw financials for programmatic access
        "_financieel": financieel,
        "_bik": bik,
    }


async def _build_renteoverzicht_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
) -> dict:
    """Build extra context for the renteoverzicht template."""
    base = await build_base_context(db, tenant_id, case)
    financieel = base["_financieel"]

    # Flatten interest periods across all claims into one list
    rente_regels = []
    interest_details = financieel.get("interest_details", {})
    claims_details = interest_details.get("claims", [])

    for claim_detail in claims_details:
        periods = claim_detail.get("periods", [])
        for p in periods:
            rente_regels.append(
                {
                    "van": _fmt_date(p.get("start_date")),
                    "tot": _fmt_date(p.get("end_date")),
                    "dagen": str(p.get("days", 0)),
                    "tarief": _fmt_pct(p.get("rate")),
                    "hoofdsom": _fmt_currency(p.get("principal")),
                    "rente": _fmt_currency(p.get("interest")),
                }
            )

    # BIK inclusive fields
    bik = base["_bik"]
    has_btw = bik["btw_amount"] > 0
    bik_incl_label = "BIK (incl. BTW)" if has_btw else ""
    bik_incl_bedrag = _fmt_currency(bik["bik_inclusive"]) if has_btw else ""

    # Payments heading
    betalingen_kop = "Ontvangen betalingen" if base["betalingen"] else "Betalingen"

    base.update(
        {
            "rente_regels": rente_regels,
            "bik_incl_label": bik_incl_label,
            "bik_incl_bedrag": bik_incl_bedrag,
            "betalingen_kop": betalingen_kop,
        }
    )

    return base


# ── Merge field definitions (for field picker endpoint) ───────────────────


def get_merge_field_definitions() -> dict[str, dict]:
    """Return all merge field definitions grouped by category with NL labels.

    Used by the GET /api/documents/merge-fields endpoint.
    """
    return MERGE_FIELD_DEFINITIONS


# ── Public API ─────────────────────────────────────────────────────────────


def get_available_templates() -> list[dict]:
    """Return list of available docx template types."""
    result = []
    for ttype, filename in TEMPLATE_FILES.items():
        path = TEMPLATES_DIR / filename
        result.append(
            {
                "template_type": ttype,
                "filename": filename,
                "available": path.exists(),
            }
        )
    return result


async def render_docx(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    template_type: str,
    pre_built_context: dict | None = None,
) -> tuple[bytes, str, str, bytes]:
    """Render a .docx template with case data.

    Checks ManagedTemplate table first (custom > builtin),
    falls back to disk files if not found.

    Args:
        pre_built_context: Optional pre-built context from build_base_context().
            If provided, skips internal context building (avoids duplicate DB queries).

    Returns:
        Tuple of (docx_bytes, filename, template_type, template_snapshot)
    """
    from app.documents.template_service import get_template_by_key

    # Try managed template first
    managed = await get_template_by_key(db, tenant_id, template_type)

    if managed:
        template_snapshot = managed.file_data
        try:
            tpl = DocxTemplate(io.BytesIO(template_snapshot))
        except Exception as e:
            raise BadRequestError(f"Fout bij laden sjabloon: {e}")
    else:
        # Fallback to disk files
        if template_type not in TEMPLATE_FILES:
            raise NotFoundError(
                f"Onbekend sjabloontype: {template_type}. "
                f"Beschikbaar: "
                f"{', '.join(TEMPLATE_FILES.keys())}"
            )
        template_path = TEMPLATES_DIR / TEMPLATE_FILES[template_type]
        if not template_path.exists():
            raise NotFoundError(f"Sjabloonbestand niet gevonden: {template_path}")
        template_snapshot = template_path.read_bytes()
        tpl = DocxTemplate(str(template_path))

    # Build context based on template type (skip if pre-built context provided)
    if pre_built_context is not None:
        context = pre_built_context
    elif template_type == "renteoverzicht":
        context = await _build_renteoverzicht_context(db, tenant_id, case)
    else:
        context = await build_base_context(db, tenant_id, case)

    # Remove internal keys (prefixed with _)
    render_context = {k: v for k, v in context.items() if not k.startswith("_")}

    # Render
    try:
        tpl.render(render_context)
    except Exception as e:
        raise BadRequestError(f"Fout bij renderen sjabloon: {e}")

    # Save to bytes
    buffer = io.BytesIO()
    tpl.save(buffer)
    docx_bytes = buffer.getvalue()

    # Generate filename
    today_str = date.today().isoformat()
    filename = f"{template_type}_{case.case_number}_{today_str}.docx"

    return docx_bytes, filename, template_type, template_snapshot
