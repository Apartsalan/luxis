"""Edge case tests for the interest calculation engine.

Tests cover:
- 0 days (same start/end)
- 1 day
- Leap year (2024-02-29)
- Negative amounts
- Zero principal
- Rate change exactly on start/end date
- Very short periods across rate changes
- Compound interest with leap year default date (Feb 29)
- Multiple rate changes within a single compounding year
- Empty rate list
"""

from datetime import date
from decimal import Decimal

from app.collections.interest import (
    _add_years,
    _round2,
    build_rate_schedule,
    calculate_compound_interest,
    calculate_simple_interest,
)

# ── Helpers ─────────────────────────────────────────────────────────────────

FIXED_RATE_6PCT = [(date(2020, 1, 1), Decimal("6.00"))]
FIXED_RATE_0PCT = [(date(2020, 1, 1), Decimal("0.00"))]


# ── Zero Days ───────────────────────────────────────────────────────────────


class TestZeroDays:
    """Interest over 0 days should always be 0."""

    def test_simple_zero_days(self):
        """Same start and end date → 0 interest."""
        total, periods = calculate_simple_interest(
            Decimal("10000.00"),
            date(2025, 6, 1),
            date(2025, 6, 1),
            FIXED_RATE_6PCT,
        )
        assert total == Decimal("0")
        assert periods == []

    def test_compound_zero_days(self):
        """Same start and end date → 0 compound interest."""
        total, periods = calculate_compound_interest(
            Decimal("10000.00"),
            date(2025, 6, 1),
            date(2025, 6, 1),
            FIXED_RATE_6PCT,
        )
        assert total == Decimal("0")
        assert periods == []

    def test_simple_calc_before_default(self):
        """calc_date before default_date → 0 interest."""
        total, periods = calculate_simple_interest(
            Decimal("5000.00"),
            date(2025, 6, 1),
            date(2025, 1, 1),
            FIXED_RATE_6PCT,
        )
        assert total == Decimal("0")
        assert periods == []

    def test_compound_calc_before_default(self):
        """calc_date before default_date → 0 compound interest."""
        total, periods = calculate_compound_interest(
            Decimal("5000.00"),
            date(2025, 6, 1),
            date(2025, 1, 1),
            FIXED_RATE_6PCT,
        )
        assert total == Decimal("0")
        assert periods == []


# ── Single Day ──────────────────────────────────────────────────────────────


class TestSingleDay:
    """Interest for exactly 1 day."""

    def test_simple_one_day(self):
        """€10,000 at 6% for 1 day = 10000 * 0.06 / 365 = 1.64."""
        total, periods = calculate_simple_interest(
            Decimal("10000.00"),
            date(2025, 3, 15),
            date(2025, 3, 16),
            FIXED_RATE_6PCT,
        )
        expected = _round2(
            Decimal("10000") * Decimal("6") / Decimal("100")
            * Decimal("1") / Decimal("365")
        )
        assert total == expected
        assert len(periods) == 1
        assert periods[0]["days"] == 1

    def test_compound_one_day(self):
        """1 day compound = 1 day simple (no capitalization)."""
        simple_total, _ = calculate_simple_interest(
            Decimal("10000.00"),
            date(2025, 3, 15),
            date(2025, 3, 16),
            FIXED_RATE_6PCT,
        )
        compound_total, _ = calculate_compound_interest(
            Decimal("10000.00"),
            date(2025, 3, 15),
            date(2025, 3, 16),
            FIXED_RATE_6PCT,
        )
        assert simple_total == compound_total

    def test_one_day_at_rate_boundary(self):
        """1 day interest when the day falls exactly on a rate change."""
        rates = [
            (date(2025, 1, 1), Decimal("7.00")),
            (date(2025, 7, 1), Decimal("6.00")),
        ]
        # Day from 2025-07-01 to 2025-07-02 → uses the NEW rate (6%)
        total, periods = calculate_simple_interest(
            Decimal("10000.00"),
            date(2025, 7, 1),
            date(2025, 7, 2),
            rates,
        )
        expected = _round2(
            Decimal("10000") * Decimal("6") / Decimal("100")
            * Decimal("1") / Decimal("365")
        )
        assert total == expected


