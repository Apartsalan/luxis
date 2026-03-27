"""WIK/BIK calculation — Buitengerechtelijke incassokosten (art. 6:96 BW).

The WIK (Wet Incassokosten) staffel determines the maximum amount a creditor
can charge for out-of-court collection costs. This has been law since 1 July 2012
(Besluit vergoeding voor buitengerechtelijke incassokosten, Stb. 2012, 141).

Staffel:
    15%  over the first        €2,500
    10%  over €2,500   – €5,000
     5%  over €5,000   – €10,000
     1%  over €10,000  – €200,000
   0.5%  over €200,000+
    Minimum: €40
    Maximum: €6,775

Optional: +21% BTW if the creditor is VAT-exempt (i.e., cannot deduct BTW).
This is the case when the creditor is a consumer or a VAT-exempt organization.

For B2B cases where the creditor CAN deduct BTW, the BIK is exclusive of BTW.
The debtor pays the exclusive amount and the creditor deducts the BTW on their costs.
In practice, the creditor usually charges BIK + 21% BTW to the debtor when the
creditor cannot deduct BTW themselves.
"""

from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")

# WIK staffel tiers: (ceiling, percentage as Decimal)
WIK_TIERS: list[tuple[Decimal | None, Decimal]] = [
    (Decimal("2500"), Decimal("0.15")),
    (Decimal("5000"), Decimal("0.10")),
    (Decimal("10000"), Decimal("0.05")),
    (Decimal("200000"), Decimal("0.01")),
    (None, Decimal("0.005")),  # Unlimited
]

WIK_MINIMUM = Decimal("40.00")
WIK_MAXIMUM = Decimal("6775.00")
BTW_RATE = Decimal("0.21")


def _round2(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_bik(
    principal: Decimal,
    *,
    include_btw: bool = False,
) -> dict:
    """Calculate BIK (buitengerechtelijke incassokosten) based on the WIK staffel.

    Args:
        principal: Total outstanding principal amount (hoofdsom).
        include_btw: If True, add 21% BTW to the BIK amount.
            Set to True when the creditor is a consumer or VAT-exempt.
            Set to False (default) for B2B where creditor can deduct BTW.

    Returns:
        Dict with:
            principal: Input principal
            bik_exclusive: BIK amount exclusive of BTW
            btw_amount: BTW amount (0 if include_btw=False)
            bik_inclusive: Total BIK (exclusive + BTW)
            tiers: List of tier calculations for transparency
    """
    if principal <= 0:
        return {
            "principal": principal,
            "bik_exclusive": Decimal("0"),
            "btw_amount": Decimal("0"),
            "bik_inclusive": Decimal("0"),
            "tiers": [],
        }

    remaining = principal
    total_bik = Decimal("0")
    tiers: list[dict] = []
    prev_ceiling = Decimal("0")

    for ceiling, percentage in WIK_TIERS:
        if remaining <= 0:
            break

        if ceiling is not None:
            tier_size = ceiling - prev_ceiling
            applicable = min(remaining, tier_size)
        else:
            applicable = remaining

        tier_bik = _round2(applicable * percentage)
        total_bik += tier_bik

        tiers.append(
            {
                "from": prev_ceiling,
                "to": ceiling if ceiling is not None else None,
                "percentage": percentage,
                "applicable_amount": applicable,
                "bik": tier_bik,
            }
        )

        remaining -= applicable
        if ceiling is not None:
            prev_ceiling = ceiling

    # Apply minimum and maximum
    bik_exclusive = max(WIK_MINIMUM, min(total_bik, WIK_MAXIMUM))
    bik_exclusive = _round2(bik_exclusive)

    # BTW
    btw_amount = _round2(bik_exclusive * BTW_RATE) if include_btw else Decimal("0")
    bik_inclusive = _round2(bik_exclusive + btw_amount)

    return {
        "principal": principal,
        "bik_exclusive": bik_exclusive,
        "btw_amount": btw_amount,
        "bik_inclusive": bik_inclusive,
        "tiers": tiers,
    }
