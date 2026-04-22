"""Nakosten (post-judgment costs) calculation.

Per 1 februari 2026 liquidatietarief:
- €189 zonder betekening exploot
- €287 met betekening exploot
"""

from decimal import Decimal

NAKOSTEN_ZONDER_BETEKENING = Decimal("189.00")
NAKOSTEN_MET_BETEKENING = Decimal("287.00")


def calculate_nakosten(nakosten_type: str | None) -> Decimal:
    """Return nakosten amount based on type."""
    if nakosten_type == "zonder_betekening":
        return NAKOSTEN_ZONDER_BETEKENING
    if nakosten_type == "met_betekening":
        return NAKOSTEN_MET_BETEKENING
    return Decimal("0.00")
