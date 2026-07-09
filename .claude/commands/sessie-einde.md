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
Update ook de 4 header-regels (laatst bijgewerkt, laatste feature/fix, openstaand, volgende sessie).
**Houd die 4 regels KORT — max 1-2 zinnen per regel.** Alle detail hoort in de sessie-entry, NIET in de kop
(anders groeien ze uit tot alinea's die elke afsluiting traag maken). Verwijs naar de entry voor het detail.

### Archief-regels (VERPLICHT — houden de levende docs klein, sinds 9 juli 2026)
- **SESSION-NOTES.md: max 10 sessie-entries.** Nieuwe entry erbij → verplaats de oudste entry
  VERBATIM naar `docs/archief/SESSION-ARCHIVE.md` (onderaan Blok 2, chronologisch oplopend).
- **Kop = exact de 4 regels.** Géén "Vorige kop"-stapels — de oude kopregel vervalt gewoon
  (die informatie staat al in de sessie-entry).
- **LUXIS-ROADMAP.md: precies één prioriteit-sectie** ("🎯 Huidige prioriteit") en in de intro
  precies één "Laatst bijgewerkt"-regel (géén "Vorige:"-stapels). Afgeronde sprints, audits en
  volgelopen bug-tabellen → `docs/archief/ROADMAP-ARCHIEF.md`. Open punten eerst overnemen in Backlog.
- **Sessieprompts:** na het schrijven van `PROMPT-S(N+1)` → verplaats `PROMPT-S(N-1)` en ouder
  naar `docs/archief/prompts/`.
- **Verplaatsen, nooit verwijderen.** Archiefbestanden niet herformuleren.

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

**VERPLICHT: de eerste INHOUDELIJKE stap van elke prompt is `/sessie-start`.**
Dat commando leest via de researcher-subagent SESSION-NOTES.md + LUXIS-ROADMAP.md, scant de
bestaande modules/pagina's (existence-check-discipline) en laadt de verbindingskaart. Zet dit
dus altijd bovenaan — niet zelf de docs opsommen die `/sessie-start` al leest. Alleen
taak-specifieke extra docs (een plan, een auditrapport) apart benoemen ná `/sessie-start`.

**Daarna het sessie-prompt format:**

```
cd Documents\luxis && claude --dangerously-skip-permissions

Sessie N — [onderwerp]

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): [plan/rapport-bestand, of "geen"].

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
