"""Extended tests for art. 6:44 BW payment distribution with multiple partial payments.

Tests cover:
- Sequential partial payments that gradually pay off the full debt
- Multiple small payments (druppelsgewijze betalingen)
- Payment exactly matching one component (costs, interest, principal)
- Overpayment scenarios
- Edge cases: very small payments, payments with many decimals
- Realistic incasso scenario with BIK + interest + principal
"""

from decimal import Decimal

from app.collections.payment_distribution import distribute_payment

# ── Helper ──────────────────────────────────────────────────────────────────


def apply_sequential_payments(
    payments: list[Decimal],
    initial_costs: Decimal,
    initial_interest: Decimal,
    initial_principal: Decimal,
) -> list[dict]:
    """Apply a sequence of payments and return the result of each distribution.

    After each payment, the remaining amounts carry over to the next payment.
    """
    results = []
    costs = initial_costs
    interest = initial_interest
    principal = initial_principal

    for payment in payments:
        result = distribute_payment(
            payment_amount=payment,
            outstanding_costs=costs,
            outstanding_interest=interest,
            outstanding_principal=principal,
        )
        results.append(result)

        # Update outstanding amounts for next payment
        costs = result["remaining_costs"]
        interest = result["remaining_interest"]
        principal = result["remaining_principal"]

    return results


# ── Sequential Payments: Gradual Payoff ─────────────────────────────────────


class TestSequentialPayments:
    """Multiple partial payments gradually paying off the entire debt."""

    def test_three_payments_pay_everything(self):
        """Three payments that together cover costs + interest + principal.

        Debt: €875 costs + €600 interest + €5000 principal = €6,475
        Payment 1: €1,000 → 875 costs + 125 interest
        Payment 2: €1,000 → 475 interest + 525 principal
        Payment 3: €4,475 → 4475 principal (fully paid)
        """
        results = apply_sequential_payments(
            payments=[Decimal("1000.00"), Decimal("1000.00"), Decimal("4475.00")],
            initial_costs=Decimal("875.00"),
            initial_interest=Decimal("600.00"),
            initial_principal=Decimal("5000.00"),
        )

        # Payment 1
        assert results[0]["to_costs"] == Decimal("875.00")
        assert results[0]["to_interest"] == Decimal("125.00")
        assert results[0]["to_principal"] == Decimal("0")
        assert results[0]["remaining_costs"] == Decimal("0")
        assert results[0]["remaining_interest"] == Decimal("475.00")

        # Payment 2
        assert results[1]["to_costs"] == Decimal("0")
        assert results[1]["to_interest"] == Decimal("475.00")
        assert results[1]["to_principal"] == Decimal("525.00")
        assert results[1]["remaining_interest"] == Decimal("0")
        assert results[1]["remaining_principal"] == Decimal("4475.00")

        # Payment 3
        assert results[2]["to_costs"] == Decimal("0")
        assert results[2]["to_interest"] == Decimal("0")
        assert results[2]["to_principal"] == Decimal("4475.00")
        assert results[2]["remaining_principal"] == Decimal("0")
        assert results[2]["overpayment"] == Decimal("0")

    def test_five_equal_payments(self):
        """Five equal payments of €1,295.

        Debt: €875 costs + €600 interest + €5000 principal = €6,475
        5 × €1,295 = €6,475
        """
        results = apply_sequential_payments(
            payments=[Decimal("1295.00")] * 5,
            initial_costs=Decimal("875.00"),
            initial_interest=Decimal("600.00"),
            initial_principal=Decimal("5000.00"),
        )

        # Verify full debt is paid off
        final = results[-1]
        assert final["remaining_costs"] == Decimal("0")
        assert final["remaining_interest"] == Decimal("0")
        assert final["remaining_principal"] == Decimal("0")
        assert final["overpayment"] == Decimal("0")

        # Verify total allocated matches
        total_to_costs = sum(r["to_costs"] for r in results)
        total_to_interest = sum(r["to_interest"] for r in results)
        total_to_principal = sum(r["to_principal"] for r in results)
        assert total_to_costs == Decimal("875.00")
        assert total_to_interest == Decimal("600.00")
        assert total_to_principal == Decimal("5000.00")


# ── Many Small Payments (druppelsgewijs) ────────────────────────────────────


