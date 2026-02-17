"""Tests for art. 6:44 BW payment distribution (kosten → rente → hoofdsom)."""

from decimal import Decimal

from app.collections.payment_distribution import distribute_payment


def test_full_payment_covers_everything():
    """Payment covers all costs, interest, and principal."""
    result = distribute_payment(
        payment_amount=Decimal("6475.00"),
        outstanding_costs=Decimal("875.00"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("875.00")
    assert result["to_interest"] == Decimal("600.00")
    assert result["to_principal"] == Decimal("5000.00")
    assert result["remaining_costs"] == Decimal("0")
    assert result["remaining_interest"] == Decimal("0")
    assert result["remaining_principal"] == Decimal("0")
    assert result["overpayment"] == Decimal("0")


def test_partial_payment_costs_only():
    """Small payment only covers part of costs."""
    result = distribute_payment(
        payment_amount=Decimal("500.00"),
        outstanding_costs=Decimal("875.00"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("500.00")
    assert result["to_interest"] == Decimal("0")
    assert result["to_principal"] == Decimal("0")
    assert result["remaining_costs"] == Decimal("375.00")
    assert result["remaining_interest"] == Decimal("600.00")
    assert result["remaining_principal"] == Decimal("5000.00")


def test_partial_payment_costs_and_some_interest():
    """Payment covers costs and part of interest."""
    result = distribute_payment(
        payment_amount=Decimal("1200.00"),
        outstanding_costs=Decimal("875.00"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("875.00")
    assert result["to_interest"] == Decimal("325.00")
    assert result["to_principal"] == Decimal("0")
    assert result["remaining_interest"] == Decimal("275.00")


def test_payment_covers_costs_interest_partial_principal():
    """Payment covers costs + interest + part of principal."""
    result = distribute_payment(
        payment_amount=Decimal("2000.00"),
        outstanding_costs=Decimal("875.00"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("875.00")
    assert result["to_interest"] == Decimal("600.00")
    assert result["to_principal"] == Decimal("525.00")
    assert result["remaining_principal"] == Decimal("4475.00")


def test_overpayment():
    """Payment exceeds total outstanding — should show overpayment."""
    result = distribute_payment(
        payment_amount=Decimal("7000.00"),
        outstanding_costs=Decimal("875.00"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("875.00")
    assert result["to_interest"] == Decimal("600.00")
    assert result["to_principal"] == Decimal("5000.00")
    assert result["overpayment"] == Decimal("525.00")


def test_no_costs():
    """When there are no costs, payment goes to interest first."""
    result = distribute_payment(
        payment_amount=Decimal("400.00"),
        outstanding_costs=Decimal("0"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("0")
    assert result["to_interest"] == Decimal("400.00")
    assert result["to_principal"] == Decimal("0")


def test_no_interest():
    """When there is no interest, payment goes from costs to principal."""
    result = distribute_payment(
        payment_amount=Decimal("1000.00"),
        outstanding_costs=Decimal("200.00"),
        outstanding_interest=Decimal("0"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("200.00")
    assert result["to_interest"] == Decimal("0")
    assert result["to_principal"] == Decimal("800.00")


def test_zero_payment():
    """Zero payment should not allocate anything."""
    result = distribute_payment(
        payment_amount=Decimal("0"),
        outstanding_costs=Decimal("875.00"),
        outstanding_interest=Decimal("600.00"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_costs"] == Decimal("0")
    assert result["to_interest"] == Decimal("0")
    assert result["to_principal"] == Decimal("0")
    assert result["remaining_costs"] == Decimal("875.00")


def test_small_payment_with_cents():
    """Payment with cents should distribute correctly."""
    result = distribute_payment(
        payment_amount=Decimal("123.45"),
        outstanding_costs=Decimal("100.00"),
        outstanding_interest=Decimal("50.00"),
        outstanding_principal=Decimal("3000.00"),
    )
    assert result["to_costs"] == Decimal("100.00")
    assert result["to_interest"] == Decimal("23.45")
    assert result["to_principal"] == Decimal("0")
    assert result["remaining_interest"] == Decimal("26.55")


def test_principal_only():
    """When only principal remains, full payment goes to principal."""
    result = distribute_payment(
        payment_amount=Decimal("2000.00"),
        outstanding_costs=Decimal("0"),
        outstanding_interest=Decimal("0"),
        outstanding_principal=Decimal("5000.00"),
    )
    assert result["to_principal"] == Decimal("2000.00")
    assert result["remaining_principal"] == Decimal("3000.00")


def test_exact_costs_payment():
    """Payment exactly equal to costs."""
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