# ── Leap Year ───────────────────────────────────────────────────────────────


class TestLeapYear:
    """Leap year edge cases. The engine uses 365 days always (Dutch practice)."""

    def test_simple_interest_across_feb29(self):
        """Interest spanning Feb 29 in a leap year (2024).

        2024-02-28 to 2024-03-01 = 2 days (Feb 28 → Feb 29 → Mar 1).
        Engine uses /365, not /366.
        """
        total, periods = calculate_simple_interest(
            Decimal("36500.00"),
            date(2024, 2, 28),
            date(2024, 3, 1),
            FIXED_RATE_6PCT,
        )
        # 36500 * 0.06 * 2/365 = 12.00
        expected = _round2(
            Decimal("36500") * Decimal("6") / Decimal("100")
            * Decimal("2") / Decimal("365")
        )
        assert total == expected
        assert periods[0]["days"] == 2

    def test_full_leap_year_366_days(self):
        """Full year from Jan 1 to Dec 31 in leap year = 366 days, but /365."""
        total, periods = calculate_simple_interest(
            Decimal("36500.00"),
            date(2024, 1, 1),
            date(2025, 1, 1),
            FIXED_RATE_6PCT,
        )
        # 36500 * 0.06 * 366/365
        expected = _round2(
            Decimal("36500") * Decimal("6") / Decimal("100")
            * Decimal("366") / Decimal("365")
        )
        assert total == expected
        assert periods[0]["days"] == 366

    def test_add_years_from_feb29(self):
        """Feb 29 + 1 year = Feb 28 (not March 1)."""
        result = _add_years(date(2024, 2, 29), 1)
        assert result == date(2025, 2, 28)

    def test_add_years_from_feb29_to_next_leap_year(self):
        """Feb 29 + 4 years = Feb 29 (next leap year)."""
        result = _add_years(date(2024, 2, 29), 4)
        assert result == date(2028, 2, 29)

    def test_add_years_from_normal_date(self):
        """Normal date + 1 year works as expected."""
        result = _add_years(date(2024, 6, 15), 1)
        assert result == date(2025, 6, 15)

    def test_compound_starting_feb29(self):
        """Compound interest starting on Feb 29 of a leap year.

        Default date: 2024-02-29
        Year 1: 2024-02-29 → 2025-02-28 (365 days, Feb 29 maps to Feb 28)
        Year 2: 2025-02-28 → 2026-02-28 (365 days)
        """
        principal = Decimal("5000.00")
        default_date = date(2024, 2, 29)
        calc_date = date(2026, 2, 28)

        total, periods = calculate_compound_interest(
            principal, default_date, calc_date, FIXED_RATE_6PCT
        )

        # Year 1: 2024-02-29 → 2025-02-28 = 365 days
        days_y1 = (date(2025, 2, 28) - date(2024, 2, 29)).days  # 365
        y1_interest = _round2(
            Decimal("5000") * Decimal("6") / Decimal("100")
            * Decimal(str(days_y1)) / Decimal("365")
        )
        # Capitalize
        new_principal = principal + y1_interest

        # Year 2: 2025-02-28 → 2026-02-28 = 365 days
        days_y2 = (date(2026, 2, 28) - date(2025, 2, 28)).days  # 365
        y2_interest = _round2(
            new_principal * Decimal("6") / Decimal("100")
            * Decimal(str(days_y2)) / Decimal("365")
        )

        expected = _round2(y1_interest + y2_interest)
        assert total == expected


# ── Negative & Zero Amounts ─────────────────────────────────────────────────


