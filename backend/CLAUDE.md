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

- `pytest tests/ -v` — all tests must pass
- `conftest.py` creates async test DB automatically
- Every financial calc needs test with known-correct values from legal sources
- Test files mirror module structure: `test_interest.py`, `test_wik.py`, `test_payment_distribution.py`

## Dependencies

- `bcrypt` for passwords (NOT passlib)
- `python-jose` for JWT
- `sqlalchemy[asyncio]` + `asyncpg` for DB
- `ruff` for linting
