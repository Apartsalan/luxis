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

Genereer een COMPLETE prompt die de volgende Claude kan copy-pasten.

**VERPLICHT: Prompt begint ALTIJD met het opstart-commando:**
```
cd Documents\luxis && claude --dangerously-skip-permissions
```
Dit is de eerste regel van elke sessie-prompt. De gebruiker kopieert dit in PowerShell om Claude Code te openen met permission bypass.

**Daarna het sessie-prompt format:**

```
cd Documents\luxis && claude --dangerously-skip-permissions

Sessie N — [onderwerp]

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie [relevant]) en SESSION-NOTES.md (sessie N-1). Geef compacte samenvatting."

## Taak
[Concrete beschrijving — wat moet er gebouwd/gefixt worden]
[Startpunt: welk bestand/functie, maar ALLEEN als het niet obvious is]

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -v`
- Lint: `docker compose exec backend ruff check app/`
- Build: `cd frontend && npm run build`

## Constraints (wat NIET doen)
[Expliciet benoemen wat buiten scope is]

## Commit
Commit + push naar main met conventional commit message. Deploy automatisch via SSH.
```

De prompt moet LEAN zijn (<50KB). Verwijs naar docs/ bestanden i.p.v. alles erin te zetten.

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
