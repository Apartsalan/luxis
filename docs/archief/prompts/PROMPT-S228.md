cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 228 — Opmaak-restpunt Arsalan + S221b-UX-restant

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules/pagina's, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Model: **Opus** (bouwen/klikwerk); wissel naar Fable voor review (vaste cyclus —
zie memory `feedback_model_choice`, niet meer ter discussie stellen).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md` + STAND in `docs/archief/prompts/PROMPT-S215.md`),
dán de rest. NEE → direct door.

## Taak 1 — Opmaak-restpunt uitvragen (EERST, kort)
S227 heeft de briefopmaak breed geveegd (vaste witregels, extra regel na aanhef,
alinea's op alle routes — zie SESSION-NOTES entry S227) en een opmaaktest-mail
naar Arsalans gmail gestuurd. Zijn oordeel: **"niet goed maar prima, laat maar —
komt later"** — wat er precies nog schort is NIET gespecificeerd.
→ Vraag Arsalan om een screenshot of aanwijzing van wat er nog niet klopt
(één AskUser-vraag, geen catalogus), en fix dan gericht dát onderdeel. De maten
staan nu centraal (`_inline_paragraph_spacing` / `plain_paragraphs_html` in
`backend/app/email/incasso_templates.py`) — één maat aanpassen, niet opnieuw vegen.

## Taak 2 — S221b-UX-restant (zover de tijd reikt, in deze volgorde)
- Review-scherm classificatie+concept naast elkaar.
- Voortgangsindicator bij concept-genereren (generatie duurt ~30-40 s, geen feedback).
- Tijdlijn-mailregel klikbaar (deep-link naar correspondentie; id-betekenis eerst verifiëren).
- Follow-up sorteerbare koppen (vergt server-side sortering).
- Intake-detectie dempen.
- Échte HTML-tabellen in AI-mails (injectie-oppervlak — apart afwegen).
- Blok 6-beslismemo b2b/b2c (alleen memo, geen code).

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail).
Prod-mutaties: dry-run/telling + GO. Geen `git add -A`. Bayar IN100613 NIET
aanraken. Testdata 2026-00007 t/m -00019 opruimen mag alleen ná GO (natelling).
Classificatie-antwoord-route niet zomaar live vuren (verstuurt echt + raakt
Arsalans reviewwachtrij).

## Verificatie
- Backend: relevante `pytest` (detached bij full suite), `uvx ruff check app/`.
- Frontend: `npx tsc --noEmit`.
- Kruispunt-check (skill `breed-testen`) bij elk gedeeld effect.
- CI groen na push (`gh run list`) — vaste afsluitcheck.
- Live doorklikken op 2026-00006.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag
sessie-228 + PROMPT-S229).

## Nog open na S227
- DMARC ontbreekt op kestinglegal.nl → Arsalan/BaseNet publiceert record (SPF+DKIM OK).
- Auto-concept-gate: menselijke steekproef Lisanne (~10 concepten) vóór activering.
- Klant-update-endpoint UI-dood (S224-klasse beslispunt: opruimen of knop geven).
- KvK-backfill zodra sleutel binnen (~22 juli) — houdt voorrang.
