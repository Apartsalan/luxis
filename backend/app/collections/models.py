"""Collections module models — Claims, Payments, Arrangements, InterestRate.

This is the core of the incasso system. All financial amounts use
NUMERIC(15,2) for exact precision — never use float for money.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin
from app.shared.models import TenantBase


class Claim(TenantBase):
    """A financial claim (vordering) within a case.

    A case can have multiple claims (e.g. multiple invoices).
    Interest is calculated per claim based on the case's interest settings.
    """

    __tablename__ = "claims"

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)

    description: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # e.g. "Factuur 2026-001 dd. 15-01-2026"

    principal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)  # Hoofdsom

    default_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )  # Verzuimdatum — interest starts accruing from this date

    invoice_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Original invoice number

    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # Original invoice date

    rate_basis: Mapped[str] = mapped_column(
        String(10), nullable=False, default="yearly"
    )  # LF-03: "monthly" or "yearly" — if monthly, rate * 12 for annual calculation

    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # DF122-06: optional custom rate (%). NULL = use case-level rate (wettelijk/commercial/etc)

    invoice_file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("case_files.id"), nullable=True
    )  # LF-09: link uploaded invoice PDF to this claim

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Payment(TenantBase):
    """A payment received for a case.

    Payments are distributed according to art. 6:44 BW:
    costs → interest → principal
    """

    __tablename__ = "payments"

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # bank, contant, deurwaarder

    # Art. 6:44 BW distribution (calculated and stored)
    allocated_to_costs: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0"), nullable=False
    )
    allocated_to_interest: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0"), nullable=False
    )
    allocated_to_principal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0"), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PaymentArrangement(TenantBase):
    """A payment arrangement (betalingsregeling) for a case.

    Tracks agreed installments and their status.
    """

    __tablename__ = "payment_arrangements"

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )  # Total agreed amount

    installment_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )  # Amount per installment

    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )  # weekly, monthly, quarterly

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, completed, defaulted

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    installments: Mapped[list["PaymentArrangementInstallment"]] = relationship(
        back_populates="arrangement",
        lazy="noload",
    )


class PaymentArrangementInstallment(TenantBase):
    """A single installment (termijn) within a payment arrangement.

    Each arrangement generates N installments when created.
    Status flow: pending → paid/partial/overdue/missed/waived
    """

    __tablename__ = "payment_arrangement_installments"

    arrangement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("payment_arrangements.id"), nullable=False
    )

    arrangement: Mapped["PaymentArrangement"] = relationship(
        back_populates="installments",
        lazy="noload",
    )

    installment_number: Mapped[int] = mapped_column(nullable=False)  # 1, 2, 3, ...

    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0"), nullable=False
    )

    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("payments.id"), nullable=True
    )  # Link to the Payment record when paid

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | paid | partial | overdue | missed | waived

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class InterestRate(Base, TimestampMixin):
    """Historical interest rates — GLOBAL reference table (no tenant_id).

    This table stores the official rates from:
    - Wettelijke rente (art. 6:119 BW) — type: 'statutory'
    - Wettelijke handelsrente (art. 6:119a BW) — type: 'commercial'
    - Overheidshandelsrente (art. 6:119b BW) — type: 'government'

    NOTE: This model does NOT inherit from TenantBase because interest rates
    are the same for all tenants. It uses Base + TimestampMixin directly.
    """

    __tablename__ = "interest_rates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    rate_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # statutory, commercial, government

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)

    rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False
    )  # Annual percentage (e.g. 6.00 for 6%)

    source: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # e.g. "Staatsblad 2025, 480"
