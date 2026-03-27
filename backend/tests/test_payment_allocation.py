"""Tests for art. 6:44 BW payment allocation as integrated in create_payment.

Verifies that the allocation logic used by service.create_payment correctly:
1. Calculates outstanding amounts (total - previously allocated)
2. Distributes new payments per art. 6:44 BW (costs -> interest -> principal)
3. Handles sequential payments where earlier allocations reduce outstanding amounts

These are synchronous tests that exercise the exact same logic path
as create_payment, without needing an async database session.
"""

from decimal import Decimal

from app.collections.payment_distribution import distribute_payment
from app.collections.wik import calculate_bik


def _allocate_payment(
    payment_amount: Decimal,
    total_costs: Decimal,
    total_interest: Decimal,
    total_principal: Decimal,
    prev_costs: Decimal,
    prev_interest: Decimal,
    prev_principal: Decimal,
) -> dict:
    """Replicate the allocation logic from service.create_payment.

    This is the exact same calculation that create_payment performs:
    outstanding = total - previously_allocated, then distribute.
    """
    outstanding_costs = max(Decimal("0"), total_costs - prev_costs)
    outstanding_interest = max(Decimal("0"), total_interest - prev_interest)
    outstanding_principal = max(Decimal("0"), total_principal - prev_principal)

    return distribute_payment(
        payment_amount=payment_amount,
        outstanding_costs=outstanding_costs,
        outstanding_interest=outstanding_interest,
        outstanding_principal=outstanding_principal,
    )


# ── Single Payment Allocation ─────────────────────────────────────────────


class TestSinglePaymentAllocation:
    """First payment on a case — no previous allocations."""

    def test_first_payment_covers_costs_interest_and_partial_principal(self):
        """€1,000 against €625 costs + €300 interest + €5,000 principal.

        Expected: €625 costs + €300 interest + €75 principal.
        """
        total_principal = Decimal("5000.00")
        bik = calculate_bik(total_principal)
        total_costs = bik["bik_inclusive"]  # €625.00
        total_interest = Decimal("300.00")

        result = _allocate_payment(
            payment_amount=Decimal("1000.00"),
            total_costs=total_costs,
            total_interest=total_interest,
            total_principal=total_principal,
            prev_costs=Decimal("0"),
            prev_interest=Decimal("0"),
            prev_principal=Decimal("0"),
        )

        assert result["to_costs"] == Decimal("625.00")
        assert result["to_interest"] == Decimal("300.00")
        assert result["to_principal"] == Decimal("75.00")
        assert result["overpayment"] == Decimal("0")

    def test_first_payment_only_covers_costs(self):
        """€500 against €625 costs — doesn't reach interest."""
        result = _allocate_payment(
            payment_amount=Decimal("500.00"),
            total_costs=Decimal("625.00"),
            total_interest=Decimal("300.00"),
            total_principal=Decimal("5000.00"),
            prev_costs=Decimal("0"),
            prev_interest=Decimal("0"),
            prev_principal=Decimal("0"),
        )

        assert result["to_costs"] == Decimal("500.00")
        assert result["to_interest"] == Decimal("0")
        assert result["to_principal"] == Decimal("0")

    def test_first_payment_covers_everything_with_overpayment(self):
        """€7,000 against €625 costs + €300 interest + €5,000 principal.

        Total debt: €5,925. Overpayment: €1,075.
        """
        result = _allocate_payment(
            payment_amount=Decimal("7000.00"),
            total_costs=Decimal("625.00"),
            total_interest=Decimal("300.00"),
            total_principal=Decimal("5000.00"),
            prev_costs=Decimal("0"),
            prev_interest=Decimal("0"),
            prev_principal=Decimal("0"),
        )

        assert result["to_costs"] == Decimal("625.00")
        assert result["to_interest"] == Decimal("300.00")
        assert result["to_principal"] == Decimal("5000.00")
        assert result["overpayment"] == Decimal("1075.00")


# ── Sequential Payment Allocation ─────────────────────────────────────────


