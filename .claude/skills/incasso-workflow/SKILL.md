---
name: incasso-workflow
description: Incasso pipeline kennis — stappen, batch acties, deadline kleuren, dossier-toewijzing
---

# Incasso Workflow

## Pipeline architectuur
- `IncassoPipeline` → heeft meerdere `IncassoPipelineStep` (geordend op `order`)
- `IncassoCase` (dossier) → gekoppeld aan een step via `current_step_id`
- Dossiers zonder `current_step_id` staan in "Nog niet toegewezen"

## Belangrijke bestanden
- Backend service: `backend/app/incasso/service.py`
- Backend schemas: `backend/app/incasso/schemas.py`
- Backend models: `backend/app/incasso/models.py`
- Frontend pagina: `frontend/src/app/(dashboard)/incasso/page.tsx`
- Frontend hook: `frontend/src/hooks/use-incasso.ts`

## Batch acties
- `BatchActionRequest` schema bevat `action`, `case_ids`, `target_step_id`, `auto_assign_step`
- `batch_preview()` — toont hoeveel dossiers "gereed" zijn
- `batch_execute()` — voert de actie uit op geselecteerde dossiers

## Deadline kleuren (sessie 23)
- `_compute_deadline_status()` in service.py
- Groen = binnen termijn, Oranje = bijna verlopen, Rood = verlopen, Grijs = geen deadline
- `max_wait_days` kolom op `IncassoPipelineStep` (migratie 033)

## Frontend structuur
- `WerkstroomTab` — kanban-achtig overzicht per stap
- `StappenTab` — configuratie van stappen (volgorde, dagen, template)
- `PreFlightDialog` — batch actie bevestiging
