# CLAUDE.md — Luxis Development Guide

## Project Overview

Luxis is a practice management system (PMS) for Dutch law firms. First client: Kesting Legal (1 lawyer, collections/insolvency law, Amsterdam). Replaces Basenet.

**Dutch interface, English code.**

## Commands

```bash
# Development (with hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production-like
docker compose up

# Run backend tests
docker compose exec backend pytest tests/ -v

# Run linter
docker compose exec backend ruff check app/

# Run type checker
docker compose exec backend mypy app/

# Run database migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Seed data
docker compose exec backend python -m scripts.seed_interest_rates
```

## Architecture

### Stack
- **Backend:** FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic
- **Database:** PostgreSQL 16 with NUMERIC precision and Row-Level Security
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind CSS
- **Auth:** Custom JWT (python-jose + passlib)
- **Docs:** docxtpl (Word) + WeasyPrint (PDF)
- **Task queue:** Celery + Redis
- **Deployment:** Docker Compose on Hetzner VPS

### Critical Rules

#### Financial Precision
- **ALL monetary values use Python `Decimal` and PostgreSQL `NUMERIC(15, 2)`.**
- **NEVER use `float` for money.** Not for interest, not for invoices, not for VAT, not for anything financial.
- Use `Decimal('0.00')` notation, never `Decimal(0.0)`.
- All rounding uses `ROUND_HALF_UP` and is explicit.
- Every financial calculation must have a test with known-correct values.

#### Multi-Tenant
- Every database model inherits from `TenantBase` which includes `tenant_id`.
- Every query is scoped to the current tenant via middleware.
- PostgreSQL Row-Level Security is the enforcement layer.
- Never write a query that doesn't respect tenant isolation.

#### Module Structure
Each module (auth, relations, cases, collections, documents) follows this pattern:
```
module/
├── router.py    # FastAPI endpoints
├── service.py   # Business logic (no HTTP concerns)
├── models.py    # SQLAlchemy models
└── schemas.py   # Pydantic request/response schemas
```

### Path Alias
- Backend imports: `from app.auth.service import ...`
- Frontend: `@/*` resolves to `src/*`

### API Conventions
- All endpoints under `/api/` prefix (except `/auth/` and `/health`)
- JSON responses with snake_case keys
- Pagination: `?page=1&per_page=20`
- Errors: `{"detail": "message"}` with appropriate HTTP status

### Testing
- Every feature needs tests BEFORE it ships.
- Financial calculations need tests with known-correct values.
- Run `pytest tests/ -v` and all tests must pass.
- Test database is created automatically by conftest.py.

### Commit Messages
Follow conventional commits:
- `feat(module): description` — new feature
- `fix(module): description` — bug fix
- `refactor(module): description` — code change without feature/fix
- `test(module): description` — test additions
- `docs: description` — documentation
- `chore: description` — maintenance

### What Claude Should Always Do
- Think about functionality from the lawyer's perspective, not just technical correctness.
- Flag when something is uncertain about Dutch legal rules (interest rates, WIK changes, WWFT requirements, procedural rules).
- Write tests for every financial calculation.
- Use Decimal everywhere money is involved.
- Keep the API documented — FastAPI auto-generates OpenAPI docs.

## External References
- Full tech stack decisions: `DECISIONS.md`
- Dutch statutory interest rates: seed script in `scripts/seed_interest_rates.py`
- WIK scale (art. 6:96 BW): implemented in `backend/app/collections/wik.py`
