# Sessie 24 — Incasso Workflow P1 vervolg

> **LEES ALLEEN DIT BESTAND.** Alle benodigde context staat hieronder. Lees NIET `LUXIS-ROADMAP.md` of `SESSION-NOTES.md` — te groot, verspilt context.

## Project in het kort

- **Luxis** = praktijkmanagementsysteem voor Kesting Legal (1 advocaat, incasso/insolventie, Amsterdam)
- **Stack:** FastAPI (Python 3.12) + Next.js 15 + PostgreSQL 16 + Docker Compose
- **Productie:** https://luxis.kestinglegal.nl — VPS op `/opt/luxis`
- **Taal:** Nederlandse UI, Engelse code. Geen i18n framework.
- **Auth:** JWT (python-jose + bcrypt). Login: arsal@kestinglegal.nl
- **Financial precision:** Altijd `Decimal` + `NUMERIC(15,2)`, nooit float
- **Multi-tenant:** `TenantBase` + `tenant_id` op alles

## Architectuur snel-referentie

- **Backend:** `backend/app/` — routers in `*/router.py`, services in `*/service.py`, models in `*/models.py`, schemas in `*/schemas.py`
- **Frontend:** `frontend/src/app/(dashboard)/` — Next.js App Router, hooks in `frontend/src/hooks/`
- **Migraties:** `backend/alembic/versions/` — nummering: `033_...`, `034_...` etc.
- **Config:** `backend/app/config.py` — pydantic BaseSettings, leest env vars
- **Templates:** `templates/` dir (docx bestanden voor documentgeneratie)
- **Documenten service:** `backend/app/documents/docx_service.py` — docxtpl rendering

## Wat er vorige sessie (23) gebouwd is

✅ **Stap 5+6 van P1 incasso workflow:**
- `max_wait_days` kolom op `IncassoPipelineStep` (migratie 033)
- `_compute_deadline_status()` in `backend/app/incasso/service.py` — groen/oranje/rood/grijs
- Frontend: "Min. dagen" + "Grens rood" kolommen in Stappen-tab, gekleurde bolletjes in Werkstroom-tab

## Wat deze sessie moet doen

### Prioriteit 1: Fix dossier-toewijzing aan pipeline stappen

**Probleem:** Dossiers in de "Nog niet toegewezen" sectie van de pipeline kunnen niet naar een stap verplaatst worden. De "Stap wijzigen" batch-actie toont "0 gereed" voor ongeassigneerde dossiers.

**Gewenste flow:**
1. In de "Nog niet toegewezen" sectie: dossiers selecteren met checkboxes
2. "Stap wijzigen" → dropdown toont alle stappen → dossiers worden naar gekozen stap verplaatst
3. De `auto_assign_step` flag in `BatchActionRequest` bestaat al maar wordt mogelijk niet goed gebruikt

**Bestanden:**
- `backend/app/incasso/service.py` — `batch_execute()` en `batch_preview()` functies
- `backend/app/incasso/schemas.py` — `BatchActionRequest`, `BatchPreviewResponse`
- `frontend/src/app/(dashboard)/incasso/page.tsx` — `PreFlightDialog` en `WerkstroomTab`
- `frontend/src/hooks/use-incasso.ts` — `useBatchPreview` en `useBatchExecute`

### Prioriteit 2: Template Editor UI (stap 1 van P1)

**Wat:** Lisanne kan DOCX-briefsjablonen uploaden en beheren. Geen WYSIWYG — ze bewerkt in Word en uploadt naar Luxis.

**Backend (nieuw):**
- Model: `ManagedTemplate` in `backend/app/documents/models.py`
  - `id`, `tenant_id`, `name`, `description`, `template_key`, `file_data` (LargeBinary), `filename`, `is_builtin`, `is_active`, timestamps
- Endpoints in `backend/app/documents/router.py`:
  - `POST /api/documents/templates/upload` — Upload .docx
  - `GET /api/documents/templates` — Lijst
  - `PUT /api/documents/templates/{id}` — Update metadata
  - `DELETE /api/documents/templates/{id}` — Verwijder
  - `GET /api/documents/templates/{id}/preview/{case_id}` — Preview met echte data
- `docx_service.py` aanpassen: check eerst `ManagedTemplate` tabel, fallback naar disk

**Frontend (nieuw):**
- Pagina: `frontend/src/app/(dashboard)/instellingen/templates/page.tsx`
  - Lijst, upload (drag & drop), preview, download, bewerken, verwijderen
  - Badge: "Ingebouwd" vs "Aangepast"
- Hook: `frontend/src/hooks/use-templates.ts`
- Pipeline stappen-tab: template-koppeling per stap

## Deploy-instructies (KRITISCH — lees dit!)

```bash
# SSH naar VPS, dan:
cd /opt/luxis && git pull

# Als er Alembic migraties zijn (ALTIJD `run`, niet `exec`):
docker compose run --rm backend python -m alembic upgrade head

# Rebuild + restart:
docker compose build --no-cache backend frontend
docker compose up -d
```

**COMPOSE_FILE** staat al in `.env` → gewoon `docker compose` werkt (pakt automatisch prod override).

## Fouten uit het verleden — VOORKOM DEZE

1. **NOOIT `localhost:8000` in frontend code** — altijd relatieve URLs (`""`). Next.js rewrite proxy `/api/*` → `backend:8000`.
2. **POSTGRES_PASSWORD werkt alleen bij eerste volume-init** — later wijzigen? → `docker compose exec db psql -U luxis -d luxis -c "ALTER USER luxis PASSWORD '...';"` + restart backend.
3. **Alembic: gebruik `run` niet `exec`** als backend crashed: `docker compose run --rm backend python -m alembic upgrade head`
4. **Frontend build MOET slagen** voordat je commit: `cd frontend && npm run build`
5. **Backend lint check:** `cd backend && ruff check app/`
6. **Nooit float voor geld** — altijd `Decimal` + `NUMERIC(15,2)`
7. **Exclude_unset bug:** Bij PATCH/PUT: gebruik `value if value else None` NIET `value || undefined`. Lege strings moeten als `null` naar backend.
8. **SQLAlchemy async:** Nested relaties laden vereist explicit `selectinload().selectinload()` — lazy loading werkt niet async.
9. **Commit message format:** `feat:`, `fix:`, `docs:` prefix. Eindig met `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

## P1 Incasso Workflow — totaal overzicht

| # | Feature | Status |
|---|---------|--------|
| 1 | Template editor UI | ❌ Deze sessie (prio 2) |
| 2 | Batch brief + email verzenden | ❌ Toekomstig |
| 3 | Auto-complete taken | ❌ Toekomstig |
| 4 | Auto-advance pipeline | ❌ Toekomstig |
| 5 | Deadline kleuren per stap | ✅ Sessie 23 |
| 6 | Instelbare dagen per stap | ✅ Sessie 23 |
