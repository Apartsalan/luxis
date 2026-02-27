---
name: template-systeem
description: Document template systeem — DOCX rendering, ManagedTemplate model, template editor UI
---

# Template Systeem

## Huidige situatie
- `backend/app/documents/docx_service.py` — rendert DOCX via docxtpl
- Templates staan als fysieke bestanden in `templates/` directory
- WeasyPrint voor PDF conversie

## Geplande uitbreiding (P1 stap 1)
ManagedTemplate model zodat Lisanne templates kan uploaden/beheren.

### Backend
- Model: `ManagedTemplate` in `backend/app/documents/models.py`
  - `id`, `tenant_id`, `name`, `description`, `template_key`
  - `file_data` (LargeBinary), `filename`, `is_builtin`, `is_active`, timestamps
- Endpoints in `backend/app/documents/router.py`:
  - `POST /api/documents/templates/upload`
  - `GET /api/documents/templates`
  - `PUT /api/documents/templates/{id}`
  - `DELETE /api/documents/templates/{id}`
  - `GET /api/documents/templates/{id}/preview/{case_id}`
- `docx_service.py` aanpassen: eerst ManagedTemplate tabel, fallback naar disk

### Frontend
- Pagina: `frontend/src/app/(dashboard)/instellingen/templates/page.tsx`
- Hook: `frontend/src/hooks/use-templates.ts`
- Features: lijst, upload (drag & drop), preview, download, bewerken, verwijderen
- Badges: "Ingebouwd" vs "Aangepast"
