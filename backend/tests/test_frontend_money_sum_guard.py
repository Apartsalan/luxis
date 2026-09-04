"""Wachter (S256) — de frontend telt geldbedragen nooit op als tekst.

De API serialiseert elke Decimal als string ("78469.57"), zie
ARCHITECTUUR-KAART ("frontend: Number()"). De TypeScript-types zeggen intussen
`total: number`, dus de compiler ziet niets. Wie dan schrijft
`invoices.reduce((sum, inv) => sum + inv.total, 0)` krijgt in JavaScript geen
som maar een aaneenrijging: 0 + "145.20" + "868.45" + "48.40" wordt
"0145.20868.4548.40", en formatCurrency maakt daar via parseFloat € 145,21 van.

Zo stond het op prod (S256, gemeten):
- dashboard "Open facturen" toonde € 0,00 terwijl 88 vervallen facturen
  (€ 78.469,57) openstonden;
- dossier IN100016, tabblad Documenten: "totaal gefactureerd" € 145,21 waar
  drie facturen samen € 1.062,05 zijn.

Dat is een SOORT: elke nieuwe optelling van een geldveld zonder Number() gaat
op dezelfde manier stuk. Deze wachter leest de frontend-broncode en valt rood
zodra een reduce-callback een geldveld rechtstreeks bij de accumulator optelt.
Toegestaan: `sum + Number(x.total)` of `sum + parseFloat(x.amount)`.
"""

import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_FRONTEND_CANDIDATES = [
    BACKEND_ROOT.parent / "frontend" / "src",
    BACKEND_ROOT / "frontend_src",
]

# Velden die de API als Decimal-string levert. Tellingen (count, *_minutes,
# invoice_count) zijn echte getallen en horen hier bewust NIET in.
_GELDVELDEN = (
    "total|subtotal|amount|paid_amount|line_total|btw_amount|principal|"
    "principal_amount|total_paid|total_principal|total_outstanding|outstanding|"
    "balance|interest|costs|hourly_rate"
)

# `=> sum + inv.total` of `=> sum + (inv.total ?? 0)`. Een wrapper als
# Number(inv.total) matcht niet: na de `+` volgt dan `Number(` en geen `x.veld`.
# Twee vormen: de pijl-expressie `=> sum + x.total` en de blokvorm
# `{ return sum + x.total; }` (sabotageproef S256: de eerste versie zag alleen
# de pijl-vorm en liet een reduce met accolades stil door).
_TEKST_SOM = re.compile(
    r"(?:=>|\breturn)\s*(\w+)\s*\+\s*\(?\s*\w+\.(?:" + _GELDVELDEN + r")\b"
)
_COMMENT = re.compile(r"^\s*(//|\*|/\*)")


def _frontend_src() -> Path:
    for candidate in _FRONTEND_CANDIDATES:
        if candidate.is_dir():
            return candidate
    pytest.fail(
        "frontend/src niet gevonden — deze wachter mag NIET stil overgeslagen "
        f"worden. Gezocht in: {[str(c) for c in _FRONTEND_CANDIDATES]}."
    )


def _bronbestanden() -> list[Path]:
    root = _frontend_src()
    return [
        p
        for p in [*root.rglob("*.ts"), *root.rglob("*.tsx")]
        if "node_modules" not in p.parts
    ]


def test_geldvelden_worden_niet_als_tekst_opgeteld():
    """`sum + inv.total` mag nergens staan; alleen `sum + Number(inv.total)`."""
    root = _frontend_src()
    treffers: list[str] = []
    for pad in _bronbestanden():
        for nr, regel in enumerate(pad.read_text(encoding="utf-8").splitlines(), 1):
            if _COMMENT.match(regel):
                continue
            if _TEKST_SOM.search(regel):
                treffers.append(
                    f"{pad.relative_to(root).as_posix()}:{nr} — {regel.strip()[:110]}"
                )

    assert not treffers, (
        "Deze plekken tellen een geldveld op zonder Number(): de API levert "
        "Decimals als string, dus dit wordt tekst-aaneenrijging en toont een "
        "verkeerd bedrag. Schrijf `sum + Number(x.veld)`:\n  " + "\n  ".join(treffers)
    )
