# Sessie 23 — Incasso Workflow Automatisering (P1)

## Project: Luxis (praktijkmanagementsysteem)
- **Tech:** FastAPI + Next.js 15 + PostgreSQL + Docker
- **Code:** `C:\Users\arsal\Documents\luxis\`
- **Productie:** https://luxis.kestinglegal.nl
- **Login:** seidony@kestinglegal.nl / Hetbaken-KL-5

## Lees bij start
1. `CLAUDE.md` (wordt automatisch geladen)
2. `SESSION-NOTES.md` — recente sessies, huidige status
3. `LUXIS-ROADMAP.md` sectie "Incasso Workflow Automatisering (P1)" — de volledige feature-beschrijving

## Status
- **Alle 27 bugs zijn opgelost en geverifieerd op productie** (BUG-1 t/m BUG-27)
- Applicatie draait stabiel op productie
- Klaar voor feature development

## Jouw taak: Incasso Workflow Automatisering (P1)

**Doel:** Eén klik op "Verstuur brief" voor 40 dossiers tegelijk → brief genereren + emailen + taak afvinken + pipeline doorschuiven. Alles automatisch.

### De 6 sub-features (in volgorde):

1. **Template editor UI** — Lisanne kan zelf briefsjablonen bewerken in de UI (huisstijl, logo, kleuren). Eenmalig instellen, daarna herbruikbaar.
2. **Batch brief + email verzenden** — "Verstuur brief" genereert documenten EN emailt ze naar de wederpartij via Outlook SMTP. Nu is er alleen documentgeneratie per stuk.
3. **Auto-complete taken** — Na verzenden brief: bijbehorende workflow-taak automatisch afvinken.
4. **Auto-advance pipeline** — Na taak afgerond: pipeline schuift automatisch naar volgende stap, volgende taak + deadline wordt actief.
5. **Deadline kleuren per stap** — Groen = op tijd, Rood = te laat. Per stap zichtbaar in het pipeline-overzicht.
6. **Instelbare dagen per stap** — Wachtdagen per pipeline-stap configureerbaar (bestaat deels al via `min_wait_days`).

### Bestaande code om te bekijken:
- `backend/app/workflow/` — workflow rules, taken, status transities, scheduler
- `backend/app/documents/` — template management, document generatie (docxtpl + WeasyPrint)
- `backend/app/incasso/` — claims, pipeline, betalingen
- `frontend/src/app/(dashboard)/zaken/[id]/components/` — dossier detail tabs
- `frontend/src/app/(dashboard)/incasso/` — incasso pipeline UI
- `frontend/src/hooks/use-email-sync.ts` — email verzending (SMTP al werkend)

### Werkwijze (VERPLICHT per CLAUDE.md):
1. **Onderzoek eerst** — zoek hoe Clio, Basenet, Legalsense batch brief+email afhandelen
2. **Plan Mode** — `EnterPlanMode` gebruiken, plan presenteren aan gebruiker
3. **Na goedkeuring** pas bouwen
4. **Na bouwen** verifiëren via Playwright op productie

## Deploy (voor gebruiker op VPS):
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend backend
```

Als er migraties zijn:
```bash
docker compose exec backend python -m alembic upgrade head
```

## LEES GEEN andere bestanden tenzij je ze echt nodig hebt.