class TestManySmallPayments:
    """Druppelsgewijze betalingen — many small amounts."""

    def test_ten_small_payments(self):
        """Ten payments of €100 against €300 costs + €200 interest + €500 principal.

        Total debt: €1,000
        10 × €100 = €1,000 (exactly covers everything)
        """
        results = apply_sequential_payments(
            payments=[Decimal("100.00")] * 10,
            initial_costs=Decimal("300.00"),
            initial_interest=Decimal("200.00"),
            initial_principal=Decimal("500.00"),
        )

        # After 3 payments: costs fully paid
        assert results[2]["remaining_costs"] == Decimal("0")
        # After 5 payments: interest fully paid
        assert results[4]["remaining_interest"] == Decimal("0")
        # After 10 payments: everything paid
        assert results[9]["remaining_principal"] == Decimal("0")

        total_to_costs = sum(r["to_costs"] for r in results)
        total_to_interest = sum(r["to_interest"] for r in results)
        total_to_principal = sum(r["to_principal"] for r in results)
        assert total_to_costs == Decimal("300.00")
        assert total_to_interest == Decimal("200.00")
        assert total_to_principal == Decimal("500.00")

    def test_very_small_payments_one_cent(self):
        """Payments of 1 cent — should still distribute correctly."""
        results = apply_sequential_payments(
            payments=[Decimal("0.01")] * 5,
            initial_costs=Decimal("0.03"),
            initial_interest=Decimal("0.01"),
            initial_principal=Decimal("0.01"),
        )

        # First 3 pennies → costs
        assert results[0]["to_costs"] == Decimal("0.01")
        assert results[1]["to_costs"] == Decimal("0.01")
        assert results[2]["to_costs"] == Decimal("0.01")
        assert results[2]["remaining_costs"] == Decimal("0")

        # 4th penny → interest
        assert results[3]["to_interest"] == Decimal("0.01")
        assert results[3]["remaining_interest"] == Decimal("0")

        # 5th penny → principal
        assert results[4]["to_principal"] == Decimal("0.01")
        assert results[4]["remaining_principal"] == Decimal("0")


# ── Payment Exactly Matching One Component ──────────────────────────────────


