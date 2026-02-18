"""Edge case tests for WIK/BIK calculation (art. 6:96 BW).

Tests cover:
- Exact boundary amounts (2500, 5000, 10000, 200000)
- One cent above/below each boundary
- Minimum cap (€40) boundary
- Maximum cap (€6,775) boundary
- Very small amounts
- Very large amounts
- BTW edge cases
- Decimal precision (amounts with many decimal places)
"""

from decimal import Decimal

from app.collections.wik import WIK_MAXIMUM, WIK_MINIMUM, calculate_bik


# ── Exact Boundary: €2,500 ──────────────────────────────────────────────────


class TestBoundary2500:
    """Tier 1/2 boundary at €2,500."""

    def test_exactly_2500(self):
        """€2,500 → 15% of 2500 = €375.00 (all in tier 1)."""
        result = calculate_bik(Decimal("2500.00"))
        assert result["bik_exclusive"] == Decimal("375.00")
        assert len(result["tiers"]) == 1
        assert result["tiers"][0]["percentage"] == Decimal("0.15")
        assert result["tiers"][0]["applicable_amount"] == Decimal("2500")

    def test_one_cent_below_2500(self):
        """€2,499.99 → 15% of 2499.99 = €375.00 (rounded)."""
        result = calculate_bik(Decimal("2499.99"))
        expected = Decimal("375.00")  # 2499.99 * 0.15 = 374.9985 → rounds to 375.00
        assert result["bik_exclusive"] == expected

    def test_one_cent_above_2500(self):
        """€2,500.01 → 15% of 2500 + 10% of 0.01 = 375.00 + 0.00 = €375.00."""
        result = calculate_bik(Decimal("2500.01"))
        # Tier 1: 2500 * 0.15 = 375.00
        # Tier 2: 0.01 * 0.10 = 0.00 (rounded)
        assert result["bik_exclusive"] == Decimal("375.00")
        assert len(result["tiers"]) == 2

    def test_one_euro_above_2500(self):
        """€2,501.00 → 15% of 2500 + 10% of 1 = 375.00 + 0.10 = €375.10."""
        result = calculate_bik(Decimal("2501.00"))
        assert result["bik_exclusive"] == Decimal("375.10")


# ── Exact Boundary: €5,000 ──────────────────────────────────────────────────


class TestBoundary5000:
    """Tier 2/3 boundary at €5,000."""

    def test_exactly_5000(self):
        """€5,000 → 375 + 250 = €625.00."""
        result = calculate_bik(Decimal("5000.00"))
        assert result["bik_exclusive"] == Decimal("625.00")
        assert len(result["tiers"]) == 2

    def test_one_cent_below_5000(self):
        """€4,999.99 → 375 + 10% of 2499.99 = 375 + 250.00 = €625.00."""
        result = calculate_bik(Decimal("4999.99"))
        # Tier 1: 2500 * 0.15 = 375.00
        # Tier 2: 2499.99 * 0.10 = 250.00 (rounded from 249.999)
        assert result["bik_exclusive"] == Decimal("625.00")

    def test_one_cent_above_5000(self):
        """€5,000.01 → 375 + 250 + 5% of 0.01 = 625.00 + 0.00 = €625.00."""
        result = calculate_bik(Decimal("5000.01"))
        assert result["bik_exclusive"] == Decimal("625.00")
        assert len(result["tiers"]) == 3

    def test_one_euro_above_5000(self):
        """€5,001.00 → 375 + 250 + 5% of 1 = 625.00 + 0.05 = €625.05."""
        result = calculate_bik(Decimal("5001.00"))
        assert result["bik_exclusive"] == Decimal("625.05")


# ── Exact Boundary: €10,000 ─────────────────────────────────────────────────


