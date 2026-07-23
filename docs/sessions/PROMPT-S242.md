cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 242 — veegsessie voorstel-lijst (3 kleine verbeteringen)

## Model
Dit is BOUWWERK → **Opus**. Check bij start welk model actief is; staat er Fable,
vraag Arsalan te wisselen (memory `feedback_model_choice`).

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context: `docs/sessions/S241-SCENARIOS.md` (vondsten + voorstellen) en
`docs/sessions/S240-SCENARIOS.md` (vondst 2 = dubbelklik-betaling).

**Administratie-check bij start:**
1. CI natrekken: commits `275d9f4` (bundeling) en `1ab82ec` (logboek) — bundeling was
   al groen bij S241-einde, logboek-run liep nog (`gh run list`).
2. Staat er nog geen S240-entry in SESSION-NOTES.md (parallelle terminal), schrijf hem
   dan compact uit `docs/sessions/S240-SCENARIOS.md` + git log en verplaats
   `docs/sessions/PROMPT-S241.md` naar `docs/archief/prompts/`.
3. **Signaleer aan Arsalan (niet zelf oppakken — rolverdeling S240):** door de
   bundeling zijn 2 verjaringsmeldingen zichtbaar geworden: IN100015 (VERJAARD,
   verjaringsdatum 15-10-2025) en IN100127 (verjaringsdatum 23-3-2026) — beide
   "overweeg een stuitingshandeling"; en de 2 open mails (IN100128, IN100586)
   wachten nog op antwoord van Arsalan/Lisanne.

## Taak — drie kleine verbeteringen, elk met wachter (rode test eerst bij bugs)

**1. Dubbelklik-betaling-slot (S240 vondst 2, bug).** Twee gelijktijdige identieke
deelbetalingen (dubbelklik of 2 tabs) worden nu allebei geboekt; de UI-disable dempt
alleen. Bouw een idempotentie-poort in de service-laag (niet alleen de router — de
agent-laag-afspraak S237 geldt). Kijk eerst hoe `create_payment` loopt en kies de
lichtste betrouwbare vorm (bv. dedup-venster op identieke betaling binnen enkele
seconden, of een unieke sleutel vanaf de client). Reproduceer eerst met een rode test.

**2. Belofte-taak naast actieve regeling (S241 voorstel 2, ergernis).** Een
belofte-mail op een zaak met lopende regeling maakt nu een tweede bewakingstaak naast
de termijn-bewaking (S241 live bewezen op wegwerpdossier: zelfde datum, twee taken).
Kies een gedrag + onderbouw kort in de commit (voor de hand: geen belofte-taak
aanmaken als er een actieve regeling loopt — de termijnen bewaken die betaling al;
check `ensure_payment_promise_task` in `backend/app/collections/service.py`).
Tegenproef: belofte op zaak zónder regeling blijft gewoon een taak geven.

**3. Eigenaarloze te-laat-taken-melding (S241 voorstel 3, ergernis).** De dagelijkse
meldingen-job stuurt de melding voor een taak zonder eigenaar naar de "eerste"
gebruiker — willekeurige volgorde (`daily_deadline_notifications` in
`backend/app/workflow/scheduler.py`, `users[0]`). Meld eigenaarloze taken aan álle
actieve gebruikers (consistent met de werklijst, die eigenaarloze taken ook aan
iedereen toont). Let op de bestaande 30-dagen-dedup per (user, case, task).

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "payment or promise or notification or scheduler" -v` (relevante modules, één run tegelijk)
- Lint: `uvx ruff check backend/app` | Frontend geraakt → `npx tsc --noEmit`
- Kruispunt-check (skill `breed-testen`): betaling boeken heeft meerdere routes
  (API, UI, termijn-registratie) — de poort moet op het gedeelde punt zitten.
- Na push: CI groen (`gh run list`), deploy via SSH met `--force-recreate`.

## Constraints
- Alleen deze drie punten; de rest van de voorstel-lijst (categorie 'onduidelijk',
  overbetaling-knop, cascade, weekend-logica, kostenblokje) = voorstel, geen actie.
- Geen echte debiteuren/cliënten mailen; IN100128/IN100586/IN100592 niet aanraken;
  KvK: niet naar vragen; opruimronde is van Arsalan+Lisanne.
- Prod-testsporen: terugdraaien + natellen (S239/S240/S241-discipline).
- S238-huisregel: prompt-JSON gewijzigd → schema mee.

## Commit
Per punt een eigen conventional commit + push naar main; deploy automatisch via SSH
(skill `deploy-regels`). Afsluiten met `/sessie-einde`.
