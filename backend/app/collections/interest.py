"""Interest calculation engine — the mathematical core of the incasso module.

Implements Dutch statutory interest calculation per:
- Art. 6:119 BW (wettelijke rente) — COMPOUND, annual capitalization
- Art. 6:119a BW (handelsrente) — COMPOUND, annual capitalization
- Art. 6:119b BW (overheidshandelsrente) — COMPOUND, annual capitalization
- Contractual interest — SIMPLE or COMPOUND (configurable per case)

Key rules:
1. Interest accrues from the "verzuimdatum" (default date) — NOT from 1 January
2. The compounding year runs from the default date, NOT from calendar year start
3. "Telkens na afloop van een jaar" — at the end of each full year since the
   default date, accrued interest is capitalized (added to principal)
4. When the rate changes mid-period, the period is split into sub-periods
5. All calculations use Decimal with ROUND_HALF_UP to 2 decimal places
6. Pro-rata calculation: days/365 (consistent, even in leap years)

Example compound interest calculation:
  Principal: €5,000, default date: 2024-03-15, calc date: 2026-06-15
  Year 1: 2024-03-15 → 2025-03-15 (rate may change within this period)
  Year 2: 2025-03-15 → 2026-03-15 (capitalize year 1 interest, then compute)
  Remaining: 2026-03-15 → 2026-06-15 (partial year, no capitalization)
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collections.models import InterestRate

# Precision constant
TWO_PLACES = Decimal("0.01")
DAYS_IN_YEAR = Decimal("365")


def _round2(value: Decimal) -> Decimal:
    """Round a Decimal to 2 places using ROUND_HALF_UP."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


# ── Rate Schedule Builder ────────────────────────────────────────────────────


async def get_rates_from_db(
    db: AsyncSession,
    rate_type: str,
) -> list[tuple[date, Decimal]]:
    """Fetch interest rates from the database, ordered by date.

    Returns: list of (effective_from, rate) tuples
    """
    result = await db.execute(
        select(InterestRate.effective_from, InterestRate.rate)
        .where(InterestRate.rate_type == rate_type)
        .order_by(InterestRate.effective_from)
    )
    return [(row[0], row[1]) for row in result.all()]


def build_rate_schedule(
    start: date,
    end: date,
    rates: list[tuple[date, Decimal]],
) -> list[tuple[date, date, Decimal]]:
    """Build a list of (period_start, period_end, rate) for a date range.

    Takes the full rate history and clips it to the [start, end) range.
    Returns segments where each segment has a constant rate.

    Example:
        rates = [(2024-01-01, 7%), (2025-01-01, 6%), (2026-01-01, 4%)]
        start = 2024-06-15, end = 2025-06-15
        → [(2024-06-15, 2025-01-01, 7%), (2025-01-01, 2025-06-15, 6%)]
    """
    if not rates or start >= end:
        return []

    schedule: list[tuple[date, date, Decimal]] = []

    # Find the applicable rate at 'start'
    current_rate: Decimal | None = None
    for effective_from, rate in rates:
        if effective_from <= start:
            current_rate = rate
        else:
            break

    if current_rate is None:
        # No rate found before start — use the earliest available rate
        current_rate = rates[0][1]

    # Build segments
    segment_start = start

    for effective_from, rate in rates:
        if effective_from <= start:
            continue  # Already accounted for
        if effective_from >= end:
            break  # Past our range

        # A rate change within our range — close current segment
        schedule.append((segment_start, effective_from, current_rate))
        segment_start = effective_from
        current_rate = rate

    # Close the final segment
    if segment_start < end:
        schedule.append((segment_start, end, current_rate))

    return schedule


# ── Simple Interest ──────────────────────────────────────────────────────────


def calculate_simple_interest(
    principal: Decimal,
    default_date: date,
    calc_date: date,
    rates: list[tuple[date, Decimal]],
) -> tuple[Decimal, list[dict]]:
    """Calculate simple (enkelvoudige) interest.

    No capitalization — interest is always calculated on the original principal.

    Returns: (total_interest, list of period details)
    """
    if calc_date <= default_date:
        return Decimal("0"), []

    schedule = build_rate_schedule(default_date, calc_date, rates)
    total_interest = Decimal("0")
    periods: list[dict] = []

    for seg_start, seg_end, rate in schedule:
        days = (seg_end - seg_start).days
        interest = _round2(principal * (rate / Decimal("100")) * Decimal(days) / DAYS_IN_YEAR)
        total_interest += interest
        periods.append(
            {
                "start_date": seg_start,
                "end_date": seg_end,
                "days": days,
                "rate": rate,
                "principal": principal,
                "interest": interest,
            }
        )

    return _round2(total_interest), periods


