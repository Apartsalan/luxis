# Bekende test-skips — Luxis backend

Tests die geskipt zijn met reden. Elke `@pytest.mark.skip(reason=...)` in de
suite moet hier gelogd staan.

## KNOWN-001 — Derdengelden endpoint verplaatst naar trust_funds module — OPGELOST

**Status:** 3 dead-code tests verwijderd uit `test_collections_router.py` en
`test_integration_api.py`. Dekking nu volledig in `test_trust_funds.py`
(26 tests over CRUD + saldo + offset).

## KNOWN-002 — SEPA-export test infrastructure bug — OPGELOST (S147)

**Tests (nu unskipped + groen):**
- `tests/test_trust_funds.py::test_sepa_export_*` (4 tests)
- `tests/test_trust_funds_offset.py` — alle 9 offset tests

**Root cause + fix (S147):** De conftest-bug uit KNOWN-003 (zie hieronder) was de
échte blokkade — `setup_database` herbouwde het schema per test. Opgelost door
session-éénmalige schema-creatie + per-test `TRUNCATE ... RESTART IDENTITY CASCADE`.
Na het unskippen bleek nog één losstaande oorzaak voor de 4 SEPA-tests: de dev-
container was **stale** (`sepaxml>=2.6.0` staat in `pyproject.toml` maar was niet
geïnstalleerd) → `ModuleNotFoundError: No module named 'sepaxml'`. CI/prod bouwen
fresh, dus daar speelde dit niet. Lokaal opgelost met een container-rebuild.

## KNOWN-003 — Conftest setup_database fixture failure — OPGELOST (S147)

**Tests (nu unskipped + groen):**
- `tests/test_documents.py::test_generate_docx_14_dagenbrief`
- `tests/test_documents.py::test_generate_docx_sommatie`
- `tests/test_documents.py::test_generate_docx_renteoverzicht`
- `tests/test_documents.py::test_docx_financial_amounts_present`

**Root cause + fix (S147):** `conftest.py::setup_database` deed
`DROP SCHEMA CASCADE; CREATE SCHEMA; create_all()` vóór elke test. asyncpg's
prepared-statement cache raakte out-of-sync na de schema-recreate → `relation
"tenants" does not exist` bij INSERT (intermittent — afhankelijk van connectie-
hergebruik). Opgelost: schema wordt nu **éénmalig per test-proces** gebouwd
(module-flag) en elke test start schoon via `TRUNCATE ... RESTART IDENTITY CASCADE`
— geen DDL meer per test, dus de statement-cache blijft geldig.

Na het unskippen bleek nog één stale test-assertie: de docx-tests checkten op
`"EUR"` in de gerenderde tekst, maar de templates renderen het euro-symbool `€`
(zie `_fmt_currency` in dezelfde file). Assertions bijgewerkt naar `€`.

## KNOWN-005 — Bestaande E2E specs stale t.o.v. nieuwe UI

