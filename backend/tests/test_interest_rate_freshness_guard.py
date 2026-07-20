"""Wachter: de rentetabel mag niet stilletjes verouderen (S230, V2).

De wettelijke rente en de handelsrente wisselen elk halfjaar (1 januari en
1 juli). De tabel is in februari 2026 gevuld en stond daarna anderhalf jaar
stil: de handelsrente per 1-7-2026 (10,40%) ontbrak tot S230. Niemand merkte
dat, want een ontbrekende rij geeft geen foutmelding — het systeem rekent
gewoon door met het laatst bekende tarief.

Deze wachter is een wekker, geen inhoudelijke controle: hij valt om zodra de
laatst gecontroleerde peildatum meer dan ~7 maanden achter loopt. Dan moet een
mens rijksoverheid.nl raadplegen en:
  - is er een nieuw tarief? → migratie met de nieuwe rij toevoegen;
  - is het tarief onveranderd? → geen rij nodig;
en in beide gevallen RENTETABEL_GECONTROLEERD_TM hieronder bijwerken naar de
datum waarop is gecontroleerd. Zo blijft een ongewijzigd halfjaar geen vals
alarm en blijft een gemist halfjaar wél zichtbaar.
"""

from datetime import date

from dateutil.relativedelta import relativedelta

# Laatste keer dat de rentetabel tegen de officiële bron is gelegd.
# Bijwerken hoort bij het controleren, niet bij het toevoegen van een rij.
RENTETABEL_GECONTROLEERD_TM = date(2026, 7, 1)

# Tarieven wisselen per halfjaar; één maand speling om de bekendmaking heen.
MAX_ACHTERSTAND = relativedelta(months=7)


def _verlopen_op(gecontroleerd_tm: date) -> date:
    return gecontroleerd_tm + MAX_ACHTERSTAND


def test_wachter_valt_om_bij_verouderde_tabel():
    """De wekker moet echt afgaan — anders bewaakt hij niets."""
    oud = date(2025, 7, 1)  # één halfjaarwissel gemist
    assert date.today() > _verlopen_op(oud)


def test_rentetabel_is_recent_gecontroleerd():
    verlopen_op = _verlopen_op(RENTETABEL_GECONTROLEERD_TM)
    assert date.today() <= verlopen_op, (
        f"De rentetabel is voor het laatst gecontroleerd t/m "
        f"{RENTETABEL_GECONTROLEERD_TM} en is nu verlopen (sinds {verlopen_op}). "
        "Controleer rijksoverheid.nl op nieuwe wettelijke rente / handelsrente "
        "(wisselt 1 januari en 1 juli), voeg zo nodig een migratie met de nieuwe "
        "rij toe, en werk RENTETABEL_GECONTROLEERD_TM bij naar vandaag."
    )
