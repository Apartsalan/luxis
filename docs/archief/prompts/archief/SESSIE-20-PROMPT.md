# Sessie 20 — Luxis QA via Browser + Bugfixes

## Repo
`C:\Users\arsal\Documents\luxis`

## Lees bij start (in deze volgorde)
1. `CLAUDE.md` — projectregels, architectuur, werkwijze
2. `SESSION-NOTES.md` — wat er gedaan is (t/m sessie 19)
3. `LUXIS-ROADMAP.md` — source of truth, alle bugs + features
4. `QA-CHECKLIST.md` — volledige testlijst (alles nog `[ ]`)

---

## Stap 0: Deploy sessie 18+19 fixes

Sessie 18 (BUG-18 t/m BUG-21) en sessie 19 (advocaat wederpartij: inline aanmaken, auto ContactLink, CaseParty filter) zijn gepusht maar mogelijk nog niet gedeployed. Vraag de gebruiker of dit al gedeployed is. Zo niet, geef dit commando:

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend
```

Frontend EN backend — beide zijn gewijzigd. Geen migraties nodig.

---

## Stap 1: QA — Volledige applicatie testen via browser

**URL:** `https://luxis.kestinglegal.nl`
**Login:** `seidony@kestinglegal.nl` / `Hetbaken-KL-5`

Loop `QA-CHECKLIST.md` systematisch af. Test ELKE sectie (14 secties).

### Specifiek verifiëren (sessie 18+19 fixes):
- **BUG-18:** Klik op taak in dashboard/Mijn Taken → navigeert naar dossier
- **BUG-19:** Factuur aanmaken → GEEN "fout bij laden" meer
- **BUG-20:** Instellingen → Modules → budget aan/uitzetten werkt
- **BUG-21:** Nieuw dossier met budget + advocaat wederpartij → beide zichtbaar na aanmaken
- **Sessie 19:** Nieuw dossier → advocaat wederpartij inline aanmaken werkt
- **Sessie 19:** Advocaat wederpartij relatiepagina → gelinkte dossiers zichtbaar
- **Sessie 19:** Advocaat wederpartij relatiepagina → gelinkte bedrijven zichtbaar (als nieuw dossier aangemaakt met wederpartij=bedrijf)

### Hoe te testen
- Gebruik browser tools (Playwright / Claude in Chrome) om naar de URL te navigeren
- Neem screenshots bij elke pagina/sectie
- Bij een gevonden bug: noteer pagina, stappen, verwacht vs. werkelijk, ernst
- Update `QA-CHECKLIST.md` live: `[x]` voor geslaagd, `[BUG-XX]` voor bugs

---

## Stap 2: Bugs fixen

Elk gevonden bug direct fixen als het kan (S of M grootte). Per bug:

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

Na alle fixes:

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
- Update `LUXIS-ROADMAP.md` — nieuwe bugs toevoegen met status
- Update `SESSION-NOTES.md` — voeg sessie 20 sectie toe
- Update `QA-CHECKLIST.md` — vink alles af dat getest is

---

## Belangrijk

- **Werk zelfstandig** — fix alle gevonden bugs, build, commit, push, update docs
- **Commit conventie:** `fix(module): korte beschrijving` in het Engels
- **Push na elke commit** — `git push origin main`
- **Alleen specifieke bestanden toevoegen** — geen `git add .`
- **Frontend build moet slagen** voordat je commit
- **Geef deploy commando** na de laatste commit

## Context: Alle bugs t/m sessie 19

| Bug | Status |
|-----|--------|
| BUG-1 t/m BUG-21 | ✅ Allemaal gefixt |
| Inline advocaat aanmaken | ✅ Sessie 19 |
| Auto ContactLink advocaat-bedrijf | ✅ Sessie 19 |
| CaseParty filter in list_cases | ✅ Sessie 19 |

**Alle 21 bugs + 3 features zijn gefixt. Sessie 20 is puur QA: alles testen, nieuwe bugs vinden en fixen.**
