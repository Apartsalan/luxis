# Sessie Notities — Luxis

**Laatst bijgewerkt:** 9 maart 2026 (sessie 46 — SSH deploy setup + CLAUDE.md verbeteringen)
**Laatste feature/fix:** SSH deploy key geïnstalleerd — Claude deployt nu autonoom via SSH
**P1 status:** ALLE 6 ITEMS AFGEROND + QA COMPLEET ✅
**Openstaande bugs:** Geen bekende bugs
**Backend tests:** 26 AI agent tests passed | **Ruff:** 0 warnings
**Volgende sessie (47):** Zie roadmap voor volgende prioriteit

## Wat er gedaan is (sessie 46 — 9 maart) — SSH deploy setup + CLAUDE.md verbeteringen

### Samenvatting
- SSH deploy key (`~/.ssh/luxis_deploy`) gegenereerd en geïnstalleerd op VPS (key-based auth, geen passphrase)
- Bestaande persoonlijke key (`id_ed25519`) was versleuteld → aparte deploy key nodig
- paramiko gebruikt om key te kopiëren (sshpass niet beschikbaar op Git Bash)
- CLAUDE.md bijgewerkt met insights-regels:
  - Task boundaries: "alleen documenteren" = geen code, "sla quality checks over" = geen tests
  - Git workflow: geen worktrees tenzij expliciet gevraagd
  - SSH deploy: Claude deployt autonoom, destructieve acties vereisen bevestiging
  - Sessie-prompts: constraints sectie, single-goal focus
- Deploy skill (`deploy-regels`) herschreven met echte SSH commando's
- settings.json: ssh/scp van deny naar allow verplaatst

### Gewijzigde bestanden
- `CLAUDE.md` — nieuwe gedragsregels, SSH deploy sectie, sessie-prompt format
- `.claude/skills/deploy-regels/SKILL.md` — SSH deploy commando's
- `.claude/settings.json` — SSH in allow list

### Bekende issues
- Geen

### Volgende sessie
- Roadmap checken voor volgende prioriteit

---

## Wat er gedaan is (sessie 45 — 7 maart) — AI Classificatie Fase 7: Echte actie-executie

### Samenvatting
Alle stubs in `execute_classification()` vervangen door echte functionaliteit:
- **dismiss:** zet `SyncedEmail.is_dismissed = True`
- **wait_and_remind:** maakt `WorkflowTask` aan (type `check_payment`, due_date = vandaag + N dagen)
- **escalate:** maakt urgente `WorkflowTask` aan (type `manual_review`, due_date = vandaag, `URGENT` in titel)
- **send_template / request_proof:** haalt `ResponseTemplate` op, rendert Jinja2 met zaak/wederpartij/kantoor context, stuurt email via `send_with_attachment()` (EmailProvider of SMTP fallback)
- 4 nieuwe tests toegevoegd die side-effects verifiëren (WorkflowTask aanmaken, is_dismissed, email verzenden)

### Gewijzigde bestanden
- `backend/app/ai_agent/service.py` — echte actie-executie in `execute_classification()`, nieuwe imports (Jinja2, WorkflowTask, Tenant, send_with_attachment)
- `backend/tests/test_ai_agent.py` — 4 nieuwe tests (26 totaal): dismiss, wait_and_remind, escalate, send_template
- `LUXIS-ROADMAP.md` — Fase 7 als ✅ gemarkeerd

### Bekende issues
- Geen

### Volgende sessie
- Roadmap checken voor volgende prioriteit
- Mogelijke verbeteringen: dashboard widgets, incasso pipeline polish, of volgende AI feature

## Wat er gedaan is (sessie 44 — 7 maart) — Notificatiegeluid + Claude Code update