# ── Compound Interest ────────────────────────────────────────────────────────


def calculate_compound_interest(
    principal: Decimal,
    default_date: date,
    calc_date: date,
    rates: list[tuple[date, Decimal]],
) -> tuple[Decimal, list[dict]]:
    """Calculate compound (samengestelde) interest per Dutch law.

    The compounding year runs from the default date:
    - Year 1: default_date → default_date + 1 year
    - Year 2: default_date + 1 year → default_date + 2 years
    - etc.

    At the end of each full year, accrued interest is added to principal.
    Partial years (the last period) do NOT capitalize.

    Returns: (total_interest, list of period details)
    """
    if calc_date <= default_date:
        return Decimal("0"), []

    current_principal = principal
    total_interest = Decimal("0")
    all_periods: list[dict] = []

    # Determine compounding year boundaries
    year_start = default_date
    while year_start < calc_date:
        # End of this compounding year
        year_end = _add_years(year_start, 1)
        is_full_year = year_end <= calc_date
        period_end = year_end if is_full_year else calc_date

        # Calculate interest for this compounding year (or partial year)
        schedule = build_rate_schedule(year_start, period_end, rates)
        year_interest = Decimal("0")

        for seg_start, seg_end, rate in schedule:
            days = (seg_end - seg_start).days
            interest = _round2(
                current_principal * (rate / Decimal("100")) * Decimal(days) / DAYS_IN_YEAR
            )
            year_interest += interest
            all_periods.append(
                {
                    "start_date": seg_start,
                    "end_date": seg_end,
                    "days": days,
                    "rate": rate,
                    "principal": current_principal,
                    "interest": interest,
                }
            )

        total_interest += year_interest

        # Capitalize at end of full year (add interest to principal)
        if is_full_year:
            current_principal = _round2(current_principal + year_interest)

        year_start = period_end

    return _round2(total_interest), all_periods


def _add_years(d: date, years: int) -> date:
    """Add years to a date, handling leap year edge cases.

    Feb 29 + 1 year → Feb 28 (not March 1).
    """
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # Feb 29 in a leap year → Feb 28 in a non-leap year
        return d.replace(year=d.year + years, day=28)


# ── Contractual Interest Helper ──────────────────────────────────────────────


def build_contractual_rate_schedule(
    start: date,
    end: date,
    rate: Decimal,
) -> list[tuple[date, Decimal]]:
    """Build a 'rate history' for a fixed contractual rate.

    Since contractual rates don't change, this returns a single-entry list
    that the standard calculation functions can use.
    """
    return [(start, rate)]


# ── Interest with Principal Reductions (art. 6:44 BW) ─────────────────────


def calculate_interest_with_reductions(
    principal: Decimal,
    default_date: date,
    calc_date: date,
    rates: list[tuple[date, Decimal]],
    principal_reductions: list[tuple[date, Decimal]],
    compound: bool,
) -> tuple[Decimal, list[dict]]:
    """Calculate interest accounting for principal reductions from payments.

    After a partial payment reduces the principal (per art. 6:44 BW),
    subsequent interest accrues only on the remaining balance.

    Args:
        principal_reductions: sorted list of (payment_date, amount_to_principal)
            — only reductions BEFORE calc_date are applied.
    """
    if not principal_reductions:
        if compound:
            return calculate_compound_interest(principal, default_date, calc_date, rates)
        return calculate_simple_interest(principal, default_date, calc_date, rates)

    relevant = [(d, amt) for d, amt in principal_reductions if default_date < d < calc_date]
    if not relevant:
        if compound:
            return calculate_compound_interest(principal, default_date, calc_date, rates)
        return calculate_simple_interest(principal, default_date, calc_date, rates)

    if not compound:
        return _simple_interest_with_reductions(
            principal, default_date, calc_date, rates, relevant
        )
    return _compound_interest_with_reductions(
        principal, default_date, calc_date, rates, relevant
    )


