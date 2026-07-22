cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 236 — Open beslispunten afhandelen + losse punten

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): entry S235 in
`SESSION-NOTES.md`. Model: **Fable** voor onderzoek/beslis-analyse, **Opus** voor
klik-/bouwwerk (vaste cyclus — memory `feedback_model_choice`; wissel ACTIEF signaleren).

## Taak — drie open punten, in deze volgorde
1. **IN100613** (afgesloten 15-7, maar op pijplijnstap 'Tweede sommatie'). Vraag Arsalan
   of Lisanne al geantwoord heeft. Zo ja: zaak-data rechtzetten met dry-run + GO +
   natelling. Zo nee: laten liggen, NIET zelf aannemen.
2. **Beslispunt werklijst** (Fable-vondst S234-review): doorschuiven maakt sinds
   S232/S234 geen taak meer aan op de nieuwe stap — de takenpagina leunt volledig op de
   follow-up-adviseur. Leg Arsalan de keuze voor: takenpagina óf follow-up-pagina als
   dé werklijst van Lisanne. Bouw daarna wat uit de keuze volgt (bv. taak-aanmaak terug
   op de gedeelde motor, óf de takenpagina-teller/menu-ingang herzien).
3. **De 7 import-dossiers op 'Eerste sommatie'** (IN100592/98/99, IN100602/03/04/06):
   hun eerste sommatie is nog NOOIT verstuurd (bevestigd 22-7; Luxis is de waarheid,
   BaseNet doet geen incasso meer). De 7 pending follow-up-adviezen zijn terecht.
   Bespreek met Arsalan of ze de deur uit mogen — verzending alleen per expliciete GO
   (echte debiteuren!).

## Constraints
Geen echte debiteuren mailen zonder GO per geval (testkanaal 2026-00006 = Arsalans
gmail). MAILSLOT OPEN. Elke prod-mutatie: dry-run/telling + GO + natelling. Geen
`git add -A`. Kruispunt-check bij elk gedeeld effect (skill `breed-testen`). KvK: niet
naar vragen. Deploy via SSH mét `--force-recreate`. Inlognaam Lisanne:
kesting@kestinglegal.nl.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v`
- Lint: `uvx ruff check backend/app`
- Frontend: `cd frontend && npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-236 + PROMPT-S237; verplaats PROMPT-S234 en ouder naar `docs/archief/prompts/`).

## Losse punten (niet deze sessie tenzij tijd over)
BaseNet-delisting melden, derde AI-testronde (± 110 calls → eerst GO), Lisanne-steekproef
auto-conceptbatch, kostenblokje dashboard, Outlook-route weghalen, fysieke-telefoon-check,
opmaak-restpunt S227, DMARC, testdata opruimen, 4 cosmetische restjes S235 (zie entry).