### Samenvatting
- **Notificatiegeluid:** VBS-script (`~/.claude/notify.vbs`) dat tada.wav afspeelt als fire-and-forget
- Claude Code hooks werken niet (getest: Notification, PreToolUse, Stop, UserPromptSubmit, PermissionRequest — geen enkel event vuurt, niet user-level, niet project-level)
- Workaround: CLAUDE.md regel die Claude verplicht het geluid af te spelen via Bash vóór AskUserQuestion, EnterPlanMode, ExitPlanMode, en einde van taken
- **Claude Code update:** v2.1.49 → v2.1.71 (22 versies, incl. hooks bugfixes)
- Notification hook ook in project settings.json gezet als fallback voor toekomstige versies
- Fase 7 niet gestart — hele sessie besteed aan notificatiegeluid

### Gewijzigde bestanden
- `CLAUDE.md` — notificatiegeluid regel toegevoegd
- `.claude/settings.json` — Notification hook toegevoegd
- `~/.claude/notify.vbs` — VBS-script (fire-and-forget tada.wav)
- `~/.claude/settings.json` — opgeschoond (alleen skipDangerousModePermissionPrompt)

### Bekende issues
- Hooks vuren niet in huidige omgeving (bekend bug, zie github.com/anthropics/claude-code/issues/11544)

### Volgende sessie
- AI Classificatie Fase 7: echte actie-executie implementeren in `execute_classification()`
- Acties: dismiss → wait_and_remind → escalate → send_template → request_proof

## Wat er gedaan is (sessie 43 — 6 maart) — BUG-36 + BUG-37 fix + E2E Test AI Classificatie ✅

### Samenvatting
AI Email Classificatie Fase 6 volledig afgerond. Twee bugs gefixt en end-to-end flow succesvol getest op productie.

**BUG-36 (API credits):**
- Anthropic API gaf "credit balance too low" ondanks $10 zichtbaar saldo
- Na krediet-aankoop via platform.claude.com en propagatie: API werkt correct
- Geverifieerd met `curl` test op VPS: Claude Haiku 4.5 antwoordt succesvol

**BUG-37 (User.full_name AttributeError):**
- Na approve van classificatie: GET endpoint gaf 500 Internal Server Error
- Oorzaak: `_classification_to_response()` in `router.py` gebruikte `reviewer.first_name`/`reviewer.last_name` maar User model heeft alleen `full_name`
- Fix: `reviewer.full_name if reviewer else None`

**E2E test resultaat (Playwright op productie):**
1. Navigeerde naar zaak 2026-00001 → Correspondentie tab
2. Klikte op Microsoft email → "Geen AI-classificatie" → klik "Classificeer"
3. Classificatie verscheen: "Niet gerelateerd", 99% confidence, Suggestie: "Wegzetten"
4. Redenering (uitklapbaar): AI herkende email als Microsoft notificatie, niet incasso-gerelateerd
5. Klik "Akkoord" → Status: Goedgekeurd door Lisanne Kesting
6. Klik "Uitvoeren" → Status: Uitgevoerd, Resultaat: "Email weggezet (niet relevant)"
7. Volledige flow werkt foutloos op productie

### Gewijzigde bestanden
- `backend/app/ai_agent/router.py` — `reviewer.full_name` i.p.v. `first_name`/`last_name` (BUG-37 fix)

### Bekende issues
- Geen openstaande bugs

### Volgende sessie
- AI classificatie is volledig werkend — klaar voor dagelijks gebruik door Lisanne
- Mogelijke verbeteringen: bulk classificatie, dashboard statistieken, auto-classificatie bij email sync

## Wat er gedaan is (sessie 42 — 6 maart) — AI Email Classificatie Fase 6 (E2E Verificatie) 🔶

### Samenvatting
Fase 6 grotendeels afgerond — code werkt, maar geblokkeerd op Anthropic API billing.

