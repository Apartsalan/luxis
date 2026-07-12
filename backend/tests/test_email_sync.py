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
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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


# ── All Emails (volledige mailbox + zoeken) ──────────────────────────────────


@pytest.mark.asyncio
async def test_get_all_emails_filter_and_search(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """'/all' toont alles, filtert op koppelstatus en doorzoekt inhoud."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id)

    await _create_synced_email(
        db, test_tenant.id, account.id, case_id=case.id, subject="Sommatie Jansen"
    )
    await _create_synced_email(db, test_tenant.id, account.id, subject="Vraag van debiteur")
    await _create_synced_email(db, test_tenant.id, account.id, is_dismissed=True, subject="Genegeerd")
    await db.commit()

    # filter=all → gekoppeld + ongekoppeld, maar niet de genegeerde
    resp = await client.get("/api/email/all?filter=all&limit=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2

    # filter=linked → alleen de gekoppelde, mét dossiernummer
    resp = await client.get("/api/email/all?filter=linked", headers=auth_headers)
    linked = resp.json()
    assert linked["total"] == 1
    assert linked["emails"][0]["case_number"] == case.case_number

    # filter=unlinked → alleen de ongekoppelde
    resp = await client.get("/api/email/all?filter=unlinked", headers=auth_headers)
    assert resp.json()["total"] == 1

    # zoeken op onderwerp
    resp = await client.get("/api/email/all?search=Sommatie", headers=auth_headers)
    found = resp.json()
    assert found["total"] == 1
    assert found["emails"][0]["subject"] == "Sommatie Jansen"


# ── Link Email ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_link_email_to_case(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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


@pytest.mark.asyncio
async def test_rematch_respects_dismissed(
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Regressie S188c: de her-koppelronde mag een GENEGEERDE mail niet alsnog aan
    een dossier hangen. Een niet-genegeerde mail met dezelfde afzender wordt wél
    gekoppeld — zo bewijzen we dat het filter precies is en niets extra's breekt."""
    from app.email.sync_service import _rematch_unlinked_emails

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id)  # client-contact = debiteur@test.nl

    dismissed = await _create_synced_email(
        db, test_tenant.id, account.id, from_email="debiteur@test.nl", is_dismissed=True
    )
    active = await _create_synced_email(
        db, test_tenant.id, account.id, from_email="debiteur@test.nl", is_dismissed=False
    )
    await db.commit()

    linked = await _rematch_unlinked_emails(db, test_tenant.id)
    await db.refresh(dismissed)
    await db.refresh(active)

    assert linked == 1
    assert dismissed.case_id is None  # genegeerd blijft ongekoppeld
    assert active.case_id == case.id  # niet-genegeerd wordt wel gekoppeld


@pytest.mark.asyncio
async def test_load_forwarded_attachments_reads_and_skips_missing(
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    tmp_path,
    monkeypatch,
):
    """Doorsturen laadt de bijlagen van het origineel van schijf; een ontbrekend
    bestand wordt overgeslagen (geen crash) — S188c punt 2."""
    from app.email import compose_router
    from app.email.compose_router import _load_forwarded_attachments

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(db, test_tenant.id, account.id, subject="Met bijlage")
    db.add(
        EmailAttachment(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            provider_attachment_id="att-1",
            filename="factuur.pdf",
            stored_filename="abc.pdf",
            content_type="application/pdf",
            file_size=8,
        )
    )
    await db.commit()

    monkeypatch.setattr(compose_router, "EMAIL_ATTACHMENTS_BASE", tmp_path)
    dest = tmp_path / str(test_tenant.id) / str(email.id)
    dest.mkdir(parents=True)
    (dest / "abc.pdf").write_bytes(b"%PDF-1.4")

    out = await _load_forwarded_attachments(db, test_tenant.id, email.id)
    assert len(out) == 1
    assert out[0].filename == "factuur.pdf"
    assert out[0].data == b"%PDF-1.4"

    # Tweede bijlage met ontbrekend bestand → overgeslagen, rest blijft werken.
    db.add(
        EmailAttachment(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            provider_attachment_id="att-2",
            filename="weg.pdf",
            stored_filename="ontbreekt.pdf",
            content_type="application/pdf",
            file_size=1,
        )
    )
    await db.commit()
    out2 = await _load_forwarded_attachments(db, test_tenant.id, email.id)
    assert len(out2) == 1


