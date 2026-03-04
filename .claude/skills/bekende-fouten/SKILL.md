---
name: bekende-fouten
description: Bekende fouten en valkuilen uit 32 sessies Luxis-ontwikkeling. Lees dit bij elke niet-triviale taak.
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

## Playwright / E2E Testing

16. **Next.js dev overlay `<nextjs-portal>` blokkeert clicks** — gebruik `{ force: true }` op click() calls in E2E tests
17. **Forms zonder htmlFor/id** — gebruik `getByPlaceholder()` of `locator("label:has-text('X') + input")` in Playwright
18. **`waitForURL("**/path/**")` matcht te breed** — gebruik regex: `waitForURL(/\/relaties\/[a-f0-9-]+$/)`
19. **storageState pattern voor auth** — login eenmalig in `auth.setup.ts`, hergebruik `e2e/.auth/user.json` in alle specs. Token injection via localStorage is fragiel.

## Test Hygiene

20. **Geen hardcoded datums in tests** — gebruik `date.today()` of relatieve datums, niet `"2026-02-17"`
21. **Geen exacte counts op seeded data** — gebruik `>= N` niet `== N`, gebruik subset checks niet exact equality
22. **URL paden in tests ALTIJD met `/api/` prefix** — `/api/auth/login`, niet `/auth/login`

## SQLAlchemy / Database

23. **Nested selectinload ALTIJD expliciet** — `selectinload(Model.relation).selectinload(Relation.sub)` voor geneste relaties in async context
24. **`lazy="selectin"` op self-referential models → circular load** — gebruik `lazy="noload"` en laad expliciet
25. **Service constructor updaten bij schema groei** — nieuw veld in schema? Check of `create_*()` en `update_*()` het doorgeven
26. **Alembic stamp voor pre-existing DB** — `alembic stamp head` bij eerste deploy als tabellen al bestaan, niet `upgrade head`

## Infra / VPS

27. **VPS disk vol → PostgreSQL crasht** — `docker system prune -a --volumes -f` vrijt ruimte. Check regelmatig.
28. **COMPOSE_FILE moet in .env staan op VPS** — anders wordt prod override niet geladen en draait dev-config in productie