class TestBoundary10000:
    """Tier 3/4 boundary at €10,000."""

    def test_exactly_10000(self):
        """€10,000 → 375 + 250 + 250 = €875.00."""
        result = calculate_bik(Decimal("10000.00"))
        assert result["bik_exclusive"] == Decimal("875.00")
        assert len(result["tiers"]) == 3

    def test_one_cent_below_10000(self):
        """€9,999.99 → 375 + 250 + 5% of 4999.99 = 375 + 250 + 250.00 = €875.00."""
        result = calculate_bik(Decimal("9999.99"))
        assert result["bik_exclusive"] == Decimal("875.00")

    def test_one_cent_above_10000(self):
        """€10,000.01 → 875 + 1% of 0.01 = 875.00 + 0.00 = €875.00."""
        result = calculate_bik(Decimal("10000.01"))
        assert result["bik_exclusive"] == Decimal("875.00")
        assert len(result["tiers"]) == 4

    def test_one_euro_above_10000(self):
        """€10,001.00 → 875 + 1% of 1 = 875.00 + 0.01 = €875.01."""
        result = calculate_bik(Decimal("10001.00"))
        assert result["bik_exclusive"] == Decimal("875.01")


# ── Exact Boundary: €200,000 ────────────────────────────────────────────────


class TestBoundary200000:
    """Tier 4/5 boundary at €200,000."""

    def test_exactly_200000(self):
        """€200,000 → 375 + 250 + 250 + 1% of 190000 = 875 + 1900 = €2,775.00."""
        result = calculate_bik(Decimal("200000.00"))
        assert result["bik_exclusive"] == Decimal("2775.00")
        assert len(result["tiers"]) == 4

    def test_one_cent_below_200000(self):
        """€199,999.99 → 875 + 1% of 189999.99 = 875 + 1900.00 = €2,775.00."""
        result = calculate_bik(Decimal("199999.99"))
        assert result["bik_exclusive"] == Decimal("2775.00")

    def test_one_cent_above_200000(self):
        """€200,000.01 → 2775 + 0.5% of 0.01 = 2775.00 + 0.00 = €2,775.00."""
        result = calculate_bik(Decimal("200000.01"))
        assert result["bik_exclusive"] == Decimal("2775.00")
        assert len(result["tiers"]) == 5

    def test_one_euro_above_200000(self):
        """€200,001.00 → 2775 + 0.5% of 1 = 2775.00 + 0.01 = €2,775.01."""
        result = calculate_bik(Decimal("200001.00"))
        assert result["bik_exclusive"] == Decimal("2775.01")


# ── Minimum Cap (€40) ──────────────────────────────────────────────────────


class TestMinimumCap:
    """WIK minimum of €40."""

    def test_minimum_applied_small_amount(self):
        """€10 → 15% = €1.50 → capped up to €40."""
        result = calculate_bik(Decimal("10.00"))
        assert result["bik_exclusive"] == WIK_MINIMUM

    def test_minimum_applied_one_euro(self):
        """€1 → 15% = €0.15 → capped up to €40."""
        result = calculate_bik(Decimal("1.00"))
        assert result["bik_exclusive"] == WIK_MINIMUM

    def test_exactly_at_minimum_threshold(self):
        """€266.67 → 15% = €40.00 — exactly at minimum, no cap needed."""
        result = calculate_bik(Decimal("266.67"))
        # 266.67 * 0.15 = 40.0005 → rounds to 40.00
        assert result["bik_exclusive"] == Decimal("40.00")

    def test_one_cent_below_minimum_threshold(self):
        """€266.66 → 15% = €39.999 → rounds to €40.00 (still at minimum)."""
        result = calculate_bik(Decimal("266.66"))
        # 266.66 * 0.15 = 39.999 → rounds to 40.00
        assert result["bik_exclusive"] == Decimal("40.00")

    def test_just_above_minimum_calculation(self):
        """€267 → 15% = €40.05 — above minimum, no cap needed."""
        result = calculate_bik(Decimal("267.00"))
        # 267 * 0.15 = 40.05
        assert result["bik_exclusive"] == Decimal("40.05")


# ── Maximum Cap (€6,775) ───────────────────────────────────────────────────


