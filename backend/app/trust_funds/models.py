"""Trust funds module models — TrustTransaction for derdengelden accounting.

Implements the Dutch Stichting Derdengelden requirements:
- Two-director approval for disbursements
- Balance may never go negative
- Full audit trail of all transactions and approvals
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class TrustTransaction(TenantBase):
    """A trust fund transaction (derdengelden transactie).

    Transaction types:
        - deposit: money received into the trust account
        - disbursement: money paid out from the trust account

    Status workflow:
        pending_approval → approved (after 2 approvals for disbursements)
        pending_approval → rejected

    Deposits are auto-approved. Disbursements require two-director approval
    where the approver cannot be the creator.
    """

    __tablename__ = "trust_transactions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False, index=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # deposit, disbursement

    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

    payment_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # bank, ideal, cash

    reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Bank reference / kenmerk

    # Disbursement-specific fields
    beneficiary_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    beneficiary_iban: Mapped[str | None] = mapped_column(
        String(34), nullable=True
    )

    # Approval workflow
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_approval"
    )  # pending_approval, approved, rejected

    approved_by_1: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    approved_at_1: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by_2: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    approved_at_2: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    contact: Mapped["Contact"] = relationship("Contact", lazy="selectin")  # noqa: F821
    creator: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[created_by], lazy="selectin"
    )
    approver_1: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[approved_by_1], lazy="selectin"
    )
    approver_2: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[approved_by_2], lazy="selectin"
    )