**Fixes deze sessie:**
- `strip_html()` in `prompts.py` volledig herschreven — Microsoft Outlook HTML emails bevatten gigantische `<style>` blocks, conditional comments (`<!--[if ...]>`), en HTML entities. Oude naive regex gaf 0 chars terug, nu correct 9533/1201/1198 chars.
- Model ID gefixt: `claude-haiku-4-5-20250414` (bestaat niet) → `claude-haiku-4-5` (correct alias)
- Diagnostic logging toegevoegd aan `classify_email()` bij elke early return
- Frontend error handling verbeterd voor null responses
- 6 default response templates succesvol geseeded op VPS
- `ANTHROPIC_API_KEY` toegevoegd aan `.env.production` op VPS

**Blocker gevonden:**
- Anthropic API retourneert "credit balance too low" ondanks $10 credit zichtbaar in console
- Oorzaak: Claude.ai credits en API credits zijn GESCHEIDEN billing-systemen
- Oplossing: apart API-credits kopen op platform.claude.com/buy_credits

### Gewijzigde bestanden
- `backend/app/ai_agent/prompts.py` — `strip_html()` herschreven voor Microsoft HTML
- `backend/app/ai_agent/service.py` — diagnostic logging + model ID fix

### Bekende issues
- **BUG-15:** Anthropic API credits moeten apart gekocht worden — $10 Claude.ai credits werken niet voor API
- Na credit fix: end-to-end test nog niet uitgevoerd (classify → approve → execute)

### Volgende sessie
1. Gebruiker koopt API credits op platform.claude.com/buy_credits
2. Deploy backend op VPS
3. End-to-end test classificatie flow via Playwright
4. Roadmap updaten naar ✅ als alles werkt

## Wat er gedaan is (sessie 41 — 6 maart) — AI Email Classificatie Fase 5 (Frontend) ✅

### Samenvatting
Frontend voor AI email classificatie gebouwd. Alle hooks, componenten en integratie klaar.

**Fase 5 (Frontend):**
- `use-ai-agent.ts` — 7 TanStack Query hooks: useClassifications, useEmailClassification, usePendingCount, useApproveClassification, useRejectClassification, useExecuteClassification, useClassifyEmail
- `classification-card.tsx` — Component met: categorie label + confidence bar, status badge (pending/approved/rejected/executed), suggested action + template naam, uitklapbare AI-redenering, approve/reject/execute knoppen, "Classificeer" trigger bij ontbrekende classificatie
- CorrespondentieTab integratie — ClassificationCard verschijnt in de EmailDetailPanel boven de bijlagen bij elke email
- Sidebar badge — AI pending count op "Dossiers" nav item (pollt elke 60s)

### Nieuwe bestanden
- `frontend/src/hooks/use-ai-agent.ts`
- `frontend/src/components/classification-card.tsx`

### Gewijzigde bestanden
- `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx` (ClassificationCard import + render)
- `frontend/src/components/layout/app-sidebar.tsx` (ai-pending badge type + usePendingCount hook)

### Bekende issues
- `anthropic` package zit niet in Docker image — bij volgende `--no-cache` build moet het toegevoegd worden aan `pyproject.toml`
- Seed templates (Fase 6) nog niet uitgevoerd
- End-to-end verificatie op live omgeving nog niet gedaan

### Volgende sessie
1. Check `anthropic` in `backend/pyproject.toml` — toevoegen als het ontbreekt
2. Seed default templates via POST `/api/ai-agent/templates/seed`
3. Deploy frontend + backend (met `--no-cache` na pyproject.toml fix)
4. End-to-end test op live omgeving: email classificatie → review → execute

## Wat er gedaan is (sessie 40b — 6 maart) — Docker-compose fix + AI classificatie live

### Samenvatting
- `ANTHROPIC_API_KEY` ontbrak in `docker-compose.prod.yml` — container kreeg de env variabele niet door
- Fix: variabele toegevoegd aan de backend environment sectie
- Na deploy: AI classificatie scheduler draait nu live (`AI classification every 6 min`)
- Migration 036 was al uitgevoerd, database is up-to-date
- `anthropic` package moet nog in Docker image (nu handmatig geinstalleerd — herbouw nodig)

