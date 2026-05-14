# UI Bugs Discovered During E2E Test Rewrite

Bugs ontdekt tijdens herschrijven van stale Playwright specs (sessie 2026-05-14).
Niet gefixt — uitscope. Documenteer hier voor later.

## BUG-001 — Backend: invoice_lines.btw_percentage kolom ontbreekt

**Symptoom:** `GET /api/invoices` en `POST /api/invoices` geven HTTP 500
`Internal Server Error`.

**Error in backend logs:**
```
sqlalchemy.exc.ProgrammingError: <class 'asyncpg.exceptions.UndefinedColumnError'>:
column invoice_lines.btw_percentage does not exist
```

**Oorzaak:** Het SQLAlchemy model `app/invoices/models.py` declareert
`btw_percentage` op `InvoiceLine` (regel 152) maar er is geen Alembic-migratie
die deze kolom toevoegt aan de bestaande `invoice_lines` tabel. Migratie
`015_invoices.py` creëert de tabel zonder deze kolom.

**Impact op E2E:**
- `facturen.spec.ts::F2` (create invoice via form) — BLOCKED
- `facturen.spec.ts::F3-F6` (auto-skip omdat F2 niet slaagt)
- `facturen.spec.ts::F7` (delete concept invoice) — BLOCKED, gebruikt API
  helper `createInvoice` die ook 500 geeft

**Reproductie:**
```bash
curl -X POST http://localhost:8000/api/invoices \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"contact_id":"<UUID>","invoice_date":"2026-05-14","due_date":"2026-06-13","btw_percentage":"21.00","lines":[{"description":"Test","quantity":"1","unit_price":"100.00"}]}'
# → Internal Server Error
```

**Voorgestelde fix (backend):** nieuwe Alembic-migratie die
`btw_percentage NUMERIC(5,2) NOT NULL DEFAULT 21.00` toevoegt aan
`invoice_lines`. Tegelijkertijd checken of `invoices.btw_percentage` consistent
is en of de model-defaults aansluiten op de DB.

## BUG-002 — Taken-pagina maakt geseede taken onzichtbaar bij veel openstaande items

**Symptoom:** `frontend/e2e/taken.spec.ts::T2` en `::T3` falen omdat de net
aangemaakte taak ("E2E Test Taak" / "E2E Afrond Taak") niet zichtbaar is op
de `/taken` pagina. Pagina toont 140+ openstaande taken; de nieuwe entry
verdwijnt door pagination/sortering.

**Impact op E2E:** beide tests zijn nu geskipt (flaky-not-stale-spec).

**Voorgestelde fix:**
- UI: na "Taak aangemaakt" toast bovenaan lijst tonen, of refetch met
  scroll-to-new-item.
- Tests: stricter filter toepassen (alleen geseede dossiernummer) of via
  detail-pagina valideren in plaats van /taken lijst.

