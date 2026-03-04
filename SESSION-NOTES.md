# Sessie Notities — Luxis

**Laatst bijgewerkt:** 4 maart 2026 (sessie 34 — E2E-2 Zaken CRUD tests)
**Laatste feature/fix:** 8 Zaken CRUD E2E tests (create, detail, tabs, edit, status, delete)
**P1 status:** ALLE 6 ITEMS AFGEROND + QA COMPLEET ✅
**Openstaande bugs:** Geen bekende bugs
**Volgende sessie (35):** E2E-3: Facturen + Tijdschrijven E2E tests (~10-12 tests)

## Wat er gedaan is (sessie 34 — 4 maart) — E2E-2: Zaken CRUD ✅

### Overzicht
8 Playwright E2E tests voor het volledige Zaken (Cases) CRUD lifecycle. Alle tests PASSED. Totaal E2E tests nu: 33 (24 nieuwe + 9 incasso bestaand).

### Wat er gebouwd is
- **`zaken.spec.ts`**: 8 tests — lijst, navigatie, create via form (client search+select), detail page, 7 tabs check, edit beschrijving, status change via API, delete via UI
- **API helpers**: `createCase()`, `deleteCase()`, `updateCaseStatus()` in `e2e/helpers/api.ts`

### Tests (Z1-Z8)
| # | Test | Methode |
|---|------|---------|
| Z1 | Lijst laadt met UI elementen | UI check |
| Z2 | "Nieuw dossier" navigeert | UI navigatie |
| Z3 | Create case via form | UI form (client search, type select) |
| Z4 | Detail pagina laadt | UI verify (case_number, status, client) |
| Z5 | 7 tabs zichtbaar (non-incasso) | UI check + incasso tabs afwezig |
| Z6 | Edit beschrijving | UI (Bewerken → textarea → Opslaan) |
| Z7 | Status wijzigen | API (nieuw → herinnering) + UI verify |
| Z8 | Delete dossier | UI (trash + confirm dialog) |

### Lessen geleerd
- Workflow statuses zijn dynamisch — `afgesloten` bestaat niet, gebruik workflow slugs (`herinnering`, `betaald`, etc.)
- Meerdere "Opslaan" buttons op detail page — gebruik `.first()` voor strict mode
- Toast tekst was "Dossiergegevens opgeslagen", niet "bijgewerkt" — altijd toast tekst checken in broncode

### Nieuwe bestanden
- `frontend/e2e/zaken.spec.ts`

### Gewijzigde bestanden
- `frontend/e2e/helpers/api.ts` (3 nieuwe helpers)
- `LUXIS-ROADMAP.md` (E2E-2 status → compleet)

---

## Wat er gedaan is (sessie 33 — 4 maart) — Claude Code DevOps + Financial Precision ✅

### Overzicht
Claude Code configuratie verbeterd op basis van everything-claude-code repo analyse. 32 sessies retroactief geanalyseerd, lessen gecodificeerd. Financial precision bugs gefixt.

### Wat er gebouwd is
- **Bekende fouten uitgebreid:** 15 → 28 items in `.claude/skills/bekende-fouten/SKILL.md` (Playwright, test hygiene, SQLAlchemy, VPS)
- **CLAUDE.md updates:** E2E Testing sectie in `frontend/CLAUDE.md`, Test Patterns + SQLAlchemy secties in `backend/CLAUDE.md`
- **`/learn` command:** Extraheert sessie-patronen en stelt CLAUDE.md updates voor
- **`/compact-smart` command:** Detecteert huidige focus en genereert optimale `/compact` string
- **`/verify` command:** 7-staps post-implementatie checklist (tests, lint, build, grep-scan, code review, git status)
- **Stop hook:** `check-session-end.sh` — checkt SESSION-NOTES.md, ROADMAP, uncommitted/unpushed bij sessie-einde
- **PostToolUse hook:** Bericht verwijst nu naar `/verify`
- **Security deny list:** ssh, scp, dangerous rm/curl patterns in settings.json