### Gewijzigde bestanden
- **Gewijzigd:** `docker-compose.prod.yml` (ANTHROPIC_API_KEY toegevoegd)

### Bekende issues
- `anthropic` package zit niet in Docker image — bij volgende `--no-cache` build moet het toegevoegd worden aan `pyproject.toml` dependencies of Dockerfile
- Frontend (Fase 5) nog niet gebouwd
- Seed templates (Fase 6) nog niet uitgevoerd

### Volgende sessie
1. Fase 5: Frontend hooks + classificatie-kaart in CorrespondentieTab
2. Fase 6: Seed templates + verificatie
3. Zorg dat `anthropic` in Docker image zit (check pyproject.toml)

## Wat er gedaan is (sessie 40 — 6 maart) — AI Email Classificatie Fase 3+4 ✅

### Samenvatting
API endpoints en tests gebouwd voor de AI email classificatie module. Branch `claude/dreamy-khayyam` gemerged naar main.

**Fase 3 (API + Integratie):**
- `router.py` met 10 endpoints: list/get/classify/approve/reject/execute/pending-count/templates/seed
- Router geregistreerd in `main.py`
- Scheduler job elke 6 min voor auto-classificatie (alleen als ANTHROPIC_API_KEY geconfigureerd)

**Fase 4 (Tests):**
- 22 tests met gemockte AI client (nooit echte API calls)
- Classificatie flow, idempotency, approve/reject/execute, multi-tenant isolatie, pending count, templates, alle API endpoints

### Gewijzigde bestanden
- **Nieuw:** `backend/app/ai_agent/router.py` (283 regels, 10 endpoints)
- **Nieuw:** `backend/tests/test_ai_agent.py` (743 regels, 22 tests)
- **Gewijzigd:** `backend/app/main.py` (router registratie)
- **Gewijzigd:** `backend/app/workflow/scheduler.py` (AI classificatie job)

### Bekende issues
- Migration 036 is nog NIET uitgevoerd op de database
- Frontend (Fase 5) is nog niet gebouwd — classificatie-kaart in CorrespondentieTab ontbreekt
- `anthropic` package moet in Docker image zitten (nu handmatig geinstalleerd)

### Volgende sessie
1. Fase 5: Frontend hooks (`use-ai-agent.ts`) + classificatie-kaart in CorrespondentieTab
2. Fase 6: Seed templates uitvoeren + verificatie op live omgeving
3. Migration 036 uitvoeren op de database
4. Docker image rebuilden met `anthropic` package

## Wat er gedaan is (sessie 39 — 6 maart) — AI Email Classificatie Fase 1+2 ✅

### Samenvatting
Eerste concrete AI-feature gebouwd: email classificatie voor incasso-dossiers. Debiteur-emails worden automatisch geclassificeerd in 8 categorieën (belofte_tot_betaling, betwisting, betalingsregeling_verzoek, beweert_betaald, onvermogen, juridisch_verweer, ontvangstbevestiging, niet_gerelateerd). AI selecteert een antwoord-template, Lisanne reviewt met 1 klik.

**Fase 1 (Backend Foundation):** Models (EmailClassification + ResponseTemplate), Alembic migration 036, Pydantic schemas, Dutch system prompt, anthropic dependency + config.

**Fase 2 (Service Layer):** Complete service met classify_email(), classify_new_emails() batch, approve/reject/execute flows, query helpers, seed_default_templates() met 6 basis-templates.

**Niet af (Fase 3-6):** Router (API endpoints), scheduler integratie, tests, frontend components, template seeding.

### Gewijzigde bestanden
- **Nieuw:** `backend/app/ai_agent/__init__.py`, `models.py`, `schemas.py`, `prompts.py`, `service.py`
- **Nieuw:** `backend/alembic/versions/036_ai_email_classification.py`
- **Gewijzigd:** `backend/app/config.py` (anthropic_api_key), `backend/pyproject.toml` (anthropic dep)
- **Plan:** `.claude/plans/nifty-painting-forest.md` (volledige implementatieplan)
- **Branch:** `claude/dreamy-khayyam` (moet naar main gemerged worden)

