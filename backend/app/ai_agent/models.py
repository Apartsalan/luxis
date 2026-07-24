"""AI Agent models — email classification and response templates."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models import TenantBase


class AIUsage(Base):
    """Verbruiksregel per AI-aanroep (S230 — kostenvraag Arsalan).

    Er ging tegoed doorheen zonder dat iemand kon zien waaraan: token_count op
    ai_drafts bleef leeg en classificatie/intake registreerden niets. Elke
    aanroep in kimi_client schrijft nu één regel: doel, model, tokens en de
    geschatte kosten. Globaal (geen tenant_id) — net als scheduler_heartbeat;
    het verbruik is per installatie, de sleutel is er ook maar één.
    """

    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # NULL = model niet in de prijstabel (tokens dan alsnog geregistreerd)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)


class ClassificationCategory(StrEnum):
    """Categories for debtor email classification."""

    BELOFTE_TOT_BETALING = "belofte_tot_betaling"
    BETWISTING = "betwisting"
    BETALINGSREGELING_VERZOEK = "betalingsregeling_verzoek"
    BEWEERT_BETAALD = "beweert_betaald"
    ONVERMOGEN = "onvermogen"
    JURIDISCH_VERWEER = "juridisch_verweer"
    ONTVANGSTBEVESTIGING = "ontvangstbevestiging"
    NIET_GERELATEERD = "niet_gerelateerd"


class SuggestedAction(StrEnum):
    """Actions the AI can suggest after classifying an email."""

    WAIT_AND_REMIND = "wait_and_remind"
    ESCALATE = "escalate"
    SEND_TEMPLATE = "send_template"
    DISMISS = "dismiss"
    REQUEST_PROOF = "request_proof"
    NO_ACTION = "no_action"


class ClassificationStatus(StrEnum):
    """Status of an email classification through the review workflow."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class DraftStatus(StrEnum):
    """Status of an AI-generated draft through the review workflow."""

    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    SENT = "sent"
    DISCARDED = "discarded"


# Default mapping: category → suggested action
CATEGORY_ACTION_MAP: dict[ClassificationCategory, SuggestedAction] = {
    ClassificationCategory.BELOFTE_TOT_BETALING: SuggestedAction.WAIT_AND_REMIND,
    ClassificationCategory.BETWISTING: SuggestedAction.ESCALATE,
    ClassificationCategory.BETALINGSREGELING_VERZOEK: SuggestedAction.ESCALATE,
    ClassificationCategory.BEWEERT_BETAALD: SuggestedAction.REQUEST_PROOF,
    ClassificationCategory.ONVERMOGEN: SuggestedAction.ESCALATE,
    ClassificationCategory.JURIDISCH_VERWEER: SuggestedAction.ESCALATE,
    ClassificationCategory.ONTVANGSTBEVESTIGING: SuggestedAction.NO_ACTION,
    ClassificationCategory.NIET_GERELATEERD: SuggestedAction.DISMISS,
}

# Default mapping: category → response template key (None = no template)
CATEGORY_TEMPLATE_MAP: dict[ClassificationCategory, str | None] = {
    ClassificationCategory.BELOFTE_TOT_BETALING: "bevestiging_betaalbelofte",
    ClassificationCategory.BETWISTING: "ontvangst_betwisting",
    ClassificationCategory.BETALINGSREGELING_VERZOEK: "ontvangst_regeling_verzoek",
    ClassificationCategory.BEWEERT_BETAALD: "verzoek_betalingsbewijs",
    ClassificationCategory.ONVERMOGEN: "ontvangst_onvermogen",
    ClassificationCategory.JURIDISCH_VERWEER: "doorverwijzing_advocaat",
    ClassificationCategory.ONTVANGSTBEVESTIGING: None,
    ClassificationCategory.NIET_GERELATEERD: None,
}

# Dutch display labels for categories
CATEGORY_LABELS: dict[str, str] = {
    "belofte_tot_betaling": "Belofte tot betaling",
    "betwisting": "Betwisting",
    "betalingsregeling_verzoek": "Betalingsregeling verzoek",
    "beweert_betaald": "Beweert betaald",
    "onvermogen": "Onvermogen",
    "juridisch_verweer": "Juridisch verweer",
    "ontvangstbevestiging": "Ontvangstbevestiging",
    "niet_gerelateerd": "Niet gerelateerd",
}