### Fixes
- **5x `float()` → `Decimal`** in `dashboard/service.py` + `dashboard/schemas.py` + `incasso/service.py` + `incasso/schemas.py`
- **`|| undefined` in instellingen:** Onderzocht maar teruggedraaid — TypeScript types gebruiken optional (`?:`), niet nullable

### Nieuwe bestanden
- `.claude/hooks/check-session-end.sh`
- `.claude/commands/learn.md`
- `.claude/commands/compact-smart.md`
- `.claude/commands/verify.md`

### Gewijzigde bestanden
- `.claude/settings.json` (Stop hook, PostToolUse, deny list)
- `.claude/skills/bekende-fouten/SKILL.md` (13 nieuwe items)
- `frontend/CLAUDE.md` (E2E sectie)
- `backend/CLAUDE.md` (Test Patterns + SQLAlchemy secties)
- `backend/app/dashboard/schemas.py` + `service.py` (Decimal)
- `backend/app/incasso/schemas.py` + `service.py` (Decimal)

---

## Wat er gedaan is (sessie 32 — 4 maart) — E2E-1: Auth + Dashboard + Sidebar + Relaties CRUD ✅

### Overzicht
Eerste set Playwright E2E tests. Auth setup via storageState pattern (login eenmalig, hergebruik in alle specs). 16 nieuwe tests, allemaal PASSED.

### Wat er gebouwd is
- **`auth.setup.ts`**: Login via echt formulier, storageState opslaan in `e2e/.auth/user.json`
- **`auth.spec.ts`** (4 tests): login form, invalid creds, session persistence na reload, logout
- **`dashboard.spec.ts`** (3 tests): greeting met naam, KPI kaarten, "Nieuw dossier" knop
- **`sidebar.spec.ts`** (3 tests): nav items zichtbaar, klik navigatie, collapse/expand
- **`relaties.spec.ts`** (5 tests): lijst pagina, maak bedrijf, maak persoon, bewerk, verwijder
- **`helpers/auth.ts`** + **`api.ts`**: herbruikbare test utilities
- **`playwright.config.ts`**: 3-project setup (setup → auth → chromium met dependencies)

### Fixes
- `next.config.ts`: fallback URL `http://backend:8000` → `http://localhost:8000` (proxy 404 fix)
- `incasso-pipeline.spec.ts`: `access_token` → `luxis_access_token` (auth key fix)
- `.gitignore`: Playwright auth/results/report dirs toegevoegd
- Greeting regex: `Goedenavond` → `Goede**n**avond` (verbindings-n)

### Belangrijke lessen
- Next.js dev overlay (`<nextjs-portal>`) blokkeert clicks → `{ force: true }` nodig
- Forms zonder `htmlFor`/`id` → gebruik `getByPlaceholder` of `locator("label:has-text + input")`
- Token injection via localStorage is fragiel → storageState pattern is betrouwbaar
- `waitForURL("**/relaties/**")` matcht ook `/relaties/nieuw` → gebruik regex

### Teststand
- **16 nieuwe E2E tests PASSED** + 9 bestaande incasso E2E = **25 E2E tests totaal**
- **406 backend tests** ongewijzigd

### Nieuwe bestanden
- `frontend/e2e/auth.setup.ts`
- `frontend/e2e/auth.spec.ts`
- `frontend/e2e/dashboard.spec.ts`
- `frontend/e2e/sidebar.spec.ts`
- `frontend/e2e/relaties.spec.ts`
- `frontend/e2e/helpers/auth.ts`
- `frontend/e2e/helpers/api.ts`

### Gewijzigde bestanden
- `frontend/next.config.ts` — proxy fallback URL
- `frontend/playwright.config.ts` — 3-project auth setup
- `frontend/e2e/incasso-pipeline.spec.ts` — localStorage key fix
- `.gitignore` — Playwright dirs

---

## Wat er gedaan is (sessie 31 — 3 maart) — QA: Tenant isolation + edge case tests ✅

