"""Verweer-type-woordenschat (13 types) + deterministische pre-labeler.

Vervangt de difflib-gelijkenis met de 5 bibliotheek-teksten als PRIMAIR
toewijzingsmechanisme voor het verweer-type van een geleerd antwoord (audit S172 §5).
De difflib-gelijkenis blijft in `learned_answers.backfill` alléén de DUPLICAAT-filter
(kennen-we-al-check), niet meer de type-toekenning — die kon principieel niet werken
(een nieuw type lijkt nergens op; de 9.3-tekst verschilt per opdrachtgever).

Gevalideerd (Fable, 6 juli 2026) op de 102 echte prod-kandidaten → 85% krijgt een
zinvol label. De geteste regels + prioriteitsvolgorde komen letterlijk uit
`scripts/prelabel_dryrun_s174.py`.

VALKUIL (dryrun-kernbevinding 2): een verweer-antwoord CITEERT vaak het art. 9.3/20.4-blok,
en dat blok bevat zelf woorden als "betalingsregeling treft" / "schikking treft". Matchen we
op de rauwe tekst, dan belandt elk 9.3-antwoord in `betalingsregeling_schikking`. Daarom
eerst de geciteerde voorwaarden-blokken strippen, dán op Lisanne's EIGEN tekst matchen.

De keys zijn EN (stabiel), de labels NL (UI-dropdown). LET OP bij UI-wijziging: de labels
worden gespiegeld in `frontend/.../ai-leren-tab.tsx` (DEFENSE_TYPE_LABELS) — houd ze gelijk.
"""

import re

# ── Woordenschat: key (EN) → label (NL). Volgorde = UI-dropdown (frequent eerst). ──────
DEFENSE_TYPE_LABELS: dict[str, str] = {
    "afwikkeling_intrekking": "Afwikkeling / intrekking opdracht (art. 9.3 / 20.4)",
    "verlenging_opzegging": "Stilzwijgende verlenging / opzegging",
    "betwisting_ongemotiveerd": "Ongemotiveerde betwisting",
    "reeds_betaald_verrekening": "Reeds betaald / verrekening",
    "consumentenbescherming_b2b": "Consumentenberoep (zakelijk → afgewezen)",
    "betalingsregeling_schikking": "Betalingsregeling / schikking",
    "derde_partij": "Advocaat / verzekeraar / derde partij",
    "klacht_dienstverlening": "Klacht over dienstverlening",
    "ncnp_gerechtelijke_fase": "No cure no pay (gerechtelijke fase)",
    "vertegenwoordiging": "Onbevoegde vertegenwoordiging",
    "opschorting_tegenvordering": "Opschorting / tegenvordering",
    "av_toepasselijkheid": "Toepasselijkheid voorwaarden",
    "kosten_rente_hoogte": "Hoogte kosten / rente",
    "overig": "Overig / nieuw type",
}

DEFENSE_TYPE_KEYS: tuple[str, ...] = tuple(DEFENSE_TYPE_LABELS)

# Oude library-keys (difflib-toewijzing vóór S174) → nieuwe woordenschat. Voor de
# eenmalige relabel-migratie en om bestaande kandidaten met een library-key op te vangen.
LEGACY_TYPE_ALIASES: dict[str, str] = {
    "annuleringskosten_9_3": "afwikkeling_intrekking",
    "afrekening_voorwaarden_20_4": "afwikkeling_intrekking",
    "ncnp_verweer_gerechtelijk": "ncnp_gerechtelijke_fase",
    "verlengd_abonnement": "verlenging_opzegging",
    "english_renewal_9_3": "afwikkeling_intrekking",  # verlenging + 9.3; 9.3 = afwikkeling
}


# ── Geciteerde voorwaarden-blokken (eerst strippen, zie VALKUIL) ───────────────────────
_QUOTE_BLOCKS = [
    re.compile(r"9\.3[^\n]*Indien Cliënt.*?in rekening te brengen\.?", re.S | re.I),
    re.compile(r"Indien Cliënt een incasso-opdracht intrekt.*?in rekening te brengen\.?", re.S | re.I),
    re.compile(r"20\.4[^\n]*Indien een dossier.*?gemaakte kosten\.?", re.S | re.I),
    re.compile(r"No Cure No Pay\nDe werkwijze.*?juridische fase\.?", re.S | re.I),
    re.compile(r"Disclaimer\nEen gerechtelijke procedure.*?wederpartij\.?", re.S | re.I),
]

# 9.3/20.4-vangnet: eigen tekst matcht nergens, maar de mail citeert wél de
# afwikkelings-artikelen → dan ís de mail een afwikkelings-antwoord.
_CITES_9_3_20_4 = re.compile(r"9\.3|20\.4")

