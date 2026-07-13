"""Cases module models — Case, CaseParty, CaseActivity, and CaseFile."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class Case(TenantBase):
    """A legal case (zaak).

    Case types: incasso, insolventie, advies, overig
    Status (B3, S198 — 4 vaste waarden; de incasso-pijplijn stuurt de status):
        nieuw → in_behandeling → betaald / afgesloten
    De pijplijn-stap (incasso_step_id) bepaalt het echte werk; de status is
    een grove fase-indicator die door de pijplijn wordt meegestuurd.
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

    # S207: rentedatum / bevriezing. De datum tot waar rente wordt berekend.
    # NULL = tot vandaag (lopende rente). Gezet = rente stopt op die datum en
    # het systeem rekent terug. Wordt bij het afsluiten van een zaak automatisch
    # gezet op de laatste betaaldatum (het moment van afwikkeling), maar is ook
    # handmatig aanpasbaar — zodat een afgewikkelde zaak niet eeuwig doorrent
    # (IN100350) en je een berekening op een gekozen peildatum kunt vastzetten.
    interest_freeze_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # S207c: met welke status een BaseNet-import-dossier binnenkwam. Onderscheidt
    # zaken die in BaseNet nog LIEPEN (Lopend/Wacht) — geparkeerd in Luxis, worden
    # in fases heropend — van zaken die daar al AFGEHANDELD waren (Gereed/
    # Geannuleerd/Offerte) en dicht blijven. NULL = niet uit de BaseNet-import
    # (in Luxis zelf aangemaakt). Waarde = de originele BaseNet-status, letterlijk.
    basenet_origin_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # S207d: de fijne BaseNet-WERKFASE (CustomProjectStatus.psdescription, bv.
    # "B2C 3e sommatie verstuurd", "Procedure loopt"). De hoofdgroep hierboven
    # zegt óf een zaak nog moet lopen; deze fase zegt wáár hij gebleven was —
    # nodig om bij de fase-heropening elke zaak op de juiste pijplijnstap te
    # zetten (IN100310/IN100407 bewezen: hoofdgroep kan liegen, de fase niet).
    basenet_origin_phase: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Related contacts
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"), nullable=False)
    opposing_party_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )
    billing_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )  # F7: alternate billing contact (if different from client)

    # S140: AV-versie die op dit dossier van toepassing is. NULL = geen
    # expliciete keuze; gather_case_context valt terug op smart-default
    # (versie geldig bij eerste factuur) en uiteindelijk op contact.terms_file_path
    # voor backwards-compat.
    contact_terms_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contact_terms.id"), nullable=True
    )

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

    # FIN-2 / afwikkelflow: hoe wordt het geincasseerde geld afgewikkeld?
    #   'verrekenen'  — honorarium verrekenen met het derdengelden-saldo, restant uitbetalen
    #   'doorbetalen' — volledig saldo aan de client, later los factureren
    # NULL = nog niet gekozen. Enkel een UI-hint voor het afwikkel-paneel; de
    # daadwerkelijke boekingen hebben hun eigen waarborgen (vier-ogen, consent).
    settlement_route: Mapped[str | None] = mapped_column(String(20), nullable=True)

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

    # AUD124-03: Nakosten (post-judgment costs)
    nakosten_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True, default=None
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
    )  # DF138: bodem voor honorarium-factuur naar cliënt (provisie-minimum)
    bik_minimum_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )  # DF138-16: bodem voor BIK-percentage berekening (vordering aan debiteur)
    provisie_base: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="collected_amount",
        server_default="collected_amount",
    )  # "collected_amount" or "total_claim"

    # Verweer (objection/dispute) tracking
    has_verweer: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    verweer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verweer_date: Mapped[date | None] = mapped_column(Date, nullable=True)

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
    __table_args__ = (
        Index("ix_case_files_search", "search_vector", postgresql_using="gin"),
    )

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
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('dutch', "
            "coalesce(original_filename,'') || ' ' || "
            "coalesce(description,'') || ' ' || "
            "coalesce(left(extracted_text, 300000),''))",
            persisted=True,
        ),
        deferred=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["Case"] = relationship("Case", lazy="selectin")
    uploader: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
