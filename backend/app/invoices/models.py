"""Invoices module models — Invoice, InvoiceLine, InvoicePayment, Expense.

Facturatiemodule for Dutch law firms. Invoice numbering follows
the format F{year}-{sequence:05d} (e.g. F2026-00001).
All financial amounts use NUMERIC(15,2) — never float.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase

INVOICE_STATUSES = (
    "concept",
    "approved",
    "sent",
    "partially_paid",
    "paid",
    "overdue",
    "cancelled",
)

PAYMENT_METHODS = ("bank", "ideal", "cash", "verrekening")


class Invoice(TenantBase):
    """A client invoice (factuur).

    Status workflow: concept → approved → sent → paid
                                              → overdue → paid
                     concept → cancelled (at any point before paid)
    """

    __tablename__ = "invoices"

    # Auto-generated: F2026-00001
    invoice_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="concept"
    )

    # Related entities
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True, index=True
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financials (calculated from lines)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    btw_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("21.00")
    )
    btw_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )

    # Reference / notes
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    contact: Mapped["Contact"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[contact_id], lazy="selectin"
    )
    case: Mapped["Case | None"] = relationship(  # noqa: F821
        "Case", foreign_keys=[case_id], lazy="selectin"
    )
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        lazy="selectin",
        order_by="InvoiceLine.line_number",
    )
    payments: Mapped[list["InvoicePayment"]] = relationship(
        "InvoicePayment",
        back_populates="invoice",
        lazy="selectin",
        order_by="InvoicePayment.payment_date.desc()",
    )


class InvoiceLine(TenantBase):
    """A single line item on an invoice.

    Can optionally link to a time_entry or expense for traceability.
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id"), nullable=False, index=True
    )

    line_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("1")
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )

    # Optional link to time entry or expense
    time_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("time_entries.id"), nullable=True
    )
    expense_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("expenses.id"), nullable=True
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", back_populates="lines"
    )
    time_entry: Mapped["TimeEntry | None"] = relationship(  # noqa: F821
        "TimeEntry", lazy="selectin"
    )
    expense: Mapped["Expense | None"] = relationship(  # noqa: F821
        "Expense", foreign_keys=[expense_id], lazy="selectin"
    )


class InvoicePayment(TenantBase):
    """A payment (deelbetaling) recorded against an invoice.

    When total payments reach the invoice total, the invoice status
    is automatically set to 'paid'. Partial payments set it to
    'partially_paid'.
    """

    __tablename__ = "invoice_payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id"), nullable=False, index=True
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )

    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    payment_method: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # bank, ideal, cash, verrekening

    reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", back_populates="payments"
    )
    creator: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[created_by], lazy="selectin"
    )


class Expense(TenantBase):
    """A billable expense (verschot) that can be invoiced.

    Examples: griffierecht, deurwaarderskosten, KvK-uittreksel.
    """

    __tablename__ = "expenses"

    case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True, index=True
    )

    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="overig"
    )  # griffierecht, deurwaarder, kvk, overig

    billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    invoiced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["Case | None"] = relationship(  # noqa: F821
        "Case", foreign_keys=[case_id], lazy="selectin"
    )
