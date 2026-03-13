"""Tests for the trust_funds module — derdengelden transactions, approval, balance."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.relations.models import Contact

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def case_payload(test_company: Contact) -> dict:
    """Reusable payload for creating a case."""
    return {
        "case_type": "advies",
        "description": "Trust fund test zaak",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-20",
    }


async def create_case(client: AsyncClient, auth_headers: dict, payload: dict) -> str:
    """Helper to create a case and return its ID."""
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201
    return response.json()["id"]


async def create_second_user(db: AsyncSession, tenant: Tenant) -> tuple[User, dict]:
    """Create a second user for two-director approval testing."""
    user2 = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="directeur2@kestinglegal.nl",
        hashed_password=hash_password("testpassword123"),
        full_name="Tweede Directeur",
        role="admin",
    )
    db.add(user2)
    await db.commit()
    await db.refresh(user2)
    token = create_access_token(str(user2.id), str(tenant.id))
    headers = {"Authorization": f"Bearer {token}"}
    return user2, headers


async def create_third_user(db: AsyncSession, tenant: Tenant) -> tuple[User, dict]:
    """Create a third user for additional approval testing."""
    user3 = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="directeur3@kestinglegal.nl",
        hashed_password=hash_password("testpassword123"),
        full_name="Derde Directeur",
        role="admin",
    )
    db.add(user3)
    await db.commit()
    await db.refresh(user3)
    token = create_access_token(str(user3.id), str(tenant.id))
    headers = {"Authorization": f"Bearer {token}"}
    return user3, headers


# ── Create Deposit ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_deposit(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Creating a deposit should auto-approve and return 201."""
    case_id = await create_case(client, auth_headers, case_payload)

    deposit = {
        "transaction_type": "deposit",
        "amount": "5000.00",
        "description": "Waarborgsom ontvangen",
        "payment_method": "bank",
        "reference": "INGB-2026-001",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_type"] == "deposit"
    assert Decimal(data["amount"]) == Decimal("5000.00")
    assert data["status"] == "approved"  # Deposits are auto-approved
    assert data["description"] == "Waarborgsom ontvangen"
    assert data["payment_method"] == "bank"


@pytest.mark.asyncio
async def test_create_deposit_updates_balance(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """After a deposit, the balance should reflect the new amount."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Create two deposits
    for amount in ["10000.00", "5000.00"]:
        deposit = {
            "transaction_type": "deposit",
            "amount": amount,
            "description": f"Storting {amount}",
        }
        await client.post(
            f"/api/trust-funds/cases/{case_id}/transactions",
            json=deposit,
            headers=auth_headers,
        )

    # Check balance
    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/balance",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_balance"]) == Decimal("15000.00")
    assert Decimal(data["total_deposits"]) == Decimal("15000.00")
    assert Decimal(data["total_disbursements"]) == Decimal("0.00")


# ── Create Disbursement ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_disbursement_pending(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Creating a disbursement should start as pending_approval."""
    case_id = await create_case(client, auth_headers, case_payload)

    # First deposit some money
    deposit = {
        "transaction_type": "deposit",
        "amount": "10000.00",
        "description": "Storting",
    }
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Create disbursement
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "3000.00",
        "description": "Griffierecht betaling",
        "beneficiary_name": "Rechtbank Amsterdam",
        "beneficiary_iban": "NL91ABNA0417164300",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_type"] == "disbursement"
    assert data["status"] == "pending_approval"
    assert data["beneficiary_name"] == "Rechtbank Amsterdam"


@pytest.mark.asyncio
async def test_disbursement_insufficient_balance(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Disbursement exceeding available balance should return 400."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Deposit 1000
    deposit = {
        "transaction_type": "deposit",
        "amount": "1000.00",
        "description": "Kleine storting",
    }
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Try to disburse 5000 — should fail
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "5000.00",
        "description": "Te groot bedrag",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Onvoldoende saldo" in response.json()["detail"]


@pytest.mark.asyncio
async def test_disbursement_no_balance(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Disbursement on empty account should return 400."""
    case_id = await create_case(client, auth_headers, case_payload)

    disbursement = {
        "transaction_type": "disbursement",
        "amount": "100.00",
        "description": "Geen saldo",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    assert response.status_code == 400


# ── Approval Workflow ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approve_disbursement_two_directors(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
    case_payload: dict,
):
    """Two different directors must approve a disbursement."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Deposit
    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Create disbursement (by user 1 / auth_headers)
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "3000.00",
        "description": "Uitbetaling",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    tx_id = response.json()["id"]

    # Create second and third users for approval
    _, headers2 = await create_second_user(db, test_tenant)
    _, headers3 = await create_third_user(db, test_tenant)

    # First approval by director 2
    response = await client.post(
        f"/api/trust-funds/transactions/{tx_id}/approve",
        headers=headers2,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approved_by_1"] is not None
    assert data["approved_by_2"] is None
    assert data["status"] == "pending_approval"  # Still pending after 1st approval

    # Second approval by director 3
    response = await client.post(
        f"/api/trust-funds/transactions/{tx_id}/approve",
        headers=headers3,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approved_by_2"] is not None
    assert data["status"] == "approved"  # Now fully approved


@pytest.mark.asyncio
async def test_creator_cannot_approve_own_transaction(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """The creator of a transaction cannot approve it (four-eyes principle)."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Deposit
    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Create disbursement
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "1000.00",
        "description": "Uitbetaling",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    tx_id = response.json()["id"]

    # Try to approve own transaction — should fail
    response = await client.post(
        f"/api/trust-funds/transactions/{tx_id}/approve",
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert "aanmaker" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_same_director_cannot_approve_twice(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
    case_payload: dict,
):
    """The same director cannot provide both approvals."""
    case_id = await create_case(client, auth_headers, case_payload)

    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    disbursement = {
        "transaction_type": "disbursement",
        "amount": "2000.00",
        "description": "Uitbetaling",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    tx_id = response.json()["id"]

    # Create second user
    _, headers2 = await create_second_user(db, test_tenant)

    # First approval by director 2
    response = await client.post(
        f"/api/trust-funds/transactions/{tx_id}/approve",
        headers=headers2,
    )
    assert response.status_code == 200

    # Same director tries second approval — should fail
    response = await client.post(
        f"/api/trust-funds/transactions/{tx_id}/approve",
        headers=headers2,
    )
    assert response.status_code == 403
    assert "andere persoon" in response.json()["detail"].lower()


# ── Reject Transaction ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reject_disbursement(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
    case_payload: dict,
):
    """Rejecting a pending disbursement should set status to rejected."""
    case_id = await create_case(client, auth_headers, case_payload)

    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    disbursement = {
        "transaction_type": "disbursement",
        "amount": "2000.00",
        "description": "Uitbetaling",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    tx_id = response.json()["id"]

    # Reject
    response = await client.post(
        f"/api/trust-funds/transactions/{tx_id}/reject",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


# ── Balance Calculation ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_balance_with_approved_disbursement(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
    case_payload: dict,
):
    """Balance should subtract approved disbursements."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Deposit 10000
    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Create disbursement of 3000
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "3000.00",
        "description": "Uitbetaling",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )
    tx_id = response.json()["id"]

    # Approve with two directors
    _, headers2 = await create_second_user(db, test_tenant)
    _, headers3 = await create_third_user(db, test_tenant)

    await client.post(f"/api/trust-funds/transactions/{tx_id}/approve", headers=headers2)
    await client.post(f"/api/trust-funds/transactions/{tx_id}/approve", headers=headers3)

    # Check balance
    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/balance",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_balance"]) == Decimal("7000.00")
    assert Decimal(data["total_deposits"]) == Decimal("10000.00")
    assert Decimal(data["total_disbursements"]) == Decimal("3000.00")
    assert Decimal(data["pending_disbursements"]) == Decimal("0.00")
    assert Decimal(data["available"]) == Decimal("7000.00")


@pytest.mark.asyncio
async def test_balance_with_pending_disbursement(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Pending disbursements should reduce available but not total_balance."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Deposit 10000
    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Create pending disbursement of 4000
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "4000.00",
        "description": "Uitbetaling",
    }
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )

    # Check balance
    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/balance",
        headers=auth_headers,
    )
    data = response.json()
    assert Decimal(data["total_balance"]) == Decimal("10000.00")  # Not yet approved
    assert Decimal(data["pending_disbursements"]) == Decimal("4000.00")
    assert Decimal(data["available"]) == Decimal("6000.00")  # 10000 - 4000 pending


# ── List Transactions ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_transactions(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Listing transactions should return all transactions for a case."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Create 3 deposits
    for i in range(3):
        deposit = {
            "transaction_type": "deposit",
            "amount": f"{(i + 1) * 1000}.00",
            "description": f"Storting {i + 1}",
        }
        await client.post(
            f"/api/trust-funds/cases/{case_id}/transactions",
            json=deposit,
            headers=auth_headers,
        )

    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/transactions",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_list_transactions_filter_by_type(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Filtering by transaction_type should work."""
    case_id = await create_case(client, auth_headers, case_payload)

    # Create deposit
    deposit = {"transaction_type": "deposit", "amount": "10000.00", "description": "Storting"}
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )

    # Create disbursement
    disbursement = {
        "transaction_type": "disbursement",
        "amount": "1000.00",
        "description": "Uitbetaling",
    }
    await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=disbursement,
        headers=auth_headers,
    )

    # Filter deposits only
    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/transactions?transaction_type=deposit",
        headers=auth_headers,
    )
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["transaction_type"] == "deposit"


@pytest.mark.asyncio
async def test_empty_balance(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Balance for case with no transactions should be zero."""
    case_id = await create_case(client, auth_headers, case_payload)

    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/balance",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_balance"]) == Decimal("0.00")
    assert Decimal(data["available"]) == Decimal("0.00")


# ── Decimal Precision ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decimal_precision(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
):
    """Financial amounts must maintain exact decimal precision."""
    case_id = await create_case(client, auth_headers, case_payload)

    deposit = {
        "transaction_type": "deposit",
        "amount": "12345.67",
        "description": "Precisie test",
    }
    response = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json=deposit,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["amount"]) == Decimal("12345.67")

    # Check balance
    response = await client.get(
        f"/api/trust-funds/cases/{case_id}/balance",
        headers=auth_headers,
    )
    data = response.json()
    assert Decimal(data["total_balance"]) == Decimal("12345.67")
