cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 245 — Taken + meldingen (demo-punten blok 2)

## Model
Bouwen → **Opus**. Check bij start; verkeerd model → wissel vragen.

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S245). CI van S244 natrekken.

## Hoofdtaak (4 onderdelen)
1. **Dossierinfo op taken** (demo-punt: "er staat geen zaak, nummer of naam
   bij"): `WorkflowTaskResponse` (`backend/app/workflow/schemas.py:65`) mist een
   case-subobject — de frontend heeft de weergave al (`taken/page.tsx` regel
   ~212 `task.case && …` rendert nooit). Voeg een compact case-object toe
   (case_number, debiteur-/wederpartijnaam, cliëntnaam) via selectinload in
   `wf_list_tasks` (`workflow/service.py:27`). LET OP MissingGreenlet: nooit
   lazy-loaden in async. Toon debiteurnaam ook in de taakregel.
2. **Filters op de Taken-pagina** (demo-punt): taaktype + dossier-zoek +
   eigenaar, client-side (lijst is al volledig geladen), naast de bestaande
   Openstaand/Alles/Afgerond-knoppen.
3. **Dubbel-wegklik-bug** (demo-punt: "soms 1×, soms 2× wegklikken"): eerst
   live reproduceren. Gemeten aanwijzingen (S243): `completeTask.isPending` is
   globaal voor álle rijen; geen optimistische update (rij blijft tot refetch);
   herhalende taken (G9) maken direct een opvolger met dezelfde titel. Rode
   test/bewijs eerst, dan fix: per-rij pending + optimistische verwijdering.
4. **Mail-meldingen weg na antwoord** (besluit Arsalan S243): antwoord verstuurd
   op dossier X → ongelezen meldingen van het mail-type met case_id=X op
   gelezen. Bouw naast `mark_type_read` (`notifications/service.py:189`) een
   gerichte variant; aanroepen op het gedeelde verzendpunt van reply
   (kruispunt: welke routes versturen een antwoord? skill `breed-testen`).
   Wachters: andere meldingstypes en andere dossiers blijven ongelezen.

## Verificatie
- pytest -k "workflow or task or notification"; uvx ruff; npx tsc --noEmit.
- **Playwright-klikronde prod, desktop + mobiel, screenshots**: takenlijst met
  dossierinfo, filteren, taak wegklikken (1×!), bel na antwoord.
- Deploy via SSH `--force-recreate`, login 200, CI groen.

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`
(volgende prompt = PROMPT-S246).
