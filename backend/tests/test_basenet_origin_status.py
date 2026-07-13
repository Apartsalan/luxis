"""S207c: BaseNet-origin-status backfill uit de import-notitie.

Toetst de substring-extractie die de migratie gebruikt: 'BaseNet-status: X' in
`debtor_notes` moet als X in `basenet_origin_status` belanden, en de heropen-
categorie ('nog te openen' vs 'afgehandeld') klopt.
"""

import re

import pytest

# De exacte regex uit migratie s207c (Python-equivalent van de PG-substring).
_PATTERN = re.compile(r"BaseNet-status:\s*([A-Za-z]+)")

HEROPENEN = {"Lopend", "Wacht"}
AFGEHANDELD = {"Gereed", "Geannuleerd", "Offerte"}


def _extract(note: str | None) -> str | None:
    if not note:
        return None
    m = _PATTERN.search(note)
    return m.group(1) if m else None


@pytest.mark.parametrize(
    "note,verwacht",
    [
        ("[BaseNet-import] IN100000 · systemid=42 · BaseNet-status: Lopend", "Lopend"),
        ("[BaseNet-import] IN100148 · systemid=7 · BaseNet-status: Gereed", "Gereed"),
        ("[BaseNet-import] IN100301 · systemid=9 · BaseNet-status: Geannuleerd", "Geannuleerd"),
        ("[BaseNet-import] IN100003 · systemid=1 · BaseNet-status: Wacht", "Wacht"),
        ("[BaseNet-import] IN1 · systemid=1 · BaseNet-status: Offerte", "Offerte"),
        ("Handmatig aangemaakt in Luxis", None),
        (None, None),
        ("BaseNet-status: ?", None),  # onbekend '?' matcht geen letters → NULL
    ],
)
def test_extractie_uit_notitie(note, verwacht):
    assert _extract(note) == verwacht


def test_categorie_dekt_alle_basenet_statussen():
    # De 5 mogelijke BaseNet-statussen vallen elk in precies één bucket.
    alle = HEROPENEN | AFGEHANDELD
    assert alle == {"Lopend", "Wacht", "Gereed", "Geannuleerd", "Offerte"}
    assert HEROPENEN & AFGEHANDELD == set()
