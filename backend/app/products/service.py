"""Products module service — CRUD operations for product catalog."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product
from app.products.schemas import ProductCreate, ProductUpdate


async def list_products(
    db: AsyncSession, tenant_id: uuid.UUID, active_only: bool = True
) -> list[Product]:
    """List all products for a tenant, ordered by sort_order then name."""
    query = select(Product).where(Product.tenant_id == tenant_id)
    if active_only:
        query = query.where(Product.is_active.is_(True))
    query = query.order_by(Product.sort_order, Product.name)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_product(
    db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID
) -> Product | None:
    """Get a single product by ID."""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_product_by_code(
    db: AsyncSession, tenant_id: uuid.UUID, code: str
) -> Product | None:
    """Get a product by its code."""
    result = await db.execute(
        select(Product).where(
            Product.code == code,
            Product.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def create_product(
    db: AsyncSession, tenant_id: uuid.UUID, data: ProductCreate
) -> Product:
    """Create a new product."""
    product = Product(
        tenant_id=tenant_id,
        code=data.code,
        name=data.name,
        description=data.description,
        default_price=data.default_price,
        gl_account_code=data.gl_account_code,
        gl_account_name=data.gl_account_name,
        vat_type=data.vat_type,
        vat_percentage=data.vat_percentage,
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID, data: ProductUpdate
) -> Product | None:
    """Update a product."""
    product = await get_product(db, tenant_id, product_id)
    if not product:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return product


async def delete_product(
    db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID
) -> bool:
    """Soft-delete a product (set is_active=False)."""
    product = await get_product(db, tenant_id, product_id)
    if not product:
        return False
    product.is_active = False
    await db.flush()
    return True
