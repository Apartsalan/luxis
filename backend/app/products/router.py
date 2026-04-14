"""Products module router — CRUD endpoints for product catalog."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.database import get_db
from app.products import service
from app.products.schemas import ProductCreate, ProductResponse, ProductUpdate
from app.products.seed import seed_products

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all products for the tenant."""
    return await service.list_products(db, user.tenant_id, active_only)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a single product."""
    product = await service.get_product(db, user.tenant_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product niet gevonden")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new product."""
    existing = await service.get_product_by_code(db, user.tenant_id, data.code)
    if existing:
        raise HTTPException(status_code=409, detail=f"Product met code '{data.code}' bestaat al")
    return await service.create_product(db, user.tenant_id, data)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update a product."""
    product = await service.update_product(db, user.tenant_id, product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product niet gevonden")
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Soft-delete a product."""
    deleted = await service.delete_product(db, user.tenant_id, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product niet gevonden")


@router.post("/seed", status_code=200)
async def seed_basenet_products(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Seed all 28 Basenet products. Idempotent — skips existing."""
    created = await seed_products(db, user.tenant_id)
    return {"created": created, "message": f"{created} producten aangemaakt"}
