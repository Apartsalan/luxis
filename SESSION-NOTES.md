# Sessie Notities — Luxis

**Laatst bijgewerkt:** 27 feb 2026 (sessie 25 — Incasso Workflow P1: auto-complete + auto-advance)
**Laatste feature/fix:** Auto-complete taken na document generatie + auto-advance pipeline naar volgende stap.
**Volgende sessie (26):** QA van incasso pipeline flow (taken aanmaken, auto-complete, auto-advance). VPS disk space opgelost (55GB vrij na prune).

## Wat er gedaan is (sessie 25 — 27 feb) — Auto-complete taken + Auto-advance pipeline

### P1 item 3: Auto-complete taken ✅
- Na batch "Document genereren": open taken van type `generate_document`/`send_letter` worden automatisch als voltooid gemarkeerd
- Zoekt op `task_type IN (generate_document, send_letter)` + `status IN (pending, due, overdue)`

### P1 item 4: Auto-advance pipeline ✅
- Na auto-complete: als ALLE open taken voor een dossier klaar zijn, schuift pipeline automatisch door naar volgende stap
- Volgende stap bepaald via `sort_order` (bestaande `list_pipeline_steps`)
- Nieuwe taak wordt aangemaakt voor de nieuwe stap (generate_document of manual_review)
- CaseActivity audit trail logging bij elke auto-advance

### Taken aanmaken bij stap-toewijzing ✅
- Bij batch "Stap wijzigen": automatisch taak aangemaakt voor de target stap
- Stap met `template_type` → task type `generate_document`
- Stap zonder `template_type` → task type `manual_review`
- Due date = vandaag + `min_wait_days`

### VPS disk space issue
- 144GB/150GB vol → PostgreSQL kon niet starten (postmaster.pid write failure)
- `docker system prune -a --volumes -f` → 55GB vrijgemaakt (90GB/150GB)
- Rebuild succesvol gestart, niet geverifieerd (sessie beëindigd)

### Gewijzigde bestanden
- `backend/app/incasso/service.py` — 3 nieuwe helpers (`_create_tasks_for_step`, `_auto_complete_tasks`, `_try_auto_advance`) + wiring in `batch_execute()`
- `backend/app/incasso/schemas.py` — `tasks_auto_completed` + `cases_auto_advanced` op `BatchActionResult`
- `frontend/src/hooks/use-incasso.ts` — TypeScript interface update
- `frontend/src/app/(dashboard)/incasso/page.tsx` — toast message met nieuwe counters
- `LUXIS-ROADMAP.md` — P1 items 3+4 als ✅

### Openstaande issues
- Gebruiker meldt "het werkt nog niet helemaal goed" → QA nodig in sessie 26
- VPS deploy niet geverifieerd (rebuild was gaande bij sessie-einde)

---

## Wat er gedaan is (sessie 23 — 27 feb) — Incasso Workflow Automatisering P1

### Stap 1: Instelbare dagen per stap (max_wait_days) ✅
- **Backend:** `max_wait_days` kolom toegevoegd aan `IncassoPipelineStep` model
- **Alembic migratie:** `033_incasso_max_wait_days.py` — `ADD COLUMN max_wait_days INTEGER NOT NULL DEFAULT 0`
- **Schemas:** `max_wait_days` toegevoegd aan Create/Update/Response schemas
- **Service:** `seed_default_steps()` bijgewerkt met standaard max_wait_days waarden (7, 28, 28, 28, 28, 0)
- **Frontend Stappen-tab:** "Wachtdagen" kolom gesplitst in "Min. dagen" en "Grens rood", beide bewerkbaar

### Stap 2: Deadline kleuren per stap ✅
- **Backend logica:** Nieuwe `_compute_deadline_status()` functie:
  - Groen = `days_in_step < min_wait_days` (wachtperiode)
  - Oranje = `days_in_step >= min_wait_days` (klaar voor actie)
  - Rood = `days_in_step >= max_wait_days` (te laat)
  - Grijs = geen stap toegewezen
- **Schema:** `deadline_status: str` (green/orange/red/gray) toegevoegd aan `CaseInPipeline`
- **Frontend Werkstroom-tab:** Gekleurd bolletje naast dossiernummer + gekleurde "Dagen" tekst

