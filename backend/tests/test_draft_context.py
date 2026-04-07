"""Tests for the AI draft context gatherer (DF117-03).

Lisanne demo 2026-04-07: when the AI generates a message proposal, it must
have access to ALL relevant case data — not just the basics — so it can
reference specific facts: invoice numbers, AV articles, contract clauses.

These tests verify that `_gather_case_context()` and `_build_draft_prompt()`
correctly load and surface:
- claims (vorderingen)
- invoices on the case
- recent emails
- client AV (algemene voorwaarden)
- uploaded case files (contracts, agreements, etc.) — DF117-03 new
"""

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.draft_service import _build_draft_prompt, _gather_case_context
from app.auth.models import Tenant, User
from app.cases.models import Case, CaseFile
from app.collections.models import Claim
from app.invoices.models import Invoice, InvoiceLine
from app.relations.models import Contact


@pytest_asyncio.fixture
async def case_with_data(
    db: AsyncSession, test_tenant: Tenant, test_user: User
) -> Case:
    """Build a case with: client (with AV), debtor, claim, invoice, case file."""
    # Client with AV
    client = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Cliënt BV",
        email="info@client.nl",
        terms_file_path="/tmp/fake_av.pdf",  # Will be mocked
        terms_file_name="algemene_voorwaarden.pdf",
    )
    debtor = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Debiteur BV",
        email="info@debiteur.nl",
    )
    db.add_all([client, debtor])
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number=f"{date.today().year}-99001",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        interest_type="statutory",
        contractual_compound=True,
        client_id=client.id,
        opposing_party_id=debtor.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()

    # Claim
    claim = Claim(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case.id,
        description="Onbetaalde factuur 2026-001",
        principal_amount=Decimal("5000.00"),
        invoice_number="2026-001",
        invoice_date=date(2026, 1, 15),
        default_date=date(2026, 2, 15),
    )
    db.add(claim)

    # Invoice on the case
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        invoice_number="F2026-00001",
        invoice_type="invoice",
        status="sent",
        contact_id=client.id,
        case_id=case.id,
        invoice_date=date(2026, 3, 1),
        due_date=date(2026, 3, 31),
        subtotal=Decimal("500.00"),
        btw_percentage=Decimal("21.00"),
        btw_amount=Decimal("105.00"),
        total=Decimal("605.00"),
    )
    db.add(invoice)

    await db.commit()
    await db.refresh(case)
    return case


# ─── Existing context (baseline) still works ──────────────────────────────


@pytest.mark.asyncio
async def test_gather_context_returns_basic_case_info(
    db: AsyncSession, test_tenant: Tenant, case_with_data: Case
):
    """Sanity check: the basic case fields are still gathered correctly."""
    # Mock PDF extraction so the test doesn't need a real PDF on disk
    with patch("app.ai_agent.draft_service.extract_text_from_pdf", return_value=""):
        context = await _gather_case_context(db, test_tenant.id, case_with_data.id)

    assert context["case_number"] == case_with_data.case_number
    assert context["case_type"] == "incasso"
    assert context["status"] == "nieuw"
    assert len(context["claims"]) == 1
    assert context["claims"][0]["invoice_number"] == "2026-001"
    assert context["claims"][0]["principal"] == "5000.00"


# ─── DF117-03: invoices on the case ───────────────────────────────────────


@pytest.mark.asyncio
async def test_gather_context_includes_case_invoices(
    db: AsyncSession, test_tenant: Tenant, case_with_data: Case
):
    """Invoices on the case should be loaded so the AI can reference what
    has actually been billed (separate from the underlying claims)."""
    with patch("app.ai_agent.draft_service.extract_text_from_pdf", return_value=""):
        context = await _gather_case_context(db, test_tenant.id, case_with_data.id)

    assert "invoices" in context
    assert len(context["invoices"]) == 1
    inv = context["invoices"][0]
    assert inv["invoice_number"] == "F2026-00001"
    assert inv["invoice_type"] == "invoice"
    assert inv["status"] == "sent"
    assert inv["total"] == "605.00"


# ─── DF117-03: terms / AV ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gather_context_includes_terms_text(
    db: AsyncSession, test_tenant: Tenant, case_with_data: Case
):
    """The client's AV text should be loaded and trimmed to ~3000 chars."""
    fake_terms = "Artikel 5.2 — Bij niet-tijdige betaling is een rente van 8% verschuldigd."
    with patch(
        "app.ai_agent.draft_service.extract_text_from_pdf",
        return_value=fake_terms,
    ):
        context = await _gather_case_context(db, test_tenant.id, case_with_data.id)

    assert context["terms_text"] is not None
    assert "Artikel 5.2" in context["terms_text"]


