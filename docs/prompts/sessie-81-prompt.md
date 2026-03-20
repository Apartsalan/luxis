Sessie 81 — Microsoft Clarity + UX-TODO items
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie UX-TODO en Demo Feedback) en SESSION-NOTES.md (sessie 80b en 80). Geef compacte samenvatting."

## Taak

### 1. Microsoft Clarity toevoegen aan frontend
- Ga naar clarity.microsoft.com en maak een project aan voor luxis.kestinglegal.nl (of vraag de gebruiker om het project ID als hij dat al heeft)
- Voeg het Clarity script toe aan de Next.js frontend (`frontend/src/app/layout.tsx` of via `next/script`)
- Deploy naar productie

### 2. UX-TODO items afwerken (kleine verbeteringen)
- **UX-TODO-9:** Relaties lijst type-kolom sorteerbaar maken
- **UX-TODO-10:** Factuur verwijder-knop per regel
- **UX-TODO-11:** Dossier "Hoofdsom" card toont 0,00 op lijstpagina (detail is al gefixt)
- **UX-TODO-12:** Dossier overzicht rente/partijen cards nemen te veel ruimte
- **UX-TODO-13:** Testdata opruimen (E2E debug relaties, E2E test taken)

### 3. Optioneel (als er tijd over is)
- Basenet feature gap analyse voorbereiden als checklist voor gesprek met Lisanne

## Verificatie
- `docker compose exec backend pytest tests/ -v` (bij backend wijzigingen)
- `docker compose exec backend ruff check app/`
- Frontend build check via deploy
- Clarity: check of tracking script laadt op luxis.kestinglegal.nl

## Constraints (wat NIET doen)
- Geen nieuwe features bouwen
- Geen worktrees
- Geen refactors
- DF-05/DF-11/DF-13 NIET oppakken — die wachten op overleg met Lisanne

## Commit
Commit + push na elke afgeronde taak. Deploy automatisch via SSH.
