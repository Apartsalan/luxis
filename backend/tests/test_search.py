"""Tests for the search module — global search across cases, contacts, documents."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case, CaseFile
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail
from app.invoices.models import Invoice
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _seed_data(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Create a contact and case for search tests."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Bakkerij Zonneveld B.V.",
        email="info@zonneveld.nl",
    )
    db.add(contact)
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-00042",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date.today(),
        client_id=contact.id,
        description="Openstaande facturen Zonneveld",
    )
    db.add(case)
    await db.commit()
    return {"contact": contact, "case": case}


# ── Search ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_finds_contact(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search by contact name returns matching contact."""
    await _seed_data(db, test_tenant.id)

    resp = await client.get("/api/search?q=Zonneveld", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Zonneveld"
    assert data["total"] >= 1
    types = [r["type"] for r in data["results"]]
    assert "contact" in types


@pytest.mark.asyncio
async def test_search_finds_case_by_number(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search by case number returns matching case."""
    await _seed_data(db, test_tenant.id)

    resp = await client.get("/api/search?q=2026-00042", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    types = [r["type"] for r in data["results"]]
    assert "case" in types


@pytest.mark.asyncio
async def test_search_finds_invoice_by_number(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search by invoice number returns the matching invoice (CONN-11)."""
    seeded = await _seed_data(db, test_tenant.id)
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        invoice_number="F2026-09099",
        contact_id=seeded["contact"].id,
        invoice_date=date.today(),
        due_date=date.today(),
        status="sent",
        total=Decimal("250.00"),
    )
    db.add(invoice)
    await db.commit()

    resp = await client.get("/api/search?q=F2026-09099", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    matches = [r for r in data["results"] if r["type"] == "invoice"]
    assert matches, "Expected an invoice result"
    assert matches[0]["href"] == f"/facturen/{invoice.id}"


@pytest.mark.asyncio
async def test_search_finds_email_by_subject(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Search by email subject returns the matching synced email (CONN-11)."""
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="outlook",
        email_address="seidony@kestinglegal.nl",
        access_token_enc=b"x",
        refresh_token_enc=b"y",
    )
    db.add(account)
    await db.flush()

    email = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email_account_id=account.id,
        provider_message_id="msg-conn11-001",
        subject="Betalingsherinnering openstaand bedrag",
        from_email="debiteur@voorbeeld.nl",
        from_name="Jan Debiteur",
        email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.commit()

    resp = await client.get(
        "/api/search?q=Betalingsherinnering", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    matches = [r for r in data["results"] if r["type"] == "email"]
    assert matches, "Expected an email result"
    assert matches[0]["href"] == "/correspondentie"


@pytest.mark.asyncio
async def test_search_finds_email_body_with_dutch_stemming(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Een vervoegde Nederlandse term in de mailinhoud is doorzoekbaar."""
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="outlook",
        email_address="zoeken@kestinglegal.nl",
        access_token_enc=b"x",
        refresh_token_enc=b"y",
    )
    db.add(account)
    await db.flush()

    email = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email_account_id=account.id,
        provider_message_id="msg-powersearch-stemming",
        subject="Inhoudelijke reactie",
        from_email="afzender@voorbeeld.nl",
        from_name="Afzender",
        body_text="Wij betwisten alle betalingen aan Jansen.",
        email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.commit()

    resp = await client.get("/api/search?q=betaling", headers=auth_headers)

    assert resp.status_code == 200
    matches = [result for result in resp.json()["results"] if result["id"] == str(email.id)]
    assert matches, "Expected an email body result using Dutch stemming"
    assert "betalingen" in matches[0]["subtitle"].lower()


@pytest.mark.asyncio
async def test_search_finds_document_extracted_text(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Geëxtraheerde documenttekst levert een documentresultaat met snippet."""
    seeded = await _seed_data(db, test_tenant.id)
    case_file = CaseFile(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=seeded["case"].id,
        original_filename="contract.pdf",
        stored_filename="contract.pdf",
        file_size=123,
        content_type="application/pdf",
        extracted_text="huurovereenkomst kantoorpand",
        uploaded_by=test_user.id,
    )
    db.add(case_file)
    await db.commit()

    resp = await client.get("/api/search?q=huurovereenkomst", headers=auth_headers)

    assert resp.status_code == 200
    matches = [
        result for result in resp.json()["results"] if result["id"] == str(case_file.id)
    ]
    assert matches, "Expected a document content result"
    assert "huurovereenkomst" in matches[0]["subtitle"].lower()


@pytest.mark.asyncio
async def test_search_empty_result(client: AsyncClient, auth_headers: dict):
    """Search for nonexistent term returns empty results."""
    resp = await client.get("/api/search?q=xyznonexistent123", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["results"] == []


@pytest.mark.asyncio
async def test_search_requires_query(client: AsyncClient, auth_headers: dict):
    """Search without query parameter returns 422."""
    resp = await client.get("/api/search", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_respects_limit(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search limit parameter caps results."""
    # Create multiple contacts
    for i in range(5):
        db.add(
            Contact(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                contact_type="person",
                name=f"Testpersoon {i}",
                email=f"test{i}@example.nl",
            )
        )
    await db.commit()

    resp = await client.get("/api/search?q=Testpersoon&limit=2", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] <= 2


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
):
    """Search results from tenant A are not visible to tenant B."""
    await _seed_data(db, test_tenant.id)

    resp = await client.get("/api/search?q=Zonneveld", headers=second_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_fts_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    second_tenant: Tenant,
    second_user: User,
):
    """Mailinhoud van een andere tenant verschijnt niet in FTS-resultaten."""
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=second_tenant.id,
        user_id=second_user.id,
        provider="outlook",
        email_address="tenant-b@voorbeeld.nl",
        access_token_enc=b"x",
        refresh_token_enc=b"y",
    )
    db.add(account)
    await db.flush()
    email = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=second_tenant.id,
        email_account_id=account.id,
        provider_message_id="msg-powersearch-tenant-b",
        subject="Alleen voor tenant B",
        from_email="afzender@tenant-b.nl",
        from_name="Tenant B",
        body_text="onzichtbarezoekterm in vertrouwelijke inhoud",
        email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.commit()

    resp = await client.get("/api/search?q=onzichtbarezoekterm", headers=auth_headers)

    assert resp.status_code == 200
    assert all(result["id"] != str(email.id) for result in resp.json()["results"])


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    """Search without auth token returns 401."""
    resp = await client.get("/api/search?q=test")
    assert resp.status_code in (401, 403)
