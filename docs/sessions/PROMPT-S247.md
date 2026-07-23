cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 247 — AI-kennislaag (demo-punten blok 4)

## Model
Ontwerp/analyse eerst op **Fable**, daarna bouwen op **Opus** (wissel door
Arsalan, actief melden). Prompts wijzigen → derde AI-testronde verplicht
(S238-huisregel).

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S247). CI van S246 natrekken.

## Hoofdtaak (2 onderdelen)
1. **Placeholder-bug IN100606** (demo-vraag Arsalan: "waarom kan Luxis hier
   geen antwoord op geven?"). Gemeten (S243): de placeholder is bewust ontwerp
   (`backend/app/ai_agent/incasso_email_prompts.py:314-318` — onbekend verweer →
   placeholder i.p.v. verzonnen argument), maar de AI kopieerde de mal
   `<kernverweer letterlijk uit incoming_defense>` LETTERLIJK in het concept
   i.p.v. het echte verweer in te vullen. Fix de prompt-instructie + wachter op
   de substitutie. Leg Arsalan in gewone taal uit: dit is een vangnet, geen
   fout — Luxis verzint bewust geen juridische argumenten die Lisanne niet
   heeft goedgekeurd.
2. **Juridische kennisregels** (demo-wens IN100458: wederpartij-BV "wil de AV
   vernietigen" — juridisch kansloos, art. 6:235 BW, maar Luxis herkent zulke
   standaard-onzin niet). Ontwerp op Fable: curated bibliotheek
   "veelvoorkomende onjuiste stellingen + standaard-weerlegging" als uitbreiding
   van de bestaande verweer-bibliotheek (learned_answers, 132 rijen), via
   DEZELFDE goedkeur-flow — élke regel langs Lisanne vóór gebruik. Géén
   hardgecodeerde wetsartikelen zonder haar toets (juridische twijfel = flaggen).
   Signaleer ook: de 132 bestaande kandidaten wachten al op Lisanne.

## Verificatie
- Wachters op prompt↔schema-sync (test_kimi_client_structured-patroon).
- Derde AI-testronde: verse AI-antwoorden op de goud-gevallen
  (`scripts/ai/antwoord_testronde.py`, rapport S238 als vergelijk), niets
  versturen.
- uvx ruff; CI groen; deploy backend; login 200.

## Constraints
- Geen echte debiteuren mailen; kostenbewust testen (ai_usage natellen).

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`.
