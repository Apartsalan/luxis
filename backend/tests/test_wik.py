"""Tests for the WIK/BIK calculation (art. 6:96 BW).

All expected values are hand-calculated and verified against
wettelijkerente.nl BIK calculator.
"""

from decimal import Decimal

from app.collections.wik import WIK_MAXIMUM, WIK_MINIMUM, calculate_bik


def test_bik_minimum():
    """Very small principal should return minimum €40."""
    result = calculate_bik(Decimal("100.00"))
    assert result["bik_exclusive"] == WIK_MINIMUM  # €40


def test_bik_at_minimum_boundary():
    """€266.67 * 15% = €40.00 — exactly at minimum."""
    # 40 / 0.15 = 266.67
    result = calculate_bik(Decimal("266.67"))
    assert result["bik_exclusive"] == Decimal("40.00")


def test_bik_small_amount():
    """€150 → 15% of 150 = €22.50 → but minimum is €40."""
    result = calculate_bik(Decimal("150.00"))
    assert result["bik_exclusive"] == Decimal("40.00")


def test_bik_1000():
    """€1,000 → 15% = €150.00"""
    result = calculate_bik(Decimal("1000.00"))
    assert result["bik_exclusive"] == Decimal("150.00")


def test_bik_2500():
    """€2,500 → 15% of 2500 = €375.00"""
    result = calculate_bik(Decimal("2500.00"))
    assert result["bik_exclusive"] == Decimal("375.00")


def test_bik_5000():
    """€5,000 → 15% of 2500 + 10% of 2500 = 375 + 250 = €625.00"""
    result = calculate_bik(Decimal("5000.00"))
    assert result["bik_exclusive"] == Decimal("625.00")


def test_bik_10000():
    """€10,000 → 375 + 250 + 5% of 5000 = 375 + 250 + 250 = €875.00"""
    result = calculate_bik(Decimal("10000.00"))
    assert result["bik_exclusive"] == Decimal("875.00")


def test_bik_25000():
    """€25,000 → 375 + 250 + 250 + 1% of 15000 = 875 + 150 = €1,025.00"""
    result = calculate_bik(Decimal("25000.00"))
    assert result["bik_exclusive"] == Decimal("1025.00")


def test_bik_100000():
    """€100,000 → 375 + 250 + 250 + 1% of 90000 = 875 + 900 = €1,775.00"""
    result = calculate_bik(Decimal("100000.00"))
    assert result["bik_exclusive"] == Decimal("1775.00")


def test_bik_200000():
    """€200,000 → 375 + 250 + 250 + 1% of 190000 = 875 + 1900 = €2,775.00"""
    result = calculate_bik(Decimal("200000.00"))
    assert result["bik_exclusive"] == Decimal("2775.00")


def test_bik_500000():
    """€500,000 → 2775 + 0.5% of 300000 = 2775 + 1500 = €4,275.00"""
    result = calculate_bik(Decimal("500000.00"))
    assert result["bik_exclusive"] == Decimal("4275.00")


def test_bik_maximum():
    """Very large principal should cap at maximum €6,775.00.
    Maximum is reached at €1,005,000:
    375 + 250 + 250 + 1900 + 0.5% of 800000 = 2775 + 4000 = 6775
    """
    result = calculate_bik(Decimal("1005000.00"))
    assert result["bik_exclusive"] == WIK_MAXIMUM  # €6,775.00


def test_bik_above_maximum():
    """Above the ceiling should still return maximum €6,775."""
    result = calculate_bik(Decimal("5000000.00"))
    assert result["bik_exclusive"] == WIK_MAXIMUM


def test_bik_with_btw():
    """BIK with 21% BTW."""
    result = calculate_bik(Decimal("5000.00"), include_btw=True)
    assert result["bik_exclusive"] == Decimal("625.00")
    assert result["btw_amount"] == Decimal("131.25")  # 625 * 0.21
    assert result["bik_inclusive"] == Decimal("756.25")  # 625 + 131.25


def test_bik_without_btw():
    """BIK without BTW (default for B2B)."""
    result = calculate_bik(Decimal("5000.00"), include_btw=False)
    assert result["btw_amount"] == Decimal("0")
    assert result["bik_inclusive"] == result["bik_exclusive"]


def test_bik_btw_3500_vof_client():
    """AUD124-01: €3,500 principal, non-VAT client (VOF) → BIK €475 + 21% BTW = €574.75."""
    result = calculate_bik(Decimal("3500.00"), include_btw=True)
    assert result["bik_exclusive"] == Decimal("475.00")  # 15% of 2500 + 10% of 1000
    assert result["btw_amount"] == Decimal("99.75")  # 475 * 0.21
    assert result["bik_inclusive"] == Decimal("574.75")


def test_bik_no_btw_3500_bv_client():
    """AUD124-01: €3,500 principal, VAT client (BV) → BIK €475, no BTW."""
    result = calculate_bik(Decimal("3500.00"), include_btw=False)
    assert result["bik_exclusive"] == Decimal("475.00")
    assert result["btw_amount"] == Decimal("0")
    assert result["bik_inclusive"] == Decimal("475.00")


def test_bik_zero_principal():
    """Zero principal should return zero BIK."""
    result = calculate_bik(Decimal("0"))
    assert result["bik_exclusive"] == Decimal("0")
    assert result["bik_inclusive"] == Decimal("0")


def test_bik_negative_principal():
    """Negative principal should return zero BIK."""
    result = calculate_bik(Decimal("-1000.00"))
    assert result["bik_exclusive"] == Decimal("0")


def test_bik_tiers_transparency():
    """Tier breakdown should be included for transparency."""
    result = calculate_bik(Decimal("5000.00"))
    assert len(result["tiers"]) == 2
    assert result["tiers"][0]["percentage"] == Decimal("0.15")
    assert result["tiers"][0]["applicable_amount"] == Decimal("2500")
    assert result["tiers"][1]["percentage"] == Decimal("0.10")
    assert result["tiers"][1]["applicable_amount"] == Decimal("2500")


def test_bik_exact_at_3750():
    """€3,750 → 15% of 2500 + 10% of 1250 = 375 + 125 = €500.00"""
    result = calculate_bik(Decimal("3750.00"))
    assert result["bik_exclusive"] == Decimal("500.00")


def test_bik_with_cents():
    """Principal with cents should calculate correctly."""
    result = calculate_bik(Decimal("1523.47"))
    # 15% of 1523.47 = 228.52 (rounded)
    assert result["bik_exclusive"] == Decimal("228.52")
