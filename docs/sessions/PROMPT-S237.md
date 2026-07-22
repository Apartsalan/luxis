cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 237 — Reacties op de sommaties verwerken + open beslispunten

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): entry S236 in
`SESSION-NOTES.md`. Model: **Fable** voor onderzoek/review, **Opus** voor bouwen
(vaste cyclus — memory `feedback_model_choice`; wissel ACTIEF signaleren).

## Taak — in deze volgorde
1. **Reacties op de 7 sommaties van 22-7** (IN100592/98/99, 602/03/04/06 — allemaal op
   'Tweede sommatie'). Meet vers: nieuwe inkomende mails, classificaties, bounces.
   - **IN100606**: debiteur betwist (afspraken niet nagemaakt, wil desnoods rechtszaak);
     dossier staat op 'Verweer beantwoorden', AI-concept ligt klaar. Vraag Arsalan of
     Lisanne het concept al bekeken heeft; niets versturen zonder GO.
   - Overige reacties: per geval voorleggen.
2. **Drie beslispunten aan Arsalan (in één keer vragen):**
   a. Escalatie-adviezen (o.a. 5 échte 'Voorstel dagvaarding'-dossiers) óók als taak
      op de Taken-pagina spiegelen? (S236 bouwde alleen verstuur-adviezen.)
   b. IN100607: stale eerste-sommatie-advies superseden? (Zaak staat op 'Verweer
      beantwoorden' — advies is verouderd; data-fix met dry-run + natelling.)
   c. IN100613: heeft Lisanne geantwoord? Zo ja: rechtzetten (dry-run + GO + natelling);
      dat oude pending advies dan ook meenemen.
3. Bouw wat uit de keuzes volgt.

## Constraints
Geen echte debiteuren mailen zonder GO per geval (testkanaal 2026-00006 = Arsalans
gmail). Elke prod-mutatie: dry-run/telling + GO + natelling. Geen `git add -A`.
Kruispunt-check bij elk gedeeld effect (skill `breed-testen`). KvK: niet naar vragen.
Deploy via SSH mét `--force-recreate`. Inlognaam Lisanne: kesting@kestinglegal.nl.
Check eerst of CI-run 29910413122 (commits e18c2d2/1782310) groen is geworden.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v`
  (één run tegelijk — parallelle runs botsen op de test-DB, les S236)
- Lint: `uvx ruff check backend/app`
- Frontend: `cd frontend && npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-237 + PROMPT-S238; verplaats PROMPT-S236 en ouder naar `docs/archief/prompts/`).

## Losse punten (niet deze sessie tenzij tijd over)
BaseNet-delisting melden, derde AI-testronde (± 110 calls → eerst GO), Lisanne-steekproef
auto-conceptbatch, kostenblokje dashboard, Outlook-route weghalen, fysieke-telefoon-check,
opmaak-restpunt S227, DMARC, testdata opruimen, 4 cosmetische restjes S235 (zie entry).
