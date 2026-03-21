# Backend — Luxis

## Module Pattern

Every module follows: `router.py` (endpoints) → `service.py` (business logic, no HTTP) → `models.py` (SQLAlchemy) → `schemas.py` (Pydantic).

## Key Patterns

- All models with tenant scope inherit `TenantBase` (UUID pk + tenant_id FK)
- `interest_rates` is GLOBAL — inherits `Base + TimestampMixin`, no tenant_id
- Async everywhere: `AsyncSession`, `async def`, `await`
- Imports: `from app.module.service import ...`

## Financial Calculations

- `backend/app/collections/interest.py` — compound/simple interest per period
- `backend/app/collections/wik.py` — art. 6:96 BW staffel (15/10/5/1/0.5% tiers, min 40, max 6775)
- `backend/app/collections/payment_distribution.py` — art. 6:44 BW: costs -> interest -> principal
- Compound interest year runs from **verzuimdatum**, NOT January 1

## Testing

- `conftest.py` creates async test DB automatically
- Every financial calc needs test with known-correct values from legal sources
- Test files mirror module structure: `test_interest.py`, `test_wik.py`, `test_payment_distribution.py`

### Test strategie (snelheid)

- **Tijdens ontwikkeling:** alleen relevante tests draaien
  - `pytest tests/test_claims_crud.py -v` — specifiek bestand
  - `pytest tests/ -k "claim" -v` — keyword filter
- **Full suite:** alleen draaien bij wijzigingen die bestaande functionaliteit kunnen breken (refactors, gedeelde functies, schema-wijzigingen aan bestaande velden). NIET bij puur additieve wijzigingen (nieuwe velden, nieuwe endpoints).
- **NOOIT** de volledige suite draaien "voor de zekerheid" — beoordeel of het nodig is

## Test Patterns

- No hardcoded dates — use `date.today()` or relative dates, not `"2026-02-17"`
- No exact counts on seeded data — use `>=` and subset checks, not `== 3`
- All API paths use `/api/` prefix — `/api/auth/login`, not `/auth/login`
- When adding fields to a schema, always update the service `create_*()` and `update_*()` methods
- `alembic stamp head` for pre-existing databases, not `alembic upgrade head`

## SQLAlchemy Async Rules

- Nested eager loading: chain `selectinload(A.b).selectinload(B.c)` for depth
- Never rely on lazy loading in async context — it raises `MissingGreenlet`
- `lazy="selectin"` on self-referential models causes circular load — use `lazy="noload"` instead

## Dependencies

- `bcrypt` for passwords (NOT passlib)
- `PyJWT` for JWT
- `sqlalchemy[asyncio]` + `asyncpg` for DB
- `ruff` for linting
