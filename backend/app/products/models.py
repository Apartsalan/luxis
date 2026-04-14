"""Products module models — Product catalog for invoice lines.

Maps to Exact Online articles with GL account codes and VAT types.
"""

from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import TenantBase

VAT_TYPES = ("21", "0", "eu", "non_eu")


class Product(TenantBase):
    """A product/article (artikel) for invoice lines.

    Each product maps to an Exact Online article with a specific
    GL account (grootboekrekening) and VAT type.
    """

    __tablename__ = "products"

    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    default_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    gl_account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    gl_account_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # VAT type: "21" (21%), "0" (NVT/vrijgesteld), "eu" (binnen EU), "non_eu" (buiten EU)
    vat_type: Mapped[str] = mapped_column(String(20), nullable=False, default="21")
    vat_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("21.00")
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
