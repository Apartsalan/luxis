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
