"""Tests for the interest calculation engine — MOST CRITICAL TESTS.

These verify that the math is correct for court documents.
All expected values are hand-calculated and verified.
"""

from datetime import date
from decimal import Decimal

from app.collections.interest import (
    _round2,
    build_rate_schedule,
    calculate_compound_interest,
    calculate_simple_interest,
)

# ── Helper: fixed rate schedule ──────────────────────────────────────────────

FIXED_RATE_6PCT = [(date(2020, 1, 1), Decimal("6.00"))]
FIXED_RATE_7PCT = [(date(2020, 1, 1), Decimal("7.00"))]
FIXED_RATE_4PCT = [(date(2020, 1, 1), Decimal("4.00"))]


# ── Rate Schedule Building ───────────────────────────────────────────────────


def test_build_rate_schedule_single_rate():
    """Single rate covering the entire period."""
    rates = [(date(2024, 1, 1), Decimal("7.00"))]
    schedule = build_rate_schedule(
        date(2024, 6, 15), date(2025, 6, 15), rates
    )
    assert len(schedule) == 1
    assert schedule[0] == (date(2024, 6, 15), date(2025, 6, 15), Decimal("7.00"))


def test_build_rate_schedule_rate_change():
    """Rate changes mid-period should split into segments."""
    rates = [
        (date(2024, 1, 1), Decimal("7.00")),
        (date(2025, 1, 1), Decimal("6.00")),
    ]
    schedule = build_rate_schedule(
        date(2024, 6, 15), date(2025, 6, 15), rates
    )
    assert len(schedule) == 2
    # First segment: 2024-06-15 to 2025-01-01 at 7%
    assert schedule[0] == (date(2024, 6, 15), date(2025, 1, 1), Decimal("7.00"))
    # Second segment: 2025-01-01 to 2025-06-15 at 6%
    assert schedule[1] == (date(2025, 1, 1), date(2025, 6, 15), Decimal("6.00"))


def test_build_rate_schedule_multiple_changes():
    """Multiple rate changes should create multiple segments."""
    rates = [
        (date(2024, 1, 1), Decimal("7.00")),
        (date(2024, 7, 1), Decimal("6.00")),
        (date(2025, 1, 1), Decimal("4.00")),
    ]
    schedule = build_rate_schedule(
        date(2024, 3, 1), date(2025, 6, 1), rates
    )
    assert len(schedule) == 3
    assert schedule[0][2] == Decimal("7.00")
    assert schedule[1][2] == Decimal("6.00")
    assert schedule[2][2] == Decimal("4.00")


def test_build_rate_schedule_empty_range():
    """Same start/end should return empty."""
    schedule = build_rate_schedule(
        date(2024, 1, 1), date(2024, 1, 1), FIXED_RATE_6PCT
    )
    assert schedule == []


# ── Simple Interest ──────────────────────────────────────────────────────────


def test_simple_interest_full_year_6pct():
    """€5,000 at 6% for exactly 1 year = €300.00"""
    principal = Decimal("5000.00")
    default_date = date(2024, 3, 15)
    calc_date = date(2025, 3, 15)

    total, periods = calculate_simple_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )

    # 5000 * 0.06 * 365/365 = 300.00
    assert total == Decimal("300.00")
    assert len(periods) == 1
    assert periods[0]["days"] == 365


def test_simple_interest_half_year():
    """€10,000 at 7% for ~182 days (half year)."""
    principal = Decimal("10000.00")
    default_date = date(2024, 1, 1)
    calc_date = date(2024, 7, 1)  # 182 days

    total, periods = calculate_simple_interest(
        principal, default_date, calc_date, FIXED_RATE_7PCT
    )

    # 10000 * 0.07 * 182/365 = 349.04 (rounded)
    expected = _round2(
        Decimal("10000") * Decimal("7.00") / Decimal("100")
        * Decimal("182") / Decimal("365")
    )
    assert total == expected


def test_simple_interest_broken_period():
    """€2,500 at 4% for 90 days — pro-rata calculation."""
    principal = Decimal("2500.00")
    default_date = date(2025, 1, 1)
    calc_date = date(2025, 4, 1)  # 90 days

    total, periods = calculate_simple_interest(
        principal, default_date, calc_date, FIXED_RATE_4PCT
    )

    # 2500 * 0.04 * 90/365 = 24.66 (rounded)
    expected = _round2(
        Decimal("2500") * Decimal("4.00") / Decimal("100")
        * Decimal("90") / Decimal("365")
    )
    assert total == expected
    assert periods[0]["days"] == 90


