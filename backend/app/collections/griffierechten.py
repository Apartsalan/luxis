"""Griffierechten berekening — rechtbank kosten op basis van vorderingsbedrag.

Officiële tarieven per 1 januari 2026.
Bron: Regeling tot indexering Wgbz, Stcrt. 2025, 39855 (rechtspraak.nl —
griffierecht-kanton / griffierecht-civiel).

Griffierecht wordt betaald door de EISER/verzoeker (degene die de procedure
start), niet door de gedaagde. Bij incasso is dat de schuldeiser = de cliënt.
Het tarief hangt af van de rechtsvorm van die eiser:
  - niet-natuurlijke personen (rechtspersoon, vof, cv)
  - natuurlijke personen (particulier, eenmanszaak)
  - onvermogenden (laag inkomen / toevoeging) — vlak tarief
"""

from decimal import Decimal

# Kantonzaken (vorderingen t/m € 25.000) — (max_bedrag, rechtspersoon, natuurlijk, onvermogend)
GRIFFIERECHTEN_KANTON_2026 = [
    (Decimal("500"), Decimal("139"), Decimal("93"), Decimal("93")),
    (Decimal("1500"), Decimal("350"), Decimal("233"), Decimal("93")),
    (Decimal("2500"), Decimal("397"), Decimal("265"), Decimal("93")),
    (Decimal("5000"), Decimal("529"), Decimal("265"), Decimal("93")),
    (Decimal("12500"), Decimal("559"), Decimal("265"), Decimal("93")),
    (Decimal("25000"), Decimal("1504"), Decimal("753"), Decimal("93")),
]

# Civiele zaken bij de rechtbank (vorderingen boven € 25.000) —
# (max_bedrag, rechtspersoon, natuurlijk, onvermogend)
GRIFFIERECHTEN_CIVIEL_2026 = [
    (Decimal("100000"), Decimal("3083"), Decimal("1414"), Decimal("93")),
    (Decimal("1000000"), Decimal("7062"), Decimal("2803"), Decimal("93")),
    (Decimal("Infinity"), Decimal("10487"), Decimal("2803"), Decimal("93")),
]

KANTON_LIMIET = Decimal("25000")


def _tarief_uit_tier(
    tier: tuple[Decimal, Decimal, Decimal, Decimal],
    is_rechtspersoon: bool,
    is_onvermogend: bool,
) -> Decimal:
    _max, tarief_rp, tarief_np, tarief_onvermogend = tier
    if is_onvermogend:
        return tarief_onvermogend
    return tarief_rp if is_rechtspersoon else tarief_np


def calculate_griffierecht(
    vordering: Decimal,
    is_rechtspersoon: bool = True,
    is_onvermogend: bool = False,
) -> dict:
    """Calculate griffierecht based on claim amount and the eiser's legal form.

    Args:
        vordering: Total claim amount (principal).
        is_rechtspersoon: True if the eiser (the firm's client/creditor) is a
            legal entity, False for a natural person (particulier/eenmanszaak).
        is_onvermogend: True for the reduced 'onvermogenden' tariff (low income /
            toevoeging). Overrides is_rechtspersoon.

    Returns:
        dict with griffierecht amount, court type, tariff category, and tier info.
    """
    if vordering <= Decimal("0"):
        return {
            "griffierecht": Decimal("0"),
            "rechter": "n.v.t.",
            "tarief_categorie": "n.v.t.",
            "toelichting": "Geen vordering",
        }

    if vordering <= KANTON_LIMIET:
        rechter = "kantonrechter"
        table = GRIFFIERECHTEN_KANTON_2026
    else:
        rechter = "rechtbank"
        table = GRIFFIERECHTEN_CIVIEL_2026

    if is_onvermogend:
        categorie = "onvermogende"
    elif is_rechtspersoon:
        categorie = "rechtspersoon"
    else:
        categorie = "natuurlijk persoon"

    for tier in table:
        max_bedrag = tier[0]
        if vordering <= max_bedrag:
            tarief = _tarief_uit_tier(tier, is_rechtspersoon, is_onvermogend)
            grens = "" if max_bedrag.is_infinite() else f" t/m €{max_bedrag:,.0f}"
            return {
                "griffierecht": tarief,
                "rechter": rechter,
                "tarief_categorie": categorie,
                "toelichting": f"Vordering{grens} — {categorie}",
            }

    # Unreachable: the civiel table's last tier is Infinity.
    return {
        "griffierecht": Decimal("0"),
        "rechter": "onbekend",
        "tarief_categorie": "n.v.t.",
        "toelichting": "Kon griffierecht niet bepalen",
    }
