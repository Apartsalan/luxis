# Sessie 18 — Luxis Bug Fixes + QA

## Repo
`C:\Users\arsal\Documents\luxis`

## Lees bij start
1. `CLAUDE.md` — projectregels, architectuur, werkwijze
2. `SESSION-NOTES.md` — wat er al gedaan is
3. `LUXIS-ROADMAP.md` — source of truth, openstaande bugs staan hier

---

## Stap 0: Deploy BUG-16 + BUG-17

De fixes van vorige sessie zijn gecommit en gepusht maar nog NIET gedeployed. Geef de gebruiker dit deploy commando:

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend
```

Geen migraties nodig — het zijn puur frontend wijzigingen.

---

## Stap 1: Fix 4 openstaande bugs

### BUG-18: Klik op taak navigeert niet naar juiste dossier
**Ernst:** Midden | **Grootte:** S
**Symptoom:** In dashboard "Mijn Taken" widget en op de Mijn Taken pagina (`/taken`), als je op een taak klikt, navigeer je niet naar het bijbehorende dossier.
**Bestanden om te onderzoeken:**
- `frontend/src/app/(dashboard)/page.tsx` — dashboard met taken widget
- `frontend/src/app/(dashboard)/taken/page.tsx` — Mijn Taken pagina
- `frontend/src/hooks/use-workflow.ts` — task hooks, kijk of `case_id` beschikbaar is in task data

**Verwachte fix:** Klik op taak → `router.push(/zaken/${task.case_id})` of vergelijkbaar. Check of de task response een `case_id` bevat en of er een onClick/link handler is.

---

### BUG-19: Factuur aanmaken → "fout bij laden" op factuurpagina
**Ernst:** Hoog | **Grootte:** S-M
**Symptoom:** Na het aanmaken van een factuur word je doorgestuurd naar de factuurdetailpagina, maar die toont "fout bij laden".
**Bestanden om te onderzoeken:**
- `frontend/src/app/(dashboard)/facturatie/nieuw/page.tsx` — het aanmaakformulier, kijk naar redirect na submit
- `frontend/src/app/(dashboard)/facturatie/[id]/page.tsx` — de detailpagina, kijk naar data fetching
- `frontend/src/hooks/use-invoices.ts` — hooks voor create en get invoice
- `backend/app/invoices/router.py` — check of het POST response een `id` bevat dat de frontend kan gebruiken

**Mogelijke oorzaken:**
1. De redirect gebruikt een verkeerd ID (bijv. het hele response object i.p.v. `response.id`)
2. De detail-pagina fetcht op een manier die niet matcht met het URL-pad
3. Het backend response format matcht niet met wat de frontend verwacht

---

### BUG-20: Budget module niet geregistreerd als geldige module
**Ernst:** Hoog | **Grootte:** S
**Symptoom:** Bij instellingen → modules → "budget" aanzetten geeft foutmelding: "Onbekende modules: budget. Geldige opties: incasso, tijdschrijven, facturatie, wwft"
**Bestanden om te onderzoeken:**
- `backend/app/settings/` — zoek waar VALID_MODULES of een vergelijkbare lijst staat
- `backend/app/settings/service.py` of `backend/app/settings/schemas.py` — de validatie die de fout geeft
- Mogelijk `backend/app/settings/router.py`

**Verwachte fix:** Voeg `"budget"` toe aan de lijst van geldige modules in de backend validatie. Het frontend kent de budget module al (zie `frontend/src/hooks/use-modules.ts`), maar de backend weigert het.

---

### BUG-21: Advocaat wederpartij niet zichtbaar na aanmaken dossier
**Ernst:** Midden | **Grootte:** M
**Symptoom:** Bij het aanmaken van een nieuw dossier kun je een advocaat wederpartij invullen, maar na het opslaan is deze niet zichtbaar op de dossierdetailpagina.
**Bestanden om te onderzoeken:**
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — het aanmaakformulier, kijk of opposing_party_lawyer_id wordt meegestuurd
- `backend/app/cases/schemas.py` — kijk of CaseCreate `opposing_party_lawyer_id` accepteert
- `backend/app/cases/service.py` — kijk of het veld wordt opgeslagen in create_case()
- `frontend/src/app/(dashboard)/zaken/[id]/components/DossierSidebar.tsx` — kijk hoe advocaat wederpartij wordt weergegeven
- `frontend/src/app/(dashboard)/zaken/[id]/components/DetailsTab.tsx` — kijk of het veld in view/edit mode staat

**Mogelijke oorzaken:**
1. Frontend stuurt het veld niet mee bij create
2. Backend CaseCreate schema mist het veld
3. Detailpagina leest het veld niet uit de response
4. Het veld heet anders in de API dan in de frontend

---

## Stap 2: Verificatie

Na elke bugfix:
1. `npm run build` in `frontend/` — moet slagen zonder errors
2. Commit + push: `git add . && git commit -m "fix(...): beschrijving" && git push origin main`

Na alle 4 bugs:
3. Geef het deploy commando aan de gebruiker:
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend
```
Voeg `backend` toe als BUG-20 een backend wijziging is (zeer waarschijnlijk). Als er een migratie nodig is, voeg toe:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production exec backend python -m alembic upgrade head
```

## Stap 3: Update docs

Na alle fixes:
- Update `LUXIS-ROADMAP.md` — markeer BUG-18 t/m BUG-21 als ✅ met datum
- Update `SESSION-NOTES.md` — voeg sessie 18 sectie toe met wat er gedaan is

## Stap 4: QA (als er tijd over is)

Als alle bugs gefixt zijn, begin met grondige QA van de hele applicatie via browser:
- Login: `seidony@kestinglegal.nl` / `Hetbaken-KL-5`
- URL: `https://luxis.kestinglegal.nl`
- Test ELKE pagina, ELKE actie, ELKE flow
- Noteer nieuwe bugs in LUXIS-ROADMAP.md
