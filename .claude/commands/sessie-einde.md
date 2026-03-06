Sluit de huidige werksessie af. Dit is VERPLICHT aan het einde van elke sessie.

## Stap 1: Commit + push

- `git status` — check op uncommitted changes
- Commit alle wijzigingen met conventional commit message
- `git push origin main`

## Stap 2: Documentatie bijwerken

### SESSION-NOTES.md
Voeg een nieuwe entry toe BOVENAAN met:
```
## Wat er gedaan is (sessie N — datum) — [onderwerp]
### Samenvatting
- Wat er gebouwd/gefixt is (concrete wijzigingen)
### Gewijzigde bestanden
- Lijst van key bestanden die gewijzigd zijn
### Bekende issues
- Openstaande bugs of issues
### Volgende sessie
- Concrete actie, geen vage plannen
```
Update ook de header-regels (laatst bijgewerkt, laatste feature/fix, openstaande bugs, volgende sessie).

### LUXIS-ROADMAP.md
- Controleer of alle afgeronde features als ✅ staan met datum
- Nieuwe bugs → voeg BUG-# entry toe
- Nieuwe TODO's → voeg toe aan juiste sectie

### Commit docs update
- `git add SESSION-NOTES.md LUXIS-ROADMAP.md && git commit -m "docs: update session notes + roadmap for sessie N"`
- `git push origin main`

## Stap 3: Prompt voor volgende sessie genereren

Gebruik de `luxis-researcher` subagent om LUXIS-ROADMAP.md en SESSION-NOTES.md te lezen voor actuele status.

Genereer een COMPLETE prompt die de volgende Claude kan copy-pasten. Format:

```
Repo: C:\Users\arsal\Documents\luxis

## Bestanden lezen bij start
Gebruik de `luxis-researcher` subagent om te lezen:
- LUXIS-ROADMAP.md (status + planning)
- SESSION-NOTES.md (laatste 2 sessies)
- [andere relevante docs voor de taak]

## Context
- Sessienummer en datum laatste sessie
- Huidige teststatus (backend tests, E2E tests, ruff)
- Wat er in de vorige sessie is afgerond
- Bekende issues

## Taak
[Concrete beschrijving van wat de volgende sessie moet doen]
[Betrokken bestanden met paden]
[Bekende bugs/context relevant voor de taak]

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -v`
- Lint: `docker compose exec backend ruff check app/`
- E2E: `cd frontend && npx playwright test`
- Build: `cd frontend && npm run build`

## Commit-instructies
Na afronding: commit + push naar main met conventional commit message.
```

De prompt moet LEAN zijn (<50KB met gevraagde bestanden). Verwijs naar docs/ bestanden i.p.v. alles in de prompt te zetten.

## Stap 4: Deploy-commando

Als er iets gedeployd moet worden, geef het commando:
```
cd /opt/luxis && git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache [services] && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d [services]
```
Vermeld: welke services (frontend/backend/beide), en of er migraties nodig zijn.

## Stap 5: Samenvatting

Geef de gebruiker een korte samenvatting:
- Wat er gedaan is
- Of er gedeployd moet worden
- Link naar de volgende sessie-prompt hierboven
