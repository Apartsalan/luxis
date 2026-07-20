"""S233: GET /api/email/compose/cases/{id}/invoice-files.

De AI-antwoord-flow gebruikt dit endpoint om, wanneer de behandelaar "doe de
facturen erbij" vroeg, de factuur-PDF's van het dossier vooraf aan te vinken.
Levert de factuurbestanden (Claim.invoice_file_id → CaseFile) route-onafhankelijk,
i.t.t. /auto-attachments dat alleen bij een sommatie-sjabloon factuur-PDF's toont.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case, CaseFile
from app.collections.models import Claim
from app.relations.models import Contact


@pytest_asyncio.fixture
async def case_with_invoice(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact, test_user: User
) -> tuple[Case, CaseFile]:
    """Incasso-dossier met één claim die naar een factuur-PDF (CaseFile) wijst."""
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number=f"{date.today().year}-00500",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        client_id=test_company.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()

    invoice_file = CaseFile(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case.id,
        original_filename="factuur-2026-001.pdf",
        stored_filename="stored-abc.pdf",
        file_size=12345,
        content_type="application/pdf",
        uploaded_by=test_user.id,
    )
    db.add(invoice_file)
    await db.flush()

    claim = Claim(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case.id,
        description="Factuur 2026-001",
        principal_amount=Decimal("1000.00"),
        default_date=date(2026, 1, 1),
        invoice_file_id=invoice_file.id,
    )
    db.add(claim)
    await db.commit()
    return case, invoice_file


@pytest.mark.asyncio
async def test_invoice_files_returns_case_invoices(
    client: AsyncClient, auth_headers: dict, case_with_invoice: tuple[Case, CaseFile]
):
    case, invoice_file = case_with_invoice
    resp = await client.get(
        f"/api/email/compose/cases/{case.id}/invoice-files", headers=auth_headers
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(invoice_file.id)
    assert items[0]["filename"] == "factuur-2026-001.pdf"
    assert items[0]["size"] == 12345


@pytest.mark.asyncio
async def test_invoice_files_empty_when_no_invoice_linked(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
):
    """Dossier zonder factuur-koppeling → lege lijst (geen valse voorselectie)."""
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number=f"{date.today().year}-00501",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        client_id=test_company.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Claim zonder factuurbestand",
            principal_amount=Decimal("500.00"),
            default_date=date(2026, 1, 1),
        )
    )
    await db.commit()

    resp = await client.get(
        f"/api/email/compose/cases/{case.id}/invoice-files", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_invoice_files_unknown_case_404(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.get(
        f"/api/email/compose/cases/{uuid.uuid4()}/invoice-files", headers=auth_headers
    )
    assert resp.status_code == 404
