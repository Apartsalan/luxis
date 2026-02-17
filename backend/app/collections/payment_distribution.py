"""Payment distribution engine — Art. 6:44 BW.

Art. 6:44 BW determines the order in which a payment is allocated:
1. First: costs (kosten) — BIK, proceskosten, deurwaarderskosten
2. Then: accrued interest (rente)
3. Finally: principal (hoofdsom)

This means a partial payment reduces the principal LAST.
The debtor cannot choose to pay off the principal first.

Example:
    Outstanding: €5,000 principal + €600 interest + €875 BIK = €6,475 total
    Payment: €2,000
    Allocation:
        → €875 to costs (BIK fully paid)
        → €600 to interest (fully paid)
        → €525 to principal (partial — €4,475 remaining)
"""

from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")


def _round2(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def distribute_payment(
    payment_amount: Decimal,
    outstanding_costs: Decimal,
    outstanding_interest: Decimal,
    outstanding_principal: Decimal,
) -> dict:
    """Distribute a payment according to art. 6:44 BW.

    Order: costs → interest → principal

    Args:
        payment_amount: The payment to distribute
        outstanding_costs: Total outstanding costs (BIK, proceskosten, etc.)
        outstanding_interest: Total accrued and unpaid interest
        outstanding_principal: Total outstanding principal

    Returns:
        Dict with:
            payment_amount: Original payment
            to_costs: Amount allocated to costs
            to_interest: Amount allocated to interest
            to_principal: Amount allocated to principal
            remaining_costs: Costs still outstanding after payment
            remaining_interest: Interest still outstanding after payment
            remaining_principal: Principal still outstanding after payment
            overpayment: Any excess amount (payment > total outstanding)
    """
    remaining = _round2(payment_amount)

    # 1. Costs first
    to_costs = _round2(min(remaining, outstanding_costs))
    remaining -= to_costs

    # 2. Interest second
    to_interest = _round2(min(remaining, outstanding_interest))
    remaining -= to_interest

    # 3. Principal last
    to_principal = _round2(min(remaining, outstanding_principal))
    remaining -= to_principal

    # Any leftover is overpayment
    overpayment = _round2(max(remaining, Decimal("0")))

    return {
        "payment_amount": _round2(payment_amount),
        "to_costs": to_costs,
        "to_interest": to_interest,
        "to_principal": to_principal,
        "remaining_costs": _round2(outstanding_costs - to_costs),
        "remaining_interest": _round2(outstanding_interest - to_interest),
        "remaining_principal": _round2(outstanding_principal - to_principal),
        "overpayment": overpayment,
    }