# ── Regels: prioriteitsvolgorde (EERSTE match wint), letterlijk uit de dryrun ──────────
_RULES: list[tuple[str, re.Pattern[str]]] = [
    (key, re.compile(pat, re.IGNORECASE))
    for key, pat in [
        ("vertegenwoordiging", r"3:61|niet bevoegd|onbevoegd|gerechtvaardigd vertrouwen|opgewekt vertrouwen|schijn van|handtekening.{0,30}vervalst"),
        ("ncnp_gerechtelijke_fase", r"no cure no pay|ncnp"),
        ("consumentenbescherming_b2b", r"herroeping|bedenktijd|reflex-?werking|14-?dagenbrief|consumentenovereenkomst|als zakelijke partij"),
        ("av_toepasselijkheid", r"terhandstelling|6:23[34]|voorwaarden (zijn )?(wél|wel|nooit|niet).{0,30}(ontvangen|ter hand|gesloten)|registratieformulier"),
        ("opschorting_tegenvordering", r"6:7[45]|opschort|schuldeisers?verzuim|tegenvordering|verrekeningsgrond|wanprestatie|ingebrekestelling"),
        ("reeds_betaald_verrekening", r"reeds (betaald|voldaan)|al betaald|gecrediteerd|creditfactuur|creditnota|verreken|deelbetaling|bankafschrift|betalingen? aan facturen"),
        ("verlenging_opzegging", r"stilzwijgend|verlengd|verlenging|opgezegd|opzegging|opzegtermijn|aangetekend"),
        ("kosten_rente_hoogte", r"incassokosten.{0,160}(hoog|toelichting)|staffel|Besluit vergoeding|hoogte van de (rente|kosten)|minimumbedrag|minimumtarief"),
        ("betalingsregeling_schikking", r"betalingsregeling|finale kwijting|tegenvoorstel|schikkingsvoorstel|voorstel tot afwikkeling|bereid .{0,30}€|voorstel .{0,20}€|€.{0,40}tegen finale"),
        ("derde_partij", r"uw advocaat|advocaat in deze|rechtsbijstand|verzekeraar|overgedragen aan uw|via uw advocaat|advocate"),
        ("klacht_dienstverlening", r"inspanningsverplichting|klacht|dienstverlening|geen resultaat|BOOS"),
        ("afwikkeling_intrekking", r"9\.3|20\.4|afgewikkeld|intrekt|ingetrokken|intrekken|eindafrekening|afwikkeling|afgerond|af te ronden|afwikkelen|beëindigd"),
        ("betwisting_ongemotiveerd", r"stelplicht|bewijslast|niet onderbouwd|onderbouwt u niet|laat na .{0,40}(bewijs|onderbouw)|geen inhoudelijk verweer|toont u .{0,25}niet aan|aan u om .{0,40}(bewijzen|aan te tonen|bewijzen)|gemotiveerd (aan te tonen|uiteen)|mist .{0,25}grondslag|zonder concrete onderbouwing|niet.{0,15}gestaafd|snijden geen hout|algemene verwijten"),
    ]
]


def _strip_quoted_terms(body: str) -> str:
    """Haal de geciteerde art. 9.3/20.4/NCNP/disclaimer-blokken weg (zie VALKUIL)."""
    t = body or ""
    for q in _QUOTE_BLOCKS:
        t = q.sub(" ", t)
    return t


def prelabel_defense_type(body: str) -> str:
    """Ken een verweer-type toe op basis van trefwoorden (of 'overig').

    Eerst de geciteerde voorwaarden-blokken strippen, dán op de eigen tekst matchen in
    prioriteitsvolgorde (eerste match wint). Vangnet: matcht niets, maar de mail citeert
    9.3/20.4 → `afwikkeling_intrekking`.
    """
    own = _strip_quoted_terms(body)
    for key, pat in _RULES:
        if pat.search(own):
            return key
    if _CITES_9_3_20_4.search(body or ""):
        return "afwikkeling_intrekking"
    return "overig"


def normalize_defense_type(defense_type: str | None) -> str:
    """Map een (mogelijk oude) key naar de huidige woordenschat; onbekend → 'overig'."""
    if not defense_type:
        return "overig"
    if defense_type in DEFENSE_TYPE_LABELS:
        return defense_type
    return LEGACY_TYPE_ALIASES.get(defense_type, "overig")


if __name__ == "__main__":
    # ponytail: één runnbare zelfcheck — bewijst de prioriteit + de 9.3-valkuil.
    # Antwoord dat 9.3 citeert MAG niet in betalingsregeling belanden (de valkuil):
    cite_9_3 = (
        "Cliënte heeft de opdracht afgewikkeld op grond van art. 9.3 van de voorwaarden: "
        "9.3 Indien Cliënt een incasso-opdracht intrekt buiten het Incassocenter om; een "
        "betalingsregeling treft met de Debiteur; of met de Debiteur een schikking treft; "
        "is het Incassocenter gerechtigd 15% commissie in rekening te brengen."
    )
    assert prelabel_defense_type(cite_9_3) == "afwikkeling_intrekking", prelabel_defense_type(cite_9_3)
    # Eigen betalingsregeling-tekst (zonder 9.3-citaat) → wél betalingsregeling:
    assert prelabel_defense_type(
        "Cliënte is bereid een betalingsregeling te treffen tegen finale kwijting."
    ) == "betalingsregeling_schikking"
    # Prioriteit: 'no cure no pay' wint van een los 'verlengd' verderop:
    assert prelabel_defense_type(
        "U stelt no cure no pay; de overeenkomst is bovendien verlengd."
    ) == "ncnp_gerechtelijke_fase"
    # Vertegenwoordiging (3:61) wint bovenaan:
    assert prelabel_defense_type("De medewerker was niet bevoegd (art. 3:61 BW).") == "vertegenwoordiging"
    # Niets herkenbaar → overig:
    assert prelabel_defense_type("Zie bijlage, met vriendelijke groet.") == "overig"
    # Alias-normalisatie:
    assert normalize_defense_type("annuleringskosten_9_3") == "afwikkeling_intrekking"
    assert normalize_defense_type("verlengd_abonnement") == "verlenging_opzegging"
    assert normalize_defense_type(None) == "overig"
    assert normalize_defense_type("iets_onbekends") == "overig"
    print("defense_types self-check OK")