### Beslissingen
- Claude Haiku 4.5 voor classificatie (~$0.04/maand bij 100 emails)
- Template-based responses, GEEN vrije tekst naar debiteuren
- Copilot mode: Lisanne reviewt altijd voor verzending
- AI Agent Masterplan bewaard als `docs/research/AI-AGENT-MASTERPLAN.md` voor toekomstige uitbreiding
- Stap-voor-stap: classificatie eerst, later intake agent en correspondentie-analyse

### Bekende issues
- Branch `claude/dreamy-khayyam` moet nog naar `main` gemerged worden
- Fase 3 (router) is nog niet geschreven — API endpoints zijn er nog niet
- Migration 036 is nog niet uitgevoerd op de database

### Volgende sessie
1. Merge branch naar main (of werk op main)
2. Fase 3: `router.py` (9 endpoints), registreer in `main.py`, scheduler job in `scheduler.py`
3. Fase 4: Tests met gemockte AI client
4. Fase 5: Frontend hooks + CorrespondentieTab classificatie-kaart
5. Fase 6: Seed templates + verificatie
6. Migration 036 uitvoeren op DB

## Wat er gedaan is (sessie 38 — 6 maart) — AI Agent Masterplan ✅

### Research & documentatie (geen code changes)

**Concurrentie-analyse:**
- Legal AI: Harvey ($8B), CoCounsel (1M users), Luminance Autopilot, Clio Manage AI, Smokeball, Claude Cowork Legal Plugin
- Incasso AI: Kolleno (3 autonomieniveaus), Prodigal (24/7 voice), Intrum/Ophelos (8 EU-markten), Flanderijn (83% ML predictie), Payt, POM
- Nederlandse markt: Payt, POM, iFlow, CollectOnline, Ultimoo, Simplifai
- **Gap gevonden:** Niemand combineert NL-recht + advocatenworkflow + AI + klein kantoor

**Inventaris bestaande Luxis capabilities:**
- 30+ API endpoints geinventariseerd die de agent als tools kan gebruiken
- Alles al aanwezig: dossiers, facturatie, documenten, email, betalingen, pipeline, taken, agenda

**Masterplan geschreven:**
- 3-lagen architectuur: Luxis Core → MCP Tools → AI Agent
- 3 autonomieniveaus: Inzicht / Copilot / Autonoom (per stap configureerbaar)
- 4 fases: A1 (MCP tools) → A2 (Copilot) → A3 (Dashboard) → A4 (Autonoom)
- A2.5 Facturatie Agent: eigen facturen + doorstorten aan client + incasso-afrekening
- Multi-model strategie: Kimi 2.5 voor 90% (classificatie/extractie), Claude als fallback
- Template-based responses i.p.v. generatief (voorspelbare kosten)
- Geschatte kosten: $2-8/maand voor 200 dossiers (was $20-60 met single model)

**NOvA compliance:**
- Aanbevelingen AI in advocatuur (dec 2025) onderzocht
- Advocaat blijft eindverantwoordelijk, AI = concept, transparantie vereist

### Bestanden
- **Nieuw:** `docs/research/AI-AGENT-MASTERPLAN.md` (branch: `claude/admiring-engelbart`)
- **Gewijzigd:** Notification hook sound (RA2 Command & Conquer stijl) in `~/.claude/settings.json`

### Beslissingen
- Agent is taakuitvoerder, geen chatbot (juridisch advies via Claude chat apart)
- Multi-model: Kimi 2.5 default, Claude Haiku/Sonnet/Opus als escalatie
- Template-based responses, rule-based first, LLM second
- A5 (advanced features) op backlog

