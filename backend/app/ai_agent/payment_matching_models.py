"""Payment matching models — bank statement import and auto-matching for incasso cases."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class ImportStatus(StrEnum):
    """Status of a bank statement import."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchStatus(StrEnum):
    """Status of a payment match through the review workflow."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class MatchMethod(StrEnum):
    """How a match was found."""

    CASE_NUMBER = "case_number"  # Dossiernummer in omschrijving
    INVOICE_NUMBER = "invoice_number"  # Factuurnummer in omschrijving
    IBAN = "iban"  # IBAN afzender matches opposing party
    AMOUNT = "amount"  # Bedrag matches outstanding
    NAME = "name"  # Naam afzender matches opposing party
    MANUAL = "manual"  # Handmatig gekoppeld door gebruiker


# Confidence scores per match method
MATCH_CONFIDENCE: dict[str, int] = {
    MatchMethod.CASE_NUMBER: 95,
    MatchMethod.INVOICE_NUMBER: 90,
    MatchMethod.IBAN: 85,
    MatchMethod.AMOUNT: 70,
    MatchMethod.NAME: 50,
    MatchMethod.MANUAL: 100,
}

# Dutch labels for match methods
MATCH_METHOD_LABELS: dict[str, str] = {
    MatchMethod.CASE_NUMBER: "Dossiernummer in omschrijving",
    MatchMethod.INVOICE_NUMBER: "Factuurnummer in omschrijving",
    MatchMethod.IBAN: "IBAN debiteur",
    MatchMethod.AMOUNT: "Bedrag komt overeen",
    MatchMethod.NAME: "Naam debiteur",
    MatchMethod.MANUAL: "Handmatig gekoppeld",
}


class BankStatementImport(TenantBase):
    """A bank statement CSV import.

    Tracks the import of a Rabobank CSV file with metadata about
    the import process and results.
    """

    __tablename__ = "bank_statement_imports"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    bank: Mapped[str] = mapped_column(String(50), nullable=False, default="rabobank")
    account_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ImportStatus.PROCESSING)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    debit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    imported_by_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    # Relationships
    imported_by: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
    transactions: Mapped[list["BankTransaction"]] = relationship(
        "BankTransaction", back_populates="statement_import", lazy="noload"
    )


class BankTransaction(TenantBase):
    """A single transaction from a bank statement.

    Stores the raw data from the CSV plus parsed fields used for matching.
    Only credit (incoming) transactions are stored — debits are skipped
    since this is a derdengeldrekening where all credits are incasso payments.
    """

    __tablename__ = "bank_transactions"

    import_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("bank_statement_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core transaction data
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Rabobank-specific fields
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # Rentedatum

    # Matching status
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    statement_import: Mapped["BankStatementImport"] = relationship(
        "BankStatementImport", back_populates="transactions", lazy="selectin"
    )
    matches: Mapped[list["PaymentMatch"]] = relationship(
        "PaymentMatch", back_populates="transaction", lazy="noload"
    )


class PaymentMatch(TenantBase):
    """A proposed match between a bank transaction and an incasso case.

    Generated automatically by the matching algorithm, then reviewed
    by the lawyer. On execution, creates a derdengelden deposit +
    payment record with art. 6:44 BW distribution.
    """

    __tablename__ = "payment_matches"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("bank_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Match details
    match_method: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    match_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Review workflow
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=MatchStatus.PENDING)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution result
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("payments.id"), nullable=True
    )
    derdengelden_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("derdengelden.id"), nullable=True
    )

    # Relationships
    transaction: Mapped["BankTransaction"] = relationship(
        "BankTransaction", back_populates="matches", lazy="selectin"
    )
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    reviewed_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )
