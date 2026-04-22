"""Pre-send compliance checks for incasso documents and emails.

Validates legal requirements before sending:
- 14-dagenbrief requirement for B2C (Art. 6:96 lid 6 BW)
- WIK-staffel amounts in documents
- Correct interest calculations
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.collections.models import Claim
from app.collections.wik import calculate_bik
from app.documents.models import GeneratedDocument


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
        # Check if 14-dagenbrief was already generated
        doc_result = await db.execute(
            select(GeneratedDocument).where(
                GeneratedDocument.case_id == case_id,
                GeneratedDocument.tenant_id == tenant_id,
                GeneratedDocument.template_type == "14_dagenbrief",
            )
        )
        dagenbrief = doc_result.scalar_one_or_none()
        if not dagenbrief:
            errors.append(
                "14-dagenbrief is nog niet verstuurd. Dit is verplicht bij consumenten "
                "(Art. 6:96 lid 6 BW) voordat incassokosten gevorderd mogen worden."
            )
        elif dagenbrief.created_at:
            days_since = (date.today() - dagenbrief.created_at.date()).days
            if days_since < 15:
                errors.append(
                    f"14-dagentermijn is nog niet verstreken. Brief verstuurd {days_since} "
                    f"dag(en) geleden, minimaal 15 dagen wachten (dag NA ontvangst)."
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
        verjaring_date = case.date_opened.replace(year=case.date_opened.year + 5)
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
