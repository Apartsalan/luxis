cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 235 — Betalingsregeling herkennen + flexibel termijnschema

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): entry S234 in
`SESSION-NOTES.md` (deze sessie borduurt daarop voort). Model: **Fable** voor
onderzoek/ontwerp (in de bron meten), **Opus** voor het bouwwerk; Fable weer voor de
review aan het eind (vaste cyclus — memory `feedback_model_choice`; wissel ACTIEF
signaleren).

## EERST afhandelen — 2 open vragen uit S234 (vóór het bouwen)
1. **IN100613** staat op status 'afgesloten' (15-7) maar op pijplijnstap 'Tweede sommatie'.
   Er ligt een doorstuurbare vraag voor Lisanne klaar (zie hieronder / entry S234). Zodra
   Arsalan/Lisanne antwoordt: zaak-data rechtzetten (dry-run + GO + natelling). NIET zelf
   aannemen wat er moet gebeuren.
2. **Auto-afsluiten bij volledige betaling.** Het systeem zet een dossier ál automatisch op
   'betaald' + date_closed bij €0 openstaand (`workflow/hooks.py::on_payment_received`).
   Arsalan koos in S234 "taak i.p.v. automatisch" — dat is dus een WIJZIGING van bestaand
   gedrag. Eerst met Arsalan bevestigen: wil hij de auto-afsluiting vervangen door een taak
   "Volledig betaald — afsluiten?", of laten zoals het is? Pas daarna bouwen.

## Hoofdtaak — betalingsregeling + flexibel termijnschema
De classificatie herkent al een "betalingsregeling"-signaal uit inkomende mail. Bouw daarop:
- **Onderzoek eerst (in de bron):** welke regeling-modellen bestaan al (`Treffen van regeling`,
  `Bijhouden regeling`-stappen; `installments`/`_auto_link_payment_to_installments` in
  `collections`)? Wat is er van een flexibel termijnschema al aanwezig (elke termijn heeft al
  zijn eigen bedrag/datum) en wat ontbreekt? Meet vóór je voorstelt.
- **Ontwerp (Plan Mode):** herken een regelingsvoorstel uit de mail → concept/taak; flexibel
  schema (bv. 2× €200, daarna €1.000) invoeren en bijhouden; koppeling met de pijplijn
  (regeling-stappen zijn hold-stappen — schuiven bewust niet door).
- NIET bouwen vóór akkoord op het ontwerp.

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail; hotmail via M365).
MAILSLOT OPEN. Elke prod-mutatie: dry-run/telling + GO + natelling. Geen `git add -A`.
Kruispunt-check bij elk gedeeld effect (skill `breed-testen`). KvK: niet naar vragen.
Deploy via SSH mét `--force-recreate`. Inlognaam Lisanne: kesting@kestinglegal.nl.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "installment or regeling or payment or followup" -v`
- Lint: `uvx ruff check backend/app`
- Frontend: `cd frontend && npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-235 + PROMPT-S236; verplaats PROMPT-S233 en ouder naar `docs/archief/prompts/`).

## Losse punten (niet deze sessie tenzij tijd over)
BaseNet-delisting melden, derde AI-testronde (± 110 calls → eerst GO), Lisanne-steekproef
auto-conceptbatch, kostenblokje dashboard, Outlook-route weghalen, fysieke-telefoon-check
(AI-antwoord-generatieflow S233), opmaak-restpunt S227, DMARC, testdata opruimen.
