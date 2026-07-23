cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 245 — Taken + meldingen (demo-punten blok 2)

## Model
Bouwen → **Opus**. LET OP: het opgeslagen standaardmodel staat sinds S244 op
Fable — check bij start welk model actief is en vraag om de wissel vóór je
begint. Eindreview op Fable (wissel melden).

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S245). CI S244 is volledig nagetrokken (alles groen, incl. de 3
Fable-reviewfixes t/m `d2aef7c`) — geen achterstallige controle.

## Context uit S244 (kort)
- Mail-werkbank live: draad-gegroepeerde correspondentie, draad overal,
  Verzonden-map, vrij bericht-shell. Draad-groepering = genormaliseerd
  onderwerp (thread-ids bleken op dossier-mails bijna waardeloos).
- Parallelle S243-tegenlezing (`9808e3f`): 11 tijdlijn-rijen hersteld,
  zoekbalk-tekst uitgebreid; 2 regeling-taken (IN100281/IN100537) zijn ECHT
  werk voor Lisanne — bij het bouwen/testen van taken-features NIET sluiten.
- Encoding-les: bronbestanden nooit met PowerShell Get/Set-Content
  herschrijven (mojibake-incident S244) — Edit-tool gebruiken.

## Hoofdtaak (4 onderdelen)
1. **Dossierinfo op taken** (demo-punt: "er staat geen zaak, nummer of naam
   bij"): `WorkflowTaskResponse` (`backend/app/workflow/schemas.py`) mist een
   case-subobject — de frontend heeft de weergave al (`taken/page.tsx`,
   `task.case && …` rendert nooit). Voeg een compact case-object toe
   (case_number, debiteur-/wederpartijnaam, cliëntnaam) via selectinload in
   `wf_list_tasks` (`workflow/service.py`). LET OP MissingGreenlet: nooit
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
   gelezen. Bouw naast `mark_type_read` (`notifications/service.py`) een
   gerichte variant; aanroepen op het gedeelde verzendpunt van reply
   (kruispunt: welke routes versturen een antwoord? skill `breed-testen` —
   let op: sinds S244 prefillt "Beantwoorden" de vrij-bericht-shell, maar de
   verzendroute is onveranderd compose/send). Wachters: andere meldingstypes
   en andere dossiers blijven ongelezen.

## Verificatie (HARD)
- pytest -k "workflow or task or notification"; uvx ruff; npx tsc --noEmit.
- **Playwright-klikronde prod, desktop + mobiel 390×844, screenshots — en de
  beelden ook echt BEKIJKEN (S244-les: 2 van de 4 reviewvondsten zaten in
  screenshots die wel gemaakt maar niet bekeken waren; mobiel = eerst
  scrollen tot de content in beeld staat)**: takenlijst met dossierinfo,
  filteren, taak wegklikken (1×!), bel na antwoord.
- Testen op testdossiers (2026-00006); de echte taken (o.a. IN100281/IN100537
  regeling-taken, 11× "Vervolg bepalen" dagvaarden) NIET sluiten.
- Deploy via SSH `--force-recreate`, login 200, CI groen.

## Constraints
- Geen echte debiteuren mailen zonder GO per geval.
- Inhoudelijk werk (taken afhandelen, mails beantwoorden) is aan Lisanne —
  signaleren, niet oppakken.

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`
(volgende prompt = PROMPT-S246).