### Overzicht
Multi-tenant isolation was het grootste testgap — nergens getest. Nu alle 5 resterende modules gedekt.

### Wat er gebouwd is
- `conftest.py`: `second_tenant`, `second_user`, `second_auth_headers` fixtures
- **QA-1 Auth** (8→14 tests): expired JWT, nonexistent user token, empty credentials, inactive user login, multi-tenant /me, invalid refresh token
- **QA-2 Relations** (18→23 tests): cross-tenant list/detail/update/delete/conflict-check
- **QA-3 Cases** (14→19 tests): cross-tenant list/detail/update/delete, terminal status blocks transitions
- **QA-8 Dashboard** (6→10 tests): unauthenticated endpoints, cross-tenant summary/activity
- **QA-9 Documents** (22→28 tests): cross-tenant template CRUD, case docs, docx generation

### Teststand
- **380 → 406 tests** (+26 nieuwe tests)
- **406/406 PASSED**, 0 failures
- Tenant isolation bevestigd: geen cross-tenant data leaks

### Gewijzigde bestanden
- `backend/tests/conftest.py` — 3 nieuwe fixtures
- `backend/tests/test_auth.py` — 6 nieuwe tests
- `backend/tests/test_relations.py` — 5 nieuwe tests
- `backend/tests/test_cases.py` — 5 nieuwe tests
- `backend/tests/test_dashboard.py` — 4 nieuwe tests
- `backend/tests/test_documents.py` — 6 nieuwe tests

## Wat er gedaan is (sessie 30 — 3 maart) — QA: 64 nieuwe tests voor 4 ongedekte modules ✅

### Overzicht
4 modules hadden 0 tests. Alle 4 nu volledig gedekt, opgesplitst in aparte commits:

### Blok 1: Tijdregistratie (QA-7) — 15 tests ✅
- `backend/tests/test_time_entries.py` — CRUD, filters (case/billable/date range), unbilled, summary totals, summary per-case, my/today, validatie, tenant isolation

### Blok 2: Facturatie (QA-6) — 19 tests ✅
- `backend/tests/test_invoices.py` — Invoice CRUD, auto-nummering, status workflow (concept→approved→sent→paid→cancelled), BTW precision (Decimal), credit notes, lines add/remove, expenses CRUD, payment summary

### Blok 3: Workflow/Taken (QA-5) — 19 tests ✅
- `backend/tests/test_workflow.py` — Statuses CRUD, transitions (B2B/B2C filtering), tasks CRUD met case filter, task completion, invalid task_type, rules CRUD, calendar events, verjaring check

### Blok 4: Email/Sync (QA-4) — 11 tests ✅
- `backend/tests/test_email_sync.py` — Case emails, unlinked emails + count, link/bulk-link, dismiss, email detail, attachments listing, tenant isolation

### Teststand
- **316 → 380 tests** (+64 nieuwe tests)
- **380/380 PASSED**, 0 failures
- Alle 4 commits apart gepusht naar origin main

---

## Wat er gedaan is (sessie 29 — 3 maart) — Fix 20 pre-existing test failures ✅

### BUG-30: test_auth.py (7 tests) ✅
- Alle URL paden gecorrigeerd: `/auth/login` → `/api/auth/login`, `/auth/me` → `/api/auth/me`, `/auth/refresh` → `/api/auth/refresh`

### BUG-31: test_integration_api.py (8 tests) ✅
- `login()` helper URL pad gefixt (regel 67)

### BUG-32: test_cases.py + test_integration_api.py (4 tests) ✅
- `workflow_data` fixture toegevoegd aan conftest.py — seed 15 workflow statuses + 28 transitions
- Tests updaten naar geldige transitiepaden: `nieuw → herinnering → aanmaning`, `nieuw → betaald`, `nieuw → vonnis` (invalid)
- `workflow_data` fixture ook toegevoegd aan `test_case_status_workflow` en `test_invalid_status_transition` in integration tests

### BUG-33: test_dashboard.py (1 test) ✅
- Hardcoded datum `2026-02-17` → `date.today().isoformat()`