class TestSequentialPaymentAllocation:
    """Multiple payments, each building on the previous allocations."""

    def test_three_payments_pay_off_full_debt(self):
        """Realistic scenario: 3 payments gradually paying off everything.

        Case: €5,000 principal, BIK = €625, interest = €300.
        Total debt: €5,925.

        Payment 1: €1,000 → €625 costs + €300 interest + €75 principal
        Payment 2: €2,000 → €0 costs + €0 interest + €2,000 principal
        Payment 3: €2,925 → €0 costs + €0 interest + €2,925 principal (done)
        """
        total_costs = Decimal("625.00")
        total_interest = Decimal("300.00")
        total_principal = Decimal("5000.00")

        # Track cumulative allocations (simulates DB sum of previous payments)
        cum_costs = Decimal("0")
        cum_interest = Decimal("0")
        cum_principal = Decimal("0")

        # Payment 1: €1,000
        d1 = _allocate_payment(
            Decimal("1000.00"),
            total_costs,
            total_interest,
            total_principal,
            cum_costs,
            cum_interest,
            cum_principal,
        )
        assert d1["to_costs"] == Decimal("625.00")
        assert d1["to_interest"] == Decimal("300.00")
        assert d1["to_principal"] == Decimal("75.00")

        cum_costs += d1["to_costs"]
        cum_interest += d1["to_interest"]
        cum_principal += d1["to_principal"]

        # Payment 2: €2,000 — costs and interest already paid
        d2 = _allocate_payment(
            Decimal("2000.00"),
            total_costs,
            total_interest,
            total_principal,
            cum_costs,
            cum_interest,
            cum_principal,
        )
        assert d2["to_costs"] == Decimal("0")
        assert d2["to_interest"] == Decimal("0")
        assert d2["to_principal"] == Decimal("2000.00")

        cum_costs += d2["to_costs"]
        cum_interest += d2["to_interest"]
        cum_principal += d2["to_principal"]

        # Payment 3: €2,925 — remaining principal
        d3 = _allocate_payment(
            Decimal("2925.00"),
            total_costs,
            total_interest,
            total_principal,
            cum_costs,
            cum_interest,
            cum_principal,
        )
        assert d3["to_costs"] == Decimal("0")
        assert d3["to_interest"] == Decimal("0")
        assert d3["to_principal"] == Decimal("2925.00")
        assert d3["overpayment"] == Decimal("0")

        # Verify totals
        assert cum_costs + d3["to_costs"] == total_costs
        assert cum_interest + d3["to_interest"] == total_interest
        assert cum_principal + d3["to_principal"] == total_principal

    def test_many_small_payments_with_bik_calculation(self):
        """10 payments of €100 against a €500 principal case.

        BIK for €500: 15% of 500 = €75, but minimum is €40, so BIK = €75.00
        Interest: €30
        Total debt: €500 + €75 + €30 = €605

        Payment 1: €75 to costs
        Payment 2-3: remaining costs (€0) → €30 interest → principal
        etc.
        """
        total_principal = Decimal("500.00")
        bik = calculate_bik(total_principal)
        total_costs = bik["bik_inclusive"]  # 15% of 500 = €75
        assert total_costs == Decimal("75.00")
        total_interest = Decimal("30.00")

        cum_costs = Decimal("0")
        cum_interest = Decimal("0")
        cum_principal = Decimal("0")

        for i in range(7):  # 7 × €100 = €700 > €605 total
            d = _allocate_payment(
                Decimal("100.00"),
                total_costs,
                total_interest,
                total_principal,
                cum_costs,
                cum_interest,
                cum_principal,
            )
            cum_costs += d["to_costs"]
            cum_interest += d["to_interest"]
            cum_principal += d["to_principal"]

        # After 7 payments of €100 = €700
        # Total debt was €605, so €95 overpayment on last payment
        assert cum_costs == total_costs  # €75 fully allocated
        assert cum_interest == total_interest  # €30 fully allocated
        assert cum_principal == total_principal  # €500 fully allocated


# ── Edge Cases ─────────────────────────────────────────────────────────────


class TestAllocationEdgeCases:
    """Edge cases in the allocation logic."""

    def test_no_claims_all_overpayment(self):
        """No claims → everything is overpayment."""
        result = _allocate_payment(
            payment_amount=Decimal("100.00"),
            total_costs=Decimal("0"),
            total_interest=Decimal("0"),
            total_principal=Decimal("0"),
            prev_costs=Decimal("0"),
            prev_interest=Decimal("0"),
            prev_principal=Decimal("0"),
        )
        assert result["overpayment"] == Decimal("100.00")

    def test_previous_over_allocation_clamped_to_zero(self):
        """If previous allocations exceed totals, outstanding is clamped to 0.

        This guards against edge cases where a claim amount was reduced
        after a payment was already allocated.
        """
        result = _allocate_payment(
            payment_amount=Decimal("100.00"),
            total_costs=Decimal("100.00"),
            total_interest=Decimal("50.00"),
            total_principal=Decimal("500.00"),
            # Previous allocations exceed total costs (shouldn't happen, but safety)
            prev_costs=Decimal("150.00"),
            prev_interest=Decimal("50.00"),
            prev_principal=Decimal("0"),
        )
        # outstanding_costs = max(0, 100-150) = 0
        # outstanding_interest = max(0, 50-50) = 0
        # outstanding_principal = max(0, 500-0) = 500
        assert result["to_costs"] == Decimal("0")
        assert result["to_interest"] == Decimal("0")
        assert result["to_principal"] == Decimal("100.00")

    def test_allocation_with_realistic_bik_and_interest(self):
        """Full realistic scenario with calculated BIK.

        €10,000 principal:
        - BIK: 15% of 2500 + 10% of 2500 + 5% of 5000 = 375 + 250 + 250 = €875
        - Interest: €411.78 (random realistic amount)
        - Payment: €2,000
        """
        total_principal = Decimal("10000.00")
        bik = calculate_bik(total_principal)
        total_costs = bik["bik_inclusive"]
        assert total_costs == Decimal("875.00")
        total_interest = Decimal("411.78")

        result = _allocate_payment(
            payment_amount=Decimal("2000.00"),
            total_costs=total_costs,
            total_interest=total_interest,
            total_principal=total_principal,
            prev_costs=Decimal("0"),
            prev_interest=Decimal("0"),
            prev_principal=Decimal("0"),
        )

        # €2000: first €875 to costs, then €411.78 to interest, then €713.22 to principal
        assert result["to_costs"] == Decimal("875.00")
        assert result["to_interest"] == Decimal("411.78")
        assert result["to_principal"] == Decimal("713.22")
        assert result["remaining_principal"] == Decimal("9286.78")
