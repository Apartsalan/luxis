"""S174 V3 — trefwoord-pre-labeler + woordenschat (`app/ai_agent/defense_types.py`).

Eén bewijzende case per verweer-type (prioriteitsvolgorde bewaakt), plus de kern-VALKUIL
uit de dryrun: een antwoord dat het art. 9.3-blok CITEERT mag niet in
`betalingsregeling_schikking` belanden (dat blok bevat zelf "betalingsregeling treft").
"""

import pytest

from app.ai_agent.defense_types import (
    DEFENSE_TYPE_LABELS,
    LEGACY_TYPE_ALIASES,
    normalize_defense_type,
    prelabel_defense_type,
)

# (verwacht_type, bewijzende tekst) — telkens één schoon signaal, geen hoger-prioriteit-woord.
_PROVING_CASES = [
    ("vertegenwoordiging", "De ondertekenaar was niet bevoegd om cliënte te binden (art. 3:61 BW)."),
    ("ncnp_gerechtelijke_fase", "U beroept zich op no cure no pay in deze fase."),
    ("consumentenbescherming_b2b", "U doet een beroep op herroeping en bedenktijd, maar handelde als zakelijke partij."),
    ("av_toepasselijkheid", "De voorwaarden zijn wel degelijk ter hand gesteld; van gebrekkige terhandstelling is geen sprake."),
    ("opschorting_tegenvordering", "Cliënte beroept zich op opschorting wegens een tegenvordering."),
    ("reeds_betaald_verrekening", "De factuur is reeds betaald blijkens het bijgevoegde bankafschrift."),
    ("verlenging_opzegging", "De overeenkomst is stilzwijgend verlengd; er is niet tijdig opgezegd."),
    ("kosten_rente_hoogte", "De hoogte van de rente en de gehanteerde staffel behoeven toelichting."),
    ("betalingsregeling_schikking", "Cliënte is bereid een betalingsregeling te treffen tegen finale kwijting."),
    ("derde_partij", "De vordering is overgedragen aan uw advocaat / rechtsbijstand."),
    ("klacht_dienstverlening", "Uw klacht over de dienstverlening betreft een inspanningsverplichting."),
    ("afwikkeling_intrekking", "Cliënte heeft de opdracht afgewikkeld conform art. 9.3 van de voorwaarden."),
    ("betwisting_ongemotiveerd", "Uw betwisting is niet onderbouwd; op u rust de stelplicht en bewijslast."),
]


@pytest.mark.parametrize("expected,text", _PROVING_CASES, ids=[c[0] for c in _PROVING_CASES])
def test_prelabel_assigns_expected_type(expected: str, text: str):
    assert prelabel_defense_type(text) == expected


def test_all_13_types_have_a_proving_case():
    """Elk niet-'overig' type uit de woordenschat is door precies één case gedekt."""
    covered = {c[0] for c in _PROVING_CASES}
    vocab = set(DEFENSE_TYPE_LABELS) - {"overig"}
    assert covered == vocab


def test_valkuil_geciteerd_9_3_blok_wordt_afwikkeling_niet_betalingsregeling():
    """De dryrun-kernbevinding: eerst het geciteerde 9.3-blok strippen. Anders trekt het
    woord 'betalingsregeling treft' IN dat citaat de hele mail naar betalingsregeling."""
    cite_9_3 = (
        "Cliënte heeft de ter incasso gestelde opdracht afgewikkeld op grond van art. 9.3 "
        "van de voorwaarden:\n\n"
        "9.3 Indien Cliënt een incasso-opdracht intrekt buiten het Incassocenter om; een "
        "betalingsregeling treft met de Debiteur; of met de Debiteur een schikking treft; "
        "is het Incassocenter gerechtigd 15% commissie in rekening te brengen.\n\n"
        "De verplichting tot betaling staat hiermee vast."
    )
    assert prelabel_defense_type(cite_9_3) == "afwikkeling_intrekking"


def test_overig_when_no_signal():
    assert prelabel_defense_type("Zie bijlage. Met vriendelijke groet, Kesting Legal.") == "overig"
    assert prelabel_defense_type("") == "overig"


def test_normalize_maps_legacy_keys_and_unknowns():
    assert normalize_defense_type("annuleringskosten_9_3") == "afwikkeling_intrekking"
    assert normalize_defense_type("afrekening_voorwaarden_20_4") == "afwikkeling_intrekking"
    assert normalize_defense_type("verlengd_abonnement") == "verlenging_opzegging"
    assert normalize_defense_type("ncnp_verweer_gerechtelijk") == "ncnp_gerechtelijke_fase"
    assert normalize_defense_type("afwikkeling_intrekking") == "afwikkeling_intrekking"  # al nieuw
    assert normalize_defense_type(None) == "overig"
    assert normalize_defense_type("iets_totaal_onbekends") == "overig"


def test_every_legacy_alias_points_to_a_real_type():
    for target in LEGACY_TYPE_ALIASES.values():
        assert target in DEFENSE_TYPE_LABELS
