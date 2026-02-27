# Sessie 19 — Luxis QA via Browser + Bugfixes

## Repo
`C:\Users\arsal\Documents\luxis`

## Lees bij start (in deze volgorde)
1. `CLAUDE.md` — projectregels, architectuur, werkwijze
2. `SESSION-NOTES.md` — wat er gedaan is (t/m sessie 18)
3. `LUXIS-ROADMAP.md` — source of truth, alle bugs + features
4. `QA-CHECKLIST.md` — volledige testlijst (alles nog `[ ]`)

---

## Stap 0: Deploy sessie 18 hotfix

De laatste commit (fix: missing fields in `create_case` + `selectinload` voor `parties→contact`) is gepusht maar mogelijk nog niet gedeployed. Vraag de gebruiker of dit al gedeployed is. Zo niet, geef dit commando:

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d backend
```

Alleen backend — frontend is niet gewijzigd in de laatste commit.

---

## Stap 1: QA — Volledige applicatie testen via browser

**URL:** `https://luxis.kestinglegal.nl`
**Login:** `seidony@kestinglegal.nl` / `Hetbaken-KL-5`

Loop `QA-CHECKLIST.md` systematisch af. Test ELKE sectie:

1. **Login & Authenticatie** (sectie 1)
2. **Dashboard** (sectie 2) — inclusief BUG-16/18 fixes verifiëren
3. **Relaties** (sectie 3) — CRUD + veld wissen (BUG-17 fix)
4. **Dossiers** (sectie 4) — BELANGRIJK:
   - Nieuw dossier aanmaken met budget + advocaat wederpartij → verifieer BUG-21 fix
   - Detail sidebar: budget progress bar, advocaat wederpartij zichtbaar?
   - Bewerken + opslaan + veld wissen
   - Alle tabs: Overzicht, Procesgegevens, Partijen, Taken, Correspondentie, Documenten, Vorderingen, Betalingen, Financieel, Facturen
5. **Mijn Taken** (sectie 5) — klik navigeert naar dossier (BUG-18)
6. **Correspondentie** (sectie 6) — ongesorteerde email wachtrij
7. **Incasso** (sectie 7) — pipeline + smart work queue + batch acties
8. **Uren** (sectie 8)
9. **Facturen** (sectie 9) — aanmaken zonder "fout bij laden" (BUG-19)
10. **Documenten** (sectie 10)
11. **Agenda** (sectie 11)
12. **Instellingen** (sectie 12) — modules toggles inclusief budget (BUG-20)
13. **Keyboard shortcuts** (sectie 13)
14. **Cross-cutting checks** (sectie 14)

### Hoe te testen
- Gebruik de browser tools (Playwright / Claude in Chrome) om naar de URL te navigeren, in te loggen, en elke pagina/actie te testen
- Neem screenshots bij elke pagina/sectie
- Bij een gevonden bug: noteer pagina, stappen om te reproduceren, verwacht vs. werkelijk gedrag, ernst
- Update `QA-CHECKLIST.md` live: `[x]` voor geslaagd, `[BUG-XX]` voor gevonden bugs

---

## Stap 2: Bugs fixen

Elk gevonden bug direct fixen als het kan (S of M grootte). Werkwijze per bug:

1. Analyseer root cause (lees relevante bestanden)
2. Implementeer fix
3. `npm run build` in `frontend/` (als frontend gewijzigd)
4. Commit + push:
   ```bash
   git add <specifieke bestanden> && git commit -m "fix(...): beschrijving" && git push origin main
   ```
5. Noteer in `QA-CHECKLIST.md` tabel "Gevonden bugs"

---

## Stap 3: Deploy

Na alle fixes, geef deploy commando:

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend
```

Voeg migratie toe als er schema-wijzigingen zijn:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production exec backend python -m alembic upgrade head
```

---

## Stap 4: Update docs

Na alle fixes:
- Update `LUXIS-ROADMAP.md` — nieuwe bugs toevoegen met status ✅ als gefixt
- Update `SESSION-NOTES.md` — voeg sessie 19 sectie toe
- Update `QA-CHECKLIST.md` — vink alles af dat getest is

---

## Belangrijk

- **Werk zelfstandig** — fix alle gevonden bugs, build, commit, push, update docs
- **Commit conventie:** `fix(module): korte beschrijving` in het Engels
- **Push na elke commit** — `git push origin main`
- **Alleen specifieke bestanden toevoegen** — geen `git add .`
- **Frontend build moet slagen** voordat je commit
- **Geef deploy commando** na de laatste commit

## Context: Wat er al gefixt is (ter referentie)

| Bug | Beschrijving | Status |
|-----|-------------|--------|
| BUG-1 t/m BUG-3 | Relatie koppeling, rente-velden, renteberekening | ✅ |
| BUG-6 t/m BUG-12 | Conflict check, edit mode, advocaat wederpartij, taken | ✅ |
| BUG-13 | Email-bijlage download 401 → blob URL | ✅ |
| BUG-14 | Bijlage opslaan in dossier | ✅ |
| BUG-15 | Reset-password → Next.js rewrite proxy | ✅ |
| BUG-16 | Dashboard taken widget → correct endpoint | ✅ |
| BUG-17 | Veld wissen → `\|\| null` i.p.v. `\|\| undefined` (51 instances) | ✅ |
| BUG-18 | Taak klik → Link naar dossier | ✅ |
| BUG-19 | Factuur aanmaken → explicit commit + cache pre-populate | ✅ |
| BUG-20 | Budget module → VALID_MODULES | ✅ |
| BUG-21 | Advocaat wederpartij + budget → selectinload + missing fields | ✅ |

**Alle 21 bugs zijn gefixt. Sessie 19 is puur QA: alles testen, nieuwe bugs vinden en fixen.**
