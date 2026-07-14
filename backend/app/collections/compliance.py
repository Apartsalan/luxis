"""Pre-send compliance checks for incasso documents and emails.

Validates legal requirements before sending:
- 14-dagenbrief requirement for B2C (Art. 6:96 lid 6 BW)
- WIK-staffel amounts in documents
- Correct interest calculations
"""

import uuid
from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.collections.models import Claim
from app.collections.wik import calculate_bik
from app.incasso.models import CaseStepHistory, IncassoPipelineStep

# Naam van de wettelijk verplichte B2C-startstap (art. 6:96 lid 6 BW). Zie
# incasso.service.DEFAULT_PIPELINE_STEPS.
DAGENBRIEF_STEP_NAME = "14-dagenbrief"

# ── Renteoverzicht-bijlage (S211) ─────────────────────────────────────────────
#
# Sjabloontypes waarbij het renteoverzicht als PDF-bijlage meegaat: de
# 14-dagenbrief en de eerste sommatie (besluit C, S210). Match op template_type
# i.p.v. sort_order — dat is stabiel op prod (0/1) én in een verse test-DB waar
# de nummering bij 1 begint.
RENTE_BIJLAGE_TEMPLATE_TYPES = frozenset({"14_dagenbrief", "sommatie_drukte"})

# Rechtsvormen met BEPERKTE aansprakelijkheid → géén renteoverzicht-bijlage
# (besluit A, S210). Kernwoord-match op de KvK-rechtsvorm, GEEN exacte string:
# de KvK levert varianten ("Besloten Vennootschap met gewone structuur", ...).
# Let op: match op de VOLLEDIGE term "besloten/naamloze vennootschap" — niet op
# los "vennootschap", want een VOF ("vennootschap onder firma") en CV
# ("commanditaire vennootschap") zijn juist WÉL privé aansprakelijk.
EXCLUDED_LEGAL_FORM_KEYWORDS = (
    "besloten vennootschap",  # BV
    "naamloze vennootschap",  # NV
    "stichting",
    "coöperat",  # coöperatie / coöperatieve vereniging
    "cooperat",  # zonder trema (encoding-veiligheid)
)


def should_attach_rente_bijlage(opposing_party, debtor_type: str | None = None) -> bool:
    """Moet het renteoverzicht als PDF-bijlage mee bij de 14-dagenbrief/eerste
    sommatie? Ja bij een privé aansprakelijke wederpartij (particulier,
    eenmanszaak, VOF, maatschap, CV), nee bij een BV/NV/stichting/coöperatie.

    Leest ALLEEN het opgeslagen `legal_form`-veld (+ debtor_type) — NOOIT live
    de KvK. Besluiten A/B/C (S210):
    - b2c/particulier → altijd wél (privé aansprakelijk).
    - zakelijk, rechtsvorm bekend én beperkt aansprakelijk → niet.
    - zakelijk, rechtsvorm onbekend/leeg → wél (besluit B: veilige kant).
    """
    if debtor_type == "b2c":
        return True
    if opposing_party is None:
        return True  # geen partij bekend → veilige kant (besluit B)
    legal_form = (getattr(opposing_party, "legal_form", None) or "").lower()
    return not any(kw in legal_form for kw in EXCLUDED_LEGAL_FORM_KEYWORDS)

# Minimum aantal dagen tussen de 14-dagenbrief en een BIK-claimende sommatie.
# 14 dagen termijn + 1 dag (de termijn loopt vanaf de dag NÁ ontvangst) → nooit
# eerder dan 15 dagen versturen.
DAGENBRIEF_MIN_DAYS = 15


async def get_dagenbrief_entered_at(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID
) -> date | None:
    """Datum waarop de zaak de 14-dagenbrief-stap binnenkwam, of None als de zaak
    die stap nooit heeft doorlopen. Leest het ECHTE spoor (CaseStepHistory) i.p.v.
    de generated_documents-tabel, die het live verzendpad niet meer vult (S203 #5/#7).
    """
    result = await db.execute(
        select(CaseStepHistory.entered_at)
        .join(IncassoPipelineStep, CaseStepHistory.step_id == IncassoPipelineStep.id)
        .where(
            CaseStepHistory.tenant_id == tenant_id,
            CaseStepHistory.case_id == case_id,
            IncassoPipelineStep.name == DAGENBRIEF_STEP_NAME,
        )
        .order_by(CaseStepHistory.entered_at.asc())
        .limit(1)
    )
    entered = result.scalar_one_or_none()
    return entered.date() if entered else None


