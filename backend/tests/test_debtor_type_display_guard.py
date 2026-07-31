"""Wachter (S255) — geen enkel scherm vertaalt `debtor_type` nog zelf naar
"B2B"/"B2C"-tekst.

S255 verving het etiket in de dossierkop door wát de wederpartij écht is
(Consument / Eenmanszaak / BV), met een kleur die zegt of iemand privé
aansprakelijk is. Bij de review bleek de incassolijst intussen nog gewoon
"B2B" te tonen: hetzelfde dossier, twee talen, en de lijst zweeg over precies
het onderscheid dat bepaalt of de rentebijlage meegaat.

Dat is een SOORT, geen los geval: elk nieuw scherm dat `debtor_type` toont kan
opnieuw zijn eigen vertaling verzinnen. Deze wachter leest de frontend-broncode
en valt rood zodra ergens een expressie `debtor_type` rechtstreeks omzet naar
zichtbare "B2B"/"B2C"-tekst. De enige toegestane weg is `partijEtiket()` in
`lib/status-constants.ts` — die leest de rechtsvorm mee en haalt de
aansprakelijkheids-kleur uit de backend, waar dezelfde constante de
rentebijlage-beslissing stuurt.

Keuzemenu's ("welk soort debiteur is dit?") zijn iets anders dan het TONEN van
een bestaand dossier: daar kiest de gebruiker een waarde. Die staan op de
allowlist hieronder, mét de reden, en gebruiken gewone taal.
"""

import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Zelfde vindwijze als test_notification_labels.py: in CI staat de hele repo
# uitgecheckt, in de dev-container zit frontend/src als read-only mount.
_FRONTEND_CANDIDATES = [
    BACKEND_ROOT.parent / "frontend" / "src",
    BACKEND_ROOT / "frontend_src",
]

# Bestanden die B2B/B2C-tekst mogen bevatten, mét reden. Geen kale uitzondering:
# wie hier iets toevoegt moet uitleggen waarom het geen scherm-vertaling is.
ALLOWLIST = {
    "lib/status-constants.ts": (
        "de enige toegestane vertaler (partijEtiket); noemt B2B/B2C alleen in "
        "commentaar over wat vervangen is"
    ),
    "hooks/use-documents.ts": (
        "juridische omschrijving van een sjabloon ('Verplichte aanmaning voor "
        "B2C op grond van art. 6:96 BW') — geen etiket op een dossier"
    ),
    "app/(dashboard)/instellingen/knowledge-rules-section.tsx": (
        "kennisregel-bereik ('Alleen zakelijk (B2B)') — kennisregels worden "
        "bewust niet aangeraakt; het gewone woord staat vooraan"
    ),
}

# Een expressie die debtor_type omzet naar zichtbare B2B/B2C-tekst. Twee vormen,
# allebei op prod aangetroffen bij de S255-review:
#   1. de ternary:      debtor_type === "b2b" ? "B2B" : ...
#   2. de sluiproute:   debtor_type.toUpperCase()  — levert óók "B2B" op het
#      scherm, maar bevat de letters nergens letterlijk. Zonder dit patroon zou
#      de wachter die stil doorlaten (gevonden doordat de eerste versie hem miste).
_VERTALING = re.compile(
    r"debtor_type[^\n]{0,200}?\"B2[BC]\"|debtor_type[^\n]{0,80}?toUpperCase"
)
# Losse schermtekst "B2B"/"B2C": als JSX-tekstknoop (>...B2B...<) of in een
# string. LET OP de eerste versie hiervan eiste dat B2B direct tegen de tags aan
# stond (`>B2B<`) en liet daardoor `>B2B (bedrijf)<` door — precies de tekst die
# in de keuzemenu's stond. Gevonden door de sabotage-proef; zonder die proef was
# de fix onbewaakt gebleven. Daarom nu: B2B/B2C als los WOORD, waar dan ook in
# de tekstknoop of de string.
_LOSSE_TEKST = re.compile(r">[^<>{}]*\bB2[BC]\b|[\"'][^\"']*\bB2[BC]\b")

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


def _relatief(pad: Path) -> str:
    return pad.relative_to(_frontend_src()).as_posix()


def _strip_blokcommentaar(bron: str) -> str:
    """Vervang /* ... */ (ook de JSX-variant {/* ... */}) door spaties.

    Regelnummers blijven kloppen omdat alleen niet-newline-tekens verdwijnen.
    Nodig omdat uitleg-commentaar over deze wachter zélf de woorden B2B/B2C
    bevat: zonder dit zou de wachter zijn eigen documentatie als overtreding
    aanrekenen, en dan wordt hij ooit "opgelost" door de uitleg te wissen.
    """
    return re.sub(
        r"/\*.*?\*/",
        lambda m: "".join(c if c == "\n" else " " for c in m.group()),
        bron,
        flags=re.DOTALL,
    )


def _code_regels(pad: Path) -> list[tuple[int, str]]:
    """Regels zonder commentaar — commentaar mag B2B/B2C noemen als uitleg."""
    bron = _strip_blokcommentaar(pad.read_text(encoding="utf-8"))
    return [
        (nr, regel)
        for nr, regel in enumerate(bron.splitlines(), 1)
        if not _COMMENT.match(regel)
    ]


def test_geen_scherm_vertaalt_debtor_type_zelf():
    """`debtor_type === "b2b" ? "B2B" : ...` mag nergens meer staan."""
    treffers: list[str] = []
    for pad in _bronbestanden():
        naam = _relatief(pad)
        if naam in ALLOWLIST:
            continue
        for nr, regel in _code_regels(pad):
            if _VERTALING.search(regel):
                treffers.append(f"{naam}:{nr} — {regel.strip()[:120]}")

    assert not treffers, (
        "Deze plekken vertalen debtor_type zelf naar B2B/B2C-tekst. Gebruik "
        "partijEtiket() uit lib/status-constants.ts — die toont de echte "
        "rechtsvorm en kleurt naar privé-aansprakelijkheid, uit dezelfde bron "
        "als de rentebijlage-beslissing:\n  " + "\n  ".join(treffers)
    )


def test_geen_losse_b2b_schermtekst():
    """Ook zonder debtor_type ernaast: "B2B" als zichtbare tekst is jargon.

    Vangt het keuzemenu-geval (`<option value="b2b">B2B</option>`) en elke
    toekomstige plek die het woord gewoon neerzet. Toegestane uitzonderingen
    staan in ALLOWLIST, mét reden.
    """
    treffers: list[str] = []
    for pad in _bronbestanden():
        naam = _relatief(pad)
        if naam in ALLOWLIST:
            continue
        for nr, regel in _code_regels(pad):
            if _LOSSE_TEKST.search(regel):
                treffers.append(f"{naam}:{nr} — {regel.strip()[:120]}")

    assert not treffers, (
        "Zichtbare 'B2B'/'B2C'-tekst gevonden. Luxis praat gewone taal: "
        "'Zakelijk (bedrijf)' en 'Consument (particulier)' in keuzemenu's, "
        "partijEtiket() bij het tonen van een bestaand dossier:\n  "
        + "\n  ".join(treffers)
    )


def test_allowlist_verwijst_naar_bestaande_bestanden():
    """Een allowlist die naar verdwenen bestanden wijst dekt stilletjes niets af."""
    root = _frontend_src()
    ontbreekt = [naam for naam in ALLOWLIST if not (root / naam).is_file()]
    assert not ontbreekt, (
        f"ALLOWLIST noemt bestanden die niet (meer) bestaan: {ontbreekt}. "
        "Verwijder ze, anders dekt de uitzondering niets af."
    )