class TestExactComponentPayments:
    """Payments that exactly match one outstanding component."""

    def test_payment_equals_costs(self):
        """Payment exactly covers all costs, nothing else."""
        result = distribute_payment(
            payment_amount=Decimal("875.00"),
            outstanding_costs=Decimal("875.00"),
            outstanding_interest=Decimal("600.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["to_costs"] == Decimal("875.00")
        assert result["to_interest"] == Decimal("0")
        assert result["to_principal"] == Decimal("0")
        assert result["remaining_costs"] == Decimal("0")

    def test_payment_equals_costs_plus_interest(self):
        """Payment covers exactly costs + interest."""
        result = distribute_payment(
            payment_amount=Decimal("1475.00"),
            outstanding_costs=Decimal("875.00"),
            outstanding_interest=Decimal("600.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["to_costs"] == Decimal("875.00")
        assert result["to_interest"] == Decimal("600.00")
        assert result["to_principal"] == Decimal("0")
        assert result["remaining_costs"] == Decimal("0")
        assert result["remaining_interest"] == Decimal("0")
        assert result["remaining_principal"] == Decimal("5000.00")

    def test_payment_equals_total_debt(self):
        """Payment exactly matches total outstanding debt."""
        result = distribute_payment(
            payment_amount=Decimal("6475.00"),
            outstanding_costs=Decimal("875.00"),
            outstanding_interest=Decimal("600.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["remaining_costs"] == Decimal("0")
        assert result["remaining_interest"] == Decimal("0")
        assert result["remaining_principal"] == Decimal("0")
        assert result["overpayment"] == Decimal("0")


# ── Overpayment Scenarios ──────────────────────────────────────────────────


class TestOverpayment:
    """Payments exceeding the total outstanding debt."""

    def test_large_overpayment(self):
        """Payment far exceeds total debt."""
        result = distribute_payment(
            payment_amount=Decimal("100000.00"),
            outstanding_costs=Decimal("875.00"),
            outstanding_interest=Decimal("600.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["to_costs"] == Decimal("875.00")
        assert result["to_interest"] == Decimal("600.00")
        assert result["to_principal"] == Decimal("5000.00")
        assert result["overpayment"] == Decimal("93525.00")

    def test_one_cent_overpayment(self):
        """Payment exceeds total by exactly 1 cent."""
        result = distribute_payment(
            payment_amount=Decimal("6475.01"),
            outstanding_costs=Decimal("875.00"),
            outstanding_interest=Decimal("600.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["overpayment"] == Decimal("0.01")

    def test_sequential_with_overpayment_at_end(self):
        """Last payment in sequence causes small overpayment."""
        results = apply_sequential_payments(
            payments=[Decimal("2000.00"), Decimal("2000.00"), Decimal("3000.00")],
            initial_costs=Decimal("875.00"),
            initial_interest=Decimal("600.00"),
            initial_principal=Decimal("5000.00"),
        )
        # Total paid: 7000, Total debt: 6475, Overpayment: 525
        assert results[-1]["overpayment"] == Decimal("525.00")


# ── No Outstanding Amounts ──────────────────────────────────────────────────


class TestNoOutstandingAmounts:
    """Edge cases where one or more components are zero."""

    def test_all_zero(self):
        """Everything is 0, any payment is overpayment."""
        result = distribute_payment(
            payment_amount=Decimal("100.00"),
            outstanding_costs=Decimal("0"),
            outstanding_interest=Decimal("0"),
            outstanding_principal=Decimal("0"),
        )
        assert result["to_costs"] == Decimal("0")
        assert result["to_interest"] == Decimal("0")
        assert result["to_principal"] == Decimal("0")
        assert result["overpayment"] == Decimal("100.00")

    def test_only_principal_remaining(self):
        """Only principal remains — payment goes directly to principal."""
        result = distribute_payment(
            payment_amount=Decimal("2000.00"),
            outstanding_costs=Decimal("0"),
            outstanding_interest=Decimal("0"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["to_principal"] == Decimal("2000.00")
        assert result["remaining_principal"] == Decimal("3000.00")

    def test_only_interest_remaining(self):
        """Only interest remains — payment goes to interest."""
        result = distribute_payment(
            payment_amount=Decimal("300.00"),
            outstanding_costs=Decimal("0"),
            outstanding_interest=Decimal("600.00"),
            outstanding_principal=Decimal("0"),
        )
        assert result["to_interest"] == Decimal("300.00")
        assert result["remaining_interest"] == Decimal("300.00")

    def test_only_costs_remaining(self):
        """Only costs remain — payment goes to costs."""
        result = distribute_payment(
            payment_amount=Decimal("500.00"),
            outstanding_costs=Decimal("875.00"),
            outstanding_interest=Decimal("0"),
            outstanding_principal=Decimal("0"),
        )
        assert result["to_costs"] == Decimal("500.00")
        assert result["remaining_costs"] == Decimal("375.00")


# ── Realistic Incasso Scenario ─────────────────────────────────────────────


class TestRealisticScenario:
    """Realistic incasso scenario as Lisanne would handle it.

    Case: Schuldeiser B.V. vs. Piet Schuldenaar
    Principal: €3,750 (unpaid invoice)
    BIK: €500 (15% of 2500 + 10% of 1250)
    Interest (estimated): €225 (6% for 1 year)
    Total: €4,475

    Payments arrive over several months.
    """

    def test_realistic_three_payment_scenario(self):
        """Three payments over 3 months, eventually paying off everything."""
        results = apply_sequential_payments(
            payments=[Decimal("1500.00"), Decimal("1500.00"), Decimal("1475.00")],
            initial_costs=Decimal("500.00"),
            initial_interest=Decimal("225.00"),
            initial_principal=Decimal("3750.00"),
        )

        # Payment 1: €1500 → €500 costs + €225 interest + €775 principal
        assert results[0]["to_costs"] == Decimal("500.00")
        assert results[0]["to_interest"] == Decimal("225.00")
        assert results[0]["to_principal"] == Decimal("775.00")
        assert results[0]["remaining_principal"] == Decimal("2975.00")

        # Payment 2: €1500 → €0 costs + €0 interest + €1500 principal
        assert results[1]["to_costs"] == Decimal("0")
        assert results[1]["to_interest"] == Decimal("0")
        assert results[1]["to_principal"] == Decimal("1500.00")
        assert results[1]["remaining_principal"] == Decimal("1475.00")

        # Payment 3: €1475 → exact remaining principal
        assert results[2]["to_principal"] == Decimal("1475.00")
        assert results[2]["remaining_principal"] == Decimal("0")
        assert results[2]["overpayment"] == Decimal("0")

    def test_realistic_with_partial_costs_payment(self):
        """Debtor starts paying small amounts that don't even cover costs.

        BIK: €625 (€5000 principal)
        Interest: €300
        Principal: €5000
        Total: €5925

        Payments: €200, €200, €225, €300, €5000
        """
        results = apply_sequential_payments(
            payments=[
                Decimal("200.00"),
                Decimal("200.00"),
                Decimal("225.00"),
                Decimal("300.00"),
                Decimal("5000.00"),
            ],
            initial_costs=Decimal("625.00"),
            initial_interest=Decimal("300.00"),
            initial_principal=Decimal("5000.00"),
        )

        # Payment 1: €200 → all to costs
        assert results[0]["to_costs"] == Decimal("200.00")
        assert results[0]["remaining_costs"] == Decimal("425.00")

        # Payment 2: €200 → all to costs
        assert results[1]["to_costs"] == Decimal("200.00")
        assert results[1]["remaining_costs"] == Decimal("225.00")

        # Payment 3: €225 → finishes costs
        assert results[2]["to_costs"] == Decimal("225.00")
        assert results[2]["remaining_costs"] == Decimal("0")
        assert results[2]["to_interest"] == Decimal("0")

        # Payment 4: €300 → all to interest
        assert results[3]["to_costs"] == Decimal("0")
        assert results[3]["to_interest"] == Decimal("300.00")
        assert results[3]["remaining_interest"] == Decimal("0")

        # Payment 5: €5000 → all to principal
        assert results[4]["to_principal"] == Decimal("5000.00")
        assert results[4]["remaining_principal"] == Decimal("0")
        assert results[4]["overpayment"] == Decimal("0")


# ── Decimal Precision Under Stress ─────────────────────────────────────────


class TestDecimalPrecision:
    """Verify no floating-point errors accumulate over many payments."""

    def test_many_payments_no_precision_loss(self):
        """50 payments of €1.00 against €20 costs + €10 interest + €20 principal.

        Total: €50. Should end with exactly 0 remaining.
        """
        results = apply_sequential_payments(
            payments=[Decimal("1.00")] * 50,
            initial_costs=Decimal("20.00"),
            initial_interest=Decimal("10.00"),
            initial_principal=Decimal("20.00"),
        )
        final = results[-1]
        assert final["remaining_costs"] == Decimal("0")
        assert final["remaining_interest"] == Decimal("0")
        assert final["remaining_principal"] == Decimal("0")
        assert final["overpayment"] == Decimal("0")

    def test_payments_with_cents(self):
        """Payments with odd cent amounts should not cause rounding drift."""
        results = apply_sequential_payments(
            payments=[
                Decimal("33.33"),
                Decimal("33.33"),
                Decimal("33.34"),  # together = 100.00
            ],
            initial_costs=Decimal("50.00"),
            initial_interest=Decimal("25.00"),
            initial_principal=Decimal("25.00"),
        )
        # Total paid: 100.00, Total debt: 100.00
        final = results[-1]
        assert final["remaining_costs"] == Decimal("0")
        assert final["remaining_interest"] == Decimal("0")
        assert final["remaining_principal"] == Decimal("0")
        assert final["overpayment"] == Decimal("0")

    def test_repeating_decimals(self):
        """Payments that create repeating decimal situations."""
        # 10 / 3 = 3.333... → each payment rounds
        result1 = distribute_payment(
            payment_amount=Decimal("3.33"),
            outstanding_costs=Decimal("10.00"),
            outstanding_interest=Decimal("0"),
            outstanding_principal=Decimal("0"),
        )
        assert result1["to_costs"] == Decimal("3.33")
        assert result1["remaining_costs"] == Decimal("6.67")

        result2 = distribute_payment(
            payment_amount=Decimal("3.33"),
            outstanding_costs=Decimal("6.67"),
            outstanding_interest=Decimal("0"),
            outstanding_principal=Decimal("0"),
        )
        assert result2["remaining_costs"] == Decimal("3.34")

        result3 = distribute_payment(
            payment_amount=Decimal("3.34"),
            outstanding_costs=Decimal("3.34"),
            outstanding_interest=Decimal("0"),
            outstanding_principal=Decimal("0"),
        )
        assert result3["remaining_costs"] == Decimal("0")
        assert result3["overpayment"] == Decimal("0")


# ── Transition Between Components ──────────────────────────────────────────


class TestComponentTransitions:
    """Payments that span the boundary between two components."""

    def test_payment_splits_across_costs_and_interest(self):
        """Single payment that partially covers costs and partially interest."""
        result = distribute_payment(
            payment_amount=Decimal("1000.00"),
            outstanding_costs=Decimal("750.00"),
            outstanding_interest=Decimal("500.00"),
            outstanding_principal=Decimal("3000.00"),
        )
        assert result["to_costs"] == Decimal("750.00")
        assert result["to_interest"] == Decimal("250.00")
        assert result["to_principal"] == Decimal("0")

    def test_payment_splits_across_interest_and_principal(self):
        """Payment covers remaining interest and part of principal."""
        result = distribute_payment(
            payment_amount=Decimal("800.00"),
            outstanding_costs=Decimal("0"),
            outstanding_interest=Decimal("300.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["to_interest"] == Decimal("300.00")
        assert result["to_principal"] == Decimal("500.00")

    def test_payment_spans_all_three_components(self):
        """Single payment covers costs + interest + part of principal."""
        result = distribute_payment(
            payment_amount=Decimal("2000.00"),
            outstanding_costs=Decimal("200.00"),
            outstanding_interest=Decimal("300.00"),
            outstanding_principal=Decimal("5000.00"),
        )
        assert result["to_costs"] == Decimal("200.00")
        assert result["to_interest"] == Decimal("300.00")
        assert result["to_principal"] == Decimal("1500.00")
        assert result["remaining_principal"] == Decimal("3500.00")
