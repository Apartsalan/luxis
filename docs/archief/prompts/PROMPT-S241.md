cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 241 — scenario-testronde 3: verse brillen (parallel aan S240-afronding)

## Model
Deze sessie is TESTWERK/onderzoek → **Fable**. Check bij start welk model actief is;
staat er Opus, vraag Arsalan te wisselen (memory `feedback_model_choice`). Alleen als
er een fix gebouwd moet worden mag dat op Fable blijven (kleine fixes) — grote
bouwklus → melden.

## Parallel-spelregels (S240 kan nog openstaan in een andere terminal)
- S240 rondt daar af: CI-natrek + sessie-einde-administratie (notities, roadmap, tag,
  PROMPT-verplaatsing). **Doe die administratie hier NIET.**
- `git pull` vóór élke commit; alleen expliciete paden stagen (NOOIT `git add -A`).
- Eén testrun tegelijk (niet parallel met een run van de andere terminal); deploys
  alleen als er hier een fix gecommit is, mét `--force-recreate`.
- Testsporen: elke prod-mutatie terugdraaien + natellen, zelfde discipline als S239/S240.

## Start
Lees `docs/sessions/S240-SCENARIOS.md` (wat ronde 2 al dekte — NIET herhalen) en
SESSION-NOTES entry S239 (ronde 1: 32 scenario's). De nieuwe S240-functies die nu
live staan: (a) melding bij elke nieuwe ongesorteerde inbound-mail (type
`email_unsorted`, doorklik naar Mail-pagina Ongesorteerd-tab), (b) taak
"Betaalbelofte controleren — {zaaknummer}" met due = herkende beloofde datum, sluit
automatisch bij volledige betaling (afgevinkt) en bij handmatig afsluiten (vervallen).

## Hoofdtaak — scenario-ronde 3, brillen die nog niet gedraaid zijn
Zelfde discipline als S239/S240: per scenario VOORAF het verwachte resultaat
opschrijven; vondsten in drie bakken (fout → fixen met rode test eerst; ergernis →
fixen; gemis → voorstel-lijst); logboek in `docs/sessions/S241-SCENARIOS.md`.
Testterrein: wegwerpdossiers (aanmaken → exact wissen + natellen) en testkanaal
2026-00006. NIETS naar echte debiteuren.

**Bril A — de nieuwe functies op hun kruispunten (geen AI-kosten):**
1. Belofte + lopende regeling tegelijk: mail met belofte op een zaak in 'Bijhouden
   regeling' — ontstaat er dubbel bewakingswerk of blijft het logisch?
2. Belofte-datum in het verleden (oude mail gesynct) — taak direct 'te laat'?
3. Belofte herkend, daarna betwisting op dezelfde zaak — bijten de taak en de
   verweer-keten elkaar?
4. Zaak met open belofte-taak wordt heropend na betaling-verwijderen — wat is de
   eindstand van de taak (afgevinkt blijven = acceptabel, documenteer het)?
5. Ongesorteerd-melding: komt er bij een dossier-sync (sync vanuit een dossier) ooit
   een onterechte melding? En bij de 5-minuten-autosync een storm als er 3 nieuwe
   ongesorteerde mails tegelijk binnenkomen?
6. Dismissed-mail her-gesynct → geen nieuwe melding (poort na "Negeren").

**Bril B — twee gebruikers / rollen (droog + read-only):**
7. Lisanne's account (kesting@) en Arsalans account zien dezelfde tellers/taken —
   klopt de werklijst voor allebei? (read-only vergelijken)
8. Medewerker-rol: de rollen-matrix (docs/security/rollen.md) live steekproeven op
   3 gevoelige routes (gebruikersbeheer, instellingen, verwijderen).

**Bril C — de ochtend van morgen (droog, code + planning lezen):**
9. Welke dagelijkse jobs draaien er om 06:00-09:00 en wat gaan ze doen met de
   S240-taken/meldingen (taken-job zet pending→due; komt er dubbele melding-druk)?
10. De 21 open follow-up-adviezen + 16 aanvragen + 61 taken: wat ziet Lisanne
    morgenochtend als ze inlogt — is dat werkbaar of verzuipt ze? (meting, geen fix)

**Optioneel blok D — derde AI-antwoordronde (±110 echte AI-calls, kost geld):**
ALLEEN met expliciete GO van Arsalan in deze sessie. Zo ja: zelfde opzet als de
S238-ronde (scenario's + goud-gevallen, corrector aan, niets versturen), rapport
naast het logboek.

## Constraints
Geen echte debiteuren/cliënten mailen; de 2 open mails (IN100128, IN100586) en het
verse IN100592-verweer zijn van Arsalan+S240 — NIET aanraken. KvK: niet naar vragen.
Opruimronde (spooktaken, oude test-taken, 81 ongesorteerde oudjes) is van
Arsalan+Lisanne — niet zelfstandig doen. S238-huisregel: prompt-JSON gewijzigd →
schema mee.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v`
- Lint: `uvx ruff check backend/app` | Frontend geraakt → `npx tsc --noEmit`
- Bij fixes: CI groen na push (`gh run list`).

## Afsluiten
Logboek compleet + vondsten-tabel ingevuld. GEEN sessie-einde-administratie als S240
nog open is — meld de eindstand aan Arsalan; de S240-terminal (of een latere sessie)
verwerkt de notities.