def _simple_interest_with_reductions(
    principal: Decimal,
    default_date: date,
    calc_date: date,
    rates: list[tuple[date, Decimal]],
    reductions: list[tuple[date, Decimal]],
) -> tuple[Decimal, list[dict]]:
    """Simple interest split at payment dates — principal decreases, no capitalization."""
    total_interest = Decimal("0")
    all_periods: list[dict] = []
    current_principal = principal
    segment_start = default_date

    for red_date, red_amount in reductions:
        if segment_start < red_date:
            seg_interest, seg_periods = calculate_simple_interest(
                current_principal, segment_start, red_date, rates
            )
            for p in seg_periods:
                p["principal"] = current_principal
            total_interest += seg_interest
            all_periods.extend(seg_periods)
        current_principal = max(Decimal("0"), current_principal - red_amount)
        segment_start = red_date

    if segment_start < calc_date and current_principal > Decimal("0"):
        seg_interest, seg_periods = calculate_simple_interest(
            current_principal, segment_start, calc_date, rates
        )
        for p in seg_periods:
            p["principal"] = current_principal
        total_interest += seg_interest
        all_periods.extend(seg_periods)

    return _round2(total_interest), all_periods


def _compound_interest_with_reductions(
    principal: Decimal,
    default_date: date,
    calc_date: date,
    rates: list[tuple[date, Decimal]],
    reductions: list[tuple[date, Decimal]],
) -> tuple[Decimal, list[dict]]:
    """Compound interest with mid-year principal reductions.

    Compounding years run from default_date anniversary.
    When a payment falls mid-year, the year is split:
    interest before payment on old principal, after on reduced.
    Capitalization still happens at year boundaries.
    """
    current_principal = principal
    total_interest = Decimal("0")
    all_periods: list[dict] = []

    red_idx = 0
    year_start = default_date

    while year_start < calc_date and current_principal > Decimal("0"):
        year_end = _add_years(year_start, 1)
        is_full_year = year_end <= calc_date
        period_end = year_end if is_full_year else calc_date

        year_interest = Decimal("0")
        seg_start = year_start

        while red_idx < len(reductions) and reductions[red_idx][0] <= seg_start:
            current_principal = max(Decimal("0"), current_principal - reductions[red_idx][1])
            red_idx += 1

        seg_cursor = seg_start
        while red_idx < len(reductions) and reductions[red_idx][0] < period_end:
            red_date, red_amount = reductions[red_idx]

            if seg_cursor < red_date:
                schedule = build_rate_schedule(seg_cursor, red_date, rates)
                for s_start, s_end, rate in schedule:
                    days = (s_end - s_start).days
                    interest = _round2(
                        current_principal * (rate / Decimal("100")) * Decimal(days) / DAYS_IN_YEAR
                    )
                    year_interest += interest
                    all_periods.append({
                        "start_date": s_start,
                        "end_date": s_end,
                        "days": days,
                        "rate": rate,
                        "principal": current_principal,
                        "interest": interest,
                    })

            current_principal = max(Decimal("0"), current_principal - red_amount)
            seg_cursor = red_date
            red_idx += 1

        if seg_cursor < period_end and current_principal > Decimal("0"):
            schedule = build_rate_schedule(seg_cursor, period_end, rates)
            for s_start, s_end, rate in schedule:
                days = (s_end - s_start).days
                interest = _round2(
                    current_principal * (rate / Decimal("100")) * Decimal(days) / DAYS_IN_YEAR
                )
                year_interest += interest
                all_periods.append({
                    "start_date": s_start,
                    "end_date": s_end,
                    "days": days,
                    "rate": rate,
                    "principal": current_principal,
                    "interest": interest,
                })

        total_interest += year_interest

        if is_full_year:
            current_principal = _round2(current_principal + year_interest)

        year_start = period_end

    return _round2(total_interest), all_periods


# ── High-Level Case Interest Calculator ──────────────────────────────────────


