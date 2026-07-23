cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 247 — Fable-eindreview S246 + AI-kennislaag (demo-punten blok 4)

## Model
Deze sessie begint met REVIEW → start op **Fable** (`/model` → Fable 5,
`/effort max`). Pas ná deel A omschakelen naar **Opus** voor het bouwwerk.
**Meld de wissel zelf** — les S246: "bouwen → Opus" in een sessieprompt slaat op
de BOUWfase; de plan- en reviewfase zijn altijd Fable.

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S247). S246 (uitgesteld versturen) is LIVE — zie entry S246 in
SESSION-NOTES. CI van S246 natrekken.

## Deel A (Fable) — eindreview S246, VERPLICHT en eerst
S246 raakte élke verzendroute en de eindreview is nog niet gedraaid. Geen snelle
zelfcontrole maar een zelfstandige brede jacht:
- Lees de hele diff `9197f66`→`4269592` vers tegen.
- Kruispunt-matrix over alle verzendroutes: doet een INGEPLANDE mail iets anders
  dan een direct verstuurde? Let vooral op de afsplitsing `perform_compose_send`
  in `compose_router.py` — is er gedrag verloren gegaan?
- Actief proberen te weerleggen: wat als de gebruiker die de mail inplande
  intussen gedeactiveerd is of van rol wisselt? Als het dossier gesloten/betaald
  is? Als een bijlage van schijf verdwenen is? Bij twee backend-instanties
  (claim-vangrail)? Blijven 'mislukt'-rijen ergens zichtbaar of verdwijnen ze
  stil? Wat gebeurt er met een geplande mail als de wederpartij intussen
  antwoordt?
- Eigen visuele ronde op prod (desktop + mobiel), screenshots ook echt bekijken.
- Bevindingen eerst voorleggen; repareren gebeurt op Opus.

## Deel B (Opus, na de review) — AI-kennislaag
1. **Placeholder-bug IN100606** (demo-vraag Arsalan: "waarom kan Luxis hier geen
   antwoord op geven?"). Gemeten (S243): de placeholder is bewust ontwerp
   (`backend/app/ai_agent/incasso_email_prompts.py:314-318` — onbekend verweer →
   placeholder i.p.v. verzonnen argument), maar de AI kopieerde de mal
   `<kernverweer letterlijk uit incoming_defense>` LETTERLIJK in het concept
   i.p.v. het echte verweer in te vullen. Fix de prompt-instructie + wachter op
   de substitutie. Leg Arsalan in gewone taal uit: dit is een vangnet, geen fout
   — Luxis verzint bewust geen juridische argumenten die Lisanne niet heeft
   goedgekeurd.
2. **Juridische kennisregels** (demo-wens IN100458: wederpartij-BV "wil de AV
   vernietigen" — juridisch kansloos, art. 6:235 BW, maar Luxis herkent zulke
   standaard-onzin niet). Ontwerp op Fable: curated bibliotheek
   "veelvoorkomende onjuiste stellingen + standaard-weerlegging" als uitbreiding
   van de bestaande verweer-bibliotheek (learned_answers, 132 rijen), via
   DEZELFDE goedkeur-flow — élke regel langs Lisanne vóór gebruik. Géén
   hardgecodeerde wetsartikelen zonder haar toets (juridische twijfel = flaggen).
   Signaleer ook: de 132 bestaande kandidaten wachten al op Lisanne.

## Verificatie
- Kruispunt-check skill `breed-testen`: wachter per foutSOORT, niet per geval.
- Wachters op prompt↔schema-sync (test_kimi_client_structured-patroon).
- Derde AI-testronde: verse AI-antwoorden op de goud-gevallen
  (`scripts/ai/antwoord_testronde.py`, rapport S238 als vergelijk), niets
  versturen.
- **Eén testrun tegelijk** — twee gelijktijdige pytest-runs op dezelfde testDB
  gaven in S246 68 spookfouten die op een regressie leken.
- uvx ruff; tsc; CI groen; deploy via SSH; login 200.

## Constraints (wat NIET doen)
- **Geen "Verstuur later" op de lopende-band-knoppen** (batch/follow-up) zonder
  expliciet besluit van Arsalan — bewust uitgesteld in S246. Daar zit
  doc-generatie + doorschuiven in de aanroeper, dus het vraagt eerst een keuze:
  schuift de zaak door bij het inplannen, of pas als de mail echt weg is?
- Geen echte debiteuren mailen; kostenbewust testen (ai_usage natellen).
- Geen inhoudelijk dossierwerk (mails beantwoorden, dossierbeslissingen) — dat is
  Lisanne. Vondsten signaleren in het verslag, niet aanbieden op te pakken.
- KvK: niet naar vragen.

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`
(volgende prompt = PROMPT-S248).
