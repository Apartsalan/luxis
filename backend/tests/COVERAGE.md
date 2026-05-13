# Backend Test Coverage — Luxis

Dit document beschrijft welke workflows en domeinregels worden gedekt door de
backend test-suite. Voor frontend-coverage zie `frontend/e2e/COVERAGE.md`.

## Statistiek (laatste meting)

Run `docker compose exec backend python -m pytest --cov=app --cov-fail-under=80 --cov-report=term`
voor de actuele cijfers. De suite bevat 800+ tests.

## Bekende skips

Zie `backend/tests/KNOWN_BUGS.md` voor een lijst van geskipte tests met reden.

---

## Domeinregels — financiële kernlogica

| Onderdeel | Bestand | Dekt |
|-----------|---------|------|
| Wettelijke rente (simple/compound) | `test_interest.py`, `test_interest_edge_cases.py`, `test_interest_inheritance.py` | Art. 6:119/119a BW — simple + compound, monthly + yearly basis, rente vanaf verzuimdatum (niet 1 jan), capitalisatie, deelbetaling, NULL rate |
| WIK-staffel (BIK) | `test_wik.py`, `test_wik_edge_cases.py` | Art. 6:96 BW — alle 5 staffeltrappen (15/10/5/1/0.5%), min EUR 40, max EUR 6.775, exact-grenzen (EUR 2.500/5.000/10.000/200.000), BTW 21% |
| Betalingstoerekening | `test_payment_distribution.py`, `test_payment_distribution_extended.py` | Art. 6:44 BW — kosten -> rente -> hoofdsom, edge cases (betaling < kosten, = totaal, > totaal) |
| Nakosten | `test_nakosten.py` | Liquidatietarief per 1 feb 2026 — EUR 189/287 |
| Griffierechten | impliciet via `test_collections_router.py` | Vorderingsbedrag-staffel |

## Domeinregels — incasso workflow

| Onderdeel | Bestand | Dekt |
|-----------|---------|------|
| Pipeline (5 stappen) | `test_incasso_pipeline.py` | Eerste sommatie, Tweede sommatie, Derde sommatie, Sommatie laatste mogelijkheid, Verzoekschrift faillissement |
| Templates | `test_incasso_templates.py` | Template seed + retrieval |
| Invoice preview | `test_incasso_invoice_preview.py` | Factuur-tabel in pipeline-mails |
| Automation rules | `test_incasso_router.py` | Trigger condities + actie-toepassing |
| Contact-resolution | `test_resolve_contact_person.py` | Aanhef (mr/mrs/unknown), bedrijf via ContactLink, persoon last_name fallback (DF138-22 regressie) |
| HTML renderer | `test_html_renderer.py`, `test_incasso_invoice_preview.py` | Factuur-rijen, Rente-cel vulling (DF138-21/23 regressie) |
| Draft context | `test_draft_context.py` | Variabelen voor AI compose |

## CRUD per resource

| Resource | Bestand | Dekt |
|----------|---------|------|
| Relations | `test_relations.py` | Create company/person, search, filter, sort (DF138-10), 409 bij gekoppeld dossier (DF138-09), salutation veld (DF138-04) |
| Cases | `test_cases.py`, `test_claims_crud.py` | Create/update/delete dossier, partijen, status, BIK-minimum (DF138-14), minimum_fee vs bik_minimum_fee (DF138-16) |
| Invoices | `test_invoices.py`, `test_invoice_parser.py`, `test_invoice_payments.py`, `test_invoice_pdf.py`, `test_invoice_send_email.py` | Create/approve/send factuur, PDF, betaling registreren, parser bij upload |
| Payments | `test_payment_allocation.py`, `test_payment_arrangements.py`, `test_payment_matching.py` | Toerekening, betalingsregeling, AI-matching |
| Time entries | `test_time_entries.py` | CRUD uren, billable, hourly rate |
| Documents | `test_documents.py` | Upload + retrieval |
| Trust funds | `test_trust_funds.py`, `test_trust_funds_offset.py` | Derdengelden CRUD, SEPA-export, offset tegen facturen |
| Auth | `test_auth.py` | Login, JWT, password hash, role |
| Workflow | `test_workflow.py` | Statuses, transitions, taken, automatische regels |
| Calendar | `test_calendar.py` | Agenda CRUD |
| Notifications | `test_notifications.py` | In-app notifications |
| Settings | `test_settings.py` | Tenant config |
| Products | `test_products.py` | Productcatalogus |
| Search | `test_search.py` | Globale zoek |
| Dashboard | `test_dashboard.py` | Stats endpoints |

## AI / Email integratie

| Onderdeel | Bestand | Dekt |
|-----------|---------|------|
| Email router | `test_email_router.py` | Inkomende email → dossier matching |
| Email sync | `test_email_sync.py` | OutlookProvider sync, attachments |
| AI agent | `test_ai_agent.py` | Classificatie, intake |
| AI tools | `test_ai_tools/test_registry.py`, `test_ai_tools/test_executor.py`, `test_ai_tools/test_serializer.py` | Tool registry + execution |
| Intake | `test_intake.py`, `test_intake_address_parsing.py` | Cliënt-intake, NL-adres parsing |
| Followup | `test_followup.py` | Automatische follow-up scheduler |
| Integration API | `test_integration_api.py` | End-to-end API flows |

## Externe integraties

| Onderdeel | Bestand | Dekt |
|-----------|---------|------|
| Exact Online | `test_exact_online.py` | OAuth + sync |
| Billing features | `test_billing_features.py` | BIK/rente combinaties, BTW |

---

## Regressie-tests per demo-bug (sessie 138/139)

Onderstaande bugs zijn als regressie-test gedekt. Frontend-regressies staan
in `frontend/e2e/regression.spec.ts`.

| Bug | Backend-dekking |
|-----|-----------------|
| DF138-04 (salutation veld) | `test_relations.py` — create/update met `salutation` |
| DF138-08 (created_at in lijst) | `test_relations.py` — `ContactSummary` schema |
| DF138-09 (409 bij verwijderen met dossier) | `test_relations.py` — delete met actieve case |
| DF138-10 (sort whitelist) | `test_relations.py` — sort_by/sort_dir parameters |
| DF138-13 (rate_basis cascade) | `test_cases.py`, `test_billing_features.py` |
| DF138-14 (BIK-minimum bodem) | `test_billing_features.py`, `test_wik.py` |
| DF138-16 (apart bik_minimum_fee) | `test_billing_features.py`, `test_cases.py` |
| DF138-17 (geen suffix in bik_source) | `test_billing_features.py` |
| DF138-21 (Rente-cel vulling) | `test_html_renderer.py`, `test_incasso_invoice_preview.py` |
| DF138-22 (aanhef alleen achternaam) | `test_resolve_contact_person.py` |
| DF138-23 (lege placeholder-rijen) | `test_html_renderer.py`, `test_incasso_invoice_preview.py` |
| S139-av-versies | `test_relations.py` — `select_terms_for_date` smart-default |

## Multi-tenant isolatie

| Bestand | Dekt |
|---------|------|
| `test_collections_router.py::test_claims_tenant_isolation` | Tenant A claims niet zichtbaar voor Tenant B |
| Diverse modules | Per-module isolatie via `second_tenant`/`second_auth_headers` fixtures |