**Bestanden (volledig of gedeeltelijk geskipt via `test.skip` / `test.describe.skip`):**
- `frontend/e2e/auth.spec.ts::A4` — logout-button heeft nu aria-label, geen title — **STATUS: GEFIXT** — selector vervangen door `getByRole("button", { name: "Uitloggen" })`
- `frontend/e2e/agenda.spec.ts::A2` — dialog-flow veranderd — **STATUS: GEFIXT** — submit-knop heet nu "Aanmaken"; created-event ID via response capture voor cleanup; day-detail klik vervangen door directe text-assertion in kalendergrid
- `frontend/e2e/correspondentie.spec.ts` — empty-state tekst veranderd — **STATUS: GEFIXT** — h1 nu "Mail", tab-buttons toegevoegd, C2 schakelt naar Ongesorteerd-tab
- `frontend/e2e/dashboard.spec.ts` — greeting heading veranderd (was "Goede morgen/middag/avond") — **STATUS: GEFIXT** — describe.skip verwijderd, user-naam check aangepast naar "E2E" (e2e-test user full_name = "E2E Test User")
- `frontend/e2e/documenten.spec.ts` — page structure veranderd — **STATUS: GEFIXT** — h1 nu "Sjablonen" met tabs Word-sjablonen + HTML Sjablonen
- `frontend/e2e/facturen.spec.ts::F2`, `::F7` — wizard flow + delete-confirm dialog veranderd — **STATUS: GEFIXT** — backend-blocker opgelost met Alembic-migratie `df140a_invoice_lines_btw` (voegt `invoice_lines.btw_percentage NUMERIC(5,2) DEFAULT 21.00` toe); F2 draait nu tegen huidige wizard-UI; F7 gebruikt React-AlertDialog patroon (zelfde als R5/T5).
- `frontend/e2e/incasso-pipeline.spec.ts` — pipeline steps hernoemd naar "Eerste/Tweede/Derde sommatie" — **STATUS: GEFIXT** — describe.skip verwijderd; E1 switcht naar "Per stap" view en checkt op nieuwe stap-namen (Eerste/Tweede/Derde sommatie + Sommatie laatste mogelijkheid + Verzoekschrift faillissement); E3-E5 gebruiken `tbody tr` selector i.p.v. cursor-pointer hack
- `frontend/e2e/instellingen.spec.ts` — tab-structure veranderd — **STATUS: GEFIXT** — nieuwe tab-sidebar (Profiel/Kantoor/Modules/etc); tenant + KvK staan nu in inputs binnen Kantoor-tab; tests scopen op `main nav` om bell-icon te vermijden
- `frontend/e2e/sidebar.spec.ts` — dashboard greeting check faalt voor beforeEach — **STATUS: GEFIXT** — beforeEach gebruikt nu sidebar Dashboard-link i.p.v. greeting heading
- `frontend/e2e/relaties.spec.ts::R5` — delete-confirm dialog is nu custom React component (geen `window.confirm`), `page.on('dialog')` werkt niet meer — **STATUS: GEFIXT** — `page.on("dialog")` vervangen door `page.getByRole("alertdialog")` patroon
- `frontend/e2e/tijdregistratie.spec.ts::T5` — zelfde delete-confirm dialog issue — **STATUS: GEFIXT** — `page.on("dialog")` vervangen door `page.getByRole("alertdialog")` patroon
- `frontend/e2e/zaken.spec.ts::Z3` — dossier-wizard client-search input is verplaatst naar later stap, niet zichtbaar zonder voorafgaande stap-navigatie — **STATUS: GEFIXT** — Z3 navigeert nu eerst stap 1 (case_type="advies") → klikt "Volgende" → client-search verschijnt in stap 2; toast-assertie gebruikt waitFor pre-redirect; Z8 ook geüpgraded naar AlertDialog patroon

**Reden:** UI is geëvolueerd in sessies 130-139 (nieuwe pipeline, bulk-toolbars,
nieuwe instellingen-tabs). De E2E specs uit eerdere sessies verwachten nog de
oude UI-strings en componenten.

**Dekking elders:** De nieuwe `regression.spec.ts`, `edge-cases.spec.ts` en
`ui-rendering.spec.ts` (52 tests) dekken de huidige UI met DF138/S139 regressie
checks. Smoke-tests op pagina-load zitten verspreid in groep B/D.

**Actie:** Bij volgende sessie deze specs herschrijven tegen huidige UI.

## KNOWN-004 — Greeting-injection logic veranderd voor DF138-22 — OPGELOST

**Status:** Beide tests in `tests/test_html_renderer.py` aangepast aan nieuwe
salutation-specifieke aanhef met alleen achternaam:
- `test_lone_comma_template_gets_greeting_injected` — gebruikt salutation=mr → "Geachte heer Jansen"
- `test_normal_template_greeting_replaced_with_contact` — gebruikt salutation=mrs → "Geachte mevrouw Jansen"
Beide tests draaien nu groen (18/18 in test_html_renderer.py).