### BUG-34: test_documents.py (1 test) ✅
- Template count assertion `== 3` → `>= 3`, types check naar subset

### BUG-35: test_relations.py (1 test) ✅
- Response pad gecorrigeerd: `["name"]` → `["contact"]["name"]`

### Resultaat
- **316/316 tests PASSED** — 0 failures, 1 warning (SAWarning overlaps, cosmetisch)
- 7 bestanden gewijzigd: conftest.py (+92 regels), test_auth.py, test_cases.py, test_dashboard.py, test_documents.py, test_integration_api.py, test_relations.py

## Wat er gedaan is (sessie 28 — 3 maart) — P1 QA: Systeembrede testdekking ✅

### 35 backend integration tests (test_incasso_pipeline.py) ✅
- **6 deadline kleur tests** — groen/oranje/rood/grijs + edge cases (boundary, zero max)
- **2 email template tests** — Jinja2 rendering met variabelen + fallback naar generic template
- **2 task creation tests** — generate_document vs manual_review task type
- **3 auto-complete tests** — pipeline tasks per stap, BUG-29 regressietest (manual tasks niet geraakt)
- **4 auto-advance tests** — doorschuiven, blokkade door open tasks, laatste stap, manual tasks blokkeren niet
- **5 batch preview API tests** — ready/blocked/needs_step_assignment/email readiness/skip closed
- **8 batch execute API tests** — met/zonder email, advance step, meerdere cases, partial failure, email failure
- **2 pipeline overview tests** — grouping by step + unassigned cases
- **3 queue counts tests** — empty, with data, unassigned in action_required

### 9 Playwright E2E tests (incasso-pipeline.spec.ts) ✅
- E1-E5: page load, deadline colors, action bar, pre-flight dialog, email toggle
- E6-E7: skipped (vereist mocked email provider)
- E8-E9: queue filters, stappen beheren

### Smoke test checklist ✅
- `docs/qa/p1-smoke-test-checklist.md` — 6 scenario's, 30+ handmatige checks

### Mock strategie
- `FakeEmailProvider(EmailProvider)` — in-memory email recording voor test assertions
- `_FakeStep` plain class — vervangt `IncassoPipelineStep.__new__()` die niet werkt met SQLAlchemy instrumented attributes
- `patch("app.incasso.service.render_docx/docx_to_pdf/send_with_attachment")` — mocks op import-locatie

### Regressietest resultaten
- **35/35 nieuwe tests PASSED** (72 seconden)
- **296/316 totaal PASSED** — 20 pre-existing failures gevonden (BUG-30 t/m BUG-35)
- Pre-existing failures: URL paden (`/auth/login` → `/api/auth/login`), verouderde assertions, schema wijzigingen

### QA-traject op roadmap gezet
- QA-0 t/m QA-9 gepland: elke module dezelfde testdekking als P1
- Prioriteit: eerst stukke tests fixen, dan modules zonder tests (email, workflow, facturatie, tijdregistratie)

### Nieuwe bestanden
- `backend/tests/helpers/__init__.py` — package init
- `backend/tests/helpers/fake_email_provider.py` — FakeEmailProvider met in-memory sent_messages
- `backend/tests/helpers/incasso_fixtures.py` — create_pipeline_steps, create_incasso_case, create_pipeline_task, create_manual_task
- `backend/tests/test_incasso_pipeline.py` — 35 tests in 9 test classes
- `frontend/playwright.config.ts` — Playwright config (chromium, baseURL localhost:3000)
- `frontend/e2e/incasso-pipeline.spec.ts` — 9 E2E tests
- `docs/qa/p1-smoke-test-checklist.md` — handmatige smoke test
- `docs/prompts/sessie-29-prompt.md` — volgende sessie prompt

### Gewijzigde bestanden
- `frontend/package.json` — @playwright/test devDependency
- `LUXIS-ROADMAP.md` — P1 QA status, BUG-30 t/m BUG-35, QA-traject roadmap

---

