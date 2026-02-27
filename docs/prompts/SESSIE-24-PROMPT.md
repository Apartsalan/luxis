# Sessie 24 — Incasso Workflow P1 vervolg: Dossier-toewijzing fix + Template Editor UI

## Context

Luxis is het praktijkmanagementsysteem van Kesting Legal. Sessie 23 heeft **stap 1+2** van de P1 incasso workflow gebouwd:
- ✅ Instelbare dagen per stap (`max_wait_days` kolom + "Min. dagen" / "Grens rood" UI)
- ✅ Deadline kleuren (groen/oranje/rood bolletjes in pipeline view)

**Probleem ontdekt:** Dossiers kunnen niet handmatig aan pipeline stappen worden toegewezen. De "Stap wijzigen" batch-actie werkt alleen als dossiers AL in een stap zitten. Ongeassigneerde dossiers (in de "Nog niet toegewezen" sectie) kunnen niet naar een stap verplaatst worden.

## Wat deze sessie moet doen

### Prioriteit 1: Fix dossier-toewijzing aan pipeline stappen

**Probleem:** Als er geen dossiers in stappen staan, kan de gebruiker ze niet toewijzen. De batch "advance_step" actie toont "0 gereed" voor ongeassigneerde dossiers.

**Gewenste flow:**
1. In de "Nog niet toegewezen" sectie moet je dossiers kunnen selecteren
2. Bij "Stap wijzigen" moet je ze naar de eerste stap (of elke stap) kunnen toewijzen
3. De `auto_assign_step` flag in `BatchActionRequest` bestaat al in het schema maar wordt mogelijk niet goed gebruikt

**Bestanden om te onderzoeken:**
- `backend/app/incasso/service.py` — `batch_execute()` en `batch_preview()` functies
- `frontend/src/app/(dashboard)/incasso/page.tsx` — PreFlightDialog en WerkstroomTab
- `frontend/src/hooks/use-incasso.ts` — `useBatchPreview` en `useBatchExecute`

### Prioriteit 2: Template Editor UI (stap 3 uit P1 plan)

**Wat:** Lisanne kan DOCX-briefsjablonen uploaden, beheren en koppelen aan pipeline-stappen. Geen WYSIWYG-editor — Lisanne bewerkt in Word en uploadt naar Luxis.

**Backend:**
- Nieuw `ManagedTemplate` model in `backend/app/documents/models.py`:
  - `id`, `tenant_id`, `name`, `description`, `template_key`, `file_data` (LargeBinary), `filename`, `is_builtin`, `is_active`, timestamps
- Nieuwe endpoints in `backend/app/documents/router.py`:
  - `POST /api/documents/templates/upload` — Upload .docx
  - `GET /api/documents/templates` — Lijst alle templates
  - `PUT /api/documents/templates/{id}` — Metadata bijwerken
  - `DELETE /api/documents/templates/{id}` — Verwijderen
  - `GET /api/documents/templates/{id}/preview/{case_id}` — Preview met echte data
- `backend/app/documents/docx_service.py` aanpassen: check eerst ManagedTemplate, fallback naar disk

**Frontend:**
- Nieuwe pagina: `frontend/src/app/(dashboard)/instellingen/templates/page.tsx`
  - Lijst templates, upload knop met drag & drop, preview, download, bewerken, verwijderen
  - Merge field referentie-panel
  - Badge: "Ingebouwd" vs "Aangepast"
- Nieuwe hook: `frontend/src/hooks/use-templates.ts`
- Pipeline stappen-tab: template dropdown inclusief custom templates

## Essentieel om te lezen

1. `SESSION-NOTES.md` — status na sessie 23
2. `LUXIS-ROADMAP.md` — P1 roadmap en wat er al gedaan is
3. `backend/app/incasso/service.py` — bestaande batch logica
4. `backend/app/documents/docx_service.py` — bestaande template rendering
5. `frontend/src/app/(dashboard)/incasso/page.tsx` — huidige pipeline UI

## Deploy-instructies

Na bouwen:
```bash
# Op VPS (/opt/luxis):
git pull
docker compose run --rm backend python -m alembic upgrade head  # als er migraties zijn
docker compose build --no-cache backend frontend
docker compose up -d
```

Let op: `.env` op VPS bevat nu `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`, dus gewoon `docker compose` werkt.

## Wat er mis ging in sessie 23 (lessen)

1. **COMPOSE_FILE niet ingesteld op VPS** — `docker compose up -d` gebruikte alleen base compose (dev config), niet de prod override. Gevolg: backend kreeg dev-wachtwoord. Fix: `COMPOSE_FILE` env var.
2. **PostgreSQL wachtwoord in volume** — `POSTGRES_PASSWORD` wordt alleen bij eerste volume-initialisatie gebruikt. Later wijzigen vereist `ALTER USER` via psql.
3. **Alembic migratie vereist `run` niet `exec`** — Als backend crashed, werkt `docker compose exec` niet. Gebruik `docker compose run --rm backend python -m alembic upgrade head`.
