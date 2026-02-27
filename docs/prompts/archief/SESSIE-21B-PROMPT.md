# Sessie 21B — QA Vervolg

## Project: Luxis (praktijkmanagementsysteem)
- **Tech:** FastAPI + Next.js 15 + PostgreSQL
- **Code:** `C:\Users\arsal\Documents\luxis\`
- **Productie:** https://luxis.kestinglegal.nl
- **Login:** seidony@kestinglegal.nl / Hetbaken-KL-5

## Wat al getest is (sessie 21A)
Uren (6 PASS), Facturen (9 PASS), Documenten (3 PASS). Bug gevonden: BUG-25 (timer FAB z-index overlap). Details: `QA-SESSIE-21A-RESULTATEN.md`

## Jouw taak: Test deze 20 items via Playwright MCP

**BELANGRIJK: Alleen bugs NOTEREN in `QA-SESSIE-21B-RESULTATEN.md`, NIET fixen!**

### Tests:
1. Document preview: dossier → Documenten tab → 👁 knop → PDF modal
2. Agenda /agenda: laadt, navigeren weken/maanden, events zichtbaar, event aanmaken
3. Instellingen /instellingen: kantoorgegevens laden+opslaan, e-mail tab, modules toggles, module aan/uit → sidebar wijzigt
4. Keyboard shortcuts op dossierdetail: 1-9 tabs, T timer, N notitie, niet actief in inputs
5. Cross-cutting: page refresh, empty states, loading spinners, toasts, console errors, 404 pagina

### Tips om context te sparen:
- Gebruik `browser_snapshot` (niet screenshot)
- Ga snel door, noteer resultaat direct
- Geen code-analyse — alleen testen

## Deploy (voor gebruiker op VPS):
```bash
cd /opt/luxis && git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend backend
```

## Lees GEEN andere bestanden tenzij je ze echt nodig hebt voor een test.
