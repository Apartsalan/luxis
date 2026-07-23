cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 238 — Native structured outputs-refactor (AI-fundament)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): entry S237 in
`SESSION-NOTES.md` + `docs/TOEKOMST-REPOS.md`. Model: **Opus** (bouwsessie); Fable
voor de eindreview (wissel ACTIEF signaleren — memory `feedback_model_choice`).

## Taak — native structured outputs-refactor
**Waarom (S237-onderzoek):** `ai_agent/kimi_client.py` raadt nu welk JSON-schema bij
een AI-aanroep hoort via een Nederlands TREFWOORD in de prompttekst
(`_detect_schema` / `_PROMPT_SCHEMA_MAP`: "classificeert" → classificatie-schema).
Wijzigt iemand een promptzin, dan valt die aanroep stil terug op tekst-parsen
(`_parse_json`). Dat is de kwetsbaarste eigen laag in het AI-fundament.

**Wat er moet gebeuren:**
1. **Lees eerst de actuele Anthropic-documentatie** (skill `claude-api` / web) over
   native structured outputs (GA voor Sonnet 4.5+/Haiku 4.5, juli 2026) — niet uit
   het geheugen bouwen; verifieer parameternamen/response-vorm.
2. Laat elke aanroeper zijn schema EXPLICIET meegeven (geen trefwoord-detectie meer);
   aanroepers: classificatie (`service.py`), intake (`intake_service.py`), factuur
   (`invoice_parser.py`), concepten (`incasso/automation_service.py`,
   `draft_service.py`, `unified_draft_service.py`) — meet de volledige lijst zelf
   vers met grep op `call_intake_ai|call_draft_ai|call_claude_with_pdf`.
3. Stap over op native structured outputs waar dat kan; forced tool_use mag blijven
   als de docs daar redenen voor geven (PDF-route!). `_detect_schema` + `_parse_json`
   weg zodra geen pad ze meer raakt.
4. Kruispunt-check (skill `breed-testen`): dit raakt álle AI-routes — draai de
   AI-gerelateerde suites (unified_draft, classificatie, intake, invoice, followup)
   en één echte prod-natelling per route na deploy (bijv. 1 handmatige classificatie
   op een testdossier).
5. `ai_usage`-registratie moet blijven werken (kosten per aanroep).

## Constraints
Geen nieuwe dependencies (dit is juist de nul-dependency-route; Instructor NIET
toevoegen — besluit S237). Geen prompt-teksten herschrijven (alleen de schema-koppeling).
Geen echte debiteuren mailen; testkanaal 2026-00006. Geen `git add -A`. Deploy via
SSH mét `--force-recreate`. Eén testrun tegelijk. KvK: niet naar vragen.
Lopende zaken (niet deze sessie tenzij Arsalan erom vraagt): verweer-concepten
IN100592/IN100606 en IN100492-vraag liggen bij Lisanne; opruimronde wacht op
Arsalan+Lisanne (zie entry S237).

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v`
- Lint: `uvx ruff check backend/app` | Frontend niet geraakt (tenzij toch: `npx tsc --noEmit`)
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-238 + PROMPT-S239; verplaats PROMPT-S237 en ouder naar `docs/archief/prompts/`).

## Losse punten (niet deze sessie tenzij tijd over)
BaseNet-delisting, derde AI-testronde (± 110 calls → eerst GO), Lisanne-steekproef,
kostenblokje dashboard, fysieke-telefoon-check, opmaak-restpunt S227, S221b-rest,
DMARC, testdata opruimen, 4 cosmetische restjes S235, sharp/libvips-CVE's (update
zodra gepatcht), logboekregeltje execute-escalate (S237-review).