def test_simple_interest_rate_change():
    """Rate changes during the period should split correctly."""
    principal = Decimal("5000.00")
    rates = [
        (date(2024, 1, 1), Decimal("7.00")),
        (date(2025, 1, 1), Decimal("6.00")),
    ]
    default_date = date(2024, 7, 1)
    calc_date = date(2025, 7, 1)

    total, periods = calculate_simple_interest(
        principal, default_date, calc_date, rates
    )

    assert len(periods) == 2
    # Period 1: 2024-07-01 to 2025-01-01 = 184 days at 7%
    p1 = _round2(Decimal("5000") * Decimal("7") / Decimal("100") * Decimal("184") / Decimal("365"))
    # Period 2: 2025-01-01 to 2025-07-01 = 181 days at 6%
    p2 = _round2(Decimal("5000") * Decimal("6") / Decimal("100") * Decimal("181") / Decimal("365"))
    assert total == _round2(p1 + p2)


def test_simple_interest_no_interest_before_default():
    """calc_date before or equal to default_date should return 0."""
    total, periods = calculate_simple_interest(
        Decimal("5000"), date(2025, 6, 1), date(2025, 1, 1), FIXED_RATE_6PCT
    )
    assert total == Decimal("0")
    assert periods == []


# ── Compound Interest ────────────────────────────────────────────────────────


def test_compound_1_year_equals_simple():
    """For exactly 1 year, compound = simple (no capitalization yet)."""
    principal = Decimal("5000.00")
    default_date = date(2024, 3, 15)
    calc_date = date(2025, 3, 15)

    compound_total, _ = calculate_compound_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )
    simple_total, _ = calculate_simple_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )

    assert compound_total == simple_total == Decimal("300.00")


def test_compound_2_years():
    """2 years compound: year 2 interest calculated on (principal + year 1 interest)."""
    principal = Decimal("5000.00")
    default_date = date(2024, 3, 15)
    calc_date = date(2026, 3, 15)

    total, periods = calculate_compound_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )

    # Year 1: 5000 * 0.06 * 365/365 = 300.00
    year1_interest = Decimal("300.00")
    # Year 2 principal: 5000 + 300 = 5300
    # Year 2 interest: 5300 * 0.06 * 365/365 = 318.00
    year2_interest = Decimal("318.00")
    expected = _round2(year1_interest + year2_interest)

    assert total == expected  # 618.00

    # Verify that year 2 used the higher principal
    year2_periods = [p for p in periods if p["start_date"] >= date(2025, 3, 15)]
    assert year2_periods[0]["principal"] == Decimal("5300.00")


def test_compound_1_5_years():
    """1.5 years: 1 full year capitalizes, then 6 months on new principal."""
    principal = Decimal("10000.00")
    default_date = date(2024, 1, 1)
    calc_date = date(2025, 7, 1)

    total, periods = calculate_compound_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )

    # Year 1 (full): 2024-01-01 to 2025-01-01 = 366 days (2024 is leap year)
    days_y1 = (date(2025, 1, 1) - date(2024, 1, 1)).days  # 366
    rate = Decimal("6") / Decimal("100")
    year1 = _round2(principal * rate * Decimal(str(days_y1)) / Decimal("365"))
    new_principal = principal + year1
    # Remaining 181 days on new principal
    days_rem = (calc_date - date(2025, 1, 1)).days  # 181
    remaining = _round2(
        new_principal * Decimal("6") / Decimal("100")
        * Decimal(str(days_rem)) / Decimal("365")
    )
    expected = _round2(year1 + remaining)
    assert total == expected


def test_compound_year_runs_from_default_date_not_january():
    """CRITICAL: Compounding year starts from default date, not January 1.

    Default date: 2024-06-15
    Year 1: 2024-06-15 → 2025-06-15 (capitalize)
    Year 2: 2025-06-15 → 2026-06-15 (capitalize)

    NOT:
    2024-06-15 → 2025-01-01 → 2025-06-15 (wrong!)
    """
    principal = Decimal("5000.00")
    default_date = date(2024, 6, 15)
    calc_date = date(2026, 6, 15)

    total, periods = calculate_compound_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )

    # Year 1: 5000 * 0.06 = 300, capitalize → 5300
    # Year 2: 5300 * 0.06 = 318
    # Total: 618.00
    assert total == Decimal("618.00")

    # Check that year boundaries are at June 15, not January 1
    # Period 1 should start at 2024-06-15
    assert periods[0]["start_date"] == date(2024, 6, 15)
    # After capitalization, the second year's principal should be 5300
    year2_start = date(2025, 6, 15)
    year2_periods = [p for p in periods if p["start_date"] >= year2_start]
    assert year2_periods[0]["principal"] == Decimal("5300.00")


def test_compound_rate_change_within_year():
    """Rate change mid-compounding-year should split the period correctly.

    Default date: 2024-06-15
    Rate 7% until 2025-01-01, then 6%
    Year 1: 2024-06-15 → 2025-06-15
      Sub-period A: 2024-06-15 → 2025-01-01 (200 days at 7%)
      Sub-period B: 2025-01-01 → 2025-06-15 (165 days at 6%)
    """
    principal = Decimal("5000.00")
    rates = [
        (date(2024, 1, 1), Decimal("7.00")),
        (date(2025, 1, 1), Decimal("6.00")),
    ]
    default_date = date(2024, 6, 15)
    calc_date = date(2025, 6, 15)

    total, periods = calculate_compound_interest(
        principal, default_date, calc_date, rates
    )

    # Sub-period A: 200 days at 7%
    days_a = (date(2025, 1, 1) - date(2024, 6, 15)).days  # 200
    interest_a = _round2(
        Decimal("5000") * Decimal("7") / Decimal("100")
        * Decimal(str(days_a)) / Decimal("365")
    )
    # Sub-period B: 165 days at 6%
    days_b = (date(2025, 6, 15) - date(2025, 1, 1)).days  # 165
    interest_b = _round2(
        Decimal("5000") * Decimal("6") / Decimal("100")
        * Decimal(str(days_b)) / Decimal("365")
    )
    expected = _round2(interest_a + interest_b)

    assert len(periods) == 2
    assert total == expected


