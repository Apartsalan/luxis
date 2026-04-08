"""Trust funds module models — TrustTransaction for derdengelden accounting.

Implements the Dutch Stichting Derdengelden requirements (Voda art. 6.19–6.27):
- Two-director approval for disbursements and offsets
- Balance may never go negative
- Full audit trail of all transactions and approvals
- Offsets against own invoices require explicit per-transaction client consent
  (art. 6.19 lid 5 Voda — algemene clausule is onvoldoende)
- Transactions are immutable; corrections happen via reversal entries
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class TrustTransaction(TenantBase):
    """A trust fund transaction (derdengelden transactie).

    Transaction types:
        - deposit: money received into the trust account
        - disbursement: money paid out from the trust account
        - offset_to_invoice: balance offset against own invoice (verrekening)
          — requires explicit written client consent per Voda art. 6.19 lid 5

    Status workflow:
        pending_approval → approved (after 2 approvals for disbursements/offsets)
        pending_approval → rejected

    Deposits are auto-approved. Disbursements and offsets require two-director
    approval where the approver cannot be the creator (4-eyes). For single-user
    tenants, self-approval can be enabled via TRUST_FUNDS_ALLOW_SELF_APPROVAL.

    Transactions are immutable. Corrections are made by creating a reverse
    transaction that points back via reversed_by_id.
    """

    __tablename__ = "trust_transactions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False, index=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"), nullable=False)

    transaction_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # deposit, disbursement, offset_to_invoice

    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    payment_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # bank, ideal, cash

    reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Bank reference / kenmerk

    # Disbursement-specific fields
    beneficiary_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    beneficiary_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)

    # Offset-to-invoice fields (Voda art. 6.19 lid 5 — verrekening)
    target_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("invoices.id"), nullable=True
    )
    consent_received_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    consent_method: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # email, document, mondeling, anders
    consent_document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reversal pointer (immutability — corrections via tegenboeking)
    reversed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("trust_transactions.id"), nullable=True
    )

    # SEPA-export tracking — set when an approved disbursement has been
    # included in a SEPA pain.001 batch and downloaded for upload to the bank.
    sepa_exported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sepa_batch_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    # Approval workflow
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_approval"
    )  # pending_approval, approved, rejected

    approved_by_1: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    approved_at_1: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_2: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    approved_at_2: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    # Relationships
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    contact: Mapped["Contact"] = relationship("Contact", lazy="selectin")  # noqa: F821
    target_invoice: Mapped["Invoice | None"] = relationship(  # noqa: F821
        "Invoice", foreign_keys=[target_invoice_id], lazy="selectin"
    )
    creator: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[created_by], lazy="selectin"
    )
    approver_1: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[approved_by_1], lazy="selectin"
    )
    approver_2: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[approved_by_2], lazy="selectin"
    )