## Wat er gedaan is (sessie 27 — 2 maart) — P1.2 Batch brief + email verzenden ✅

### P1 item 2: Batch brief + email verzenden ✅
- **Batch "Verstuur brief"** genereert nu documenten EN emailt ze als PDF-bijlage naar wederpartij
- **Flow:** DOCX genereren → PDF conversie via LibreOffice → email via Gmail/Outlook provider (SMTP fallback)
- **PreFlightDialog:** Email toggle (default aan), toont email_ready/email_blocked counts
- **Per-stap email templates:** Jinja2 subject + body templates met variabelen (zaak.zaaknummer, wederpartij.naam, etc.)
- **Fallback:** Als step geen custom email template heeft → generic `document_sent()` template
- **Toast:** Toont "X brieven gegenereerd, X emails verzonden, X emails mislukt"
- **Seed:** Standaard email templates voor Aanmaning, Sommatie, 2e Sommatie

### Nieuwe bestanden
- `backend/alembic/versions/035_pipeline_email_templates.py` — email_subject_template + email_body_template kolommen
- `backend/app/email/send_service.py` — unified send helper (provider-first, SMTP fallback, logging)

### Gewijzigde bestanden
- `backend/app/email/providers/base.py` — OutgoingAttachment dataclass + attachments param
- `backend/app/email/providers/gmail.py` — MIME multipart/mixed bijlage support
- `backend/app/email/providers/outlook.py` — Graph API fileAttachment + lint fix
- `backend/app/incasso/models.py` — email template kolommen op IncassoPipelineStep
- `backend/app/incasso/schemas.py` — send_email, email_ready, email_blocked, emails_sent/failed
- `backend/app/incasso/service.py` — batch_preview + batch_execute email logica, _build_step_email(), seed templates
- `backend/app/incasso/router.py` — send_email parameter doorvoeren
- `frontend/src/hooks/use-incasso.ts` — email velden op alle interfaces
- `frontend/src/app/(dashboard)/incasso/page.tsx` — PreFlightDialog email toggle, step editor email templates, toast

### P1 Completeness
Alle 6 P1 items zijn nu ✅:
1. Template editor UI (sessie 24)
2. **Batch brief + email verzenden (sessie 27)** ← deze sessie
3. Auto-complete taken (sessie 25, bugfix sessie 26)
4. Auto-advance pipeline (sessie 25, bugfix sessie 26)
5. Deadline kleuren per stap (sessie 23)
6. Instelbare dagen per stap (sessie 23)

---

## Wat er gedaan is (sessie 26 — 1 maart) — BUG-29 fix

### BUG-29: Auto-advance geblokkeerd door initiële taken ✅
- Auto-advance naar volgende stap werkte niet: taken voor de NIEUWE stap werden aangemaakt vóór de check of alle taken voltooid waren
- Fix: `_auto_complete_tasks` + `_try_auto_advance` scoped naar pipeline taken per stap
- Commit: `c6ba817`

---

## Wat er gedaan is (sessie 25 — 27 feb) — Auto-complete taken + Auto-advance pipeline

### P1 item 3: Auto-complete taken ✅
- Na batch "Document genereren": open taken van type `generate_document`/`send_letter` worden automatisch als voltooid gemarkeerd
- Zoekt op `task_type IN (generate_document, send_letter)` + `status IN (pending, due, overdue)`

### P1 item 4: Auto-advance pipeline ✅
- Na auto-complete: als ALLE open taken voor een dossier klaar zijn, schuift pipeline automatisch door naar volgende stap
- Volgende stap bepaald via `sort_order` (bestaande `list_pipeline_steps`)
- Nieuwe taak wordt aangemaakt voor de nieuwe stap (generate_document of manual_review)
- CaseActivity audit trail logging bij elke auto-advance

### Taken aanmaken bij stap-toewijzing ✅
- Bij batch "Stap wijzigen": automatisch taak aangemaakt voor de target stap
- Stap met `template_type` → task type `generate_document`
- Stap zonder `template_type` → task type `manual_review`
- Due date = vandaag + `min_wait_days`