def test_compound_real_rates_example():
    """Realistic example with actual Dutch statutory rates.

    €5,000 from 2024-03-15 to 2026-02-17
    Statutory rates: 7% (2024-01-01), 6% (2025-01-01), 4% (2026-01-01)

    Year 1: 2024-03-15 → 2025-03-15
      Sub A: 2024-03-15 → 2025-01-01 (292 days at 7%)
      Sub B: 2025-01-01 → 2025-03-15 (73 days at 6%)
    Capitalize → new principal

    Year 2 partial: 2025-03-15 → 2026-02-17
      Sub A: 2025-03-15 → 2026-01-01 (292 days at 6%)
      Sub B: 2026-01-01 → 2026-02-17 (47 days at 4%)
    """
    principal = Decimal("5000.00")
    rates = [
        (date(2024, 1, 1), Decimal("7.00")),
        (date(2025, 1, 1), Decimal("6.00")),
        (date(2026, 1, 1), Decimal("4.00")),
    ]
    default_date = date(2024, 3, 15)
    calc_date = date(2026, 2, 17)

    total, periods = calculate_compound_interest(
        principal, default_date, calc_date, rates
    )

    # Year 1:
    d = Decimal
    y1_sub_a = _round2(d("5000") * d("7") / d("100") * d("292") / d("365"))
    y1_sub_b = _round2(d("5000") * d("6") / d("100") * d("73") / d("365"))
    year1_total = y1_sub_a + y1_sub_b

    # Capitalize
    new_principal = principal + year1_total

    # Year 2 (partial — 2025-03-15 to 2026-02-17):
    y2_sub_a = _round2(new_principal * d("6") / d("100") * d("292") / d("365"))
    y2_sub_b = _round2(new_principal * d("4") / d("100") * d("47") / d("365"))
    year2_total = y2_sub_a + y2_sub_b

    expected = _round2(year1_total + year2_total)

    assert total == expected
    assert len(periods) == 4  # 2 sub-periods per compounding year


def test_compound_3_years():
    """3 full years of compound interest at 6%."""
    principal = Decimal("10000.00")
    default_date = date(2023, 1, 1)
    calc_date = date(2026, 1, 1)

    total, _ = calculate_compound_interest(
        principal, default_date, calc_date, FIXED_RATE_6PCT
    )

    # Compute expected using actual day counts (2024 is a leap year)
    d = Decimal
    p = principal
    days_y1 = (date(2024, 1, 1) - date(2023, 1, 1)).days  # 365
    y1 = _round2(p * d("6") / d("100") * d(str(days_y1)) / d("365"))
    p += y1
    days_y2 = (date(2025, 1, 1) - date(2024, 1, 1)).days  # 366 (leap)
    y2 = _round2(p * d("6") / d("100") * d(str(days_y2)) / d("365"))
    p += y2
    days_y3 = (date(2026, 1, 1) - date(2025, 1, 1)).days  # 365
    y3 = _round2(p * d("6") / d("100") * d(str(days_y3)) / d("365"))
    expected = _round2(y1 + y2 + y3)
    assert total == expected


# ── Edge Cases ───────────────────────────────────────────────────────────────


def test_small_principal():
    """Small principal should still calculate correctly."""
    total, _ = calculate_simple_interest(
        Decimal("50.00"), date(2025, 1, 1), date(2025, 7, 1),
        FIXED_RATE_6PCT,
    )
    # 50 * 0.06 * 181/365 = 1.49 (rounded)
    expected = _round2(
        Decimal("50") * Decimal("6") / Decimal("100")
        * Decimal("181") / Decimal("365")
    )
    assert total == expected


def test_very_large_principal():
    """Large principal should not lose precision."""
    total, _ = calculate_simple_interest(
        Decimal("1000000.00"), date(2025, 1, 1), date(2026, 1, 1),
        FIXED_RATE_6PCT,
    )
    assert total == Decimal("60000.00")


def test_single_day_interest():
    """1 day of interest should calculate correctly."""
    total, periods = calculate_simple_interest(
        Decimal("365000.00"), date(2025, 1, 1), date(2025, 1, 2),
        FIXED_RATE_6PCT,
    )
    # 365000 * 0.06 * 1/365 = 60.00
    assert total == Decimal("60.00")
    assert periods[0]["days"] == 1
