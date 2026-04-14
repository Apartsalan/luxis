"""DF120-10: Verweer-bibliotheek — voorbeeldreacties op veelvoorkomende verweren.

These are real response templates from Kesting Legal, used as reference
material for the AI when generating draft responses to debtor defenses.
The AI uses these to match tone, legal argumentation style, and structure.

Source: 5 Basenet .eml templates exported 8 april 2026.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DefenseExample:
    """A reference response to a specific type of debtor defense."""

    key: str
    title: str
    description: str
    language: str
    # Which email classification categories this example is relevant for
    relevant_categories: tuple[str, ...]
    # The core legal argumentation (stripped of signatures/disclaimers)
    body: str


DEFENSE_EXAMPLES: list[DefenseExample] = [
    DefenseExample(
        key="afrekening_voorwaarden_20_4",
        title="Afrekening art. 20.4 voorwaarden",
        description=(
            "Wanneer een dossier gesloten wordt: eindafrekening "
            "incassokosten, rente, salaris gemachtigde, honorarium "
            "en kosten van derden op basis van art. 20.4."
        ),
        language="nl",
        relevant_categories=(
            "juridisch_verweer",
            "betwisting",
        ),
        body="""\
Cliënte heeft haar ter incasso gestelde opdracht afgewikkeld \
op grond van de overeengekomen voorwaarden en tarieven, meer \
in het bijzonder art. 20.4 van de voorwaarden, als volgt:

20.4 Indien een dossier wordt gesloten, wordt een eindafrekening \
gemaakt waarop aan Cliënt in rekening wordt gebracht de toegewezen \
incassokosten, rente, salaris gemachtigde, honorarium en kosten \
van derden, vermeerderd met eventuele overige toegekende \
vergoedingen en gemaakte kosten.

De verplichting tot betaling staat hiermee dan ook vast.""",
    ),
    DefenseExample(
        key="annuleringskosten_9_3",
        title="Annuleringskosten art. 9.3 voorwaarden",
        description=(
            "Wanneer cliënt opdracht intrekt, zelf regeling treft, "
            "of incasso belemmert: 15% commissie + €25 registratie "
            "+ overige kosten op basis van art. 9.3."
        ),
        language="nl",
        relevant_categories=(
            "juridisch_verweer",
            "betwisting",
        ),
        body="""\
Cliënte heeft haar ter incasso gestelde opdracht afgewikkeld \
op grond van de overeengekomen voorwaarden en tarieven, meer \
in het bijzonder art. 9.3 van de voorwaarden, als volgt:

9.3 Indien Cliënt een incasso-opdracht intrekt buiten het \
Incassocenter om; een betalingsregeling treft met de Debiteur; \
of met de Debiteur een schikking treft; het Incassocenter zonder \
enig bericht laat; de betaling zelf regelt, dan wel een verdere \
incassobehandeling in de weg staat, is het Incassocenter niettemin \
gerechtigd over de gehele haar ter incasso gestelde vordering 15% \
commissie en een bedrag van € 25,- (exclusief btw) aan \
registratiekosten en overige kosten – waaronder alle verschuldigde \
kosten van derden, zoals buitendienst, leges, proces- en \
executiekosten – in rekening te brengen.

De verplichting tot betaling staat hiermee dan ook vast.""",
    ),
    DefenseExample(
        key="ncnp_verweer_gerechtelijk",
        title="Verweer tegen 'no cure no pay' claim",
        description=(
            "Debiteur stelt dat NCNP van toepassing is. Reactie: "
            "opdrachtbevestiging gerechtelijke fase vermeldt "
            "expliciet dat NCNP niet meer geldt + art. 9.3 + "
            "disclaimer procesrisico."
        ),
        language="nl",
        relevant_categories=(
            "juridisch_verweer",
            "betwisting",
        ),
        body="""\
U heeft gereageerd en daarbij gesteld dat sprake zou zijn van \
een afspraak op basis van "no cure no pay". Daarop het volgende.

Bij aanvang van de gerechtelijke procedure is u per e-mail de \
schriftelijke opdrachtbevestiging toegezonden, waarin expliciet \
is vermeld dat de werkwijze van no cure no pay niet langer van \
toepassing is. In de overeenkomst zelf staat hierover het \
volgende vermeld:

No Cure No Pay
De werkwijze van No Cure No Pay is uitdrukkelijk niet van \
toepassing in de juridische fase en vervalt met de aanvang \
van de juridische fase.

De door cliënte gemaakte (proces)kosten zijn dan ook volledig \
in lijn met de gesloten overeenkomst, en zien op werkzaamheden \
die daadwerkelijk zijn verricht in het kader van de gerechtelijke \
procedure.

Bovendien is in artikel 9.3 van de overeenkomst ondubbelzinnig \
bepaald dat bij tussentijdse beëindiging of belemmering van het \
traject kosten in rekening gebracht mogen worden, ongeacht het \
resultaat.

Ten overvloede: een gerechtelijke procedure brengt proces- en \
kostenrisico's met zich mee. Dit is bij aanvang expliciet \
gecommuniceerd via de disclaimer in de overeenkomst.

De verplichting tot betaling van de aan u in rekening gebrachte \
kosten staat hiermee vast.""",
    ),
    DefenseExample(
        key="verlengd_abonnement",
        title="Stilzwijgende verlenging serviceovereenkomst",
        description=(
            "Debiteur betwist factuur voor verlengd abonnement. "
            "Reactie: contract bepaalt stilzwijgende verlenging "
            "tenzij 3 maanden voor einde opgezegd, geen geldige "
            "opzegging ontvangen."
        ),
        language="nl",
        relevant_categories=(
            "juridisch_verweer",
            "betwisting",
        ),
        body="""\
U heeft met cliënte een serviceovereenkomst gesloten voor de \
duur van één jaar, met stilzwijgende verlenging telkens voor de \
duur van een jaar, tenzij uiterlijk drie maanden voor het einde \
van de lopende termijn schriftelijk wordt opgezegd.

Cliënte heeft van u geen tijdige of geldige opzegging ontvangen. \
De overeenkomst is daarmee overeenkomstig de contractuele \
bepalingen automatisch verlengd en loopt thans door. U bent om \
die reden gehouden tot betaling van het abonnementstarief voor \
de verlengde periode.

Cliënte heeft u hierover eerder geïnformeerd, doch tot op heden \
is geen betaling ontvangen. Nu sprake is van wanbetaling, is \
cliënte op grond van artikel 9.3 van de overeenkomst gerechtigd \
tot afrekening van de vordering.

De betalingsverplichting staat daarmee vast.""",
    ),
    DefenseExample(
        key="english_renewal_9_3",
        title="English: automatic renewal + cancellation costs",
        description=(
            "English version for international debtors. Covers "
            "automatic contract renewal and art. 9.3 cancellation "
            "costs for withdrawn collection assignments."
        ),
        language="en",
        relevant_categories=(
            "juridisch_verweer",
            "betwisting",
        ),
        body="""\
You entered into a service agreement with my client for a \
duration of one year, with automatic renewal for successive \
one-year terms, unless terminated in writing no later than \
three months before the end of the current term.

My client did not receive a timely or valid notice of \
termination from you. Therefore, pursuant to the contractual \
provisions, the agreement has been automatically renewed and \
remains in effect. You are therefore obligated to pay the \
subscription fee for the renewed period.

My client has previously informed you of this matter, yet no \
payment has been received to date. As non-payment constitutes \
a breach, my client is entitled, pursuant to Article 9.3 of \
the agreement, to settle the claim as follows:

Should the Client withdraw a collection assignment; reach a \
payment arrangement with the Debtor outside the Collection \
Agency; settle with the Debtor; leave the Collection Agency \
without any communication; arrange payment independently; or \
otherwise obstruct further collection proceedings, the \
Collection Agency is nevertheless entitled to charge 15% \
commission over the entire claim submitted for collection, \
a registration fee of €25 (excl. VAT), and all other costs.

The payment obligation is therefore established.""",
    ),
]


def get_relevant_examples(
    category: str | None = None,
    language: str = "nl",
) -> list[DefenseExample]:
    """Get defense examples relevant to a classification category.

    Args:
        category: Email classification category (e.g. 'juridisch_verweer')
        language: Preferred language ('nl' or 'en')

    Returns:
        List of matching DefenseExample objects
    """
    results = []
    for ex in DEFENSE_EXAMPLES:
        if category and category not in ex.relevant_categories:
            continue
        # Prefer matching language, but include all if few results
        if ex.language == language:
            results.append(ex)
    # If no language-specific results, return all matching
    if not results and category:
        results = [
            ex for ex in DEFENSE_EXAMPLES
            if category in ex.relevant_categories
        ]
    return results


def format_examples_for_prompt(
    examples: list[DefenseExample],
    max_chars: int = 4000,
) -> str:
    """Format defense examples as prompt context for AI draft generation.

    Truncates to stay within token budget.
    """
    if not examples:
        return ""

    parts = ["--- Verweer-bibliotheek (voorbeeldreacties) ---"]
    chars = len(parts[0])

    for ex in examples:
        header = f"\n[{ex.title}] — {ex.description}"
        if chars + len(header) + len(ex.body) + 10 > max_chars:
            break
        parts.append(header)
        parts.append(ex.body)
        chars += len(header) + len(ex.body) + 2

    return "\n".join(parts)