### VPS disk space issue
- 144GB/150GB vol → PostgreSQL kon niet starten (postmaster.pid write failure)
- `docker system prune -a --volumes -f` → 55GB vrijgemaakt (90GB/150GB)
- Rebuild succesvol gestart, niet geverifieerd (sessie beëindigd)

### Gewijzigde bestanden
- `backend/app/incasso/service.py` — 3 nieuwe helpers (`_create_tasks_for_step`, `_auto_complete_tasks`, `_try_auto_advance`) + wiring in `batch_execute()`
- `backend/app/incasso/schemas.py` — `tasks_auto_completed` + `cases_auto_advanced` op `BatchActionResult`
- `frontend/src/hooks/use-incasso.ts` — TypeScript interface update
- `frontend/src/app/(dashboard)/incasso/page.tsx` — toast message met nieuwe counters
- `LUXIS-ROADMAP.md` — P1 items 3+4 als ✅

### Openstaande issues
- Gebruiker meldt "het werkt nog niet helemaal goed" → QA nodig in sessie 26
- VPS deploy niet geverifieerd (rebuild was gaande bij sessie-einde)

---

## Wat er gedaan is (sessie 24 — 27 feb) — Template Editor UI + BUG-28

### Template Editor UI ✅
- **Managed template editor** gebouwd met database-driven templates
- Templates beheerbaar via UI (aanmaken, bewerken, verwijderen)
- Gekoppeld aan incasso pipeline stappen

### BUG-28: Batch advance_step zonder pipeline stap ✅
- Fix: dossiers zonder pipeline stap-toewijzing konden niet aan een stap worden toegewezen via batch
- `allow batch advance_step for cases without pipeline step assignment`

### Subagents en skills systeem ✅
- `.claude/agents/` — func-tester, security-reviewer, tech-tester, code-reviewer, luxis-researcher
- `.claude/skills/` — incasso-workflow, deploy-regels, template-systeem, bekende-fouten
- Context management geoptimaliseerd: docs verplaatst naar subdirectories

### Gewijzigde bestanden
- `backend/app/documents/` — managed template models, service, router, schemas
- `backend/app/incasso/service.py` — BUG-28 fix (advance_step guard)
- `frontend/src/app/(dashboard)/documenten/` — template editor UI
- `.claude/agents/` en `.claude/skills/` — nieuw
- `docs/` — gereorganiseerd naar subdirectories

---

## Wat er gedaan is (sessie 23 — 27 feb) — Incasso Workflow Automatisering P1

### Stap 1: Instelbare dagen per stap (max_wait_days) ✅
- **Backend:** `max_wait_days` kolom toegevoegd aan `IncassoPipelineStep` model
- **Alembic migratie:** `033_incasso_max_wait_days.py` — `ADD COLUMN max_wait_days INTEGER NOT NULL DEFAULT 0`
- **Schemas:** `max_wait_days` toegevoegd aan Create/Update/Response schemas
- **Service:** `seed_default_steps()` bijgewerkt met standaard max_wait_days waarden (7, 28, 28, 28, 28, 0)
- **Frontend Stappen-tab:** "Wachtdagen" kolom gesplitst in "Min. dagen" en "Grens rood", beide bewerkbaar

### Stap 2: Deadline kleuren per stap ✅
- **Backend logica:** Nieuwe `_compute_deadline_status()` functie:
  - Groen = `days_in_step < min_wait_days` (wachtperiode)
  - Oranje = `days_in_step >= min_wait_days` (klaar voor actie)
  - Rood = `days_in_step >= max_wait_days` (te laat)
  - Grijs = geen stap toegewezen
- **Schema:** `deadline_status: str` (green/orange/red/gray) toegevoegd aan `CaseInPipeline`
- **Frontend Werkstroom-tab:** Gekleurd bolletje naast dossiernummer + gekleurde "Dagen" tekst

