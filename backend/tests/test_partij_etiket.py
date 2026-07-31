"""S255 — het etiket op de dossierkop mag nooit iets anders zeggen dan de
rentebijlage-regel doet.

De dossierkop toont sinds S255 wát de wederpartij is (Consument, Eenmanszaak,
BV) in plaats van "B2B"/"B2C", en kleurt naar privé-aansprakelijkheid: roze =
het renteoverzicht gaat mee, blauw = niet. Die kleur komt uit
`ContactBrief.beperkt_aansprakelijk`.

Het gevaar is drift: als die vlag ooit anders gaat rekenen dan
`should_attach_rente_bijlage`, dan liegt het scherm over wat er de deur uitgaat.
Deze test pint ze aan elkaar over álle rechtsvormen die op productie voorkomen
(S255-meting op de 437 KvK-bevragingen) plus de randgevallen.
"""

import uuid
from types import SimpleNamespace

import pytest

from app.cases.schemas import ContactBrief
from app.collections.compliance import should_attach_rente_bijlage

# Exact de acht rechtsvormen die de KvK-backfill op productie opleverde,
# met hun aantallen. Geen verzonnen lijst — dit is de echte verdeling.
PROD_RECHTSVORMEN = [
    "Eenmanszaak",  # 223
    "Besloten Vennootschap",  # 172
    "Vennootschap Onder Firma",  # 35
    "Stichting",  # 2
    "Maatschap",  # 2
    "Vereniging van Eigenaars",  # 1
    "Naamloze Vennootschap",  # 1
    "Commanditaire Vennootschap",  # 1
]


def _brief(legal_form: str | None) -> ContactBrief:
    return ContactBrief(
        id=uuid.uuid4(),
        contact_type="company",
        name="Wederpartij",
        email=None,
        legal_form=legal_form,
    )


@pytest.mark.parametrize("legal_form", PROD_RECHTSVORMEN)
def test_etiketkleur_volgt_de_bijlageregel(legal_form: str):
    """Blauw (beperkt aansprakelijk) precies dan als er GEEN bijlage meegaat."""
    brief = _brief(legal_form)
    gaat_bijlage_mee = should_attach_rente_bijlage(
        SimpleNamespace(legal_form=legal_form), "b2b"
    )

    assert brief.beperkt_aansprakelijk is not gaat_bijlage_mee, (
        f"{legal_form}: etiket zegt beperkt_aansprakelijk="
        f"{brief.beperkt_aansprakelijk}, maar de bijlage gaat "
        f"{'wél' if gaat_bijlage_mee else 'niet'} mee"
    )


def test_bv_is_beperkt_aansprakelijk():
    """De grootste groep op prod (172 BV's) — expliciet vastgelegd."""
    assert _brief("Besloten Vennootschap").beperkt_aansprakelijk is True


def test_eenmanszaak_is_prive_aansprakelijk():
    """Het blinde gat uit S252 (Kaandorp) — 223 stuks op prod."""
    assert _brief("Eenmanszaak").beperkt_aansprakelijk is False


def test_onbekende_rechtsvorm_geeft_geen_oordeel():
    """Leeg = None, niet False.

    Bij een onbekende rechtsvorm gaat de bijlage vóór de zekerheid wél mee
    (besluit B). Zou dit False teruggeven, dan zou het scherm dat als een
    hard "privé aansprakelijk" tonen terwijl we het simpelweg niet weten —
    en dan is er geen zichtbaar verschil meer tussen "weten we" en "gokken we".
    """
    assert _brief(None).beperkt_aansprakelijk is None
    assert _brief("").beperkt_aansprakelijk is None


def test_hoofdletters_maken_niet_uit():
    """De KvK levert 'Besloten Vennootschap', handmatig komt vaak 'bv' binnen."""
    assert _brief("BESLOTEN VENNOOTSCHAP").beperkt_aansprakelijk is True
    assert _brief("besloten vennootschap").beperkt_aansprakelijk is True
