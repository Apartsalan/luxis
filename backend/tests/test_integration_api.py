"""Integration tests — full API flow: login → create contact → create case → add claim → calculate.

These tests exercise the API endpoints end-to-end through the ASGI test client.
They verify the complete incasso workflow as a real user (Lisanne) would use it.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.collections.models import InterestRate


# ── Fixtures for seeding interest rates ─────────────────────────────────────


@pytest_asyncio.fixture
async def seed_interest_rates(db: AsyncSession):
    """Seed the required interest rates for integration tests."""
    rates = [
        InterestRate(
            id=uuid.uuid4(),
            rate_type="statutory",
            effective_from=date(2024, 1, 1),
            rate=Decimal("7.00"),
            source="Test fixture",
        ),
        InterestRate(
            id=uuid.uuid4(),
            rate_type="statutory",
            effective_from=date(2025, 1, 1),
            rate=Decimal("6.00"),
            source="Test fixture",
        ),
        InterestRate(
            id=uuid.uuid4(),
            rate_type="commercial",
            effective_from=date(2024, 1, 1),
            rate=Decimal("12.50"),
            source="Test fixture (ECB + 8pp)",
        ),
        InterestRate(
            id=uuid.uuid4(),
            rate_type="commercial",
            effective_from=date(2025, 1, 1),
            rate=Decimal("11.50"),
            source="Test fixture (ECB + 8pp)",
        ),
    ]
    for rate in rates:
        db.add(rate)
    await db.commit()


# ── Helper: login and get headers ──────────────────────────────────────────


async def login(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    """Login and return auth headers."""
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Test: Full incasso flow ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_incasso_flow(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
    seed_interest_rates,
):
    """Complete incasso workflow: login → contact → case → claim → interest."""

    # Step 1: Login
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    # Step 2: Create client (creditor) contact
    create_client_resp = await client.post(
        "/api/contacts",
        json={
            "contact_type": "company",
            "name": "Schuldeiser B.V.",
            "email": "info@schuldeiser.nl",
            "kvk_number": "99887766",
        },
        headers=headers,
    )
    assert create_client_resp.status_code == 201
    creditor_id = create_client_resp.json()["id"]

    # Step 3: Create debtor (opposing party) contact
    create_debtor_resp = await client.post(
        "/api/contacts",
        json={
            "contact_type": "person",
            "name": "Piet Schuldenaar",
            "first_name": "Piet",
            "last_name": "Schuldenaar",
            "email": "piet@example.nl",
        },
        headers=headers,
    )
    assert create_debtor_resp.status_code == 201
    debtor_id = create_debtor_resp.json()["id"]

    # Step 4: Create incasso case
    create_case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "description": "Onbetaalde factuur Schuldeiser B.V.",
            "interest_type": "statutory",
            "client_id": creditor_id,
            "opposing_party_id": debtor_id,
            "date_opened": "2025-01-15",
        },
        headers=headers,
    )
    assert create_case_resp.status_code == 201
    case_data = create_case_resp.json()
    case_id = case_data["id"]
    assert case_data["case_type"] == "incasso"
    assert case_data["status"] == "nieuw"
    assert case_data["interest_type"] == "statutory"

    # Step 5: Add a claim (vordering)
    create_claim_resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Factuur 2024-042 dd. 15-09-2024",
            "principal_amount": "5000.00",
            "default_date": "2024-10-15",
            "invoice_number": "2024-042",
            "invoice_date": "2024-09-15",
        },
        headers=headers,
    )
    assert create_claim_resp.status_code == 201
    claim_data = create_claim_resp.json()
    assert claim_data["principal_amount"] == "5000.00"
    assert claim_data["default_date"] == "2024-10-15"

    # Step 6: Calculate interest
    interest_resp = await client.get(
        f"/api/cases/{case_id}/interest",
        params={"as_of": "2025-10-15"},
        headers=headers,
    )
    assert interest_resp.status_code == 200
    interest_data = interest_resp.json()
    assert interest_data["interest_type"] == "statutory"
    assert Decimal(interest_data["total_principal"]) == Decimal("5000.00")
    # Interest should be > 0 for 1 year
    assert Decimal(interest_data["total_interest"]) > Decimal("0")

    # Step 7: Calculate BIK
    bik_resp = await client.get(
        f"/api/cases/{case_id}/bik",
        headers=headers,
    )
    assert bik_resp.status_code == 200
    bik_data = bik_resp.json()
    # €5,000 → 15% of 2500 + 10% of 2500 = 375 + 250 = €625
    assert Decimal(bik_data["bik_exclusive"]) == Decimal("625.00")

    # Step 8: Get financial summary
    summary_resp = await client.get(
        f"/api/cases/{case_id}/financial-summary",
        params={"as_of": "2025-10-15"},
        headers=headers,
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert Decimal(summary["total_principal"]) == Decimal("5000.00")
    assert Decimal(summary["total_interest"]) > Decimal("0")
    assert Decimal(summary["bik_amount"]) == Decimal("625.00")
    assert Decimal(summary["total_outstanding"]) > Decimal("5000.00")


# ── Test: Login → Create contact → Create case with multiple claims ────────


@pytest.mark.asyncio
async def test_multiple_claims_on_case(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
    seed_interest_rates,
):
    """A case with multiple invoices (claims)."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    # Create contacts
    client_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "company", "name": "Multi B.V."},
        headers=headers,
    )
    client_id = client_resp.json()["id"]

    # Create case
    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "interest_type": "statutory",
            "client_id": client_id,
            "date_opened": "2025-03-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]

    # Add 3 claims with different dates
    claims = [
        {
            "description": "Factuur 2024-001",
            "principal_amount": "1500.00",
            "default_date": "2024-06-01",
        },
        {
            "description": "Factuur 2024-002",
            "principal_amount": "2500.00",
            "default_date": "2024-09-01",
        },
        {
            "description": "Factuur 2024-003",
            "principal_amount": "3000.00",
            "default_date": "2025-01-01",
        },
    ]
    for claim in claims:
        resp = await client.post(
            f"/api/cases/{case_id}/claims", json=claim, headers=headers
        )
        assert resp.status_code == 201

    # List claims
    claims_resp = await client.get(
        f"/api/cases/{case_id}/claims", headers=headers
    )
    assert claims_resp.status_code == 200
    assert len(claims_resp.json()) == 3

    # Calculate interest for all claims
    interest_resp = await client.get(
        f"/api/cases/{case_id}/interest",
        params={"as_of": "2025-06-01"},
        headers=headers,
    )
    assert interest_resp.status_code == 200
    data = interest_resp.json()
    # Total principal = 1500 + 2500 + 3000 = 7000
    assert Decimal(data["total_principal"]) == Decimal("7000.00")
    # Each claim should have its own interest calculation
    assert len(data["claims"]) == 3

    # BIK on total principal
    bik_resp = await client.get(
        f"/api/cases/{case_id}/bik", headers=headers
    )
    assert bik_resp.status_code == 200
    # €7,000 → 375 + 250 + 5% of 2000 = 625 + 100 = €725
    assert Decimal(bik_resp.json()["bik_exclusive"]) == Decimal("725.00")