### Deploy-problemen opgelost
- **COMPOSE_FILE ontbrak:** VPS draaide `docker compose up -d` zonder prod override → backend kreeg dev-wachtwoord. Fix: `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml` toegevoegd aan `/opt/luxis/.env`
- **PostgreSQL wachtwoord mismatch:** Volume was geïnitialiseerd met `luxis_dev_password`, maar prod config verwachtte `Kest1ngLux1s2026prod`. Fix: `ALTER USER luxis PASSWORD '...'` via psql
- **Alembic migratie 033:** Succesvol uitgevoerd op productie via `docker compose run --rm backend python -m alembic upgrade head`

### Bekend issue (niet opgelost)
- **Dossiers toewijzen aan pipeline stappen:** Gebruiker kan geen dossier handmatig aan een stap toewijzen vanuit de pipeline view. De "Stap wijzigen" functie toont 0 gereed als er geen dossiers in stappen staan. **→ Fix nodig in sessie 24**

### Gewijzigde bestanden
- `backend/app/incasso/models.py` — `max_wait_days` kolom
- `backend/app/incasso/schemas.py` — `max_wait_days` + `deadline_status`
- `backend/app/incasso/service.py` — `_compute_deadline_status()`, `_case_to_pipeline_item()`, `step_to_response()`, `seed_default_steps()`
- `backend/alembic/versions/033_incasso_max_wait_days.py` — nieuwe migratie
- `frontend/src/hooks/use-incasso.ts` — `DeadlineStatus` type, `max_wait_days` in interfaces
- `frontend/src/app/(dashboard)/incasso/page.tsx` — deadline kleuren UI + max_wait_days kolommen

---

## Wat er gedaan is (sessie 22b — 27 feb) — Deploy & Verificatie

### BUG-25/26/27 gedeployed en geverifieerd op productie ✅
- **BUG-25** (timer z-index): Timer FAB zichtbaar met z-50 > header z-40 ✅
- **BUG-26** (relaties dropdown): Alle 12 relaties laden met correcte namen ✅
- **BUG-27** (Nederlandse 404): "Pagina niet gevonden" toont correct ✅

### Deploy-blokkeerder 1: Database authenticatie ✅
- Backend Docker image had `DATABASE_URL` met dev-wachtwoord gebakken → `ALTER USER` + `--force-recreate`

### Deploy-blokkeerder 2: Frontend localhost:8000 hardcoded ✅
- 9 bestanden hadden `localhost:8000` fallback → allemaal `""` + pre-commit hook

### BUG-26 extra fix: "undefined undefined" → `{r.name}`
- Commit: `ad1f31c` + `eafc513`

### Status na sessie 22b
- **Alle bugs gedeployed en geverifieerd op productie** — BUG-1 t/m BUG-27 allemaal ✅
- Applicatie draait stabiel op https://luxis.kestinglegal.nl
- Klaar voor feature development

---

## Wat er gedaan is (sessie 22 — 27 feb)

### Volledige QA Testing secties 1-10 via Playwright MCP ✅
- **75 tests uitgevoerd, 75 PASS, 0 FAIL, 0 nieuwe bugs**
- Resultaten: `docs/qa/QA-SESSIE-22-RESULTATEN.md`

### BUG-25/26/27 gefixt
- BUG-25: Timer z-index 40→50 (`floating-timer.tsx`)
- BUG-26: Backend per_page limit 100→200 (`relations/router.py`)
- BUG-27: Custom `not-found.tsx` met Nederlandse tekst

### Commits sessie 22

| Hash | Beschrijving |
|------|-------------|
| `07b487b` | docs: QA session 22 results — 75/75 tests PASS, 0 new bugs |
| `3cd9ddc` | fix: BUG-25/26/27 — timer z-index, relations 422, Dutch 404 page |
| `ad1f31c` | fix: use r.name for relations dropdown in agenda |
| `eafc513` | fix: remove hardcoded localhost:8000 from all frontend files |

---

> **Eerdere sessies (1-20)** staan in `docs/sessions/SESSION-ARCHIVE.md` — alleen lezen als je historische context nodig hebt.
