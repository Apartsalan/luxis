"""Tests for managed-template preview (AUDIT-H8).

The preview endpoint imported a non-existent symbol (`_build_base_context`
instead of `build_base_context`), so every preview of a non-"renteoverzicht"
template raised ImportError -> HTTP 500. The import sits inside the handler,
so it only fired when the endpoint was actually called.
"""

import io
import uuid
from datetime import date
from decimal import Decimal

import pytest
from docx import Document
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.models import InterestRate
from app.documents.models import ManagedTemplate
from app.relations.models import Contact


def _minimal_docx() -> bytes:
    """A valid, placeholder-free .docx that docxtpl can render as-is."""
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Sommatie test")
    doc.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_preview_non_renteoverzicht_template_renders(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
):
    """A 'sommatie' template preview must render (200), not crash with 500."""
    # build_base_context computes statutory interest -> needs a seeded rate
    db.add(
        InterestRate(
            id=uuid.uuid4(),
            rate_type="statutory",
            effective_from=date(2024, 1, 1),
            rate=Decimal("6.00"),
            source="Test fixture",
        )
    )

    # Seed a case
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-08001",
        description="Preview-test",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today(),
        total_principal=0,
        total_paid=0,
    )
    db.add(case)

    docx_bytes = _minimal_docx()
    template = ManagedTemplate(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Sommatie",
        template_key="sommatie",  # NOT 'renteoverzicht' -> hits build_base_context
        file_data=docx_bytes,
        original_filename="sommatie.docx",
        file_size=len(docx_bytes),
        is_builtin=False,
        is_active=True,
    )
    db.add(template)
    await db.commit()

    resp = await client.post(
        f"/api/documents/managed-templates/{template.id}/preview/{case.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )
