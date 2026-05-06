"""AI-prompts per incasso-stap voor gepersonaliseerde email-generatie.

Bron-sjablonen: `templates/lisanne/*.eml` (Lisanne's originele emails).
Geïmporteerd in `IncassoPipelineStep.email_subject_template` + `email_body_template`.

Doel: AI gebruikt het opgeslagen sjabloon als BASIS, vult ALLEEN dossier-specifieke
plekken in (namen, bedragen, factuurnummers, kenmerk) en past situatie-afhankelijke
alinea's aan indien nodig (bv. bij verweer, deelbetaling). Layout, standaardzinnen
en ondertekening blijven IDENTIEK aan het sjabloon.

Bij stap "Verweer beantwoorden" wordt aanvullend de verweer-bibliotheek
(`defense_library.DEFENSE_EXAMPLES`) als referentiemateriaal meegestuurd:
- afrekening art. 20.4
- annuleringskosten art. 9.3
- NCNP verweer gerechtelijk
- verlengd abonnement (stilzwijgende verlenging)
- english renewal art. 9.3
9 van de 10 keer matcht 1 van deze 5 op het inkomend verweer; AI gebruikt die als
basis-tekst en voegt een korte situatie-specifieke alinea toe.

LET OP — deze prompts zijn NOG NIET aangesloten op de email-engine. Eerst review
door Arsalan/Lisanne, daarna pas integreren in het auto-draft pad.
"""

from decimal import Decimal
from typing import Any

from app.ai_agent.defense_library import (
    DEFENSE_EXAMPLES,
    format_examples_for_prompt,
)

# ── System prompt (universeel) ────────────────────────────────────────────


SYSTEM_PROMPT = """Je bent een email-assistent voor advocaat mr. L. Kesting van Kesting Legal in Amsterdam, gespecialiseerd in incasso (B2B faillissementsroute).

Jouw enige taak: een gepersonaliseerde versie van een vast email-sjabloon opleveren, op basis van dossier-context.

ABSOLUTE REGELS — strikt volgen:

1. **Sjabloon is leidend.** Layout, opmaak, witregels, standaardzinnen, juridische tekst, ondertekening, footer en disclaimer NIET wijzigen of weglaten.

2. **Vul ALLEEN deze plekken in met dossier-data:**
   - Aanhef (naam debiteur, "Geachte heer/mevrouw [Naam]")
   - Cliënt-introductie ("Cliënt [naam] heeft mij verzocht...")
   - "Betreft:" regel — vul kenmerk + dossiernummer in
   - Factuurregels-tabel (factuurnummer, datum, vervaldatum, bedrag per regel)
   - Bedragen-tabel (hoofdsom, rente, incassokosten, BTW, totaal, voldaan, te voldoen)
   - Te-voldoen bedrag in zin "openstaande bedrag van €..."
   - Kenmerk-vermelding bij IBAN-instructie
   - Dossiernummer waar gevraagd

3. **Situatie-specifiek aanpassen mag ALLEEN:**
   - Als debiteur betwist: voeg in de juiste alinea een korte weerlegging toe op basis van AV en eerder verweer.
   - Als deelbetaling is ontvangen: vermeld het ontvangen bedrag en het resterende bedrag.
   - Als factuur betwist wordt om specifieke reden (bv. abonnement niet opgezegd, dienst niet geleverd): voeg 1 korte alinea toe die op basis van AV en dossier de betwisting weerlegt.
   - Pas ALLEEN de relevante alinea aan. Rest van het sjabloon blijft IDENTIEK.

4. **NOOIT:**
   - Nieuwe afsluiting verzinnen ("Hoogachtend" + handtekening = vast).
   - Disclaimer of footer wijzigen of weglaten.
   - Andere stijl, toon of formulering gebruiken dan het sjabloon.
   - Bedragen of feiten verzinnen die niet in het dossier staan.
   - Juridische beweringen doen die niet in AV of dossier onderbouwd zijn.

5. **Bedragen-formatting:**
   - Nederlands formaat: `€ 1.234,56` (duizendtal-punt, decimaal-komma, spatie na €).
   - Als waarde `0`: schrijf `€ 0,00`.
   - Geen valutaformaat anders dan Euro.

6. **Output:** uitsluitend JSON met:
   ```json
   {
     "subject": "string — gepersonaliseerde Betreft-regel",
     "body": "string — volledige email-body, plain text, met \\r\\n voor regelovergangen"
   }
   ```
   Geen extra tekst, geen markdown, geen uitleg buiten JSON.
"""


# ── Per-stap context-builder ──────────────────────────────────────────────


def build_user_prompt(
    *,
    step_name: str,
    template_subject: str,
    template_body: str,
    case_data: dict[str, Any],
    debtor_data: dict[str, Any],
    client_data: dict[str, Any],
    invoices: list[dict[str, Any]],
    amounts: dict[str, Decimal],
    av_text: str | None = None,
    incoming_defense: str | None = None,
    prior_correspondence: list[dict[str, Any]] | None = None,
) -> str:
    """Construeer de user-prompt voor een incasso-stap.

    Parameters dekken alle bronnen die de AI mag raadplegen:
    - case_data: dossiernummer, kenmerk, type, openingsdatum
    - debtor_data: naam, adres, contactpersoon
    - client_data: naam (cliënt van Lisanne), contactgegevens
    - invoices: lijst van openstaande facturen
    - amounts: hoofdsom, rente, incassokosten, BTW, totaal, voldaan, te_voldoen
    - av_text: algemene voorwaarden van de cliënt (relevant bij verweer)
    - incoming_defense: tekst van inkomende verweer-mail (alleen bij Verweer beantwoorden)
    - prior_correspondence: lijst van eerdere mails in/uit (voor context bij verweer)
    """

    sections = [
        f"## Stap: {step_name}",
        "",
        "### Sjabloon (LEIDEND — neem letterlijk over, vul alleen aan):",
        "",
        f"**Subject template:**\n```\n{template_subject}\n```",
        "",
        f"**Body template:**\n```\n{template_body}\n```",
        "",
        "### Dossier-context",
        "",
        f"- Dossiernummer: {case_data.get('case_number', '?')}",
        f"- Kenmerk: {case_data.get('reference', case_data.get('case_number', '?'))}",
        f"- Type: {case_data.get('debtor_type', 'b2b')}",
        f"- Openingsdatum: {case_data.get('opened_at', '?')}",
        "",
        "### Cliënt (schuldeiser, vertegenwoordigd door Kesting Legal)",
        "",
        f"- Naam: {client_data.get('name', '?')}",
        f"- Adres: {client_data.get('address', '?')}",
        f"- KvK: {client_data.get('coc_number', 'n.v.t.')}",
        "",
        "### Debiteur (geadresseerde van deze email)",
        "",
        f"- Naam: {debtor_data.get('name', '?')}",
        f"- Adres: {debtor_data.get('address', '?')}",
        f"- Contactpersoon: {debtor_data.get('contact_person', '—')}",
        f"- Email: {debtor_data.get('email', '—')}",
        "",
        "### Openstaande facturen",
        "",
    ]
    if invoices:
        for inv in invoices:
            sections.append(
                f"- Factuur {inv['number']} | uitgegeven {inv['date']} | "
                f"vervalt {inv['due_date']} | € {inv['amount']}"
            )
    else:
        sections.append("(geen factuurregels in dossier)")

    sections.extend([
        "",
        "### Bedragen (gebruik exact in tabel)",
        "",
        f"- Hoofdsom: € {amounts.get('hoofdsom', Decimal('0.00'))}",
        f"- Rente: € {amounts.get('rente', Decimal('0.00'))}",
        f"- Hoofdsom + rente: € {amounts.get('hoofdsom_plus_rente', Decimal('0.00'))}",
        f"- Incassokosten (BIK): € {amounts.get('incassokosten', Decimal('0.00'))}",
        f"- BTW 21%: € {amounts.get('btw', Decimal('0.00'))}",
        f"- Totaal: € {amounts.get('totaal', Decimal('0.00'))}",
        f"- Voldaan bij klant: € {amounts.get('voldaan_bij_klant', Decimal('0.00'))}",
        f"- Door ons ontvangen: € {amounts.get('door_ons_ontvangen', Decimal('0.00'))}",
        f"- **Te voldoen: € {amounts.get('te_voldoen', Decimal('0.00'))}**",
    ])

    if av_text:
        sections.extend([
            "",
            "### Algemene Voorwaarden van cliënt (referentie bij verweer)",
            "",
            av_text[:2000] + ("..." if len(av_text) > 2000 else ""),
        ])

    if incoming_defense:
        sections.extend([
            "",
            "### Inkomend verweer van debiteur (weerleggen op basis van AV en feiten)",
            "",
            incoming_defense,
            "",
            "### Verweer-bibliotheek (5 voorbeeldreacties — kies de passende, neem letterlijk over, voeg korte situatie-specifieke alinea toe)",
            "",
            format_examples_for_prompt(DEFENSE_EXAMPLES, max_chars=8000),
        ])

    if prior_correspondence:
        sections.extend([
            "",
            "### Eerdere correspondentie (chronologisch, voor context)",
            "",
        ])
        for c in prior_correspondence[-5:]:
            sections.append(
                f"- [{c.get('date', '?')}] {c.get('direction', '?')} — "
                f"{c.get('subject', '(geen onderwerp)')}: "
                f"{(c.get('snippet', '') or '')[:200]}"
            )

    sections.extend([
        "",
        "### Output",
        "",
        "Genereer JSON met `subject` en `body`. Volg het sjabloon LETTERLIJK behalve de plekken die je moet invullen.",
    ])

    return "\n".join(sections)


# ── Stap-specifieke aanvullende instructies ──────────────────────────────


STEP_SPECIFIC_GUIDANCE: dict[str, str] = {
    "Eerste sommatie": (
        "Eerste contactmoment. Vul cliënt-introductie, factuurregels, bedragen "
        "en kenmerk in. Geen verwijzing naar eerdere brieven."
    ),
    "Tweede sommatie": (
        "Verwijs naar eerdere sommatie ('Eerder heb ik u aangeschreven betreffende...'). "
        "Toon urgentie, maar gebruik exact de zinnen uit het sjabloon. Sjabloon "
        "(GEEN VERWEER) gebruiken — debiteur heeft NIET gereageerd."
    ),
    "Derde sommatie": (
        "Formeel de 3e sommatie, gebruik echter HETZELFDE sjabloon als Tweede sommatie "
        "(GEEN VERWEER). Vermeld in passende plek dat dit de derde keer is dat we sommeren. "
        "Toon harder dan tweede sommatie, exact volgens sjabloon."
    ),
    "Sommatie laatste mogelijkheid": (
        "Aankondiging faillissementsverzoek. Sjabloon SOMMATIE AANKONDIGING FAILLISSEMENT. "
        "Vermeld dat dit de LAATSTE mogelijkheid is voor debiteur. Bij volgende stap volgt "
        "verzoekschrift. Houd toon volgens sjabloon (streng + zakelijk)."
    ),
    "Verzoekschrift faillissement": (
        "Korte begeleidende email bij het verzoekschrift-PDF (bijlage). Vermeld dat "
        "het verzoekschrift NU wordt ingediend bij de rechtbank. Vraag laatste reactie "
        "binnen korte termijn (zoals in sjabloon). Verzoekschrift-PDF wordt automatisch "
        "als bijlage meegestuurd — niet zelf in body verwerken."
    ),
    "Verweer beantwoorden": (
        "Sjabloon: TWEEDE SOMMATIE INDIEN WEL VERWEER. Lees `incoming_defense` zorgvuldig.\n\n"
        "STAPPEN:\n"
        "1. Lees de verweer-bibliotheek (5 voorbeeldreacties) hieronder. 9 van de 10 keer "
        "matcht 1 van deze 5 op het inkomend verweer — annuleringskosten, eindafrekening "
        "20.4, NCNP, verlengd abonnement, of Engelstalig.\n"
        "2. Kies de meest passende voorbeeldreactie en NEEM DE TEKST LETTERLIJK over "
        "in de daarvoor bedoelde verweer-alinea van het sjabloon.\n"
        "3. Voeg een KORT situatie-specifiek stukje toe (1-3 zinnen) dat reageert op "
        "wat debiteur concreet heeft gezegd — bv. 'U heeft gesteld dat de dienst niet "
        "geleverd is. Cliënte heeft dit gedaan op [datum] en kan dit aantonen met...'.\n"
        "4. Als geen van de 5 voorbeelden past, of als feiten ontbreken: markeer met "
        "'[handmatig invullen door Lisanne: ...]'. Zo weet Lisanne waar ze nog input "
        "moet geven. Geen losse argumenten verzinnen.\n"
        "5. Rest van het sjabloon (aanhef, afsluiting, ondertekening, disclaimer) "
        "blijft IDENTIEK."
    ),
}


def get_step_guidance(step_name: str) -> str:
    """Aanvullende stap-specifieke instructies voor de AI."""
    return STEP_SPECIFIC_GUIDANCE.get(step_name, "")


# ── Volledige prompt-builder ──────────────────────────────────────────────


def build_full_prompt(
    *,
    step_name: str,
    template_subject: str,
    template_body: str,
    **context: Any,
) -> tuple[str, str]:
    """Geeft (system_prompt, user_prompt) terug voor een gegeven stap.

    Aanroep:
        system, user = build_full_prompt(
            step_name="Eerste sommatie",
            template_subject=step.email_subject_template,
            template_body=step.email_body_template,
            case_data={...},
            debtor_data={...},
            ...
        )
        # Roep AI provider aan met system + user
    """

    user = build_user_prompt(
        step_name=step_name,
        template_subject=template_subject,
        template_body=template_body,
        **context,
    )
    guidance = get_step_guidance(step_name)
    if guidance:
        user += f"\n\n### Stap-specifieke aanwijzing\n\n{guidance}"

    return SYSTEM_PROMPT, user