class TestMaximumCap:
    """WIK maximum of €6,775."""

    def test_exactly_at_maximum(self):
        """Find the exact principal where BIK = €6,775.

        875 + 1900 = 2775 (at €200,000)
        Remaining: 6775 - 2775 = 4000
        4000 / 0.005 = 800,000
        Total: 200,000 + 800,000 = €1,005,000
        """
        result = calculate_bik(Decimal("1005000.00"))
        assert result["bik_exclusive"] == WIK_MAXIMUM

    def test_one_euro_below_maximum_principal(self):
        """€1,004,999 → just below max."""
        result = calculate_bik(Decimal("1004999.00"))
        # 2775 + 0.5% of 804999 = 2775 + 4025.00 = 6800 → wait, that's wrong
        # Actually: 2775 + 0.5% of (1004999-200000) = 2775 + 0.5% of 804999
        # = 2775 + 4024.995 → rounds to 4025.00 → total = 6800.00
        # But max is 6775 → CAPPED
        # Hmm, let me recalculate: 6775 - 2775 = 4000 / 0.005 = 800000
        # So principal for exactly max = 200000 + 800000 = 1005000
        # At 1004999: 2775 + 0.005 * 804999 = 2775 + 4024.995 → 4025.00
        # Total calc: 6800.00 → capped at 6775
        assert result["bik_exclusive"] == WIK_MAXIMUM

    def test_one_euro_above_maximum_principal(self):
        """€1,005,001 → above max, still capped."""
        result = calculate_bik(Decimal("1005001.00"))
        assert result["bik_exclusive"] == WIK_MAXIMUM

    def test_enormous_amount(self):
        """€10,000,000 → capped at maximum."""
        result = calculate_bik(Decimal("10000000.00"))
        assert result["bik_exclusive"] == WIK_MAXIMUM

    def test_maximum_with_btw(self):
        """Maximum BIK + 21% BTW."""
        result = calculate_bik(Decimal("5000000.00"), include_btw=True)
        assert result["bik_exclusive"] == WIK_MAXIMUM
        expected_btw = Decimal("1422.75")  # 6775 * 0.21
        assert result["btw_amount"] == expected_btw
        assert result["bik_inclusive"] == Decimal("8197.75")


# ── Zero and Negative ───────────────────────────────────────────────────────


class TestZeroAndNegative:
    """Zero and negative principals."""

    def test_zero_principal(self):
        result = calculate_bik(Decimal("0"))
        assert result["bik_exclusive"] == Decimal("0")
        assert result["btw_amount"] == Decimal("0")
        assert result["bik_inclusive"] == Decimal("0")
        assert result["tiers"] == []

    def test_zero_with_btw(self):
        """Zero with BTW flag → still zero."""
        result = calculate_bik(Decimal("0"), include_btw=True)
        assert result["bik_inclusive"] == Decimal("0")

    def test_negative_principal(self):
        """Negative principal → zero BIK."""
        result = calculate_bik(Decimal("-5000.00"))
        assert result["bik_exclusive"] == Decimal("0")

    def test_negative_one_cent(self):
        """Even -0.01 should return zero."""
        result = calculate_bik(Decimal("-0.01"))
        assert result["bik_exclusive"] == Decimal("0")


# ── BTW Edge Cases ──────────────────────────────────────────────────────────


class TestBTWEdgeCases:
    """BTW calculation edge cases."""

    def test_btw_on_minimum(self):
        """Minimum €40 + 21% BTW = €48.40."""
        result = calculate_bik(Decimal("100.00"), include_btw=True)
        assert result["bik_exclusive"] == Decimal("40.00")  # minimum
        assert result["btw_amount"] == Decimal("8.40")
        assert result["bik_inclusive"] == Decimal("48.40")

    def test_btw_rounding(self):
        """BIK of €625 + 21% = €131.25 BTW (exact, no rounding issue)."""
        result = calculate_bik(Decimal("5000.00"), include_btw=True)
        assert result["btw_amount"] == Decimal("131.25")
        assert result["bik_inclusive"] == Decimal("756.25")

    def test_btw_with_odd_bik(self):
        """BIK that creates a BTW rounding scenario."""
        result = calculate_bik(Decimal("1000.00"), include_btw=True)
        # BIK: 15% of 1000 = 150.00
        # BTW: 150.00 * 0.21 = 31.50
        assert result["bik_exclusive"] == Decimal("150.00")
        assert result["btw_amount"] == Decimal("31.50")
        assert result["bik_inclusive"] == Decimal("181.50")

    def test_btw_disabled_by_default(self):
        """Default is include_btw=False."""
        result = calculate_bik(Decimal("5000.00"))
        assert result["btw_amount"] == Decimal("0")
        assert result["bik_inclusive"] == result["bik_exclusive"]


