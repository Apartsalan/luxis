"""Maandelijks samengestelde contractuele rente (AV art. 13.3: 2% per maand).

Gouden standaard: de BaseNet-rentespecificatie van dossier IN100197
(Renteberekening.pdf, rentedatum 07-07-2026). Elke regel van die specificatie
moet er tot op de cent uitkomen — dit is de referentie waartegen Lisanne
de Luxis-bedragen controleert.
"""

from datetime import date
from decimal import Decimal

from app.collections.interest import calculate_monthly_compound_interest

# IN100197: hoofdsom €1.809,18, verzuim 25-09-2024, betaling 16-12-2025
# €1.908,10 waarvan €271,38 naar kosten (BIK) → €1.636,72 beschikbaar voor
# rente + basis. Rentedatum 07-07-2026 (inclusief) → calc_date 08-07-2026
# (halfopen conventie: rente t/m de dag vóór calc_date).
PRINCIPAL = Decimal("1809.18")
DEFAULT_DATE = date(2024, 9, 25)
CALC_DATE = date(2026, 7, 8)
RATE = Decimal("2")
PAYMENTS = [(date(2025, 12, 16), Decimal("1908.10") - Decimal("271.38"))]

# (rente, dagen) per regel, exact zoals de BaseNet-specificatie ze print.
BASENET_LINES = [
    ("36.18", 30), ("36.91", 31), ("37.65", 30), ("38.40", 31),
    ("39.17", 31), ("39.95", 28), ("40.75", 31), ("41.56", 30),
    ("42.39", 31), ("43.24", 30), ("44.11", 31), ("44.99", 31),
    ("45.89", 30), ("46.81", 31), ("33.42", 21),
    ("4.70", 9), ("15.77", 31), ("16.09", 31), ("16.41", 28),
    ("16.74", 31), ("17.07", 30), ("17.41", 31), ("7.70", 13),
]
BASENET_TOTAL = Decimal("723.31")


def test_in100197_totaal_matcht_basenet():
    total, _ = calculate_monthly_compound_interest(
        PRINCIPAL, DEFAULT_DATE, CALC_DATE, RATE, PAYMENTS
    )
    assert total == BASENET_TOTAL


def test_in100197_elke_regel_matcht_basenet():
    _, periods = calculate_monthly_compound_interest(
        PRINCIPAL, DEFAULT_DATE, CALC_DATE, RATE, PAYMENTS
    )
    assert len(periods) == len(BASENET_LINES)
    for p, (rente, dagen) in zip(periods, BASENET_LINES):
        assert p["interest"] == Decimal(rente), p
        assert p["days"] == dagen, p


def test_zonder_betaling_rente_op_rente():
    # 12 volle maanden op €1.000: 1000 × (1,02^12 − 1), per regel afgerond.
    total, periods = calculate_monthly_compound_interest(
        Decimal("1000.00"), date(2025, 1, 15), date(2026, 1, 15), RATE, []
    )
    assert len(periods) == 12
    assert periods[0]["interest"] == Decimal("20.00")
    assert periods[1]["interest"] == Decimal("20.40")  # rente óver rente
    assert total == Decimal("268.23")  # som van 12 afgeronde regels


def test_betaling_op_verzuimdatum_verlaagt_basis_vooraf():
    total_with, _ = calculate_monthly_compound_interest(
        Decimal("1000.00"), date(2025, 1, 15), date(2025, 3, 15), RATE,
        [(date(2025, 1, 15), Decimal("400.00"))],
    )
    total_without, _ = calculate_monthly_compound_interest(
        Decimal("600.00"), date(2025, 1, 15), date(2025, 3, 15), RATE, []
    )
    assert total_with == total_without


def test_basis_naar_nul_stopt_rente():
    total, _ = calculate_monthly_compound_interest(
        Decimal("1000.00"), date(2025, 1, 15), date(2025, 6, 15), RATE,
        [(date(2025, 2, 15), Decimal("5000.00"))],
    )
    # één maand rente (20,00), daarna is alles betaald
    assert total == Decimal("20.00")


def test_geen_rente_voor_verzuim():
    total, periods = calculate_monthly_compound_interest(
        Decimal("1000.00"), date(2026, 3, 1), date(2026, 3, 1), RATE, []
    )
    assert total == Decimal("0")
    assert periods == []


def test_maandgrens_eind_maand_verzuim_op_31e():
    # Verzuim op de 31e: maandgrens klemt naar de laatste dag van kortere maanden.
    total, periods = calculate_monthly_compound_interest(
        Decimal("1000.00"), date(2025, 1, 31), date(2025, 4, 30), RATE, []
    )
    # buckets: 31-01→28-02 (28d), 28-02→31-03 (31d), 31-03→30-04 (30d deel)
    assert [p["days"] for p in periods] == [28, 31, 30]