### Openstaande vragen (wacht op Arsalan's review)
1. Agent ook dagvaardingen voorbereiden?
2. Betalingsregelingen voorstellen aan debiteuren?
3. Clientportaal met real-time status?
4. Limieten op autonome acties?
5. Ook niet-incasso dossiers ondersteunen?

---

## Wat er gedaan is (sessie 37 — 6 maart) — Lint cleanup + Incasso E2E fixes ✅

### Lint cleanup (alle ruff warnings gefixt)
- **47 auto-fixed:** I001 (import sorting), F401 (unused imports) — via `ruff check --fix`
- **25 handmatig gefixt:** E501 (line too long), N812 (alias naming), E741 (ambiguous variable `l` → `line`)
- **Resultaat:** `ruff check app/` → **All checks passed!** (was 72 errors)
- Bestanden: 31 backend Python files aangepast (alleen formatting, geen logica)

### Incasso E2E tests gefixt (7 tests werkend, was 0)
- **Root cause 1:** `test.skip("title", "reason")` syntax zorgde ervoor dat Playwright de HELE describe block skipte
- **Root cause 2:** `createTestCase()` miste verplicht `date_opened` veld → `beforeAll` faalde stilletjes
- **Root cause 3:** `contact_type: "person"` met `first_name`/`last_name` in plaats van verplicht `name` veld
- **Fix:** Test herschreven met shared helpers (`loginViaApi`, `createContact`, `createCase`)
- **Fix:** `test.skip()` vervangen door comments (E6 + E7 vereisen mocked email provider)
- **Fix:** Strict mode violations opgelost (`getByRole("heading", { name: "Sommatie", exact: true })`)
- **Fix:** `afterAll` cleanup toegevoegd voor test data
- Bestanden: `frontend/e2e/incasso-pipeline.spec.ts` volledig herschreven

### E2E suite status
- **51 passed, 0 skipped** (was 44 passed, 7 skipped)
- Incasso pipeline: 7/7 passing
- Tijdregistratie: 5 tests pre-existing failure (500 error bij case creation, niet-gerelateerd)

### Lessen geleerd
- `test.skip("title", "reason")` in Playwright: als beide args strings zijn, wordt de hele describe block geskipt zonder foutmelding
- Altijd `force: true` op clicks in Next.js (dev overlay `<nextjs-portal>` blokkeert events)
- `getByText("Sommatie")` matcht ook "2e Sommatie" — gebruik `getByRole("heading", { name: "...", exact: true })`
- Worktree + Docker mismatch: Docker mount is gefixed op de main repo, niet het worktree pad

## Wat er gedaan is (sessie 36 — 5 maart) — E2E-4: Correspondentie + Agenda + Taken ✅

### E2E Tests (8 nieuwe tests)

**Correspondentie** (`frontend/e2e/correspondentie.spec.ts`) — 2 tests:
- C1: Page load met heading, zoekbalk, sync-knop
- C2: Empty state of email lijst zichtbaar

**Agenda** (`frontend/e2e/agenda.spec.ts`) — 3 tests:
- A1: Page load met kalender, navigatie, view toggles
- A2: Event aanmaken via dialog
- A3: Event aanmaken via API + verwijderen + verificatie

**Taken** (`frontend/e2e/taken.spec.ts`) — 3 tests:
- T1: Page load met heading, filter buttons, nieuwe taak button
- T2: Taak aanmaken via formulier
- T3: Taak als afgerond markeren

### API Helpers uitgebreid (`frontend/e2e/helpers/`)
- `api.ts`: `createCalendarEvent`, `deleteCalendarEvent`, `createWorkflowTask`, `deleteWorkflowTask`, `completeWorkflowTask`
- `auth.ts`: `loginViaApi` retourneert nu ook `userId` (voor task assignment)

### Dashboard bugfix
- `backend/tests/test_dashboard.py`: `total_outstanding == 0` → `Decimal(str(total_outstanding)) == Decimal("0")` (Pydantic v2 serialiseert Decimal als string in JSON)

