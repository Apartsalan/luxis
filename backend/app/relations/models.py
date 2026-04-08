"""Relations module models — Contacts (companies & persons) and their links."""

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
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class Contact(TenantBase):
    """A contact in the system — either a company or a person.

    Used for: clients (cliënten), opposing parties (wederpartijen),
    bailiffs (deurwaarders), courts (rechtbanken), and other parties.
    """

    __tablename__ = "contacts"

    contact_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'company' or 'person'

    # Shared fields
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Full name (person) or company name

    # Person-specific fields
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Primary contact person (for companies: t.a.v. / aanspreekpunt)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Contact info
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Company-specific fields
    kvk_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    btw_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Visit address
    visit_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    visit_postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    visit_city: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Postal address
    postal_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    postal_postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    postal_city: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Billing profile (F6)
    default_hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_term_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # default: 14/30
    billing_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)

    # Default interest settings — used as defaults when creating a new case
    # for this contact (Lisanne demo 2026-04-07). Migration edc1202caef9 added the columns.
    default_interest_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    default_contractual_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    # DF120 (Lisanne demo 2026-04-08): default rate_basis per client — "yearly"
    # or "monthly". Inherited at claim creation — new claims on cases of this
    # client default to this basis unless overridden.
    default_rate_basis: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # DF117-22 (Lisanne demo 2026-04-07): default BIK/incassokosten per client.
    # Same pattern as default_interest_type — when creating a new case for this client,
    # these are inherited unless explicitly set on the case. Either fixed amount OR
    # percentage of principal can be set; if both are null, the WIK-staffel default applies.
    default_bik_override: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    default_bik_override_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    # DF120 (Lisanne demo 2026-04-08): default minimum provisie (incassokosten
    # floor) per client. Inherited on new case unless explicitly set.
    default_minimum_fee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Algemene Voorwaarden (AI-UX-11)
    terms_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    terms_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Other
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    company_links: Mapped[list["ContactLink"]] = relationship(
        "ContactLink",
        foreign_keys="ContactLink.person_id",
        back_populates="person",
        lazy="selectin",
    )
    person_links: Mapped[list["ContactLink"]] = relationship(
        "ContactLink",
        foreign_keys="ContactLink.company_id",
        back_populates="company",
        lazy="selectin",
    )


class ContactLink(TenantBase):
    """Links a person contact to a company contact (e.g. employee, director)."""

    __tablename__ = "contact_links"

    __table_args__ = (
        UniqueConstraint("tenant_id", "person_id", "company_id", name="uq_contact_link"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"), nullable=False)
    role_at_company: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g. "directeur", "contactpersoon"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    person: Mapped["Contact"] = relationship(
        "Contact",
        foreign_keys=[person_id],
        back_populates="company_links",
        lazy="selectin",
    )
    company: Mapped["Contact"] = relationship(
        "Contact",
        foreign_keys=[company_id],
        back_populates="person_links",
        lazy="selectin",
    )