# Dutch display labels for actions
ACTION_LABELS: dict[str, str] = {
    "wait_and_remind": "Wacht af + herinnering",
    "escalate": "Escaleer naar advocaat",
    "send_template": "Stuur antwoord",
    "dismiss": "Wegzetten",
    "request_proof": "Vraag betalingsbewijs",
    "no_action": "Geen actie nodig",
}


class EmailClassification(TenantBase):
    """AI classification of an inbound debtor email on an incasso case."""

    __tablename__ = "email_classifications"

    synced_email_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("synced_emails.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Classification result
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Verweer-type (S174 V4): welk van de 13 types de debiteur voert — alleen gezet bij
    # betwisting/juridisch_verweer, anders None. Voedt de gerichte matching van geleerde
    # voorbeelden (get_learned_examples geeft hetzelfde type voorrang).
    defense_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Sentiment (AUDIT-28)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Suggested action
    suggested_action: Mapped[str] = mapped_column(String(50), nullable=False)
    suggested_template_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    suggested_reminder_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Payment promise extraction (AUDIT-18)
    promise_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    promise_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Human review
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ClassificationStatus.PENDING
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution tracking
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    synced_email: Mapped["SyncedEmail"] = relationship(  # noqa: F821
        "SyncedEmail", lazy="selectin"
    )
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    reviewed_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )


class ResponseTemplate(TenantBase):
    """Reusable email response template selected by the AI agent."""

    __tablename__ = "response_templates"

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        # Each tenant can have one template per key
        {"comment": "AI response templates per tenant"},
    )


class AIDraft(TenantBase):
    """AI-generated draft email, persisted for review by the lawyer."""

    __tablename__ = "ai_drafts"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    classification_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("email_classifications.id", ondelete="SET NULL"), nullable=True
    )

    subject: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(String(20), nullable=False, default="formeel")
    sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DraftStatus.GENERATED
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instruction: Mapped[str | None] = mapped_column(Text, nullable=True)

    # S233 — Taak 2: de behandelaar-instructie kan vragen de facturen bij te sluiten
    # ("doe de facturen erbij"). De AI leidt dit af en zet het signaal; het concept
    # opent dan met de factuur-PDF's al aangevinkt. Alleen op de antwoordroute — stap-
    # en batch-concepten dragen geen instructie en blijven dus False.
    attach_invoices: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # S221 3.2 — ontdubbelen + zombie-opruiming. `intent` = waarvoor het concept is
    # (next_step / reply_to_email / free_compose); `step_id` = de pijplijnstap waarop
    # de zaak stond bij generatie. Samen vormen ze de ontdubbel-sleutel en laten ze
    # een stap-wissel verouderde stap-concepten sluiten.
    intent: Mapped[str | None] = mapped_column(String(20), nullable=True)
    step_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("incasso_pipeline_steps.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    classification: Mapped["EmailClassification | None"] = relationship(
        "EmailClassification", lazy="selectin"
    )
    reviewed_by: Mapped["User | None"] = relationship("User", lazy="selectin")  # noqa: F821