# ── Message Detail ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_email_detail(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Getting email detail should return full body and metadata."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(db, test_tenant.id, account.id, subject="Detail test")
    await db.commit()

    resp = await client.get(f"/api/email/messages/{email.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["subject"] == "Detail test"
    assert "Body of: Detail test" in data["body_text"]
    assert data["direction"] == "inbound"


@pytest.mark.asyncio
async def test_get_nonexistent_email_detail(
    client: AsyncClient,
    auth_headers: dict,
):
    """Getting a nonexistent email should return 404."""
    resp = await client.get(f"/api/email/messages/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


# ── Attachments ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_attachments(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Listing attachments for an email should return all attached files."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(db, test_tenant.id, account.id, subject="With attachment")

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

    resp = await client.get(f"/api/email/messages/{email.id}/attachments", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["filename"] == "factuur.pdf"
    assert data["attachments"][0]["file_size"] == 12345


# ── Tenant Isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_email_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
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


# ── Cross-tenant link guard (AUDIT-MEDIUM) ────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_link_rejects_foreign_tenant_case(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """bulk_link_emails must refuse a case from another tenant (AUDIT-MEDIUM).

    Emails are tenant-scoped, but the target case_id was never validated against
    the tenant — a caller could attach their own emails to another tenant's
    dossier."""
    from app.email.sync_service import bulk_link_emails
    from app.shared.exceptions import NotFoundError

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(db, test_tenant.id, account.id, subject="Mine")

    other = Tenant(
        id=uuid.uuid4(), name="Other Firm A", slug="other-firm-a", kvk_number="11111111"
    )
    db.add(other)
    await db.flush()
    foreign_case = await _create_case(db, other.id, case_number="2026-99991")
    await db.flush()

    with pytest.raises(NotFoundError):
        await bulk_link_emails(db, test_tenant.id, [email.id], foreign_case.id)

    await db.refresh(email)
    assert email.case_id is None  # left untouched


@pytest.mark.asyncio
async def test_link_email_rejects_foreign_tenant_case(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Single link_email_to_case must also refuse a foreign-tenant case."""
    from app.email.sync_service import link_email_to_case
    from app.shared.exceptions import NotFoundError

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    email = await _create_synced_email(db, test_tenant.id, account.id, subject="Mine2")

    other = Tenant(
        id=uuid.uuid4(), name="Other Firm B", slug="other-firm-b", kvk_number="22222222"
    )
    db.add(other)
    await db.flush()
    foreign_case = await _create_case(db, other.id, case_number="2026-99992")
    await db.flush()

    with pytest.raises(NotFoundError):
        await link_email_to_case(db, test_tenant.id, email.id, foreign_case.id)

    await db.refresh(email)
    assert email.case_id is None


@pytest.mark.asyncio
async def test_bulk_link_same_tenant_still_works(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """The tenant guard must not break a normal same-tenant bulk link."""
    from app.email.sync_service import bulk_link_emails

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id, case_number="2026-00050")
    e1 = await _create_synced_email(db, test_tenant.id, account.id, subject="A")
    e2 = await _create_synced_email(db, test_tenant.id, account.id, subject="B")

    count = await bulk_link_emails(db, test_tenant.id, [e1.id, e2.id], case.id)
    assert count == 2
    await db.refresh(e1)
    await db.refresh(e2)
    assert e1.case_id == case.id
    assert e2.case_id == case.id


# ── save_attachment_to_case cross-tenant guard (AUDIT-H1) ─────────────────────


async def _make_attachment_with_file(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, attach_base
) -> tuple[EmailAttachment, "SyncedEmail"]:
    """Create an attachment record + a real source file on disk under attach_base."""
    account = await _create_email_account(db, tenant_id, user_id)
    email = await _create_synced_email(db, tenant_id, account.id, subject="Met bijlage")
    stored = f"{uuid.uuid4()}.pdf"
    attachment = EmailAttachment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        synced_email_id=email.id,
        provider_attachment_id="att-h1",
        filename="geheim.pdf",
        stored_filename=stored,
        content_type="application/pdf",
        file_size=8,
    )
    db.add(attachment)
    src_dir = attach_base / str(tenant_id) / str(email.id)
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / stored).write_bytes(b"%PDF-1.4")
    return attachment, email


async def _count_case_files(session_factory, case_id: uuid.UUID) -> int:
    """Count CaseFile rows for a case via a FRESH session — the shared request
    session is left in a rolled-back state after a 4xx and cannot be reused."""
    from sqlalchemy import func
    from sqlalchemy import select as sa_select

    from app.cases.models import CaseFile

    async with session_factory() as s:
        return (
            await s.execute(
                sa_select(func.count()).select_from(CaseFile).where(CaseFile.case_id == case_id)
            )
        ).scalar_one()


@pytest.mark.asyncio
async def test_save_attachment_rejects_foreign_tenant_case(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    session_factory,
    tmp_path,
    monkeypatch,
):
    """save_attachment_to_case must refuse a case from another tenant (AUDIT-H1).

    The attachment is tenant-scoped, but case_id arrives straight from the URL and
    was never validated. A real source file exists on disk, so WITHOUT the guard the
    copy succeeds and a CaseFile is created pointing at another tenant's dossier."""
    from app.email import sync_router

    monkeypatch.setattr(sync_router, "EMAIL_ATTACHMENTS_BASE", tmp_path / "attach")
    monkeypatch.setattr(sync_router, "CASE_FILES_UPLOADS_BASE", tmp_path / "casefiles")

    attachment, _ = await _make_attachment_with_file(
        db, test_tenant.id, test_user.id, tmp_path / "attach"
    )
    other = Tenant(
        id=uuid.uuid4(), name="Other Firm H1", slug="other-firm-h1", kvk_number="33333333"
    )
    db.add(other)
    await db.flush()
    foreign_case = await _create_case(db, other.id, case_number="2026-99993")
    # Capture ids before the request — a 4xx rolls back the shared session and
    # expires these instances, so reading .id afterwards would trigger lazy IO.
    attachment_id = attachment.id
    foreign_case_id = foreign_case.id
    await db.commit()

    resp = await client.post(
        f"/api/email/attachments/{attachment_id}/save-to-case/{foreign_case_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 404

    # nothing was attached to the foreign dossier
    assert await _count_case_files(session_factory, foreign_case_id) == 0


@pytest.mark.asyncio
async def test_save_attachment_same_tenant_succeeds(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    session_factory,
    tmp_path,
    monkeypatch,
):
    """The H1 guard must not break a normal same-tenant save-to-case."""
    from app.email import sync_router

    monkeypatch.setattr(sync_router, "EMAIL_ATTACHMENTS_BASE", tmp_path / "attach")
    monkeypatch.setattr(sync_router, "CASE_FILES_UPLOADS_BASE", tmp_path / "casefiles")

    attachment, _ = await _make_attachment_with_file(
        db, test_tenant.id, test_user.id, tmp_path / "attach"
    )
    case = await _create_case(db, test_tenant.id, case_number="2026-00051")
    await db.commit()

    resp = await client.post(
        f"/api/email/attachments/{attachment.id}/save-to-case/{case.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200

    assert await _count_case_files(session_factory, case.id) == 1


@pytest.mark.asyncio
async def test_sync_rejects_foreign_tenant_case(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """AUDIT-H1 (Fable-review): POST /api/email/sync?case_id=... zet case_id als
    force_case_id op gesyncte mails. Een case van een ander kantoor moet 404 geven
    (guard vuurt vóór de account-check), zodat er niets cross-tenant gekoppeld wordt."""
    other = Tenant(
        id=uuid.uuid4(), name="Other Firm Sync", slug="other-firm-sync", kvk_number="44444444"
    )
    db.add(other)
    await db.flush()
    foreign_case = await _create_case(db, other.id, case_number="2026-99994")
    foreign_case_id = foreign_case.id
    await db.commit()

    resp = await client.post(
        f"/api/email/sync?case_id={foreign_case_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_case_number_match_ignores_4digit_invoice_like_number(
    db: AsyncSession, test_tenant: Tenant
):
    """A 4-digit '20YY-NNNN' reference (e.g. an invoice/payment number) must NOT
    be treated as a dossiernummer (AUDIT-MEDIUM).

    Real case numbers are YYYY-NNNNN (>=5 digits). The old regex (\\d{4,6})
    matched 4-digit references too, so a non-existent "case number" was reported,
    which blocks the contact-email fallback and leaves the email unlinked.
    """
    from app.email.sync_service import _find_case_by_case_number

    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "Betreft factuur 2026-1234 van vorige maand"
    )
    assert has_case_number is False
    assert case_id is None

    # A real 5-digit dossiernummer is still matched
    case = await _create_case(db, test_tenant.id, case_number="2026-00077")
    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "Inzake dossier 2026-00077"
    )
    assert has_case_number is True
    assert case_id == case.id
    assert matched_by == "case_number"


@pytest.mark.asyncio
async def test_match_on_imported_in_case_number(db: AsyncSession, test_tenant: Tenant):
    """S185: BaseNet-geïmporteerde zaaknummers (IN######) worden herkend, ook in
    een antwoord-onderwerp met omringende tekst."""
    from app.email.sync_service import _find_case_by_case_number

    case = await _create_case(db, test_tenant.id, case_number="IN100215")
    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "RE: SOMMATIE TOT BETALING / IN100215 (geen verweer)"
    )
    assert case_id == case.id
    assert matched_by == "case_number"
    assert has_case_number is True


@pytest.mark.asyncio
async def test_match_on_client_reference_with_invoice_suffix(
    db: AsyncSession, test_tenant: Tenant
):
    """S185: het opdrachtgever-kenmerk matcht op de kern vóór het BaseNet-
    factuurachtervoegsel ('D102913_I62115417' → klant noemt 'D102913')."""
    from app.email.sync_service import _find_case_by_case_number

    case = await _create_case(db, test_tenant.id, case_number="IN100330")
    case.reference = "D102913_I62115417"
    await db.flush()

    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "Beste, inzake ons dossier D102913 ontvingen wij..."
    )
    assert case_id == case.id
    assert matched_by == "client_reference"
    assert has_case_number is True


