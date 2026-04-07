"""Cases module models — Case, CaseParty, CaseActivity, and CaseFile."""

import uuid
from datetime import date, datetime
from decimal import Decimal

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


class Case(TenantBase):
    """A legal case (zaak).

    Case types: incasso, insolventie, advies, overig
    Status workflow:
        nieuw → 14_dagenbrief → sommatie → dagvaarding →
        vonnis → executie → betaald → afgesloten
    """

    __tablename__ = "cases"

    # Auto-generated case number: "2026-00001"
    case_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    # Case details
    case_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="incasso"
    )  # incasso, dossier, advies

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="nieuw"
    )  # Status workflow (see docstring)

    debtor_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="b2b"
    )  # b2b or b2c — determines interest type and workflow rules

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Client's reference number
    court_case_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Rolnummer/zaaknummer bij de rechtbank

    # G3: Procesgegevens
    court_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Naam rechtbank (bijv. "Rechtbank Amsterdam")
    judge_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Behandelend rechter
    chamber: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Kamer (bijv. "Handelskamer")
    procedure_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Type procedure (dagvaarding, verzoekschrift, kort geding, etc.)
    procedure_phase: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Procesfase (aangebracht, conclusies, comparitie, vonnis, hoger beroep, etc.)

    # Interest settings (at case level, not per claim)
    interest_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="statutory"
    )  # statutory, commercial, government, contractual

    contractual_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # e.g. 8.00 (only for contractual)

    contractual_compound: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Whether contractual interest is compound

    # Related contacts
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"), nullable=False)
    opposing_party_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )
    billing_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )  # F7: alternate billing contact (if different from client)

    # Assigned to
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )

    # Incasso pipeline
    incasso_step_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("incasso_pipeline_steps.id"), nullable=True
    )  # Current step in the incasso pipeline
    step_entered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # When the case entered its current pipeline step

    # Dates
    date_opened: Mapped[date] = mapped_column(Date, nullable=False)
    date_closed: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial summary cache (updated on payment/claim changes)
    total_principal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    # G13: Budget tracking (optional, toggleable via "budget" module)
    budget: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )  # Optional budget in euros for this case

    # LF-19: Per-case hourly rate (overrides user default)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # LF-12: Manual BIK override (None = use WIK-staffel calculation)
    bik_override: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    # DF117-04 (Lisanne demo 2026-04-07): BIK as percentage of total principal,
    # an alternative to the fixed bik_override. If set, takes precedence over the
    # fixed bik_override; if both are null, the WIK-staffel default is used.
    bik_override_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # LF-22: Debtor settings
    payment_term_days: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Default payment term for this debtor
    collection_strategy: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g. "standaard", "voorzichtig", "agressief"
    debtor_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Internal notes about the debtor/case

    # LF-20/LF-21: Billing method & financial settings
    billing_method: Mapped[str] = mapped_column(
        String(20), nullable=False, default="hourly", server_default="hourly"
    )  # hourly | fixed_price | budget_cap
    fixed_price_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )  # Vaste prijs (fixed_price method)
    budget_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # Max uren (budget_cap method)
    provisie_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # Incasso succesprovisie %
    fixed_case_costs: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )  # Vaste dossierkosten
    minimum_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )  # Minimumkosten
    provisie_base: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="collected_amount",
        server_default="collected_amount",
    )  # "collected_amount" or "total_claim"

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    client: Mapped["Contact"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[client_id], lazy="selectin"
    )
    opposing_party: Mapped["Contact | None"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[opposing_party_id], lazy="selectin"
    )
    billing_contact: Mapped["Contact | None"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[billing_contact_id], lazy="selectin"
    )
    assigned_to: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[assigned_to_id], lazy="selectin"
    )
    incasso_step: Mapped["IncassoPipelineStep | None"] = relationship(  # noqa: F821
        "IncassoPipelineStep", lazy="selectin"
    )
    parties: Mapped[list["CaseParty"]] = relationship(
        "CaseParty", back_populates="case", lazy="selectin"
    )
    activities: Mapped[list["CaseActivity"]] = relationship(
        "CaseActivity",
        back_populates="case",
        lazy="selectin",
        order_by="CaseActivity.created_at.desc()",
    )


class CaseParty(TenantBase):
    """Additional parties linked to a case (e.g. bailiff, court, co-debtor)."""

    __tablename__ = "case_parties"

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # deurwaarder, rechtbank, mede-debiteur, advocaat_wederpartij, etc.

    external_reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # The other party's reference number for this case

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="parties")
    contact: Mapped["Contact"] = relationship("Contact", lazy="selectin")  # noqa: F821


class CaseActivity(TenantBase):
    """Activity log for a case — tracks status changes, notes, and actions."""

    __tablename__ = "case_activities"

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    activity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # status_change, note, phone_call, email, document, payment, etc.

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # For status changes
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="activities")
    user: Mapped["User | None"] = relationship("User", lazy="selectin")  # noqa: F821


class CaseFile(TenantBase):
    """Uploaded file attached to a case (e.g. contracts, court decisions, evidence)."""

    __tablename__ = "case_files"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_direction: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # inkomend / uitgaand
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["Case"] = relationship("Case", lazy="selectin")
    uploader: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
