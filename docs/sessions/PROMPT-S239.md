cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 239 — Lisanne-antwoorden + opruimronde (of nieuw hoofdonderwerp)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): entries S237 + S238 in
`SESSION-NOTES.md`. Model: **vraag Arsalan bij start welke taak** — opruimronde/datafixes
= Opus (klikwerk), onderzoek of ontwerp = Fable (wissel ACTIEF signaleren — memory
`feedback_model_choice`).

## Taak — kies bij start met Arsalan
**A. Lisanne-antwoorden verwerken (als ze gereageerd heeft):**
- Verweer-concepten IN100592 + IN100606: na haar GO controleren + versturen
  (per dossier vers meten vóór verzending; GO per verzending blijft gelden).
- IN100492 (afgesloten, €0 betaald, debiteur vraagt update): haar besluit uitvoeren.

**B. Opruimronde (alleen mét Arsalan+Lisanne erbij, dry-run + natelling + GO per stap):**
- Stale adviezen IN100607/IN100613/IN100521; 6 oude nakijk-taken van 21-7;
  dubbel concept + dubbele taak op IN100592; logboekregeltje execute-escalate
  (zegt "taak aangemaakt" ook als de spiegel al bestond — cosmetisch codefixje).

**C. Nieuw hoofdonderwerp naar keuze Arsalan.** Kandidaat uit S237: debiteur-reactie
vanaf een onbekend mailadres valt nu stil (alleen zichtbaar in de ongesorteerde bak)
— melding/aanwijzing bouwen zodat dit niet meer gemist wordt.

## Constraints
Geen echte debiteuren mailen zonder expliciete GO per verzending; testkanaal 2026-00006.
Geen `git add -A`. Deploy via SSH mét `--force-recreate`. Eén testrun tegelijk.
KvK: niet naar vragen. Prod-datamutaties: altijd dry-run + natelling + GO.
S238-huisregel: wijzig je een prompt-JSON-instructie, wijzig het bijbehorende schema mee
(wachters in `tests/test_kimi_client_structured.py` bewaken dit).

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v`
- Lint: `uvx ruff check backend/app` | Frontend geraakt → `npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-239 + PROMPT-S240; verplaats PROMPT-S238 en ouder naar `docs/archief/prompts/`).

## Losse punten (niet deze sessie tenzij tijd over)
BaseNet-delisting, derde AI-testronde (± 110 calls → eerst GO), Lisanne-steekproef,
kostenblokje dashboard, fysieke-telefoon-check, opmaak-restpunt S227, S221b-rest,
DMARC, testdata opruimen, 4 cosmetische restjes S235, sharp/libvips-CVE's.
