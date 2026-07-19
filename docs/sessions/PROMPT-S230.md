cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 230 — Werkorders uit de eindkeuring (V1-V4)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules/pagina's, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context: `docs/sessions/S229-eindkeuring.md` (§ "Werkorders deel 2" =
de vier vondsten met bewijs en aanpak).
Model: **Opus** voor het fixwerk; wissel naar Fable bij twijfelgevallen/herbeoordeling
(vaste cyclus — memory `feedback_model_choice`).

## Taak 1 — V1 B2C-BIK-correctie (EERST, grootste geldpost)
27 actieve consumentenzaken dragen een handmatig incassokosten-bedrag (`bik_override`,
BaseNet-import) van vlakke 15% van de hoofdsom, bóven de dwingende WIK-staffel — samen
€9.794,65 te veel. De lijst + bedragen zijn in S229 gemeten (herhaal de meting vers).
→ **Eerst met Arsalan/Lisanne:** welke van de 27 zijn bevestigd consument (bij eenmanszaak
is de staffel NIET dwingend → parkeren tot de rechtsvorm-backfill). Voor bevestigde
consumenten: `bik_override` → NULL (systeem rekent dan zelf de staffel). Dry-run + telling
vóór, GO, natelling ná. **Wachter (skill `breed-testen`, de SOORT):** een DB-brede check
`b2c && bik_override > WIK-staffel` die rood valt bij een toekomstige import.

## Taak 2 — V2 handelsrente-rij 1-7-2026
Rij `commercial 2026-07-01 = 10,4%` (Rijksoverheid) ontbreekt; de tabel eindigt bij 10,15%
(1-7-2025). Impact vandaag €0 (alle 7 handelsrente-zaken bevroren vóór 1-7), maar het gat
bijt bij een nieuwe/ontdooide zaak. → Rij toevoegen (data-only, dry-run + GO; check ook
`government`-tarief 1-7-2026). Wachter-kandidaat: actualiteitscheck "nieuwste tarief ouder
dan ~7 mnd → waarschuwing" (tabel wisselt elk halfjaar, niets bewaakt dat nu).

## Taak 3 — V3 auto-concept-poort losmaken
De S222-poortmeting hield de poort DICHT op 6 "zware fouten" — 4 bleken corrector-misser
(zie S229 spoor 4: €40,87/€22,64 waren de échte openstaande bedragen; dossiernummer stond
in het onderwerp). → (a) corrector herkalibreren met drie regels: openstaand bedrag toetsen
aan dossierdata i.p.v. factuur-optelsom; kantoornaam/dossiernummer-uit-onderwerp zijn geen
hallucinaties; terugkoppel-uitnodiging naast expliciet "verplichting blijft" is geen
toezegging. (b) niet-debiteur-mails netjes laten weigeren i.p.v. JSON-crash (4 generatie-
fouten). (c) verse ronde draaien (`scripts/ai/antwoord_testronde.py`, verstuurt niets).
(d) pas dán de menselijke steekproef Lisanne (~10 concepten) → poort AAN. Dit is Fable-werk
(herbeoordeling/kwaliteit); bouw = Opus.

## Taak 4 — V4 .env-rechten (klein)
`/opt/luxis/.env` staat op 644 → `chmod 600` (één commando via SSH). Laag risico, wel doen.

## Onverwerkt uit S228/S227 (zover de tijd reikt, ná V1-V4)
Fysieke-telefoon-check (Arsalan klikt op eigen toestel → restpunten); opmaak-restpunt S227
(screenshot uitvragen, maten in `backend/app/email/incasso_templates.py`); S221b-UX-rest;
DMARC kestinglegal.nl (Arsalan/BaseNet); testdata 2026-00007 t/m -00019 opruimen (na GO).

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail). MAILSLOT OPEN.
Elke prod-mutatie: dry-run/telling + GO + natelling. Geen `git add -A`. Bayar IN100613 niet
aanraken. Kruispunt-check (skill `breed-testen`) bij elk gedeeld effect. KvK: niet naar
vragen/checken — Arsalan komt er zelf op terug. Deploy-race: SSH mét `--force-recreate`
(memory `feedback_deploy_via_ssh`).

## Verificatie
- Backend: relevante `pytest tests/...`, `uvx ruff check app/`.
- Migraties: nieuwe tabel/rij → check tellingen op prod ná.
- CI groen na push (`gh run list`) — vaste afsluitcheck.
- V1/V3: natelling in prod-DB (read-only) dat het effect klopt.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag
sessie-230 + PROMPT-S231; verplaats PROMPT-S228 en ouder naar `docs/archief/prompts/`).