# ─── DF117-03: case files (overeenkomsten / contracts) ──────────────────


@pytest.mark.asyncio
async def test_gather_context_includes_pdf_case_files(
    db: AsyncSession, test_tenant: Tenant, test_user: User, case_with_data: Case
):
    """Uploaded case files (PDFs only) should be extracted and surfaced
    so the AI can quote from contracts / overeenkomsten."""
    case_file = CaseFile(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case_with_data.id,
        original_filename="overeenkomst.pdf",
        stored_filename="abc-overeenkomst.pdf",
        file_size=1234,
        content_type="application/pdf",
        document_direction="inkomend",
        description="Overeenkomst client en debiteur",
        uploaded_by=test_user.id,
    )
    db.add(case_file)
    await db.commit()

    fake_contract_text = (
        "OVEREENKOMST DD. 12-03-2024\n\n"
        "Artikel 3 — Leveringsvoorwaarden: betaling binnen 14 dagen.\n"
        "Artikel 4 — Bij wanbetaling is debiteur direct in verzuim."
    )
    with patch(
        "app.ai_agent.draft_service.extract_text_from_pdf",
        return_value=fake_contract_text,
    ), patch(
        "app.ai_agent.draft_service.get_file_path",
        return_value=Path("/tmp/fake_contract.pdf"),
    ), patch("pathlib.Path.exists", return_value=True):
        context = await _gather_case_context(db, test_tenant.id, case_with_data.id)

    assert "case_files" in context
    assert len(context["case_files"]) == 1
    cf = context["case_files"][0]
    assert cf["filename"] == "overeenkomst.pdf"
    assert cf["description"] == "Overeenkomst client en debiteur"
    assert cf["direction"] == "inkomend"
    assert "Artikel 3" in cf["excerpt"]
    assert "Artikel 4" in cf["excerpt"]


@pytest.mark.asyncio
async def test_gather_context_skips_non_pdf_case_files(
    db: AsyncSession, test_tenant: Tenant, test_user: User, case_with_data: Case
):
    """Word docs and images should be skipped silently — only PDFs are extracted."""
    case_file = CaseFile(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case_with_data.id,
        original_filename="screenshot.png",
        stored_filename="xyz-screenshot.png",
        file_size=5000,
        content_type="image/png",
        uploaded_by=test_user.id,
    )
    db.add(case_file)
    await db.commit()

    with patch("app.ai_agent.draft_service.extract_text_from_pdf", return_value=""):
        context = await _gather_case_context(db, test_tenant.id, case_with_data.id)

    assert context["case_files"] == []


# ─── DF117-03: prompt builder uses the new context ────────────────────────


def test_prompt_builder_includes_invoices_and_case_files():
    """The user message that goes to the AI must surface invoices and case files
    so the AI can actually use them when writing the draft."""
    context = {
        "case_number": "2026-99001",
        "case_type": "incasso",
        "status": "nieuw",
        "client": {"name": "Cliënt BV"},
        "opposing_party": {"name": "Debiteur BV", "type": "company"},
        "description": None,
        "total_principal": "5000.00",
        "total_paid": "0.00",
        "claims": [],
        "emails": [],
        "invoices": [
            {
                "invoice_number": "F2026-00001",
                "invoice_type": "invoice",
                "status": "sent",
                "invoice_date": "2026-03-01",
                "due_date": "2026-03-31",
                "total": "605.00",
            }
        ],
        "terms_text": None,
        "case_files": [
            {
                "filename": "overeenkomst.pdf",
                "description": "Overeenkomst client en debiteur",
                "direction": "inkomend",
                "excerpt": "Artikel 3 — Betaling binnen 14 dagen.",
            }
        ],
    }
    prompt = _build_draft_prompt(context, instruction=None)

    # Invoice section
    assert "Facturen op dit dossier" in prompt
    assert "F2026-00001" in prompt
    assert "605.00" in prompt
    # Case files section
    assert "Documenten op dossier" in prompt
    assert "overeenkomst.pdf" in prompt
    assert "Artikel 3" in prompt
    assert "Overeenkomst client en debiteur" in prompt
