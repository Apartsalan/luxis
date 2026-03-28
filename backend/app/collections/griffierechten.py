"""Griffierechten berekening — rechtbank kosten op basis van vorderingsbedrag.

Tarieven per 1 januari 2026 voor kantonzaken (natuurlijke personen en rechtspersonen).
Bron: Wet griffierechten burgerlijke zaken (Wgbz).

Note: dit zijn de tarieven voor dagvaardingszaken bij de kantonrechter,
de meest voorkomende procedure bij incasso.
"""

from decimal import Decimal

# Griffierechten 2026 — kantonzaken
# (max_bedrag, tarief_natuurlijk_persoon, tarief_rechtspersoon)
GRIFFIERECHTEN_KANTON_2026 = [
    (Decimal("500"), Decimal("92"), Decimal("132")),
    (Decimal("1500"), Decimal("92"), Decimal("132")),
    (Decimal("2500"), Decimal("244"), Decimal("530")),
    (Decimal("5000"), Decimal("244"), Decimal("530")),
    (Decimal("12500"), Decimal("244"), Decimal("530")),
    (Decimal("25000"), Decimal("619"), Decimal("1384")),
    (Decimal("100000"), Decimal("619"), Decimal("1384")),  # kantonrechter max 25k, maar voor volledigheid
]

# Griffierechten 2026 — rechtbank (handelszaken, boven kantongrens)
GRIFFIERECHTEN_RECHTBANK_2026 = [
    (Decimal("100000"), Decimal("1384"), Decimal("4394")),
    (Decimal("Infinity"), Decimal("1384"), Decimal("4394")),
]


def calculate_griffierecht(
    vordering: Decimal,
    is_rechtspersoon: bool = True,
) -> dict:
    """Calculate griffierecht based on claim amount.

    Args:
        vordering: Total claim amount (principal)
        is_rechtspersoon: True for legal entities (B2B), False for natural persons (B2C)

    Returns:
        dict with griffierecht amount, court type, and tier info
    """
    if vordering <= Decimal("0"):
        return {
            "griffierecht": Decimal("0"),
            "rechter": "n.v.t.",
            "toelichting": "Geen vordering",
        }

    # Kantonrechter: vorderingen t/m €25.000
    if vordering <= Decimal("25000"):
        rechter = "kantonrechter"
        for max_bedrag, tarief_np, tarief_rp in GRIFFIERECHTEN_KANTON_2026:
            if vordering <= max_bedrag:
                tarief = tarief_rp if is_rechtspersoon else tarief_np
                return {
                    "griffierecht": tarief,
                    "rechter": rechter,
                    "toelichting": f"Vordering t/m €{max_bedrag:,.0f} — {'rechtspersoon' if is_rechtspersoon else 'natuurlijk persoon'}",
                }
    else:
        # Rechtbank: vorderingen boven €25.000
        rechter = "rechtbank"
        tarief = (
            GRIFFIERECHTEN_RECHTBANK_2026[0][2]
            if is_rechtspersoon
            else GRIFFIERECHTEN_RECHTBANK_2026[0][1]
        )
        return {
            "griffierecht": tarief,
            "rechter": rechter,
            "toelichting": f"Vordering boven €25.000 — {'rechtspersoon' if is_rechtspersoon else 'natuurlijk persoon'}",
        }

    # Fallback (should not reach)
    return {
        "griffierecht": Decimal("0"),
        "rechter": "onbekend",
        "toelichting": "Kon griffierecht niet bepalen",
    }
