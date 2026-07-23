"""Cases module service — Business logic for cases, parties, and activities."""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cases.models import Case, CaseActivity, CaseParty
from app.cases.schemas import (
    CASE_TYPES,
    DEBTOR_TYPES,
    INTEREST_TYPES,
    CaseActivityCreate,
    CaseCreate,
    CasePartyCreate,
    CaseStatusUpdate,
    CaseUpdate,
)
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError, NotFoundError
from app.workflow.models import WorkflowTask

# ── Case Number Generation ───────────────────────────────────────────────────


async def generate_case_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next case number for a tenant.

    Format: YYYY-NNNNN (e.g. 2026-00001)
    """
    current_year = datetime.now(UTC).year
    prefix = f"{current_year}-"

    # S226 punt 5 — GEEN is_active-filter hier (bewust). Zacht-verwijderde
    # dossiers houden hun nummer; door ze mee te tellen wordt een nummer nooit
    # hergebruikt. Zou je hier op is_active filteren, dan geeft een verwijderd
    # dossier zijn nummer vrij → een nieuw dossier krijgt datzelfde nummer →
    # de mailsync plakt oude post met dat nummer aan het nieuwe (actieve)
    # dossier. Regressietest: test_generate_case_number_does_not_reuse_soft_deleted.
    # FOR UPDATE locks the row to prevent race conditions with concurrent requests
    result = await db.execute(
        select(Case.case_number)
        .where(
            Case.tenant_id == tenant_id,
            Case.case_number.like(f"{prefix}%"),
        )
        .order_by(Case.case_number.desc())
        .limit(1)
        .with_for_update()
    )
    last_number = result.scalar_one_or_none()

    if last_number:
        seq = int(last_number.split("-")[1]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:05d}"


# ── Task Templates per Case Type (G10) ────────────────────────────────────────

INCASSO_TASKS = [
    {
        "title": "Dossier controleren en compleet maken",
        "task_type": "manual_review",
        "days": 1,
        "description": "Controleer of alle gegevens compleet zijn: "
        "facturen, contactgegevens wederpartij, renteberekening.",
    },
    {
        "title": "Herinnering versturen",
        "task_type": "send_letter",
        "days": 3,
        "description": "Stuur een herinnering naar de debiteur.",
    },
    {
        "title": "14-dagenbrief versturen (B2C)",
        "task_type": "send_letter",
        "days": 7,
        "description": "Wettelijk verplichte 14-dagenbrief voor consumenten (B2C).",
    },
    {
        "title": "Controleer betaling na herinnering",
        "task_type": "check_payment",
        "days": 14,
        "description": "Controleer of er een betaling is ontvangen na de herinnering.",
    },
    {
        "title": "Sommatie versturen",
        "task_type": "send_letter",
        "days": 21,
        "description": "Stuur een aanmaning/sommatie naar de debiteur.",
    },
    {
        "title": "Controleer betaling na sommatie",
        "task_type": "check_payment",
        "days": 35,
        "description": "Controleer of er een betaling is ontvangen na de sommatie.",
    },
    {
        "title": "Beoordeel dagvaarding",
        "task_type": "manual_review",
        "days": 42,
        "description": "Beoordeel of dagvaarding nodig is. Neem contact op met de client.",
    },
    {
        "title": "Verjaringstermijn controleren",
        "task_type": "set_deadline",
        "days": 180,
        "description": "Controleer de verjaringstermijn en onderneem actie indien nodig.",
    },
]

ADVIES_TASKS = [
    {
        "title": "Dossier controleren en compleet maken",
        "task_type": "manual_review",
        "days": 1,
        "description": "Controleer of alle stukken en gegevens compleet zijn.",
    },
    {
        "title": "Juridisch onderzoek",
        "task_type": "manual_review",
        "days": 7,
        "description": "Voer juridisch onderzoek uit en bereid advies voor.",
    },
    {
        "title": "Concept advies opstellen",
        "task_type": "generate_document",
        "days": 14,
        "description": "Stel een concept adviesbrief op voor de client.",
    },
    {
        "title": "Advies versturen aan client",
        "task_type": "send_letter",
        "days": 21,
        "description": "Verstuur het definitieve advies naar de client.",
    },
]

INSOLVENTIE_TASKS = [
    {
        "title": "Dossier controleren en compleet maken",
        "task_type": "manual_review",
        "days": 1,
        "description": "Controleer of alle stukken compleet zijn: "
        "jaarrekeningen, crediteurenlijst, etc.",
    },
    {
        "title": "Beoordeel faillissementsaanvraag of surseance",
        "task_type": "manual_review",
        "days": 3,
        "description": "Beoordeel welke procedure het meest geschikt is.",
    },
    {
        "title": "Verzoekschrift opstellen",
        "task_type": "generate_document",
        "days": 14,
        "description": "Stel het verzoekschrift op voor de rechtbank.",
    },
    {
        "title": "Indienen bij rechtbank",
        "task_type": "manual_review",
        "days": 21,
        "description": "Dien het verzoekschrift in bij de bevoegde rechtbank.",
    },
]

OVERIG_TASKS = [
    {
        "title": "Dossier controleren en compleet maken",
        "task_type": "manual_review",
        "days": 1,
        "description": "Controleer of alle gegevens en stukken compleet zijn.",
    },
    {
        "title": "Plan van aanpak bepalen",
        "task_type": "manual_review",
        "days": 3,
        "description": "Bepaal de strategie en het plan van aanpak voor deze zaak.",
    },
]

DOSSIER_TASKS = [
    {
        "title": "Dossier controleren en compleet maken",
        "task_type": "manual_review",
        "days": 1,
        "description": "Controleer of alle gegevens en stukken compleet zijn.",
    },
    {
        "title": "Plan van aanpak bepalen",
        "task_type": "manual_review",
        "days": 3,
        "description": "Bepaal de strategie en het plan van aanpak voor deze zaak.",
    },
]

TASK_TEMPLATES: dict[str, list[dict]] = {
    "incasso": INCASSO_TASKS,
    "advies": ADVIES_TASKS,
    "dossier": DOSSIER_TASKS,
}


async def _create_initial_tasks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    user_id: uuid.UUID,
) -> list[WorkflowTask]:
    """Create initial task templates for a newly created case based on case_type.

    Incasso cases skip initial tasks — the incasso pipeline manages tasks per step.
    """
    if case.case_type == "incasso":
        return []

    templates = TASK_TEMPLATES.get(case.case_type, DOSSIER_TASKS)
    created: list[WorkflowTask] = []

    for tpl in templates:
        task = WorkflowTask(
            tenant_id=tenant_id,
            case_id=case.id,
            assigned_to_id=case.assigned_to_id or user_id,
            task_type=tpl["task_type"],
            title=tpl["title"],
            description=tpl["description"],
            due_date=case.date_opened + timedelta(days=tpl["days"]),
            status="pending",
            auto_execute=False,
        )
        db.add(task)
        created.append(task)

    if created:
        await db.flush()

    return created


# ── Case CRUD ────────────────────────────────────────────────────────────────


async def list_cases(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    case_type: str | None = None,
    status: str | None = None,
    incasso_step_id: uuid.UUID | None = None,
    basenet_phase: str | None = None,
    search: str | None = None,
    client_id: uuid.UUID | None = None,
    assigned_to_id: uuid.UUID | None = None,
    date_from: "date | None" = None,
    date_to: "date | None" = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    is_active: bool = True,
    sort_by: str = "date_opened",
    sort_dir: str = "desc",
) -> tuple[list[Case], int]:
    """List cases with optional filtering and pagination."""
    from app.relations.models import Contact

    query = select(Case).where(
        Case.tenant_id == tenant_id,
        Case.is_active == is_active,  # noqa: E712
    )

    if case_type:
        query = query.where(Case.case_type == case_type)

    if status:
        query = query.where(Case.status == status)

    # B3 (S198): filter op pijplijn-STAP (sommatie/dagvaarding/vonnis = de stap,
    # niet de status). Arsalans punt: alle zaken op één stap kunnen tonen.
    if incasso_step_id:
        query = query.where(Case.incasso_step_id == incasso_step_id)

    # S243: filter op BaseNet-werkfase — geïmporteerde dossiers zonder
    # Luxis-stap (bv. "Akkoord dagvaarden") waren via het stap-filter onvindbaar.
    if basenet_phase:
        query = query.where(Case.basenet_origin_phase == basenet_phase)

    if client_id:
        # Filter cases where this contact is client, opposing party, OR a case party
        query = query.where(
            or_(
                Case.client_id == client_id,
                Case.opposing_party_id == client_id,
                Case.parties.any(CaseParty.contact_id == client_id),
            )
        )

    if assigned_to_id:
        query = query.where(Case.assigned_to_id == assigned_to_id)

    if date_from:
        query = query.where(Case.date_opened >= date_from)

    if date_to:
        query = query.where(Case.date_opened <= date_to)

    if min_amount is not None:
        query = query.where(Case.total_principal >= min_amount)

    if max_amount is not None:
        query = query.where(Case.total_principal <= max_amount)

    if search:
        from app.collections.models import Claim

        search_term = f"%{search}%"
        query = query.where(
            or_(
                Case.case_number.ilike(search_term),
                Case.description.ilike(search_term),
                Case.reference.ilike(search_term),
                # S243: vindbaar op de BaseNet-werkfase ("Akkoord dagvaarden"…) —
                # geïmporteerde dossiers zonder Luxis-stap waren anders onvindbaar.
                Case.basenet_origin_phase.ilike(search_term),
                Case.client.has(Contact.name.ilike(search_term)),
                Case.opposing_party.has(Contact.name.ilike(search_term)),
                # S239: vindbaar op het factuurnummer van een vordering — dat
                # is wat de debiteur aan de telefoon noemt.
                Case.id.in_(
                    select(Claim.case_id).where(
                        Claim.tenant_id == tenant_id,
                        Claim.is_active == True,  # noqa: E712
                        Claim.invoice_number.ilike(search_term),
                    )
                ),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Sortering met whitelist — onbekende kolom valt terug op date_opened.
    # Map string-key naar SQLAlchemy column via getattr (whitelist boven dict).
    sort_col_attr = {
        "case_number": Case.case_number,
        "status": Case.status,
        "case_type": Case.case_type,
        "date_opened": Case.date_opened,
        "total_principal": Case.total_principal,
        "total_paid": Case.total_paid,
    }.get(sort_by, Case.date_opened)
    direction = sort_col_attr.desc() if sort_dir == "desc" else sort_col_attr.asc()

    # Apply pagination, ordering, and eager loads (CQ-16)
    query = (
        query.options(
            selectinload(Case.client),
            selectinload(Case.opposing_party),
            selectinload(Case.assigned_to),
        )
        .order_by(direction.nulls_last(), Case.case_number.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.execute(query)
    cases = list(result.scalars().all())

    return cases, total


async def list_basenet_phases(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[str]:
    """S243: distinct BaseNet-werkfases (gesorteerd) voor het fase-filter."""
    result = await db.execute(
        select(Case.basenet_origin_phase)
        .where(
            Case.tenant_id == tenant_id,
            Case.basenet_origin_phase.is_not(None),
        )
        .distinct()
        .order_by(Case.basenet_origin_phase)
    )
    return [row[0] for row in result.all()]


async def get_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> Case:
    """Get a single case by ID. Raises NotFoundError if not found."""
    result = await db.execute(
        select(Case)
        .where(
            Case.id == case_id,
            Case.tenant_id == tenant_id,
        )
        .options(
            selectinload(Case.parties).selectinload(CaseParty.contact),
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")
    return case


async def get_verjaring_basis_date(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
) -> date:
    """B2 — basisdatum voor de verjaringstermijn.

    De verjaring (art. 3:307 BW) loopt vanaf de opeisbaarheid van de vordering,
    in Luxis benaderd door de verzuimdatum (`default_date`) van de OUDSTE actieve
    vordering. De openingsdatum van het dossier is de terugval voor dossiers
    zonder vorderingen. Zelfde bron als de verjaring-monitor
    (`workflow.service.check_verjaring`), zodat badge en alarm dezelfde datum tonen.
    """
    from app.collections.models import Claim

    oldest = (
        await db.execute(
            select(func.min(Claim.default_date)).where(
                Claim.tenant_id == tenant_id,
                Claim.case_id == case.id,
                Claim.is_active.is_(True),
            )
        )
    ).scalar()
    return oldest or case.date_opened


def compute_verjaring_date(basis_date: date) -> date:
    """Verjaringsdatum = basisdatum + wettelijke termijn (art. 3:307 BW).

    Server-side omdat dateutil 29 februari correct klemt naar 28 februari;
    JavaScript's setFullYear rolt door naar 1 maart (Codex-review portie 2).
    Zelfde formule als de monitor (workflow.service.check_verjaring).
    """
    from dateutil.relativedelta import relativedelta

    from app.workflow.schemas import LEGAL_CONSTRAINTS

    return basis_date + relativedelta(years=LEGAL_CONSTRAINTS["verjaring_years"])


def resolve_client_interest_defaults(client) -> tuple[str, Decimal | None, bool | None]:
    """Rente-hiërarchie voor een nieuw dossier zonder expliciete keuze (S177):
    klantkaart (default_*, handmatige override) > uit-AV-gelezen (terms_interest_*)
    > wettelijk. Gedeeld door create_case ÉN de AI-intake (die bouwt het Case-object
    zelf en sloeg de erving voorheen volledig over — S177-review).

    Returns (interest_type, contractual_rate, contractual_compound); compound None =
    laat de caller zijn eigen default houden (alleen de AV spreekt zich erover uit).
    """
    if client is not None and client.default_interest_type:
        rate = None
        if client.default_interest_type == "contractual":
            rate = client.default_contractual_rate
        return client.default_interest_type, rate, None
    if client is not None and client.terms_interest_rate is not None:
        return "contractual", client.terms_interest_rate, bool(client.terms_interest_compound)
    return "statutory", None, None


async def create_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CaseCreate,
) -> Case:
    """Create a new case with auto-generated case number."""
    # Validate case_type
    if data.case_type not in CASE_TYPES:
        raise BadRequestError(
            f"Ongeldig zaaktype: {data.case_type}. Kies uit: {', '.join(CASE_TYPES)}"
        )

    # Validate debtor_type
    if data.debtor_type not in DEBTOR_TYPES:
        raise BadRequestError(
            f"Ongeldig debiteurtype: {data.debtor_type}. Kies uit: {', '.join(DEBTOR_TYPES)}"
        )

    # Inherit interest + BIK settings from client contact when not explicitly set.
    # Lisanne demo 2026-04-07: standaard rente (DF117-02) en standaard incassokosten
    # (DF117-22) per klant moeten automatisch overgenomen worden.
    interest_type = data.interest_type
    contractual_rate = data.contractual_rate
    contractual_compound = data.contractual_compound
    bik_override = data.bik_override
    bik_override_percentage = data.bik_override_percentage
    minimum_fee = data.minimum_fee
    bik_minimum_fee = data.bik_minimum_fee
    provisie_percentage = data.provisie_percentage

    needs_client_lookup = (
        interest_type is None
        or (bik_override is None and bik_override_percentage is None)
        or minimum_fee is None
        or bik_minimum_fee is None
        or provisie_percentage is None
    )
    client = None
    if needs_client_lookup:
        client_result = await db.execute(
            select(Contact).where(
                Contact.id == data.client_id,
                Contact.tenant_id == tenant_id,
            )
        )
        client = client_result.scalar_one_or_none()

    if interest_type is None:
        inh_type, inh_rate, inh_compound = resolve_client_interest_defaults(client)
        interest_type = inh_type
        if contractual_rate is None:
            contractual_rate = inh_rate
        if inh_compound is not None:
            contractual_compound = inh_compound

    # DF117-22: BIK inheritance — only inherit when neither field was explicitly set.
    # Percentage takes precedence over fixed amount (matches the case-level precedence).
    if bik_override is None and bik_override_percentage is None and client:
        if client.default_bik_override_percentage is not None:
            bik_override_percentage = client.default_bik_override_percentage
        elif client.default_bik_override is not None:
            bik_override = client.default_bik_override

    # DF120: minimum_fee inheritance — same pattern as BIK override
    if minimum_fee is None and client and client.default_minimum_fee is not None:
        minimum_fee = client.default_minimum_fee

    # DF138-16: bik_minimum_fee inheritance — aparte bodem voor BIK-percentage,
    # los van het provisie-minimum (minimum_fee).
    if bik_minimum_fee is None and client and client.default_bik_minimum_fee is not None:
        bik_minimum_fee = client.default_bik_minimum_fee

    # S210: provisie-% inheritance — zelfde patroon; alleen overnemen als het
    # dossier het niet expliciet zet. Basis blijft de dossierdefault (collected_amount).
    if provisie_percentage is None and client and client.default_provisie_percentage is not None:
        provisie_percentage = client.default_provisie_percentage

    # Validate interest_type
    if interest_type not in INTEREST_TYPES:
        raise BadRequestError(
            f"Ongeldig rentetype: {interest_type}. Kies uit: {', '.join(INTEREST_TYPES)}"
        )

    # Contractual rate required for contractual interest
    if interest_type == "contractual" and contractual_rate is None:
        raise BadRequestError("Contractuele rente vereist een tarief (contractual_rate)")

    # Generate case number
    case_number = await generate_case_number(db, tenant_id)

    case = Case(
        tenant_id=tenant_id,
        case_number=case_number,
        case_type=data.case_type,
        debtor_type=data.debtor_type,
        status="nieuw",
        description=data.description,
        reference=data.reference,
        court_case_number=data.court_case_number,
        court_name=data.court_name,
        judge_name=data.judge_name,
        chamber=data.chamber,
        procedure_type=data.procedure_type,
        procedure_phase=data.procedure_phase,
        interest_type=interest_type,
        contractual_rate=contractual_rate,
        contractual_compound=contractual_compound,
        client_id=data.client_id,
        opposing_party_id=data.opposing_party_id,
        billing_contact_id=data.billing_contact_id,
        contact_terms_id=data.contact_terms_id,
        assigned_to_id=data.assigned_to_id or user_id,
        date_opened=data.date_opened,
        budget=data.budget,
        bik_override=bik_override,
        bik_override_percentage=bik_override_percentage,
        nakosten_type=data.nakosten_type,
        hourly_rate=data.hourly_rate,
        payment_term_days=data.payment_term_days,
        collection_strategy=data.collection_strategy,
        debtor_notes=data.debtor_notes,
        billing_method=data.billing_method,
        fixed_price_amount=data.fixed_price_amount,
        budget_hours=data.budget_hours,
        provisie_percentage=provisie_percentage,
        provisie_base=data.provisie_base,
        fixed_case_costs=data.fixed_case_costs,
        minimum_fee=minimum_fee,
        bik_minimum_fee=bik_minimum_fee,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)

    # Log activity
    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="status_change",
        title="Zaak aangemaakt",
        description=f"Zaak {case_number} aangemaakt als {data.case_type}",
        new_status="nieuw",
    )
    db.add(activity)
    await db.flush()

    # G10: Create initial task templates based on case type
    await _create_initial_tasks(db, tenant_id, case, user_id)

    # S143: Incasso-dossiers krijgen automatisch de eerste pipeline-stap
    # toegewezen. Zonder dit verschijnen ze niet in de incasso-pagina batch-
    # toolbar en blokkeert auto-advance op een lege step-id. Per Lisanne S141
    # demo: 42 van 45 incasso-dossiers waren nooit aan een stap toegewezen.
    if case.case_type == "incasso":
        from app.incasso.service import list_pipeline_steps, move_case_to_step

        steps = await list_pipeline_steps(db, tenant_id, active_only=True)
        # S166 (punt 3 + B2C-anders-dan-B2B): kies de eerste stap die geldt voor het
        # debiteurtype van dit dossier. Zo start een B2C-dossier op de 14-dagenbrief
        # (debtor_type "b2c", laagste sort_order) en een B2B-dossier op "Eerste sommatie"
        # — de B2C-only 14-dagenbrief wordt voor een B2B-dossier overgeslagen.
        valid_steps = [
            s for s in steps if s.debtor_type in ("both", case.debtor_type)
        ]
        first_step = (
            min(valid_steps, key=lambda s: s.sort_order) if valid_steps else None
        )
        if first_step:
            await move_case_to_step(
                db,
                tenant_id,
                case,
                first_step,
                user_id=user_id,
                trigger_type="auto",
            )

    return case


async def update_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: CaseUpdate,
    user_id: uuid.UUID | None = None,
) -> Case:
    """Update case details (not status — use update_case_status for that)."""
    case = await get_case(db, tenant_id, case_id)

    update_data = data.model_dump(exclude_unset=True)

    # Validate interest_type if being changed
    if "interest_type" in update_data and update_data["interest_type"] not in INTEREST_TYPES:
        raise BadRequestError(
            f"Ongeldig rentetype: {update_data['interest_type']}. "
            f"Kies uit: {', '.join(INTEREST_TYPES)}"
        )

    # BUG-65: When switching away from contractual interest, force-reset related fields
    # Use direct assignment (not setdefault) because frontend may send null explicitly
    if "interest_type" in update_data and update_data["interest_type"] != "contractual":
        update_data["contractual_rate"] = None
        update_data["contractual_compound"] = False

    # AUDIT-23: BIK override mag niet hoger dan WIK-staffel bij B2C
    if "bik_override" in update_data and update_data["bik_override"] is not None:
        debtor_type = update_data.get("debtor_type", case.debtor_type)
        if debtor_type == "b2c":
            # Calculate max BIK from claims principal
            from app.collections.models import Claim
            from app.collections.wik import calculate_bik

            claims_result = await db.execute(
                select(func.coalesce(func.sum(Claim.principal_amount), Decimal("0")))
                .where(Claim.case_id == case_id, Claim.tenant_id == tenant_id)
            )
            total_principal = claims_result.scalar() or Decimal("0")
            include_btw = not case.client.is_btw_plichtig if case.client else False
            max_bik = calculate_bik(total_principal, include_btw=include_btw)["bik_inclusive"]
            if update_data["bik_override"] > max_bik:
                raise BadRequestError(
                    f"BIK override (€{update_data['bik_override']}) mag bij B2C niet hoger zijn "
                    f"dan de WIK-staffel (€{max_bik})"
                )

    # A pipeline-step change must run through move_case_to_step (audit #97
    # follow-up) so it leaves a CaseStepHistory + pipeline_change activity and
    # resets step_entered_at — a bare setattr skips that audit trail. Only a
    # change to a different, non-null step transitions; clearing the step
    # (null) keeps the plain assignment, same as before.
    _unset = object()
    new_step_id = update_data.get("incasso_step_id", _unset)
    transition = (
        new_step_id is not _unset
        and new_step_id is not None
        and new_step_id != case.incasso_step_id
    )
    if transition:
        update_data.pop("incasso_step_id")

    for field, value in update_data.items():
        setattr(case, field, value)

    if transition:
        from app.incasso.models import IncassoPipelineStep
        from app.incasso.service import move_case_to_step

        target = (
            await db.execute(
                select(IncassoPipelineStep).where(
                    IncassoPipelineStep.id == new_step_id,
                    IncassoPipelineStep.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if target is None:
            raise BadRequestError("Onbekende incasso-stap")
        await move_case_to_step(
            db, tenant_id, case, target, user_id=user_id, trigger_type="manual"
        )

    await db.flush()
    await db.refresh(case)
    return case


async def update_case_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CaseStatusUpdate,
) -> Case:
    """Zet de zaak-status (B3, S198 — 4 vaste waarden).

    De verwijderde workflow-engine leunde op lege configuratietabellen en liet
    elke statuswijziging falen. De directe 4-status-logica is leidend:
      - Afsluiten  → 'afgesloten' (+ date_closed); geblokkeerd zolang er nog
        onafgewikkelde derdengelden op de zaak staan (FIN-2, Voda art. 6.19).
      - Heropenen  → 'nieuw'/'in_behandeling' (date_closed leeg).
      - 'betaald'  → (+ date_closed); normaal automatisch bij €0 openstaand.
    De incasso-pijplijn stuurt de status verder (move_case_to_step).
    """
    from app.cases.schemas import CASE_STATUSES

    new_status = data.new_status
    if new_status not in CASE_STATUSES:
        raise BadRequestError(
            f"Ongeldige status: {new_status}. Kies uit: {', '.join(CASE_STATUSES)}"
        )

    case = await get_case(db, tenant_id, case_id)
    old_status = case.status

    if new_status == old_status:
        return case

    # Afsluiten mag niet zolang er nog client-geld op de derdengeldenrekening staat
    # (of trust-transacties op goedkeuring wachten) — zelfde guard als archiveren
    # en de terminale 'Afgesloten'-pijplijnstap.
    if new_status == "afgesloten":
        from app.trust_funds.service import get_unsettled_reason

        reason = await get_unsettled_reason(db, tenant_id, case_id)
        if reason:
            raise BadRequestError(reason)

    # 'betaald' betekent letterlijk volledig voldaan — niet handmatig sluiten met een
    # openstaand saldo (S198-review, Codex #2). Afsluiten mét restant = 'afgesloten'.
    if new_status == "betaald":
        from app.collections.service import get_case_outstanding

        try:
            outstanding = await get_case_outstanding(db, tenant_id, case)
        except Exception as e:
            # AUDIT-H2: fail-CLOSED. Kan het saldo niet berekend worden (bv. rente
            # zonder geseede tarieven), dan mag de zaak niet stil op 'betaald'
            # sluiten — het oude fail-open nam €0 aan, waardoor een dossier mét
            # openstaand saldo geruisloos uit de werkvoorraad verdween.
            raise BadRequestError(
                "Kan het openstaande saldo niet berekenen — probeer het opnieuw."
            ) from e
        if outstanding > Decimal("0.01"):
            raise BadRequestError(
                f"Zaak kan niet op 'betaald' gezet worden: er staat nog € {outstanding} "
                f"open. Gebruik 'Afsluiten' om de zaak met een restant af te sluiten."
            )

    case.status = new_status
    if new_status in ("betaald", "afgesloten"):
        case.date_closed = date.today()
        # S207: bevries de rente op het afwikkelmoment (laatste betaaldatum,
        # anders sluitdatum). Zo rent een handmatig afgesloten zaak niet door.
        # Een reeds handmatig gezette rentedatum blijft staan.
        if case.interest_freeze_date is None:
            from app.collections.models import Payment

            last_pay = (
                await db.execute(
                    select(func.max(Payment.payment_date)).where(
                        Payment.case_id == case_id,
                        Payment.tenant_id == tenant_id,
                        Payment.is_active.is_(True),
                    )
                )
            ).scalar()
            case.interest_freeze_date = last_pay or date.today()
    else:
        # Heropenen: dossier is weer in behandeling → sluitdatum leeg.
        case.date_closed = None
        # S207: heropend → rente weer laten lopen; automatische bevriezing wissen.
        case.interest_freeze_date = None
        # S198-review (Fable #3): stond de zaak op een TERMINALE eindstap
        # (Betaald/Afgesloten)? Met status in_behandeling zou ze onzichtbaar blijven op
        # het pijplijn-bord en in de wachtrijen (die op terminale stap-id filteren).
        # Wis de stap → de zaak komt als "niet toegewezen" terug op het bord.
        if case.incasso_step_id is not None:
            from app.incasso.models import IncassoPipelineStep

            step = (
                await db.execute(
                    select(IncassoPipelineStep).where(
                        IncassoPipelineStep.id == case.incasso_step_id,
                        IncassoPipelineStep.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            if step is not None and step.is_terminal:
                case.incasso_step_id = None
                case.step_entered_at = None

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="status_change",
        title=f"Status gewijzigd: {old_status} → {new_status}",
        description=data.note,
        old_status=old_status,
        new_status=new_status,
    )
    db.add(activity)
    await db.flush()

    # S223 (huisregel P3) — zaak gesloten → open AI-concepten vervallen zodat er geen
    # concept blijft staan dat later per ongeluk verstuurd wordt.
    # S224 (veegsessie): óók open follow-up-adviezen sluiten — een pending advies op
    # een gesloten zaak wordt bij heropenen weer zichtbaar (dubbel-verstuur-risico,
    # gemeten op IN100613: gesloten 15/7 mét pending advies van 13/7).
    if new_status in ("betaald", "afgesloten"):
        from app.ai_agent.draft_service import discard_open_drafts_on_close
        from app.incasso.service import supersede_open_recommendations

        await discard_open_drafts_on_close(db, tenant_id, case_id)
        await supersede_open_recommendations(
            db, tenant_id, case_id, reason=f"Zaak gesloten (status '{new_status}')"
        )

        # S240 (Fable-review) — gesloten zaak → open betaalbelofte-taken zijn
        # achterhaald ('skipped', S236-conventie); anders blijven ze eeuwig
        # open op een dicht dossier (S239-spooktaken-patroon).
        from app.collections.service import close_payment_promise_tasks

        await close_payment_promise_tasks(
            db, tenant_id, case_id, outcome="skipped"
        )

    await db.refresh(case)
    return case


async def delete_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> None:
    """Soft-delete a case by setting is_active=False.

    FIN-2: refuse to archive a case while it still holds client money on the
    trust account (or has pending trust transactions) — archiving would hide
    derdengelden that must first be paid out/offset (Voda art. 6.19).
    """
    from app.trust_funds.service import get_unsettled_reason
    from app.workflow.service import skip_open_tasks_for_case

    case = await get_case(db, tenant_id, case_id)

    reason = await get_unsettled_reason(db, tenant_id, case_id)
    if reason:
        raise BadRequestError(reason)

    case.is_active = False
    # Close out the case's open tasks so they stop surfacing as overdue /
    # upcoming / on the agenda once the case is archived (AUDIT-H24).
    await skip_open_tasks_for_case(db, tenant_id, case_id)
    await db.flush()


# ── Conflict Check ───────────────────────────────────────────────────────


async def conflict_check(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    role: str,
) -> list[dict]:
    """Check if a contact has conflicting roles in existing cases.

    When adding a contact as 'client', check if they appear as opposing_party
    in any active case (and vice versa). Returns a list of conflicting cases.

    Args:
        contact_id: The contact to check.
        role: The intended role — 'client' or 'opposing_party'.
    """
    if role == "client":
        # Contact is being added as client — check if they're opposing party somewhere
        query = select(Case).where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            Case.opposing_party_id == contact_id,
        )
    elif role == "opposing_party":
        # Contact is being added as opposing party — check if they're client somewhere
        query = select(Case).where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            Case.client_id == contact_id,
        )
    else:
        return []

    # Eager load client + opposing_party to avoid lazy loading crash in async context
    query = query.options(
        selectinload(Case.client),
        selectinload(Case.opposing_party),
    )

    result = await db.execute(query)
    cases = list(result.scalars().all())

    return [
        {
            "case_id": str(c.id),
            "case_number": c.case_number,
            "case_type": c.case_type,
            "status": c.status,
            "role_in_case": "wederpartij" if role == "client" else "client",
            "client_name": c.client.name if c.client else None,
            "opposing_party_name": c.opposing_party.name if c.opposing_party else None,
        }
        for c in cases
    ]


# ── Case Parties ─────────────────────────────────────────────────────────────


async def add_case_party(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: CasePartyCreate,
) -> CaseParty:
    """Add a party (deurwaarder, rechtbank, etc.) to a case."""
    # Verify the case exists
    await get_case(db, tenant_id, case_id)

    party = CaseParty(
        tenant_id=tenant_id,
        case_id=case_id,
        contact_id=data.contact_id,
        role=data.role,
    )
    db.add(party)
    await db.flush()

    # Re-query with explicit eager loading so contact is available for serialisation
    result = await db.execute(
        select(CaseParty).where(CaseParty.id == party.id).options(selectinload(CaseParty.contact))
    )
    return result.scalar_one()


async def remove_case_party(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    party_id: uuid.UUID,
) -> None:
    """Remove a party from a case."""
    result = await db.execute(
        select(CaseParty).where(
            CaseParty.id == party_id,
            CaseParty.tenant_id == tenant_id,
        )
    )
    party = result.scalar_one_or_none()
    if party is None:
        raise NotFoundError("Partij niet gevonden")
    await db.delete(party)
    await db.flush()


# ── Case Activities ──────────────────────────────────────────────────────────


async def add_activity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CaseActivityCreate,
) -> CaseActivity:
    """Add an activity entry to a case."""
    # Verify the case exists
    await get_case(db, tenant_id, case_id)

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case_id,
        user_id=user_id,
        activity_type=data.activity_type,
        title=data.title,
        description=data.description,
    )
    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return activity


async def list_activities(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CaseActivity], int]:
    """List activities for a case, newest first."""
    # Verify the case exists
    await get_case(db, tenant_id, case_id)

    query = select(CaseActivity).where(
        CaseActivity.case_id == case_id,
        CaseActivity.tenant_id == tenant_id,
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        query.order_by(CaseActivity.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )

    result = await db.execute(query)
    activities = list(result.scalars().all())

    return activities, total
