"""Tests for product catalog module (DF120-08)."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant


@pytest.mark.asyncio
async def test_list_products_empty(
    client: AsyncClient, auth_headers: dict
):
    """Empty tenant has no products."""
    resp = await client.get("/api/products", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_seed_products(
    client: AsyncClient, auth_headers: dict
):
    """Seed creates all 30 Basenet products."""
    resp = await client.post("/api/products/seed", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] >= 28

    # List should now have products
    resp2 = await client.get("/api/products", headers=auth_headers)
    assert resp2.status_code == 200
    products = resp2.json()
    assert len(products) >= 28

    # Check Honorarium exists with correct GL code
    honorarium = next(
        (p for p in products if p["code"] == "100000"), None
    )
    assert honorarium is not None
    assert honorarium["name"] == "Honorarium"
    assert honorarium["gl_account_code"] == "8000"
    assert honorarium["vat_type"] == "21"
    assert float(honorarium["vat_percentage"]) == 21.00


@pytest.mark.asyncio
async def test_seed_idempotent(
    client: AsyncClient, auth_headers: dict
):
    """Seeding twice does not create duplicates."""
    resp1 = await client.post(
        "/api/products/seed", headers=auth_headers
    )
    count1 = resp1.json()["created"]

    resp2 = await client.post(
        "/api/products/seed", headers=auth_headers
    )
    count2 = resp2.json()["created"]
    assert count2 == 0

    resp3 = await client.get("/api/products", headers=auth_headers)
    assert len(resp3.json()) == count1


@pytest.mark.asyncio
async def test_create_product(
    client: AsyncClient, auth_headers: dict
):
    """Create a custom product."""
    resp = await client.post(
        "/api/products",
        headers=auth_headers,
        json={
            "code": "CUSTOM01",
            "name": "Test Product",
            "gl_account_code": "9999",
            "gl_account_name": "Test Account",
            "vat_type": "21",
            "vat_percentage": "21.00",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "CUSTOM01"
    assert data["name"] == "Test Product"
    assert data["gl_account_code"] == "9999"


@pytest.mark.asyncio
async def test_create_duplicate_code_rejected(
    client: AsyncClient, auth_headers: dict
):
    """Cannot create two products with same code."""
    payload = {
        "code": "DUP01",
        "name": "First",
        "gl_account_code": "8000",
        "gl_account_name": "Test",
    }
    resp1 = await client.post(
        "/api/products", headers=auth_headers, json=payload
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/products",
        headers=auth_headers,
        json={**payload, "name": "Second"},
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_update_product(
    client: AsyncClient, auth_headers: dict
):
    """Update a product's name and price."""
    create = await client.post(
        "/api/products",
        headers=auth_headers,
        json={
            "code": "UPD01",
            "name": "Original",
            "gl_account_code": "8000",
            "gl_account_name": "Test",
        },
    )
    pid = create.json()["id"]

    resp = await client.put(
        f"/api/products/{pid}",
        headers=auth_headers,
        json={"name": "Updated", "default_price": "99.50"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert float(resp.json()["default_price"]) == 99.50


@pytest.mark.asyncio
async def test_delete_product(
    client: AsyncClient, auth_headers: dict
):
    """Soft-delete sets is_active=False."""
    create = await client.post(
        "/api/products",
        headers=auth_headers,
        json={
            "code": "DEL01",
            "name": "To Delete",
            "gl_account_code": "8000",
            "gl_account_name": "Test",
        },
    )
    pid = create.json()["id"]

    resp = await client.delete(
        f"/api/products/{pid}", headers=auth_headers
    )
    assert resp.status_code == 204

    # Not in active list
    resp2 = await client.get("/api/products", headers=auth_headers)
    ids = [p["id"] for p in resp2.json()]
    assert pid not in ids

    # Still in full list
    resp3 = await client.get(
        "/api/products?active_only=false", headers=auth_headers
    )
    ids2 = [p["id"] for p in resp3.json()]
    assert pid in ids2


@pytest.mark.asyncio
async def test_product_gl_codes(
    client: AsyncClient, auth_headers: dict
):
    """Verify GL account codes for key Basenet products."""
    await client.post("/api/products/seed", headers=auth_headers)
    resp = await client.get("/api/products", headers=auth_headers)
    products = {p["code"]: p for p in resp.json()}

    assert products["100014"]["gl_account_code"] == "8020"
    assert products["100014"]["vat_type"] == "0"
    assert products["100027"]["gl_account_code"] == "8300"
    assert products["100039"]["gl_account_code"] == "8020"
    assert float(products["100039"]["default_price"]) == 3083.00
    assert products["100042"]["gl_account_code"] == "1950"