@pytest.mark.asyncio
async def test_match_on_bracketed_reference(db: AsyncSession, test_tenant: Tenant):
    """S185 Fable-review: kenmerken die met blokhaken zijn opgeslagen
    ('[D102760_I56669891]') matchen ook op de kale kern ('D102760')."""
    from app.email.sync_service import _find_case_by_case_number

    case = await _create_case(db, test_tenant.id, case_number="IN100019")
    case.reference = "[D102760_I56669891]"
    await db.flush()

    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "inzake uw dossier D102760"
    )
    assert case_id == case.id
    assert matched_by == "client_reference"


@pytest.mark.asyncio
async def test_unknown_reference_does_not_block_sender(db: AsyncSession, test_tenant: Tenant):
    """S185: een IN-/kenmerk-achtig nummer dat wij niet hebben mag de afzender-
    terugval NIET blokkeren (alleen een echt Luxis-dossiernummer doet dat)."""
    from app.email.sync_service import _find_case_by_case_number

    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "Onze referentie IN999999 / D999999"
    )
    assert case_id is None
    assert has_case_number is False  # → caller mag op afzender matchen


@pytest.mark.asyncio
async def test_suggest_cases_returns_client_name(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S187: suggesties met een match crashten op het niet-bestaande
    Contact.display_name; nu komt de cliëntnaam (Contact.name) correct mee."""
    from app.email.sync_service import suggest_cases_for_email

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_case(db, test_tenant.id, case_number="2026-00001")
    email = await _create_synced_email(
        db,
        test_tenant.id,
        account.id,
        subject="Inzake dossier 2026-00001",
    )
    await db.flush()

    suggestions = await suggest_cases_for_email(db, test_tenant.id, email.id)

    match = next((s for s in suggestions if s["case_id"] == str(case.id)), None)
    assert match is not None
    # Vóór de fix wierp deze aanroep een AttributeError.
    assert match["client_name"] == "Test Debiteur B.V."


@pytest.mark.asyncio
async def test_ambiguous_reference_blocks_without_linking(
    db: AsyncSession, test_tenant: Tenant
):
    """S185: als één kenmerk-kern naar twee zaken wijst → niet auto-koppelen, wél
    blokkeren (het hoort ergens, maar we weten niet waar)."""
    from app.email.sync_service import _find_case_by_case_number

    a = await _create_case(db, test_tenant.id, case_number="IN100001")
    a.reference = "D500000_I11111111"
    b = await _create_case(db, test_tenant.id, case_number="IN100002")
    b.reference = "D500000_I22222222"
    await db.flush()

    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "inzake D500000"
    )
    assert case_id is None
    assert has_case_number is True


@pytest.mark.asyncio
async def test_own_case_number_beats_ambiguous_reference(
    db: AsyncSession, test_tenant: Tenant
):
    """S185: een duidelijk eigen zaaknummer wint van een dubbelzinnig kenmerk dat
    óók in dezelfde mail staat."""
    from app.email.sync_service import _find_case_by_case_number

    target = await _create_case(db, test_tenant.id, case_number="IN100215")
    a = await _create_case(db, test_tenant.id, case_number="IN100001")
    a.reference = "D500000_I11111111"
    b = await _create_case(db, test_tenant.id, case_number="IN100002")
    b.reference = "D500000_I22222222"
    await db.flush()

    case_id, matched_by, has_case_number = await _find_case_by_case_number(
        db, test_tenant.id, "RE: sommatie IN100215 — ons kenmerk D500000"
    )
    assert case_id == target.id
    assert matched_by == "case_number"


def test_determine_direction_handles_none_from_email():
    """A message with from_email=None (e.g. some server-side notifications) must
    not crash the sync loop with AttributeError (crash-guard)."""
    from app.email.providers.base import EmailMessage
    from app.email.sync_service import _determine_direction

    msg = EmailMessage(provider_message_id="x", from_email=None)
    # Should not raise; an unknown sender is treated as inbound.
    assert _determine_direction(msg, "lisanne@kestinglegal.nl") == "inbound"


def test_determine_direction_outbound_matches_account():
    """from_email equal to the account email is outbound (case-insensitive)."""
    from app.email.providers.base import EmailMessage
    from app.email.sync_service import _determine_direction

    msg = EmailMessage(provider_message_id="x", from_email="Lisanne@KestingLegal.nl")
    assert _determine_direction(msg, "lisanne@kestinglegal.nl") == "outbound"


@pytest.mark.asyncio
async def test_oauth_status_surfaces_sync_error(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """S203 #1: het status-endpoint geeft last_sync_at + last_sync_error door, zodat
    de UI een stil doodgegane sync kan tonen."""
    account = await _create_email_account(db, test_tenant.id, test_user.id)
    account.last_sync_at = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
    account.last_sync_error = "invalid_grant: token expired"
    await db.commit()

    resp = await client.get("/api/email/oauth/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is True
    assert data["last_sync_error"] == "invalid_grant: token expired"
    assert data["last_sync_at"] is not None
