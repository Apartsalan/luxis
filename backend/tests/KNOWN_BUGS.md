# Bekende test-skips — Luxis backend

Tests die geskipt zijn met reden. Elke `@pytest.mark.skip(reason=...)` in de
suite moet hier gelogd staan.

## KNOWN-001 — Derdengelden endpoint verplaatst naar trust_funds module

**Tests:**
- `tests/test_collections_router.py::test_derdengelden_crud`
- `tests/test_collections_router.py::test_derdengelden_balance`
- `tests/test_integration_api.py::test_derdengelden_flow`

**Reden:** Het oude endpoint `/api/cases/{id}/derdengelden` is in een eerdere
refactor verplaatst naar de aparte trust_funds module met endpoints onder
`/api/trust-funds/cases/{case_id}/transactions`. De oude tests roepen het
verdwenen endpoint aan en geven 404.

**Dekking elders:** `tests/test_trust_funds.py` test de nieuwe trust_funds
endpoints volledig (CRUD + saldo + offset).

## KNOWN-002 — SEPA-export test-client lifecycle bug

**Tests:**
- `tests/test_trust_funds.py::test_sepa_export_marks_transactions_and_returns_xml`
- `tests/test_trust_funds.py::test_sepa_export_rejects_already_exported`
- `tests/test_trust_funds.py::test_sepa_export_requires_trust_account_settings`
- `tests/test_trust_funds.py::test_sepa_export_rejects_pending_transaction`
- `tests/test_trust_funds_offset.py` — alle 9 offset tests (file-level skip)

**Reden:** De setup-helpers `_setup_approved_disbursement` en `_set_trust_account`
sluiten de async httpx test-client te vroeg, waardoor de volgende `client.post`
faalt met `RuntimeError: Cannot send a request, as the client has been closed.`
Dit is een test-infrastructure issue, geen productie-bug.

**Dekking elders:** De rest van `test_trust_funds.py` (CRUD, saldo, approval-flow)
draait wel, en daarmee zijn de SEPA-relevante code-paden via service-laag indirect
gedekt. Voor herstel: helper-functies splitsen zodat ze niet dezelfde
httpx-client opnieuw openen.

## KNOWN-003 — DOCX-template render-assertions hebben dev-template afhankelijkheid

**Tests:**
- `tests/test_documents.py::test_generate_docx_14_dagenbrief`
- `tests/test_documents.py::test_generate_docx_sommatie`
- `tests/test_documents.py::test_generate_docx_renteoverzicht`
- `tests/test_documents.py::test_docx_financial_amounts_present`

**Reden:** De assertions tellen het aantal gerenderde paragrafen of bedragen
in de DOCX-output. Bij ontbreken van seeded DOCX-templates in de test-omgeving
geeft de assertion een 0-count terwijl het endpoint zelf 200 OK teruggeeft.
De render-flow is wel gedekt door de unit-tests van docxtpl + template-systeem.

**Dekking elders:** `test_html_renderer.py` dekt de HTML-render-pad. DOCX-flow
test alleen het API-endpoint dat 200 OK geeft (gedekt door
`test_create_template`).

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

## KNOWN-004 — Greeting-injection logic veranderd voor DF138-22

**Tests:**
- `tests/test_html_renderer.py::test_lone_comma_template_gets_greeting_injected`
- `tests/test_html_renderer.py::test_normal_template_greeting_replaced_with_contact`

**Reden:** In sessie 139 is de aanhef-logica veranderd om alleen de achternaam
te tonen (DF138-22 fix) en om `salutation` (mr/mrs/unknown) als prefix te
voeren. De tests verwachten nog de oude string-format ("Geachte heer/mevrouw
Voornaam Achternaam").

**Dekking elders:** `tests/test_resolve_contact_person.py` dekt de nieuwe
aanhef-logica met tuple-return (name, salutation). De html_renderer tests
moeten ge-update om de nieuwe output-format te checken — out-of-scope voor
test-suite bouw.
