"""Tests for renaming a case file — S203 #4.

The frontend PATCHed /api/cases/{case_id}/files/{file_id}, but that endpoint did
not exist (405) → "Hernoemen" was a dead button. These tests cover the new route.
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.cases.models import Case, CaseFile
from app.relations.models import Contact


async def _create_case_with_file(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> CaseFile:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Test Client B.V.",
        email="client@example.nl",
    )
    db.add(contact)
    await db.flush()
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-09001",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date(2026, 1, 15),
        client_id=contact.id,
    )
    db.add(case)
    await db.flush()
    case_file = CaseFile(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case.id,
        original_filename="oude-naam.pdf",
        stored_filename=f"{uuid.uuid4()}.pdf",
        file_size=1234,
        content_type="application/pdf",
        uploaded_by=user_id,
    )
    db.add(case_file)
    await db.commit()
    return case_file


@pytest.mark.asyncio
async def test_rename_case_file(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    cf = await _create_case_with_file(db, test_tenant.id, test_user.id)

    resp = await client.patch(
        f"/api/cases/{cf.case_id}/files/{cf.id}",
        json={"original_filename": "nieuwe-naam.pdf"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["original_filename"] == "nieuwe-naam.pdf"


@pytest.mark.asyncio
async def test_rename_nonexistent_file(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    cf = await _create_case_with_file(db, test_tenant.id, test_user.id)
    resp = await client.patch(
        f"/api/cases/{cf.case_id}/files/{uuid.uuid4()}",
        json={"original_filename": "x.pdf"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rename_rejects_empty(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    cf = await _create_case_with_file(db, test_tenant.id, test_user.id)
    resp = await client.patch(
        f"/api/cases/{cf.case_id}/files/{cf.id}",
        json={"original_filename": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rename_cross_tenant_blocked(
    client: AsyncClient, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    cf = await _create_case_with_file(db, test_tenant.id, test_user.id)

    other_tenant = Tenant(id=uuid.uuid4(), name="Other Firm", slug="other-firm")
    db.add(other_tenant)
    await db.flush()
    other_user = User(
        id=uuid.uuid4(),
        tenant_id=other_tenant.id,
        email="other@otherfirm.nl",
        hashed_password=hash_password("password123"),
        full_name="Other User",
        role="admin",
    )
    db.add(other_user)
    await db.commit()
    other_headers = {
        "Authorization": f"Bearer {create_access_token(str(other_user.id), str(other_tenant.id))}"
    }

    resp = await client.patch(
        f"/api/cases/{cf.case_id}/files/{cf.id}",
        json={"original_filename": "hacked.pdf"},
        headers=other_headers,
    )
    assert resp.status_code == 404
