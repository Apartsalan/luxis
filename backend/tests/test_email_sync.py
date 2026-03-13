"""Tests for the email sync module — case emails, unlinked, link, dismiss, messages."""

import json
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.email.attachment_models import EmailAttachment
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(db: AsyncSession, tenant_id: uuid.UUID) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Test Debiteur B.V.",
        email="debiteur@test.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _create_case(
    db: AsyncSession, tenant_id: uuid.UUID, case_number: str = "2026-00001"
) -> Case:
    client = await _create_contact(db, tenant_id)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=datetime(2026, 1, 15).date(),
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def _create_email_account(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> EmailAccount:
    """Create a fake email account for test purposes."""
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        provider="gmail",
        email_address="test@gmail.com",
        access_token_enc=b"fake_access_token",
        refresh_token_enc=b"fake_refresh_token",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_synced_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    account_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    subject: str = "Test email",
    from_email: str = "sender@test.nl",
    is_dismissed: bool = False,
) -> SyncedEmail:
    """Insert a SyncedEmail record directly (no provider sync needed)."""
    email = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email_account_id=account_id,
        case_id=case_id,
        provider_message_id=f"msg_{uuid.uuid4().hex[:12]}",
        subject=subject,
        from_email=from_email,
        from_name="Test Sender",
        to_emails=json.dumps(["test@gmail.com"]),
        cc_emails=json.dumps([]),
        snippet=subject[:80],
        body_text=f"Body of: {subject}",
        body_html=f"<p>Body of: {subject}</p>",
        direction="inbound",
        is_read=True,
        has_attachments=False,
        is_dismissed=is_dismissed,
        email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.flush()
    await db.refresh(email)
    return email


# ── Case Emails ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_case_emails(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Getting emails for a case should return only linked emails."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id)

    # Create 2 linked + 1 unlinked email
    await _create_synced_email(db, test_tenant.id, account.id, case_id=case.id, subject="Linked 1")
    await _create_synced_email(db, test_tenant.id, account.id, case_id=case.id, subject="Linked 2")
    await _create_synced_email(db, test_tenant.id, account.id, subject="Unlinked")
    await db.commit()

    resp = await client.get(f"/api/email/cases/{case.id}/emails", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["emails"]) == 2


# ── Unlinked Emails ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_unlinked_emails(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Unlinked endpoint should return emails not linked and not dismissed."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id)

    # Linked (should NOT appear)
    await _create_synced_email(db, test_tenant.id, account.id, case_id=case.id)
    # Unlinked (should appear)
    await _create_synced_email(db, test_tenant.id, account.id, subject="Unlinked email")
    # Dismissed (should NOT appear)
    await _create_synced_email(db, test_tenant.id, account.id, is_dismissed=True)
    await db.commit()

    resp = await client.get("/api/email/unlinked", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["emails"][0]["subject"] == "Unlinked email"


@pytest.mark.asyncio
async def test_unlinked_count(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Unlinked count should return the number of unlinked, non-dismissed emails."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)

    await _create_synced_email(db, test_tenant.id, account.id, subject="Unlinked 1")
    await _create_synced_email(db, test_tenant.id, account.id, subject="Unlinked 2")
    await _create_synced_email(db, test_tenant.id, account.id, is_dismissed=True)
    await db.commit()

    resp = await client.get("/api/email/unlinked/count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


# ── Link Email ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_link_email_to_case(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Manually linking an email to a case should succeed."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id)
    email = await _create_synced_email(db, test_tenant.id, account.id, subject="To be linked")
    await db.commit()

    resp = await client.post(
        "/api/email/link",
        json={"email_id": str(email.id), "case_id": str(case.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify it now appears in case emails
    case_resp = await client.get(f"/api/email/cases/{case.id}/emails", headers=auth_headers)
    assert case_resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_link_nonexistent_email(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Linking a nonexistent email should fail (404)."""
    case = await _create_case(db, test_tenant.id)
    await db.commit()

    resp = await client.post(
        "/api/email/link",
        json={"email_id": str(uuid.uuid4()), "case_id": str(case.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── Bulk Link ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_link_emails(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Bulk linking multiple emails to a case should link all of them."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id)

    emails = []
    for i in range(3):
        e = await _create_synced_email(db, test_tenant.id, account.id, subject=f"Bulk {i}")
        emails.append(e)
    await db.commit()

    resp = await client.post(
        "/api/email/bulk-link",
        json={
            "email_ids": [str(e.id) for e in emails],
            "case_id": str(case.id),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["linked_count"] == 3


# ── Dismiss ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dismiss_emails(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Dismissing emails should remove them from the unlinked queue."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)

    emails = []
    for i in range(2):
        e = await _create_synced_email(db, test_tenant.id, account.id, subject=f"Dismiss {i}")
        emails.append(e)
    await db.commit()

    resp = await client.post(
        "/api/email/dismiss",
        json={"email_ids": [str(e.id) for e in emails]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["dismissed_count"] == 2

    # Verify they're gone from unlinked
    count_resp = await client.get("/api/email/unlinked/count", headers=auth_headers)
    assert count_resp.json()["count"] == 0


# ── Message Detail ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_email_detail(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Getting email detail should return full body and metadata."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(
        db, test_tenant.id, account.id, subject="Detail test"
    )
    await db.commit()

    resp = await client.get(f"/api/email/messages/{email.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["subject"] == "Detail test"
    assert "Body of: Detail test" in data["body_text"]
    assert data["direction"] == "inbound"


@pytest.mark.asyncio
async def test_get_nonexistent_email_detail(
    client: AsyncClient, auth_headers: dict,
):
    """Getting a nonexistent email should return 404."""
    resp = await client.get(
        f"/api/email/messages/{uuid.uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404


# ── Attachments ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_attachments(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Listing attachments for an email should return all attached files."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(
        db, test_tenant.id, account.id, subject="With attachment"
    )

    # Create an attachment record
    attachment = EmailAttachment(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        synced_email_id=email.id,
        provider_attachment_id="att_12345",
        filename="factuur.pdf",
        stored_filename=f"{uuid.uuid4()}.pdf",
        content_type="application/pdf",
        file_size=12345,
    )
    db.add(attachment)
    await db.commit()

    resp = await client.get(
        f"/api/email/messages/{email.id}/attachments", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["filename"] == "factuur.pdf"
    assert data["attachments"][0]["file_size"] == 12345


# ── Tenant Isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_email_tenant_isolation(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Emails from another tenant should not be visible."""
    from app.auth.service import create_access_token, hash_password

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    await _create_synced_email(db, test_tenant.id, account.id, subject="Tenant A email")

    # Create other tenant + user
    other_tenant = Tenant(
        id=uuid.uuid4(), name="Other Firm", slug="other-firm", kvk_number="99999999"
    )
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

    other_token = create_access_token(str(other_user.id), str(other_tenant.id))
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Other tenant should see 0 unlinked emails
    resp = await client.get("/api/email/unlinked/count", headers=other_headers)
    assert resp.json()["count"] == 0