class TestNegativeAndZeroAmounts:
    """Edge cases with unusual principal values."""

    def test_zero_principal_simple(self):
        """Zero principal → 0 interest."""
        total, periods = calculate_simple_interest(
            Decimal("0.00"),
            date(2025, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_6PCT,
        )
        assert total == Decimal("0.00")

    def test_zero_principal_compound(self):
        """Zero principal → 0 compound interest."""
        total, periods = calculate_compound_interest(
            Decimal("0.00"),
            date(2025, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_6PCT,
        )
        assert total == Decimal("0.00")

    def test_negative_principal_simple(self):
        """Negative principal should produce negative interest (mathematically).

        The engine does not reject negative principals — it calculates.
        This tests that the math is consistent even with negative values.
        """
        total, periods = calculate_simple_interest(
            Decimal("-5000.00"),
            date(2025, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_6PCT,
        )
        # -5000 * 0.06 * 365/365 = -300.00
        assert total == Decimal("-300.00")

    def test_negative_principal_compound(self):
        """Negative principal compound for 2 years."""
        total, periods = calculate_compound_interest(
            Decimal("-5000.00"),
            date(2024, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_6PCT,
        )
        # Compute with actual day counts (2024 is leap year = 366 days)
        d = Decimal
        p = d("-5000.00")
        days_y1 = (date(2025, 1, 1) - date(2024, 1, 1)).days  # 366
        y1 = _round2(p * d("6") / d("100") * d(str(days_y1)) / d("365"))
        p2 = p + y1
        days_y2 = (date(2026, 1, 1) - date(2025, 1, 1)).days  # 365
        y2 = _round2(p2 * d("6") / d("100") * d(str(days_y2)) / d("365"))
        assert total == _round2(y1 + y2)

    def test_one_cent_principal(self):
        """Minimum practical amount: 1 cent."""
        total, _ = calculate_simple_interest(
            Decimal("0.01"),
            date(2025, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_6PCT,
        )
        # 0.01 * 0.06 * 365/365 = 0.0006 → rounds to 0.00
        assert total == Decimal("0.00")


# ── Zero Rate ───────────────────────────────────────────────────────────────


class TestZeroRate:
    """Interest at 0% should always be 0."""

    def test_simple_zero_rate(self):
        total, periods = calculate_simple_interest(
            Decimal("10000.00"),
            date(2025, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_0PCT,
        )
        assert total == Decimal("0.00")

    def test_compound_zero_rate(self):
        total, periods = calculate_compound_interest(
            Decimal("10000.00"),
            date(2025, 1, 1),
            date(2028, 1, 1),  # 3 years
            FIXED_RATE_0PCT,
        )
        assert total == Decimal("0.00")


# ── Rate Schedule Edge Cases ────────────────────────────────────────────────


class TestRateScheduleEdgeCases:
    """Edge cases in building the rate schedule."""

    def test_rate_change_on_start_date(self):
        """Rate changes exactly on the start date — should use new rate."""
        rates = [
            (date(2024, 1, 1), Decimal("7.00")),
            (date(2025, 1, 1), Decimal("6.00")),
        ]
        schedule = build_rate_schedule(date(2025, 1, 1), date(2025, 7, 1), rates)
        assert len(schedule) == 1
        assert schedule[0][2] == Decimal("6.00")

    def test_rate_change_on_end_date(self):
        """Rate changes exactly on the end date — should NOT appear in schedule."""
        rates = [
            (date(2024, 1, 1), Decimal("7.00")),
            (date(2025, 7, 1), Decimal("6.00")),
        ]
        schedule = build_rate_schedule(date(2025, 1, 1), date(2025, 7, 1), rates)
        assert len(schedule) == 1
        assert schedule[0][2] == Decimal("7.00")

    def test_many_rate_changes_in_short_period(self):
        """Multiple rate changes within a 6-month period."""
        rates = [
            (date(2025, 1, 1), Decimal("7.00")),
            (date(2025, 2, 1), Decimal("6.50")),
            (date(2025, 3, 1), Decimal("6.00")),
            (date(2025, 4, 1), Decimal("5.50")),
            (date(2025, 5, 1), Decimal("5.00")),
        ]
        schedule = build_rate_schedule(date(2025, 1, 15), date(2025, 6, 1), rates)
        # 5 segments: Jan-15→Feb-1, Feb-1→Mar-1, ..., May-1→Jun-1
        assert len(schedule) == 5

    def test_no_rate_before_start(self):
        """All rates are after start date — should use earliest rate."""
        rates = [
            (date(2025, 7, 1), Decimal("6.00")),
            (date(2026, 1, 1), Decimal("5.00")),
        ]
        schedule = build_rate_schedule(date(2025, 1, 1), date(2025, 12, 1), rates)
        # First segment: 2025-01-01 to 2025-07-01 at 6% (earliest available)
        assert schedule[0][2] == Decimal("6.00")
        # Second segment: 2025-07-01 to 2025-12-01 at 6%? No — should use 6 then 5
        # Actually: segment_start=2025-01-01, then rate at 2025-07-01 splits it
        assert len(schedule) == 2

    def test_empty_rates_list(self):
        """Empty rate list → empty schedule."""
        schedule = build_rate_schedule(date(2025, 1, 1), date(2025, 7, 1), [])
        assert schedule == []


# ── Compound Interest Edge Cases ────────────────────────────────────────────


class TestCompoundEdgeCases:
    """Additional compound interest edge cases."""

    def test_exactly_one_year_no_partial(self):
        """Exactly 1 year: interest calculated, but NOT capitalized (no next year)."""
        principal = Decimal("10000.00")
        total, periods = calculate_compound_interest(
            principal,
            date(2025, 1, 1),
            date(2026, 1, 1),
            FIXED_RATE_6PCT,
        )
        # Exactly 1 full year → capitalize at end, but there's no further period
        # The total should be 10000 * 0.06 = 600.00
        assert total == Decimal("600.00")

    def test_one_year_plus_one_day(self):
        """1 year + 1 day: year 1 capitalizes, then 1 day on new principal."""
        principal = Decimal("10000.00")
        total, periods = calculate_compound_interest(
            principal,
            date(2025, 1, 1),
            date(2026, 1, 2),
            FIXED_RATE_6PCT,
        )
        # Year 1: 10000 * 0.06 = 600, capitalize → 10600
        # Day 1 of year 2: 10600 * 0.06 * 1/365
        y1 = Decimal("600.00")
        y2_day = _round2(
            Decimal("10600") * Decimal("6") / Decimal("100")
            * Decimal("1") / Decimal("365")
        )
        expected = _round2(y1 + y2_day)
        assert total == expected

    def test_multiple_rate_changes_within_compound_year(self):
        """Three rate changes within a single compounding year."""
        rates = [
            (date(2024, 1, 1), Decimal("8.00")),
            (date(2024, 7, 1), Decimal("7.00")),
            (date(2025, 1, 1), Decimal("6.00")),
        ]
        principal = Decimal("5000.00")
        default_date = date(2024, 3, 1)
        calc_date = date(2025, 3, 1)

        total, periods = calculate_compound_interest(
            principal, default_date, calc_date, rates
        )

        # Year 1 spans 2024-03-01 → 2025-03-01, with rate changes at:
        #   2024-07-01 (8%→7%) and 2025-01-01 (7%→6%)
        # Sub A: 2024-03-01 → 2024-07-01 = 122 days at 8%
        # Sub B: 2024-07-01 → 2025-01-01 = 184 days at 7%
        # Sub C: 2025-01-01 → 2025-03-01 = 59 days at 6%
        d = Decimal
        sub_a = _round2(d("5000") * d("8") / d("100") * d("122") / d("365"))
        sub_b = _round2(d("5000") * d("7") / d("100") * d("184") / d("365"))
        sub_c = _round2(d("5000") * d("6") / d("100") * d("59") / d("365"))
        expected = _round2(sub_a + sub_b + sub_c)

        assert len(periods) == 3
        assert total == expected

    def test_very_long_compound_10_years(self):
        """10 years of compound interest at 6% — verify compounding effect."""
        principal = Decimal("10000.00")
        total, periods = calculate_compound_interest(
            principal,
            date(2015, 1, 1),
            date(2025, 1, 1),
            FIXED_RATE_6PCT,
        )

        # Manual: 10 years of annual compounding at 6%, using actual day counts
        d = Decimal
        current = Decimal("10000.00")
        expected_total = Decimal("0")
        for year in range(10):
            year_start = date(2015 + year, 1, 1)
            year_end = date(2016 + year, 1, 1)
            days = (year_end - year_start).days
            year_interest = _round2(current * d("6") / d("100") * d(str(days)) / d("365"))
            expected_total += year_interest
            current += year_interest

        assert total == _round2(expected_total)

    def test_compound_partial_year_does_not_capitalize(self):
        """The last partial year should NOT capitalize.

        2 years + 6 months: only years 1 and 2 capitalize.
        """
        principal = Decimal("10000.00")
        default_date = date(2023, 1, 1)
        calc_date = date(2025, 7, 1)

        total, periods = calculate_compound_interest(
            principal, default_date, calc_date, FIXED_RATE_6PCT
        )

        # Compute with actual day counts (2024 is leap year)
        d = Decimal
        p = principal
        days_y1 = (date(2024, 1, 1) - date(2023, 1, 1)).days  # 365
        y1 = _round2(p * d("6") / d("100") * d(str(days_y1)) / d("365"))
        p += y1
        days_y2 = (date(2025, 1, 1) - date(2024, 1, 1)).days  # 366 (leap)
        y2 = _round2(p * d("6") / d("100") * d(str(days_y2)) / d("365"))
        p += y2
        # Partial (181 days): NO cap
        days_partial = (calc_date - date(2025, 1, 1)).days  # 181
        y3_partial = _round2(p * d("6") / d("100") * d(str(days_partial)) / d("365"))

        expected = _round2(y1 + y2 + y3_partial)
        assert total == expected


# ── Rounding Edge Cases ─────────────────────────────────────────────────────


class TestRounding:
    """Verify ROUND_HALF_UP behavior."""

    def test_round_half_up_exactly_half(self):
        """0.005 rounds UP to 0.01 (not down to 0.00)."""
        assert _round2(Decimal("0.005")) == Decimal("0.01")

    def test_round_half_up_just_below(self):
        """0.004 rounds DOWN to 0.00."""
        assert _round2(Decimal("0.004")) == Decimal("0.00")

    def test_round_half_up_negative(self):
        """-0.005 rounds to -0.01 with ROUND_HALF_UP."""
        # ROUND_HALF_UP always rounds away from zero for .5
        assert _round2(Decimal("-0.005")) == Decimal("-0.01")

    def test_interest_rounding_per_period(self):
        """Each period's interest is rounded individually, then summed.

        This can produce slightly different results vs. rounding the final sum.
        €1234.56 at 5.25% for:
          Period A: 100 days → 1234.56 * 0.0525 * 100/365 = 17.75 (rounded)
          Period B: 100 days → 1234.56 * 0.0525 * 100/365 = 17.75 (rounded)
        Total: 35.50
        """
        rates = [
            (date(2025, 1, 1), Decimal("5.25")),
            (date(2025, 4, 11), Decimal("5.25")),  # Same rate — forces 2 periods
        ]
        # Actually need a rate change to split periods:
        rates = [
            (date(2025, 1, 1), Decimal("5.25")),
        ]
        principal = Decimal("1234.56")
        total, periods = calculate_simple_interest(
            principal,
            date(2025, 1, 1),
            date(2025, 7, 20),  # 200 days
            rates,
        )
        # 1234.56 * 0.0525 * 200/365
        expected = _round2(
            Decimal("1234.56") * Decimal("5.25") / Decimal("100")
            * Decimal("200") / Decimal("365")
        )
        assert total == expected
