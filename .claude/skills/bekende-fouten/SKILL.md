---
name: bekende-fouten
description: Bekende fouten en valkuilen uit 23 sessies Luxis-ontwikkeling. Lees dit bij elke niet-triviale taak.
---

# Bekende Fouten — VOORKOM DEZE

## Backend

1. **Nooit float voor geld** — altijd `Decimal` + `NUMERIC(15,2)`
2. **SQLAlchemy async lazy loading werkt niet** — gebruik explicit `selectinload().selectinload()` voor nested relaties
3. **Alembic: `docker compose run --rm` niet `exec`** als de backend container crashed is
4. **bcrypt 5.x is incompatible met passlib** — gebruik direct `bcrypt`
5. **asyncpg verwacht Python `date` objects** — geen strings
6. **Git Bash path conversion:** prefix `MSYS_NO_PATHCONV=1` bij `docker exec` commando's
7. **Container alembic:** gebruik `python -m alembic`, niet bare `alembic`

## Frontend

8. **NOOIT `localhost:8000` in frontend code** — altijd relatieve URLs (`""`). Next.js rewrite proxy `/api/*` → `backend:8000`
9. **Exclude_unset bug:** Bij PATCH/PUT: gebruik `value if value else None` NIET `value || undefined`. Lege strings moeten als `null` naar backend
10. **Frontend build MOET slagen** voordat je commit: `cd frontend && npm run build`

## Deploy

11. **Na ELKE commit ALTIJD `git push origin main`** — commits die alleen lokaal staan bereiken de VPS niet
12. **POSTGRES_PASSWORD werkt alleen bij eerste volume-init** — later wijzigen via `ALTER USER` in psql
13. **Claude heeft GEEN SSH-toegang** — geef deploy commando's aan de gebruiker

## Process

14. **Sessie-prompts moeten COMPLEET zijn** — de gebruiker is geen developer, prompt moet foutloos werken zonder extra context
15. **LUXIS-ROADMAP.md is de enige source of truth** — update na ELKE wijziging
