# UI Bugs Discovered During E2E Test Rewrite

Bugs ontdekt tijdens herschrijven van stale Playwright specs (sessie 2026-05-14).
Niet gefixt — uitscope. Documenteer hier voor later.

## BUG-001 — Backend: invoice_lines.btw_percentage kolom ontbreekt — OPGELOST

**Symptoom:** `GET /api/invoices` en `POST /api/invoices` geven HTTP 500.

**Fix:** Alembic-migratie `backend/alembic/versions/df140a_invoice_lines_btw.py`
voegt de kolom toe met default 21.00.

## BUG-003 — Send-invoice endpoint vereist SMTP + email_logs

`POST /api/invoices/{id}/send` probeert echt een PDF-e-mail te versturen via
SMTP. Test-omgeving heeft geen SMTP_HOST/SMTP_FROM én de `email_logs` tabel
ontbreekt in dev-DB.

**Impact op E2E:** `facturen.spec.ts::F5` (send invoice) en `::F6`
(register payment, hangt af van F5) zijn geskipt — niet in KNOWN-005, dus
out-of-scope voor playwright-cleanup goal.

**Voorgestelde fix:** mock email provider in test-env, of `email_logs`
migratie + SMTP-mock injection.

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