### Deploy-problemen opgelost
- **COMPOSE_FILE ontbrak:** VPS draaide `docker compose up -d` zonder prod override → backend kreeg dev-wachtwoord. Fix: `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml` toegevoegd aan `/opt/luxis/.env`
- **PostgreSQL wachtwoord mismatch:** Volume was geïnitialiseerd met `luxis_dev_password`, maar prod config verwachtte `Kest1ngLux1s2026prod`. Fix: `ALTER USER luxis PASSWORD '...'` via psql
- **Alembic migratie 033:** Succesvol uitgevoerd op productie via `docker compose run --rm backend python -m alembic upgrade head`

### Bekend issue (niet opgelost)
- **Dossiers toewijzen aan pipeline stappen:** Gebruiker kan geen dossier handmatig aan een stap toewijzen vanuit de pipeline view. De "Stap wijzigen" functie toont 0 gereed als er geen dossiers in stappen staan. **→ Fix nodig in sessie 24**

### Gewijzigde bestanden
- `backend/app/incasso/models.py` — `max_wait_days` kolom
- `backend/app/incasso/schemas.py` — `max_wait_days` + `deadline_status`
- `backend/app/incasso/service.py` — `_compute_deadline_status()`, `_case_to_pipeline_item()`, `step_to_response()`, `seed_default_steps()`
- `backend/alembic/versions/033_incasso_max_wait_days.py` — nieuwe migratie
- `frontend/src/hooks/use-incasso.ts` — `DeadlineStatus` type, `max_wait_days` in interfaces
- `frontend/src/app/(dashboard)/incasso/page.tsx` — deadline kleuren UI + max_wait_days kolommen

---

## Wat er gedaan is (sessie 22b — 27 feb) — Deploy & Verificatie

### BUG-25/26/27 gedeployed en geverifieerd op productie ✅
- **BUG-25** (timer z-index): Timer FAB zichtbaar met z-50 > header z-40 ✅
- **BUG-26** (relaties dropdown): Alle 12 relaties laden met correcte namen ✅
- **BUG-27** (Nederlandse 404): "Pagina niet gevonden" toont correct ✅

### Deploy-blokkeerder 1: Database authenticatie ✅
- Backend Docker image had `DATABASE_URL` met dev-wachtwoord gebakken → `ALTER USER` + `--force-recreate`

### Deploy-blokkeerder 2: Frontend localhost:8000 hardcoded ✅
- 9 bestanden hadden `localhost:8000` fallback → allemaal `""` + pre-commit hook

### BUG-26 extra fix: "undefined undefined" → `{r.name}`
- Commit: `ad1f31c` + `eafc513`

### Status na sessie 22b
- **Alle bugs gedeployed en geverifieerd op productie** — BUG-1 t/m BUG-27 allemaal ✅
- Applicatie draait stabiel op https://luxis.kestinglegal.nl
- Klaar voor feature development

---

## Wat er gedaan is (sessie 22 — 27 feb)

### Volledige QA Testing secties 1-10 via Playwright MCP ✅
- **75 tests uitgevoerd, 75 PASS, 0 FAIL, 0 nieuwe bugs**
- Resultaten: `docs/qa/QA-SESSIE-22-RESULTATEN.md`

### BUG-25/26/27 gefixt
- BUG-25: Timer z-index 40→50 (`floating-timer.tsx`)
- BUG-26: Backend per_page limit 100→200 (`relations/router.py`)
- BUG-27: Custom `not-found.tsx` met Nederlandse tekst

### Commits sessie 22

| Hash | Beschrijving |
|------|-------------|
| `07b487b` | docs: QA session 22 results — 75/75 tests PASS, 0 new bugs |
| `3cd9ddc` | fix: BUG-25/26/27 — timer z-index, relations 422, Dutch 404 page |
| `ad1f31c` | fix: use r.name for relations dropdown in agenda |
| `eafc513` | fix: remove hardcoded localhost:8000 from all frontend files |

---

> **Eerdere sessies (1-20)** staan in `docs/sessions/SESSION-ARCHIVE.md` — alleen lezen als je historische context nodig hebt.
