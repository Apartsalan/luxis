# Luxis API Documentatie

## Toegang

FastAPI genereert automatisch interactieve API docs:

- **Swagger UI:** `http://localhost:8000/docs` (alleen dev/test)
- **ReDoc:** `http://localhost:8000/redoc` (alleen dev/test)
- **OpenAPI JSON:** `http://localhost:8000/openapi.json` (alleen dev/test)

In productie zijn deze endpoints uitgeschakeld. Draai lokaal met Docker:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
# Open http://localhost:8000/docs
```

## Authenticatie

Alle endpoints (behalve `/api/auth/login`) vereisen een JWT Bearer token.

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.nl", "password": "wachtwoord"}'

# Gebruik het token
curl http://localhost:8000/api/cases \
  -H "Authorization: Bearer <access_token>"
```

Tokens verlopen na 30 minuten. Gebruik het refresh token om een nieuw access token te krijgen.

## Conventies

- **Base URL:** `/api/`
- **Format:** JSON, snake_case velden
- **Paginatie:** `?page=1&per_page=20`
- **Errors:** `{"detail": "Beschrijving van de fout"}`
- **Financiële bedragen:** Strings (`"5000.00"`), nooit floats
- **IDs:** UUID v4
- **Datums:** ISO 8601 (`2026-03-27`)

## Modules (25 routers, 231 endpoints)

| Module | Prefix | Beschrijving |
|--------|--------|-------------|
| Auth | `/api/auth/` | Login, refresh, users CRUD |
| Cases | `/api/cases/` | Dossiers CRUD, status, partijen |
| Relations | `/api/relations/` | Contacten CRUD, KYC |
| Collections | `/api/cases/{id}/claims/` | Vorderingen, betalingen, BIK, rente |
| Invoices | `/api/invoices/` | Facturen, credit notes |
| Time Entries | `/api/time-entries/` | Uren, timer |
| Documents | `/api/documents/` | Templates, generatie (DOCX/PDF) |
| Email | `/api/email/` | SMTP status, verzenden |
| Email Sync | `/api/email/` | OAuth, inbox sync, bijlagen |
| Incasso | `/api/incasso/` | Pipeline, batch acties, queue |
| Calendar | `/api/calendar/events/` | Agenda events CRUD |
| Notifications | `/api/notifications/` | Meldingen (stub) |
| Settings | `/api/settings/` | Tenant profiel |
| Search | `/api/search/` | Globaal zoeken |
| Workflow | `/api/workflow/` | Status machine, transities |
| Tasks | `/api/tasks/` | Taken CRUD |
| Activities | `/api/activities/` | Activiteitenlog |
| Interest Rates | `/api/interest-rates/` | Wettelijke rentetarieven |
| Trust Funds | `/api/cases/{id}/derdengelden/` | Derdengelden |
| AI Agent | `/api/ai-agent/` | Intake, follow-up, matching |

## Multi-tenant

Elke request is automatisch geschoold op de tenant van de ingelogde gebruiker. Row-Level Security (RLS) in PostgreSQL voorkomt cross-tenant data access.