async def calculate_case_interest(
    db: AsyncSession,
    case_id: str,
    interest_type: str,
    contractual_rate: Decimal | None,
    contractual_compound: bool,
    claims: list[dict],
    calc_date: date,
    payments: list[dict] | None = None,
) -> dict:
    """Calculate total interest for all claims in a case.

    Args:
        db: Database session
        case_id: UUID of the case
        interest_type: 'statutory', 'commercial', 'government', or 'contractual'
        contractual_rate: Rate for contractual interest (None for statutory types)
        contractual_compound: Whether contractual interest compounds
        claims: List of dicts with 'id', 'description', 'principal_amount', 'default_date'
        calc_date: Date to calculate interest up to

    Returns: Dict with total_principal, total_interest, and per-claim details
    """
    # Get rate history based on interest type
    if interest_type == "contractual":
        if contractual_rate is None:
            raise ValueError("Contractuele rente vereist een tarief")
        # For contractual, we build a single-rate schedule
        # The rate is a constant, so we need a dummy date far in the past
        rate_history = [(date(1900, 1, 1), contractual_rate)]
    else:
        # Map interest_type to rate_type in database
        rate_type_map = {
            "statutory": "statutory",
            "commercial": "commercial",
            "government": "government",
        }
        rate_type = rate_type_map.get(interest_type, "statutory")
        rate_history = await get_rates_from_db(db, rate_type)

    if not rate_history:
        raise ValueError(
            f"Geen rentetarieven gevonden voor type '{interest_type}'. Voer eerst de seed-data uit."
        )

    # Determine if compound
    is_compound = not (interest_type == "contractual" and not contractual_compound)

    # Build per-claim principal reductions from payments (pro-rata)
    claim_reductions = _build_claim_reductions(claims, payments or [])

    # Calculate interest per claim
    total_principal = Decimal("0")
    total_interest = Decimal("0")
    claim_results: list[dict] = []

    for claim in claims:
        principal = Decimal(str(claim["principal_amount"]))
        default_dt = claim["default_date"]
        claim_rate_basis = claim.get("rate_basis", "yearly")
        claim_override_rate = claim.get("interest_rate")
        claim_id = claim["id"]

        # DF122-06: per-claim rate override takes precedence over case-level rate
        if claim_override_rate is not None:
            override_rate = Decimal(str(claim_override_rate))
            if claim_rate_basis == "monthly":
                override_rate = override_rate * Decimal("12")
            claim_rate_history = [(date(1900, 1, 1), override_rate)]
            use_compound = is_compound
        elif interest_type == "contractual" and claim_rate_basis == "monthly":
            effective_rate = contractual_rate * Decimal("12")
            claim_rate_history = [(date(1900, 1, 1), effective_rate)]
            use_compound = is_compound
        else:
            claim_rate_history = rate_history
            use_compound = is_compound

        reductions = claim_reductions.get(claim_id, [])
        interest, periods = calculate_interest_with_reductions(
            principal, default_dt, calc_date, claim_rate_history,
            reductions, use_compound,
        )

        total_principal += principal
        total_interest += interest

        claim_results.append(
            {
                "claim_id": claim_id,
                "description": claim["description"],
                "principal_amount": principal,
                "default_date": default_dt,
                "total_interest": interest,
                "periods": periods,
            }
        )

    return {
        "case_id": case_id,
        "calculation_date": calc_date,
        "interest_type": interest_type,
        "total_principal": _round2(total_principal),
        "total_interest": _round2(total_interest),
        "claims": claim_results,
    }


def _build_claim_reductions(
    claims: list[dict],
    payments: list[dict],
) -> dict[str, list[tuple[date, Decimal]]]:
    """Distribute payment principal allocations pro-rata across claims.

    Returns: {claim_id: [(payment_date, reduction_amount), ...]} sorted by date.
    """
    if not payments or not claims:
        return {}

    total_principal = sum(Decimal(str(c["principal_amount"])) for c in claims)
    if total_principal <= Decimal("0"):
        return {}

    result: dict[str, list[tuple[date, Decimal]]] = {c["id"]: [] for c in claims}

    for pmt in payments:
        allocated = Decimal(str(pmt["allocated_to_principal"]))
        if allocated <= Decimal("0"):
            continue

        pmt_date = pmt["payment_date"]
        distributed = Decimal("0")

        for i, claim in enumerate(claims):
            claim_principal = Decimal(str(claim["principal_amount"]))
            is_last = i == len(claims) - 1

            if is_last:
                share = allocated - distributed
            else:
                share = _round2(allocated * claim_principal / total_principal)
                distributed += share

            if share > Decimal("0"):
                result[claim["id"]].append((pmt_date, share))

    for claim_id in result:
        result[claim_id].sort(key=lambda x: x[0])

    return result
