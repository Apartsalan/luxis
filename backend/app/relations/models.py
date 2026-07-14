"""Relations module models — Contacts (companies & persons) and their links."""

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
    # DF138-04: aanhef voor mail-generatie. 'mr' = heer, 'mrs' = mevrouw,
    # 'unknown' = geen voorkeur → AI gebruikt "Geachte heer/mevrouw,".
    # Alleen zinvol bij contact_type='person', maar veld geldt voor alle rows
    # (default 'unknown') zodat het schema uniform blijft.
    salutation: Mapped[str] = mapped_column(
        String(10), nullable=False, default="unknown", server_default="unknown"
    )

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
    # Land alleen invullen bij niet-Nederlandse adressen (NL = impliciete standaard).
    visit_country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Postal address
    postal_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    postal_postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    postal_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_country: Mapped[str | None] = mapped_column(String(100), nullable=True)

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
    # DF120 (Lisanne demo 2026-04-08): default minimum provisie — alléén bodem
    # voor het honorarium dat aan de cliënt wordt gefactureerd. NIET voor BIK.
    default_minimum_fee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    # S210: standaard succesprovisie-% dat elk nieuw dossier van deze cliënt erft
    # (migratie s210_contact_provisie). Zelfde overerf-patroon als de default_bik_*-velden;
    # dossier-waarde wint altijd. De berekeningsbasis blijft "collected_amount" (dossierdefault).
    default_provisie_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    # DF138-16: aparte bodem voor BIK-percentage berekening. Geldt voor de
    # incassokosten die van de debiteur worden gevorderd (vordering + mail).
    # Apart van default_minimum_fee zodat factuur naar cliënt en vordering aan
    # debiteur onafhankelijk gestuurd kunnen worden.
    default_bik_minimum_fee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # S177: rente-afspraak zoals GELEZEN uit de AV van deze cliënt. Apart van de
    # handmatige default_*-velden: die zijn de override (klantkaart) en winnen altijd
    # en worden NOOIT door een her-upload overschreven. Deze terms_*-velden vormen de
    # laag "uit AV gelezen" in de hiërarchie dossier > klantkaart > uit-AV > wettelijk,
    # met zichtbare herkomst (`terms_interest_source`) in de UI.
    terms_interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    terms_interest_basis: Mapped[str | None] = mapped_column(String(10), nullable=True)  # monthly/yearly
    terms_interest_compound: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    terms_interest_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    terms_interest_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # BTW status — determines whether 21% BTW is added to BIK for this client's cases
    # server_default spiegelt migratie aud124_01 (prod heeft 'true' als DB-default);
    # zonder dit wijkt de test-DB af van prod en faalt een raw-SQL insert (S209-review).
    is_btw_plichtig: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

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


class ContactTerms(TenantBase):
    """Versie van algemene voorwaarden bij een cliënt-contact.

    Eén cliënt kan meerdere AV-versies hebben (oude facturen vallen onder
    oude versie). Bij dossier-aanmaak wordt automatisch de versie gekozen
    waarvan `valid_from <= factuur-datum AND (valid_to >= factuur-datum
    OR valid_to IS NULL)`; Lisanne kan handmatig overrulen via
    `case.contact_terms_id`.

    `valid_from` NULL betekent "altijd geldig" — fallback voor cliënten
    met maar één AV-bestand of bij data-migratie van oude single-file
    velden.
    """

    __tablename__ = "contact_terms"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    contact: Mapped["Contact"] = relationship(
        "Contact",
        foreign_keys=[contact_id],
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