async def get_dagenbrief_sent_at(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID
) -> date | None:
    """Datum waarop de 14-dagenbrief AANTOONBAAR is verstuurd, of None.

    Sterker dan `get_dagenbrief_entered_at` (S205, verstuurd-proxy verstevigd): telt
    alleen een 14-dagenbrief-staphistorie-rij waarvan `email_sent` is gezet — bewijs
    dat er echt een brief de deur uitging. Een zaak die door de stap is geschoven
    zonder ooit iets te versturen telt dus NIET meer als 'verstuurd'. Een buiten
    Luxis verstuurde brief wordt via de 'toch versturen'-override afgehandeld, niet
    hier. Het echte verzendpad (`mark_current_step_communication_sent`) zet die vlag.

    S207 (review S205): de teruggegeven datum is het échte verzendmoment
    (`email_sent_at`), niet de stap-binnenkomst — die kan dagen eerder liggen
    (batch pas later gedraaid) en zou de wettelijke 15-dagen-klok te vroeg laten
    starten. Fallback op `entered_at` alleen voor oude rijen zonder tijdstempel
    (gedrag gelijk aan vóór deze fix; prod had er nul).
    """
    result = await db.execute(
        select(CaseStepHistory.email_sent_at, CaseStepHistory.entered_at)
        .join(IncassoPipelineStep, CaseStepHistory.step_id == IncassoPipelineStep.id)
        .where(
            CaseStepHistory.tenant_id == tenant_id,
            CaseStepHistory.case_id == case_id,
            IncassoPipelineStep.name == DAGENBRIEF_STEP_NAME,
            CaseStepHistory.email_sent.is_(True),
        )
        .order_by(CaseStepHistory.entered_at.asc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    sent_at = row.email_sent_at or row.entered_at
    return sent_at.date() if sent_at else None


async def check_dagenbrief_gate(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case,
    step_name: str,
    *,
    case_number: str,
) -> str | None:
    """Wettelijke waarborg art. 6:96 lid 6 BW — de ENIGE bron van waarheid voor de
    14-dagenbrief-blokkade. Wordt gedeeld door alle verzendpaden (batch, follow-up
    'Uitvoeren', AI-concept) zodat de regel niet uit elkaar loopt.

    Geeft een blokkade-REDEN (str) terug als een BIK-claimende sommatie bij een
    consument NIET verstuurd mag worden, anders None. De gate geldt alleen voor b2c
    en NOOIT voor de 14-dagenbrief-stap zelf (die brief moet altijd verstuurd kunnen
    worden). Een reden betekent: blokkeren (overslaan mét reden, of 'toch versturen').
    """
    if getattr(case, "debtor_type", None) != "b2c" or step_name == DAGENBRIEF_STEP_NAME:
        return None

    sent_at = await get_dagenbrief_sent_at(db, tenant_id, case.id)
    if sent_at is None:
        return (
            f"{case_number}: 14-dagenbrief nog niet verstuurd — verplicht bij "
            f"consumenten vóór incassokosten (art. 6:96 lid 6 BW)"
        )
    days_since = (date.today() - sent_at).days
    if days_since < DAGENBRIEF_MIN_DAYS:
        return (
            f"{case_number}: 14-dagentermijn nog niet verstreken — 14-dagenbrief "
            f"{days_since} dag(en) geleden, minimaal {DAGENBRIEF_MIN_DAYS} dagen "
            f"wachten (art. 6:96 lid 6 BW)"
        )
    return None


# Stap-categorieën die BIK/incassokosten claimen (sommaties + gerechtelijk). Alleen
# op deze stappen geldt de 14-dagenbrief-gate voor het losse verzendpad; op
# administratieve/regeling-stappen (bv. 'Opvragen stukken', 'Treffen van regeling')
# is een consumenten-mail géén BIK-claimende sommatie en blokkeren we niets.
SOMMATIE_STEP_CATEGORIES = ("minnelijk", "gerechtelijk")


async def check_dagenbrief_gate_for_case(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID
) -> str | None:
    """14-dagenbrief-gate voor het LOSSE verzendpad (compose/send), waar alleen een
    case_id meekomt. Laadt zelf de zaak + huidige stap en gate't alleen als de zaak
    op een BIK-claimende sommatie-/dagvaardingsstap staat. Geeft None (geen blokkade)
    voor een zaak zonder stap of op een niet-sommatie-stap.
    """
    from app.incasso.models import IncassoPipelineStep

    case = (
        await db.execute(
            select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if case is None or case.incasso_step_id is None:
        return None

    step = (
        await db.execute(
            select(IncassoPipelineStep).where(
                IncassoPipelineStep.id == case.incasso_step_id,
                IncassoPipelineStep.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if step is None or step.step_category not in SOMMATIE_STEP_CATEGORIES:
        return None

    return await check_dagenbrief_gate(
        db, tenant_id, case, step.name, case_number=case.case_number
    )


async def record_dagenbrief_override(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID | None,
    reason: str,
) -> None:
    """Onuitwisbaar spoor van een 'toch versturen'-override (S205). Legt vast WIE,
    WANNEER en welke zaak — de gebruiker hoeft géén reden te typen (bewuste keuze
    Arsalan: de knop mag niet moeilijker zijn dan een ja/nee). Schrijft een
    CaseActivity én een notitie op de open staphistorie-rij van de huidige stap.
    """
    from app.cases.models import CaseActivity

    db.add(
        CaseActivity(
            tenant_id=tenant_id,
            case_id=case_id,
            user_id=user_id,
            activity_type="compliance_override",
            title="14-dagenbrief-waarschuwing overschreven ('toch versturen')",
            description=(
                "Sommatie handmatig verstuurd ondanks de 14-dagenbrief-blokkade. "
                f"Systeemwaarschuwing was: {reason}"
            ),
        )
    )

    # Notitie op de open staphistorie-rij (indien aanwezig) — extra spoor in de
    # pijplijn-tijdlijn naast de activiteit.
    case = (
        await db.execute(
            select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if case is not None and case.incasso_step_id is not None:
        history = (
            await db.execute(
                select(CaseStepHistory)
                .where(
                    CaseStepHistory.tenant_id == tenant_id,
                    CaseStepHistory.case_id == case_id,
                    CaseStepHistory.step_id == case.incasso_step_id,
                    CaseStepHistory.exited_at.is_(None),
                )
                .order_by(CaseStepHistory.entered_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if history is not None:
            stamp = date.today().strftime("%d-%m-%Y")
            note = f"[{stamp}] 14-dagenbrief-blokkade overschreven ('toch versturen')."
            history.notes = f"{history.notes}\n{note}" if history.notes else note

    await db.flush()


async def pre_send_compliance_check(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    document_type: str | None = None,
) -> dict:
    """Run compliance checks before sending a document or email.

    Returns dict with:
        - passed: bool — all checks passed
        - warnings: list of advisory warnings
        - errors: list of blocking errors
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Load case
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        return {"passed": False, "errors": ["Dossier niet gevonden"], "warnings": []}

    is_b2c = case.debtor_type == "b2c"

    # Load claims for financial checks
    claims_result = await db.execute(
        select(Claim).where(Claim.case_id == case_id, Claim.tenant_id == tenant_id)
    )
    claims = list(claims_result.scalars().all())
    total_principal = sum(c.principal_amount for c in claims)

    # ── Check 1: 14-dagenbrief requirement (B2C only) ──────────────────
    if is_b2c and document_type in ("sommatie", "tweede_sommatie", "dagvaarding"):
        # Leest het echte VERZEND-spoor (stap-historie met email_sent), niet de lege
        # generated_documents-tabel (S203 #5) en niet enkel stap-binnenkomst (S205).
        entered_at = await get_dagenbrief_sent_at(db, tenant_id, case_id)
        if entered_at is None:
            errors.append(
                "14-dagenbrief is nog niet verstuurd. Dit is verplicht bij consumenten "
                "(Art. 6:96 lid 6 BW) voordat incassokosten gevorderd mogen worden."
            )
        else:
            days_since = (date.today() - entered_at).days
            if days_since < DAGENBRIEF_MIN_DAYS:
                errors.append(
                    f"14-dagentermijn is nog niet verstreken. Brief verstuurd {days_since} "
                    f"dag(en) geleden, minimaal {DAGENBRIEF_MIN_DAYS} dagen wachten "
                    f"(dag NA ontvangst)."
                )

    # ── Check 2: BIK override validation (B2C) ────────────────────────
    if is_b2c and case.bik_override is not None:
        include_btw = not case.client.is_btw_plichtig if case.client else False
        max_bik = calculate_bik(total_principal, include_btw=include_btw)["bik_inclusive"]
        if case.bik_override > max_bik:
            errors.append(
                f"BIK override (€{case.bik_override}) overschrijdt de WIK-staffel "
                f"(€{max_bik}). Bij consumenten is dit niet toegestaan."
            )

    # ── Check 3: Missing opposing party ────────────────────────────────
    if not case.opposing_party_id:
        errors.append("Geen wederpartij (debiteur) gekoppeld aan dit dossier.")

    # ── Check 4: No claims ─────────────────────────────────────────────
    if not claims:
        errors.append("Geen vorderingen in dit dossier. Voeg eerst een vordering toe.")

    # ── Check 5: Missing default date on claims ────────────────────────
    for claim in claims:
        if not claim.default_date:
            warnings.append(
                f"Vordering '{claim.description}' heeft geen verzuimdatum. "
                f"Zonder verzuimdatum kan geen rente berekend worden."
            )

    # ── Check 6: Verjaring warning ─────────────────────────────────────
    if case.date_opened:
        verjaring_date = case.date_opened + relativedelta(years=5)
        days_until = (verjaring_date - date.today()).days
        if days_until <= 0:
            warnings.append(
                f"VERJARING: Deze zaak is mogelijk verjaard op {verjaring_date.strftime('%d-%m-%Y')} "
                f"(Art. 3:307 BW). Controleer of stuiting heeft plaatsgevonden."
            )
        elif days_until <= 90:
            warnings.append(
                f"Verjaring nadert op {verjaring_date.strftime('%d-%m-%Y')} "
                f"(nog {days_until} dagen). Overweeg een stuitingshandeling."
            )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "case_number": case.case_number,
        "debtor_type": case.debtor_type,
        "total_principal": str(total_principal),
    }
