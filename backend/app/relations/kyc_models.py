"""WWFT/KYC models — Client identification and verification per WWFT requirements."""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase

# ── Valid values ────────────────────────────────────────────────────────────

KYC_RISK_LEVELS = ("laag", "midden", "hoog")

KYC_ID_TYPES = (
    "paspoort",
    "id_kaart",
    "rijbewijs",
    "verblijfsdocument",
    "kvk_uittreksel",
    "anders",
)

KYC_STATUSES = ("niet_gestart", "in_behandeling", "voltooid", "verlopen")


class KycVerification(TenantBase):
    """WWFT/KYC verification record for a contact.

    Tracks client identification, UBO registration, risk assessment,
    and compliance checks as required by the Dutch WWFT
    (Wet ter voorkoming van witwassen en financieren van terrorisme).

    Every client (and sometimes opposing parties) must be verified before
    a law firm can provide legal services.
    """

    __tablename__ = "kyc_verifications"

    # Link to contact
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False, index=True
    )

    # Overall status
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="niet_gestart"
    )  # niet_gestart, in_behandeling, voltooid, verlopen

    # Risk classification
    risk_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # laag, midden, hoog

    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Identity document
    id_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # paspoort, id_kaart, rijbewijs, verblijfsdocument, kvk_uittreksel, anders

    id_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    id_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    id_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # UBO (Ultimate Beneficial Owner) — for companies
    ubo_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ubo_dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    ubo_nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ubo_percentage: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # e.g. "25-50%", ">50%"
    ubo_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # PEP (Politically Exposed Person) check
    pep_checked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    pep_is_pep: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    pep_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sanction list check
    sanctions_checked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    sanctions_hit: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    sanctions_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source of funds verification
    source_of_funds: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_of_funds_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Verification metadata
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    verification_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # General notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    contact: Mapped["Contact"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[contact_id], lazy="selectin"
    )
    verified_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[verified_by_id], lazy="selectin"
    )