# ── Test: Payment registration ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_payment_registration_flow(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
    seed_interest_rates,
):
    """Register payments and verify they show up."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    # Create contact + case
    contact_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "company", "name": "Betaler B.V."},
        headers=headers,
    )
    client_id = contact_resp.json()["id"]

    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "interest_type": "statutory",
            "client_id": client_id,
            "date_opened": "2025-01-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]

    # Add claim
    await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Factuur 2025-001",
            "principal_amount": "10000.00",
            "default_date": "2025-01-15",
        },
        headers=headers,
    )

    # Register first payment
    pay1_resp = await client.post(
        f"/api/cases/{case_id}/payments",
        json={
            "amount": "3000.00",
            "payment_date": "2025-04-01",
            "description": "Eerste deelbetaling",
            "payment_method": "bank",
        },
        headers=headers,
    )
    assert pay1_resp.status_code == 201
    assert Decimal(pay1_resp.json()["amount"]) == Decimal("3000.00")

    # Register second payment
    pay2_resp = await client.post(
        f"/api/cases/{case_id}/payments",
        json={
            "amount": "2000.00",
            "payment_date": "2025-05-01",
            "description": "Tweede deelbetaling",
        },
        headers=headers,
    )
    assert pay2_resp.status_code == 201

    # List payments
    payments_resp = await client.get(
        f"/api/cases/{case_id}/payments", headers=headers
    )
    assert payments_resp.status_code == 200
    assert len(payments_resp.json()) == 2


# ── Test: Unauthorized access ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_auth_returns_403(client: AsyncClient):
    """Endpoints without auth should return 403."""
    response = await client.get("/api/contacts")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    """Invalid Bearer token should return 401."""
    response = await client.get(
        "/api/contacts",
        headers={"Authorization": "Bearer invalid-garbage-token"},
    )
    assert response.status_code == 401


# ── Test: Case status transitions ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_case_status_workflow(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
):
    """Case status follows the correct workflow: nieuw → sommatie → dagvaarding."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    # Create contact + case
    contact_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "person", "name": "Status Test"},
        headers=headers,
    )
    client_id = contact_resp.json()["id"]

    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": client_id,
            "date_opened": "2025-01-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]
    assert case_resp.json()["status"] == "nieuw"

    # Transition: nieuw → sommatie (skipping 14-dagenbrief is allowed)
    status_resp = await client.put(
        f"/api/cases/{case_id}/status",
        json={"new_status": "sommatie", "note": "Sommatiebrief verstuurd"},
        headers=headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "sommatie"

    # Transition: sommatie → dagvaarding
    status_resp = await client.put(
        f"/api/cases/{case_id}/status",
        json={"new_status": "dagvaarding"},
        headers=headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "dagvaarding"


# ── Test: Invalid status transition ────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_status_transition(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
):
    """Cannot skip from 'nieuw' directly to 'vonnis'."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    contact_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "person", "name": "Invalid Transition"},
        headers=headers,
    )
    client_id = contact_resp.json()["id"]

    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": client_id,
            "date_opened": "2025-01-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]

    # Try invalid transition: nieuw → vonnis (should fail)
    status_resp = await client.put(
        f"/api/cases/{case_id}/status",
        json={"new_status": "vonnis"},
        headers=headers,
    )
    assert status_resp.status_code == 400


# ── Test: Claim CRUD ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_claim_crud(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
):
    """Create, read, update, delete a claim."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    # Setup: contact + case
    contact_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "company", "name": "CRUD Test B.V."},
        headers=headers,
    )
    client_id = contact_resp.json()["id"]

    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": client_id,
            "date_opened": "2025-02-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]

    # Create
    create_resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Test vordering",
            "principal_amount": "1234.56",
            "default_date": "2025-01-01",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    claim_id = create_resp.json()["id"]

    # Read (list)
    list_resp = await client.get(
        f"/api/cases/{case_id}/claims", headers=headers
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Update
    update_resp = await client.put(
        f"/api/cases/{case_id}/claims/{claim_id}",
        json={"principal_amount": "2000.00"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert Decimal(update_resp.json()["principal_amount"]) == Decimal("2000.00")

    # Delete (soft)
    delete_resp = await client.delete(
        f"/api/cases/{case_id}/claims/{claim_id}",
        headers=headers,
    )
    assert delete_resp.status_code == 204

    # Verify soft-deleted — list should be empty
    list_resp = await client.get(
        f"/api/cases/{case_id}/claims", headers=headers
    )
    assert len(list_resp.json()) == 0


# ── Test: Derdengelden flow ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_derdengelden_flow(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
):
    """Deposit and withdrawal from derdengelden account."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    # Setup
    contact_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "company", "name": "Derdengelden B.V."},
        headers=headers,
    )
    client_id = contact_resp.json()["id"]

    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": client_id,
            "date_opened": "2025-01-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]

    # Deposit
    dep_resp = await client.post(
        f"/api/cases/{case_id}/derdengelden",
        json={
            "transaction_type": "deposit",
            "amount": "5000.00",
            "transaction_date": "2025-03-01",
            "description": "Ontvangst debiteur",
            "counterparty": "Piet Schuldenaar",
        },
        headers=headers,
    )
    assert dep_resp.status_code == 201

    # Withdrawal
    wd_resp = await client.post(
        f"/api/cases/{case_id}/derdengelden",
        json={
            "transaction_type": "withdrawal",
            "amount": "3000.00",
            "transaction_date": "2025-03-05",
            "description": "Doorbetaling aan client",
            "counterparty": "Schuldeiser B.V.",
        },
        headers=headers,
    )
    assert wd_resp.status_code == 201

    # Check balance
    balance_resp = await client.get(
        f"/api/cases/{case_id}/derdengelden/balance",
        headers=headers,
    )
    assert balance_resp.status_code == 200
    balance = balance_resp.json()
    assert Decimal(balance["total_deposits"]) == Decimal("5000.00")
    assert Decimal(balance["total_withdrawals"]) == Decimal("3000.00")
    assert Decimal(balance["balance"]) == Decimal("2000.00")


# ── Test: BIK with BTW via API ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bik_with_btw_api(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
    seed_interest_rates,
):
    """BIK endpoint with include_btw=true."""
    headers = await login(client, "lisanne@kestinglegal.nl", "testpassword123")

    contact_resp = await client.post(
        "/api/contacts",
        json={"contact_type": "company", "name": "BTW Test B.V."},
        headers=headers,
    )
    client_id = contact_resp.json()["id"]

    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": client_id,
            "date_opened": "2025-01-01",
        },
        headers=headers,
    )
    case_id = case_resp.json()["id"]

    await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "BTW test factuur",
            "principal_amount": "5000.00",
            "default_date": "2025-01-15",
        },
        headers=headers,
    )

    # BIK without BTW (default)
    resp_no_btw = await client.get(
        f"/api/cases/{case_id}/bik", headers=headers
    )
    assert Decimal(resp_no_btw.json()["btw_amount"]) == Decimal("0")

    # BIK with BTW
    resp_btw = await client.get(
        f"/api/cases/{case_id}/bik",
        params={"include_btw": "true"},
        headers=headers,
    )
    assert resp_btw.status_code == 200
    assert Decimal(resp_btw.json()["btw_amount"]) == Decimal("131.25")
    assert Decimal(resp_btw.json()["bik_inclusive"]) == Decimal("756.25")