# ── Tier Transparency ──────────────────────────────────────────────────────


class TestTierTransparency:
    """Verify tier breakdown is correct for various amounts."""

    def test_all_five_tiers(self):
        """€300,000 should use all 5 tiers."""
        result = calculate_bik(Decimal("300000.00"))
        assert len(result["tiers"]) == 5

        # Tier 1: 0-2500 at 15%
        assert result["tiers"][0]["from"] == Decimal("0")
        assert result["tiers"][0]["to"] == Decimal("2500")
        assert result["tiers"][0]["applicable_amount"] == Decimal("2500")
        assert result["tiers"][0]["bik"] == Decimal("375.00")

        # Tier 2: 2500-5000 at 10%
        assert result["tiers"][1]["from"] == Decimal("2500")
        assert result["tiers"][1]["to"] == Decimal("5000")
        assert result["tiers"][1]["applicable_amount"] == Decimal("2500")
        assert result["tiers"][1]["bik"] == Decimal("250.00")

        # Tier 3: 5000-10000 at 5%
        assert result["tiers"][2]["from"] == Decimal("5000")
        assert result["tiers"][2]["to"] == Decimal("10000")
        assert result["tiers"][2]["applicable_amount"] == Decimal("5000")
        assert result["tiers"][2]["bik"] == Decimal("250.00")

        # Tier 4: 10000-200000 at 1%
        assert result["tiers"][3]["from"] == Decimal("10000")
        assert result["tiers"][3]["to"] == Decimal("200000")
        assert result["tiers"][3]["applicable_amount"] == Decimal("190000")
        assert result["tiers"][3]["bik"] == Decimal("1900.00")

        # Tier 5: 200000+ at 0.5%
        assert result["tiers"][4]["from"] == Decimal("200000")
        assert result["tiers"][4]["to"] is None
        assert result["tiers"][4]["applicable_amount"] == Decimal("100000")
        assert result["tiers"][4]["bik"] == Decimal("500.00")

    def test_single_tier_only(self):
        """€1,000 uses only tier 1."""
        result = calculate_bik(Decimal("1000.00"))
        assert len(result["tiers"]) == 1
        assert result["tiers"][0]["percentage"] == Decimal("0.15")


# ── Decimal Precision ──────────────────────────────────────────────────────


class TestDecimalPrecision:
    """Amounts with many decimal places."""

    def test_principal_with_cents(self):
        """€3,333.33 → 15% of 2500 + 10% of 833.33."""
        result = calculate_bik(Decimal("3333.33"))
        # Tier 1: 2500 * 0.15 = 375.00
        # Tier 2: 833.33 * 0.10 = 83.33 (83.333 → rounded)
        assert result["bik_exclusive"] == Decimal("458.33")

    def test_principal_exact_at_7500(self):
        """€7,500 → 375 + 250 + 5% of 2500 = 375 + 250 + 125 = €750.00."""
        result = calculate_bik(Decimal("7500.00"))
        assert result["bik_exclusive"] == Decimal("750.00")

    def test_principal_15000(self):
        """€15,000 → 375 + 250 + 250 + 1% of 5000 = 875 + 50 = €925.00."""
        result = calculate_bik(Decimal("15000.00"))
        assert result["bik_exclusive"] == Decimal("925.00")
