Sessie 76 — QA P1 bugfixes + test data cleanup
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Bekende Bugs' en 'Uitrolplan') en SESSION-NOTES.md (sessie 75). Geef compacte samenvatting van open bugs en wat er in sessie 75 gedaan is."

## Taak
Fix de open bugs uit QA sessie 75. Prioriteit: P1 eerst, dan P2. Referentie: `docs/qa/QA-SESSIE75.md`.

### P1 bugs (fix deze sessie):

1. **BUG-44: API call op login pagina voor auth check (401 in console)**
   - Login pagina doet een API call naar `/api/cases?page=1&per_page=20` voordat de gebruiker is ingelogd
   - Waarschijnlijk een component dat data probeert te laden voordat auth check compleet is
   - Fix: zorg dat data-fetching hooks niet triggeren op de login pagina, of voeg auth-guard toe

2. **BUG-45: AI-parsed partijnamen worden niet gematcht met bestaande contacten**
   - Na AI factuur parsing worden partijnamen als zoektekst in het veld gezet, maar triggeren geen match
   - Gebruiker moet handmatig wissen en opnieuw zoeken
   - Fix: na AI parsing, automatisch zoeken in bestaande contacten en beste match selecteren, of "Nieuwe relatie aanmaken" knop aanbieden

3. **BUG-46: case_id URL parameter vult formuliervelden niet visueel in op factuurpagina**
   - Navigeren naar nieuwe factuur met `?case_id=X` linkt het dossier correct, maar velden lijken leeg
   - Fix: pre-fill de Relatie en Dossier velden visueel wanneer case_id aanwezig is

4. **BUG-48: Stale validatiefout na succesvolle client selectie**
   - "Selecteer een client" error blijft zichtbaar nadat client WEL is geselecteerd
   - Fix: clear validation error wanneer een waarde wordt geselecteerd

### P2 bugs (fix als tijd over is):

5. **BUG-47: "Vordering(optioneel)" spatie ontbreekt**
   - In de step indicator van de wizard. Moet zijn: "Vordering (optioneel)"
   - Simpele tekst fix

6. **BUG-49: Week range off-by-one in urenregistratie**
   - Toont "15 mrt — 19 mrt 2026" maar moet "16 mrt — 20 mrt 2026" zijn
   - Bug zit in de weekrange berekening

7. **BUG-50: favicon.ico 404**
   - Geen favicon aanwezig, geeft 404 in console
   - Voeg een favicon toe (Luxis logo of generiek)

### Extra: Test data cleanup
- Verwijder rommel-relaties ("dsaas", "poephoofd", "looo", etc.) via de API of direct in de database
- Dit is voor demo-voorbereiding

## Verificatie
- Na elke fix: test via Playwright op productie (https://luxis.kestinglegal.nl)
- `docker compose exec backend ruff check app/` — geen lint errors
- Frontend build: `docker compose exec frontend npm run build` — geen build errors
- Referentie screenshots in `docs/qa/QA-SESSIE75.md` voor verwacht gedrag

## Constraints (wat NIET doen)
- Geen nieuwe features bouwen
- Geen refactors
- Geen worktrees
- Focus op bugfixes uit de QA lijst, niets meer

## Commit
Na alle fixes: commit + push met `fix(qa): resolve P1/P2 bugs from QA session 75`
Deploy via SSH: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build --no-cache frontend backend && docker compose up -d"`
Update LUXIS-ROADMAP.md met gefixte bugs (markeer als done).