class LearnedAnswer(TenantBase):
    """Verweer-antwoord-bibliotheek (S167+): een maatwerk-weerlegging die de advocaat
    ooit verstuurde, ná haar goedkeuring bewaard als extra standaardantwoord.

    Vult de hand-gecureerde `defense_library` (5 vaste voorbeelden) aan met de zeldzame
    maatwerk-gevallen die daar niet in passen. Werkwijze (herzien S167 na kritische
    review): het systeem VANGT kandidaten uit Lisanne's verstuurde antwoorden, maar
    voedt de AI pas ná HAAR goedkeuring — zij bepaalt wat een standaardantwoord wordt en
    haalt de persoonsgegevens eruit. Geen stil, automatisch leren meer (dat leverde in de
    praktijk alleen kopieën van bestaande sommaties op). Blijft een assistent (besluit S160).

    Twee teksten per record:
    * `body` = de ruw geëxtraheerde kern-weerlegging (kan nog namen/bedragen bevatten) —
      alleen voor de review, wordt NOOIT naar de AI gestuurd.
    * `anonymized_body` = de door Lisanne bevestigde, geanonimiseerde tekst — dít is wat
      (bij `status == 'goedgekeurd'`) als voorbeeld naar de AI gaat.

    Bron = Lisanne's UITGAANDE SyncedEmail. Categorie komt van de classificatie van de
    inkomende mail waarop ze reageerde.
    """

    __tablename__ = "learned_answers"

    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="nl")

    # Review-status: 'kandidaat' (wacht op beoordeling) → 'goedgekeurd' (voedt de AI) of
    # 'afgewezen' (genegeerd). Alleen 'goedgekeurd' gaat ooit naar een prompt.
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="kandidaat",
        server_default="kandidaat", index=True,
    )
    # De geanonimiseerde, door Lisanne bevestigde tekst — het enige dat de AV in mag.
    # Bij een kandidaat: het automatische anonimiseer-voorstel (nog te bevestigen).
    anonymized_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Welk type verweer dit weerlegt (library-key of 'overig') — voor gerichte matching
    # i.p.v. "nieuwste eerst".
    defense_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Wanneer Lisanne dit goedkeurde/afwees.
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Herkomst — voor dedup bij backfill en voor inzicht in de bron.
    # Primaire bron = een verzonden AI-verweerconcept (gegarandeerd een verweer-reactie
    # in de juiste categorie, door de advocaat goedgekeurd door het te versturen).
    source_ai_draft_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_drafts.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    # source_synced_email_id blijft beschikbaar voor een latere, sterkere bron: de echte
    # hand-bewerkte verzonden tekst (vergt betrouwbare draft↔mail-koppeling).
    source_synced_email_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("synced_emails.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    source_case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )

    # Aantal keer dat dit voorbeeld is meegestuurd bij een conceptgeneratie (voor het
    # dashboard: "van welke eigen antwoorden leert de AI het meest").
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )


class LegalKnowledgeRule(TenantBase):
    """Juridische kennisregel (S248) — proactieve kennis: 'déze standaard-stelling is
    onjuist, dít is de weerlegging (art. X BW)'.

    Fundamenteel anders dan `LearnedAnswer`: dat is EMPIRISCH (geknipt uit Lisanne's echte
    verstuurde mail, met bronzaak, toon-voorbeeld). Een kennisregel is CURATED juridische
    kennis die Lisanne (of Arsalan namens haar) intikt — geen bronmail, wél een harde
    toepasbaarheids-voorwaarde. Deelt alleen de goedkeur-flow met `LearnedAnswer`
    (kandidaat → goedgekeurd/afgewezen), niet de backfill-machinerie.

    Matching op de bestaande 13-type verweer-woordenschat (`defense_types.py`): een regel
    voedt de verweer-prompt alléén als de laatste inkomende mail als dat type is
    geclassificeerd ÉN de `applies_to`-poort tegen `Case.debtor_type` klopt. Die poort is
    HARD in code (niet alleen in de tekst): zo kan een zakelijke regel (bv. art. 6:235 BW,
    'de B.V. kan de AV niet vernietigen') nooit op een consument worden losgelaten — een
    consument mág de AV juist wél vernietigen (het scherpste doemscenario, ontwerp §4).
    """

    __tablename__ = "legal_knowledge_rules"

    # Matchsleutel: één van de 13 verweer-types (of 'overig'). Spiegelt de classificatie
    # van de inkomende mail (EmailClassification.defense_type).
    defense_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Harde toepasbaarheids-poort tegen Case.debtor_type: 'alle' | 'zakelijk' | 'consument'.
    applies_to: Mapped[str] = mapped_column(
        String(10), nullable=False, default="alle", server_default="alle"
    )
    # Korte naam voor het dashboard (bv. "AV-vernietiging door B.V.").
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Waaraan herken je de stelling (context voor de AI + het dashboard).
    claim_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # De standaard-weerlegging (wat de AI mag gebruiken).
    rebuttal_body: Mapped[str] = mapped_column(Text, nullable=False)
    # Wetsartikel(en), bv. "art. 6:235 lid 1 BW".
    legal_basis: Mapped[str | None] = mapped_column(String(200), nullable=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="nl")

    # Review-status: 'kandidaat' (wacht op beoordeling) → 'goedgekeurd' (voedt de AI) of
    # 'afgewezen'. Alleen 'goedgekeurd' + is_active gaat ooit naar een prompt.
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="kandidaat",
        server_default="kandidaat", index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