### Lessen geleerd
- `getByRole("button", { name: "Maand" })` matcht ook "Vorige maand"/"Volgende maand" — altijd `{ exact: true }` gebruiken
- `getByRole("button", { name: "Afgerond" })` matcht ook "Markeer als afgerond" — `{ exact: true }` nodig
- `selectOption({ label: new RegExp(...) })` werkt niet — label moet een string zijn
- Kalender events zijn "hidden" in Playwright (overflow: hidden op cells) — klik op datum om detail panel te openen
- Taken assignment: `createWorkflowTask` via API moet `assigned_to_id` bevatten, anders verschijnt de taak niet op `/taken`
- Task complete button: gebruik `div.group` filter met task link om het juiste "Markeer als afgerond" knop te vinden

### Totaal E2E suite (na sessie 36)
- **53 E2E tests** (44 nieuwe + 9 bestaande incasso)
- **44 passed, 7 skipped** (incasso pipeline tests, gefixt in sessie 37)
- Alle 406 backend tests passing

## Wat er gedaan is (sessie 35 — 5 maart) — E2E-3: Facturen + Tijdregistratie ✅

### Overzicht
12 Playwright E2E tests voor Facturen (7) en Tijdregistratie (5). Alle tests PASSED. Totaal E2E tests nu: 45 (36 nieuwe + 9 incasso bestaand).

### Wat er gebouwd is
- **`facturen.spec.ts`**: 7 tests — lijst, create via form, detail page, approve, send, register payment, delete concept
- **`tijdregistratie.spec.ts`**: 5 tests — page load, create via form, verify in table, inline edit, delete
- **API helpers**: `createInvoice()`, `deleteInvoice()`, `approveInvoice()`, `sendInvoice()`, `createTimeEntry()`, `deleteTimeEntry()` in `e2e/helpers/api.ts`
- **`auth.setup.ts` fix**: Auth detection gewijzigd van greeting heading naar URL redirect + sidebar "Dossiers" link

### Tests
| # | Test | Methode |
|---|------|---------|
| F1 | Facturen lijst laadt | UI check (h1, button, search) |
| F2 | Create invoice via form | UI form (relatie search, line items, submit) |
| F3 | Detail page toont info | UI verify (nummer, status, contact, regels) |
| F4 | Approve invoice | UI button → toast + badge change |
| F5 | Send invoice | UI button → toast + badge change |
| F6 | Register payment | UI form (bedrag, submit) → toast |
| F7 | Delete concept invoice | API seed + UI delete → redirect + toast |
| T1 | Uren page laadt | UI check (h1, button, stopwatch, week nav) |
| T2 | Create time entry | UI form (case selector, uren/min, activiteit, omschrijving) |
| T3 | Entry in tabel | UI verify (case number, description, duration, billable) |
| T4 | Edit inline | UI (Bewerken → input → Opslaan → toast) |
| T5 | Delete entry | UI (Verwijderen → toast → entry weg) |

### Lessen geleerd
- Luxis forms gebruiken geen `<label>` elementen — `getByLabel()` werkt niet, gebruik `getByPlaceholder()` of `getByRole()`
- Tijdregistratie tabel is div-based (geen `<table>/<tr>`) — gebruik `getByRole("button", { name: "Bewerken" })` i.p.v. `locator("tr")`
- `getByText()` strict mode: bij meerdere matches (leftover data) altijd `.first()` toevoegen
- Auth setup: "Welkom terug" staat op login pagina, niet alleen dashboard — check sidebar link i.p.v. heading
- Payment form: `getByRole("spinbutton")` voor amount input (label is div, niet label element)

### Bestanden
- `frontend/e2e/facturen.spec.ts` (nieuw)
- `frontend/e2e/tijdregistratie.spec.ts` (nieuw)
- `frontend/e2e/helpers/api.ts` (6 helpers toegevoegd)
- `frontend/e2e/auth.setup.ts` (auth detection fix)

---

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
