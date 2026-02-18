# CLAUDE.md — Luxis

Practice management system for Dutch law firms. First client: Kesting Legal (1 lawyer, collections/insolvency law, Amsterdam).

**Dutch UI, English code.**

## Commands

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up   # Dev with hot reload
docker compose exec backend pytest tests/ -v                         # Tests
docker compose exec backend ruff check app/                          # Lint
docker compose exec backend python -m alembic upgrade head           # Migrations
docker compose exec backend python -m alembic revision --autogenerate -m "desc"  # New migration
```

## Critical Rules

**IMPORTANT: Financial precision is non-negotiable.**
- ALL money uses Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NEVER `float`.
- `Decimal('0.00')` notation. Rounding: `ROUND_HALF_UP`, always explicit.
- Every financial calculation MUST have a test with known-correct values.

**Multi-tenant isolation:**
- Domain models inherit `TenantBase` (includes `tenant_id`). Exception: `interest_rates` is global.
- Every query scoped to tenant via middleware + Row-Level Security.

## Architecture

- **Backend:** FastAPI 3.12 + SQLAlchemy 2.0 + Alembic | Module pattern: `router.py`, `service.py`, `models.py`, `schemas.py`
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind | Path alias: `@/*` = `src/*`
- **Auth:** python-jose + bcrypt (NOT passlib) | **Docs:** docxtpl + WeasyPrint | **Queue:** Celery + Redis
- **API:** `/api/` prefix, snake_case JSON, pagination `?page=1&per_page=20`, errors `{"detail": "msg"}`

## Design & UX

Modern, levendig, professioneel (Gmail/HubSpot-stijl). Data-dense maar niet overweldigend. Sidebar met collapse. Kleuren: nog te bepalen, mag levendig zijn. UI taal: Nederlands.

## Working Agreements

- Claude werkt **zelfstandig** — geen toestemming vragen (behalve aanschaffingen/destructieve acties)
- Bij twijfel over Nederlandse juridische regels: **flaggen, niet stoppen**
- Bij elke afspraak of correctie: **CLAUDE.md updaten**
- Conventional commits: `feat(module):`, `fix(module):`, `refactor(module):`, `test(module):`, `docs:`, `chore:`

## Known Quirks

- Git Bash: `MSYS_NO_PATHCONV=1` prefix bij `docker exec`
- Container: `python -m alembic` i.p.v. bare `alembic`
- asyncpg: Python `date` objects, geen strings
- bcrypt 5.x: passlib incompatible, gebruik direct `bcrypt`

## References

- @DECISIONS.md — tech stack decisions
- @docs/dutch-legal-rules.md — wettelijke rentetarieven, WIK-staffel, art. 6:44 BW
- @backend/CLAUDE.md — backend-specifieke conventies
- @frontend/CLAUDE.md — frontend-specifieke conventies
