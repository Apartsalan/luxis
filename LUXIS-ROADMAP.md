# Luxis — Project Roadmap (Source of Truth)

**Laatst bijgewerkt:** 27 maart 2026 (sessie 109 — Backup + security + backend tests)
**Product:** Praktijkmanagementsysteem voor Nederlandse advocatenkantoren
**Eerste klant:** Kesting Legal (Lisanne Kesting, 1 advocaat, incasso/insolventie, Amsterdam)
**Productie:** https://luxis.kestinglegal.nl
**Repo:** https://github.com/Apartsalan/luxis.git (branch: main)

---

## Over het team

**Arsalan** — geen developer. IT-recruitment + business development voor Kesting Legal. Bouwt volledig samen met AI (Claude Code). Beschikbare tijd: 6-10 uur per week. Kan geen code reviewen — het systeem moet zelfcontrolerend zijn.

**Lisanne Kesting** — mr., advocaat, beëdigd 14-02-2018, arrondissement Amsterdam. VIA-lid. Enige advocaat bij Kesting Legal. Specialisatie: incasso en insolventierecht. MKB-cliënten, incassobureaus, deurwaarders. 250+ procedures gevoerd. Kantoor: IJsbaanpad 9, 1076 CV Amsterdam. KvK: 88601536.

**Huidig systeem:** Basenet (wordt pas opgezegd als Luxis de dagelijkse workflow volledig overneemt)
**Boekhouding:** Exact Online (gekoppeld aan Basenet)
**E-mail:** Outlook/365

---

## Huidige status

| Laag | Volwassenheid | Toelichting |
|------|--------------|-------------|
| Backend (FastAPI) | ~92% | 231 endpoints, 25 routers, 34 models, ~430 tests. Financial calcs uitstekend getest. Alle 7 eerder ongeteste routers nu gedekt (calendar, settings, search, notifications, collections, email, incasso). GAT: ruff format 97 files. |
| Frontend (Next.js) | ~82% | 24 pagina's (0 stubs), 29 hooks, 29 componenten. Alle 17 backend modules hebben frontend. Skeleton loaders, error boundaries, toast notifications, mobile responsive. 65 `any` types gekilld ✅, hooks cleanup ✅. GAT: E2E mist settings/OAuth/docs. Stitch redesign gepland. |
| Infra/DevOps | ~90% | Docker Compose op Hetzner VPS. Caddy reverse proxy (in repo ✅). SSH deploy key. 43 migraties, RLS, token rotation. CI/CD pipeline ✅ (GitHub Actions: lint, tests, typecheck, build, security + auto-deploy). docker-compose.prod.yml ✅. DEPLOY_SSH_KEY secret ✅. Auto-deploy na groene CI ✅. Backup actief ✅ (DB + uploads, 7-dag rotatie, dagelijks 03:00). fail2ban ✅. unattended-upgrades ✅. GAT: backend tests falen in bare-metal CI (pytest-asyncio). |

**Rode draad:** Backend is functioneel compleet maar mist router-level tests. Frontend is feature-compleet maar mist TypeScript strictness + redesign. Infra Fase 1 compleet ✅ (CI/CD + backup + security).

**TODO (klein):**
- ✅ VPS kernel reboot — 6.8.0-106 (gedaan sessie 109, terminal 3)
- ⏳ Off-site backup via rclone → Backblaze B2 (~€1/mnd). Backups staan nu alleen op de VPS zelf — bij serververlies ben je alles kwijt. Script is al voorbereid, alleen rclone config + B2 bucket nodig.

**Roadmap naar ~98% (13-15 sessies):**
1. Infra hardening (CI/CD ✅, Caddy in repo ✅, backup ✅, security ✅) — 3 sessies — COMPLEET ✅
2. Backend test coverage (7/7 routers getest ✅, 61 nieuwe tests, email import bug gefixt) — COMPLEET ✅
3. Frontend structureel (65x `any` gekilld ✅, hooks cleanup ✅) — COMPLEET ✅
4. Stitch redesign (nieuw design, component-voor-component) — 3-5 sessies
5. Frontend E2E + polish (tests na redesign, a11y, performance) — 2 sessies
6. Final hardening (API docs, disaster recovery, runbook) — 1 sessie

---

## Projectdocumenten

### In de Git repo (`C:\Users\arsal\Documents\luxis\`)

| Document | Doel | Status |
|----------|------|--------|
| `LUXIS-ROADMAP.md` | **Dit document** — overzicht van alles. Status, prioriteit, bugs, features | **ENIGE source of truth** — alle andere docs verwijzen hiernaar |
| `CLAUDE.md` | AI development guide, architectuurregels, werkwijze | Actief, bijwerken bij nieuwe afspraken |
| `backend/CLAUDE.md` | Backend-specifieke conventies | Actief |
| `frontend/CLAUDE.md` | Frontend-specifieke conventies | Actief |
| `DECISIONS.md` | Tech stack keuzes + onderbouwing | Definitief (niet wijzigen tenzij stack verandert) |
| `FEATURE-INVENTORY.md` | Complete feature-inventaris (alle 15 modules) | Referentie — de "wat zou kunnen" lijst |
| `UX-REVIEW.md` | Kritische UX analyse per feature vs. concurrentie | Referentie — de "waar staan we" analyse |
| `UX-VERBETERPLAN.md` | Gedetailleerde bouw-instructies per UX feature | Detail-doc — status/prioriteit staat hier in roadmap |
| `BUGS-EN-VERBETERPUNTEN.md` | Gedetailleerde bug-beschrijvingen met bestanden, regelnummers en fix-instructies | Detail-doc — status/prioriteit staat hier in roadmap |
| `PROMPT-TEMPLATES-IN-WORKFLOW.md` | Spec voor templates + email in workflow | Gepland (dependency: B1 zaakdetail tabs) |

### Op Bureaublad (`C:\Users\arsal\OneDrive\Bureaublad\Kesting Legal\Luxis\`)

| Document | Doel | Status |
|----------|------|--------|
| `LUXIS-PROJECT-PROMPT.md` | Oorspronkelijk projectbriefing (wie, wat, waarom, fasering) | Verwerkt in deze roadmap — bewaren als archief |
| `TECH-STACK-DECISION-PROMPT.md` | Opdracht die leidde tot DECISIONS.md | Verwerkt — bewaren als archief |


---

## Tech Stack (samenvatting)

> Volledige onderbouwing: zie `DECISIONS.md`

- **Backend:** FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic + PostgreSQL 16
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind CSS
- **Auth:** Custom JWT (python-jose + bcrypt)
- **Docs:** docxtpl + WeasyPrint
- **Queue:** Celery + Redis
- **Hosting:** Hetzner VPS (CX33, ~5,49/mnd) + Docker Compose + Nginx + Let's Encrypt
- **Monitoring:** Sentry (~26/mnd)
- **Kosten:** ~35/mnd totaal

---

## Kernregels

1. **Financial precision:** ALL money = Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NEVER float.
2. **Multi-tenant isolation:** `TenantBase` + `tenant_id` op alles. Row-Level Security.
3. **Dutch UI, English code.**
4. **Onderzoek eerst, bouw daarna.** Elke feature: onderzoek → plan → bouw → check.
5. **Lisanne-toets:** "Zou ze dit begrijpen zonder uitleg?" Zo nee, versimpel.
6. **Product, geen tooltje.** Elk scherm alsof het morgen gelanceerd wordt.

---

## Wat er al gebouwd is

### Backend (110+ endpoints, 13 routers)
- **Auth:** Login, refresh, registration, password change, user/tenant CRUD
- **Relaties:** CRUD, zoeken, typefilter, contact links (persoon-bedrijf)
- **Zaken:** CRUD, status workflow (enforced transitions), activities, parties, conflict check
- **Tijdschrijven:** CRUD, dagfilter, zaakfilter, summary, `/my/today` endpoint
- **Facturatie:** CRUD, lifecycle (concept→goedgekeurd→verzonden→betaald), PDF generatie, BTW
- **Onkosten:** CRUD, billable/uninvoiced tracking
- **Documenten:** Templates beheer, document generatie (docx/pdf), merge fields
- **Workflow:** Rules, taken CRUD, status transities, scheduler, verjaring bewaking
- **KYC/WWFT:** Identificatie, UBO, PEP/sanctie, risicoclassificatie, review scheduling
- **Incasso:** Claims, betalingen, arrangementen, derdengelden, wettelijke rente (compound), WIK/BIK, art. 6:44 BW imputatie, financieel overzicht
- **Dashboard:** Summary, recent activity, my-tasks
- **Settings:** Tenant CRUD, module management
- **Health:** Health check endpoint

### Frontend (pagina's)
- Login
- Dashboard (statistieken, recente zaken, deadlines, KYC warnings, incasso pipeline)
- Relaties (lijst, detail, aanmaken, bewerken)
- Zaken (lijst, detail, aanmaken, status wijzigen, workflow taken)
- Tijdschrijven (lijst, invoer, bewerken)
- Facturatie (lijst, aanmaken, PDF download, status transities)
- Documenten (template catalogus, generatie)
- Agenda (maand/week view, kleurcodering)
- Instellingen (kantoorgegevens, modules)

### Module systeem
Togglebare modules per tenant: `incasso`, `tijdschrijven`, `facturatie`, `wwft`, `budget`

---

## Wat er gebouwd moet worden

### Fase A: Quick Wins — Backend is al klaar (puur frontend)

| # | Feature | API klaar? | Complexiteit | Status |
|---|---------|-----------|-------------|--------|
| A1 | Timer voor tijdschrijven | ✅ `/my/today` | Klein | ✅ Gebouwd (floating timer, persistent via localStorage, globale context) |
| A2 | Global search (Ctrl+K) | ✅ `/api/search` endpoint gebouwd (F1, commit `97e9d22`) | Klein-Midden | ✅ Gebouwd (backend search router + frontend werkt) |
| A3 | "Mijn Taken" pagina | ✅ `/dashboard/my-tasks` | Klein | ✅ Gebouwd (dedicated pagina, groepering op datum, filter, complete/skip met 1 klik) |
| A4 | Activity timeline op zaakdetail | ✅ `/cases/{id}/activities` | Klein-Midden | ✅ Gebouwd (timeline met gekleurde iconen, relatieve tijden, inline notitie, paginatie, user info) |
| A5 | Contact-bedrijf koppelingen UI | ✅ `/relations/links` | Klein | ✅ Gebouwd (ContactLinks component, zoek-dropdown, rol selectie, CRUD) |
| A6 | Derdengelden UI verbeteren | ✅ Complete API | Klein | ✅ Gebouwd (saldokaarten, approval workflow, storting/uitbetaling forms, twee-directeurengoedkeuring) |
| A7 | Financieel overzicht zaak verbeteren | ✅ `/cases/{id}/financial-summary` | Klein | ✅ Gebouwd (KPI-kaarten, betalingsvoortgang progress bar, breakdown-tabel met mini-bars) |

### Fase B: Zaakdetail transformatie (kan parallel met C)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| B1 | Tabbed interface op zaakdetail | Groot | ✅ Gebouwd (9 tabs: Overzicht, Taken, Vorderingen, Betalingen, Financieel, Derdengelden, Documenten, Activiteiten, Partijen) |
| B2 | Quick actions bar op zaakdetail | Klein | ✅ Gebouwd (Uren loggen, Notitie, Document, Factuur, Renteoverzicht — contextueel) |
| B3 | Notities verbeteren | Klein | ✅ Gebouwd (rich text editor met Tiptap — bold/italic/bullets toolbar, WYSIWYG, backward compat met plain text, 11 mrt) |

### Fase C: Dashboard & Facturatie (kan parallel met B)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| C1 | Dashboard verbeteren (vandaag-focus, grafieken, KPI's) | Midden | ✅ Gebouwd (KPI's, pipeline bar, taken widget, weekoverzicht, recente facturen/activiteit) |
| C2 | Betalingstracking op facturen | Groot (nieuw DB model) | ✅ Volledig gebouwd (backend: model, CRUD, auto-status, 18 tests + frontend: payment tracking UI, progress bar, form, deels-betaald status) |
| C3 | Credit nota's | Midden | ✅ Gebouwd (20 feb) — invoice_type + linked_invoice_id, CN-nummering, credit nota aanmaken vanuit factuurdetail, regels pre-fill, purple styling, lijst-weergave met CN badge |

### Fase D: Algemene UX polish

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| D1 | Wachtwoord vergeten flow | Klein-Midden | ✅ Gebouwd (forgot-password op login, reset-password pagina met token, 3-staps flow, email sending via SMTP ✅). ✅ BUG-15 gefixt (25 feb). |
| D2 | Gebruikersbeheer (rollen, rechten) | Groot | ❌ Niet relevant (Lisanne is enige gebruiker) |
| D3 | Navigatie-verbeteringen | Klein | ✅ Gebouwd (breadcrumbs met dynamische labels, nested routes) |
| D4 | Empty states en loading states | Klein | ✅ Gebouwd (skeleton loaders op alle dashboard pagina's) |
| D5 | Agenda events aanmaken | Midden (nieuw model + CRUD) | ✅ Gebouwd (20 feb) — CalendarEvent model met 7 typen, CRUD endpoints, EventDialog create/edit/delete, unifide calendar hook, case/contact pickers |

### Frontend Polish (sessie 48, 11 maart)

| # | Verbetering | Status |
|---|-------------|--------|
| FP1 | Status badge constants geconsolideerd → `lib/status-constants.ts` (was gedupliceerd in 4+ pagina's) | ✅ |
| FP2 | Instellingen pagina opgesplitst: 2113-regels monoliet → 9 tab componenten + thin shell | ✅ |
| FP3 | Documenten pagina hernoemd naar "Sjablonen" met duidelijkere beschrijving | ✅ |
| FP4 | BUG-1 refix: wederpartij prefill bij nieuw dossier vanuit relatie detailpagina | ✅ |

### Frontend UX Polish (sessie 61, 13 maart)

| # | Verbetering | Status |
|---|-------------|--------|
| FP5 | Delete confirmations toegevoegd aan uren, documenten, factuurregels | ✅ |
| FP6 | Empty states gestandaardiseerd (taken, uren, documenten → standaard patroon) | ✅ |
| FP7 | Mobile responsive tables: non-essentiële kolommen hidden op sm: breakpoint | ✅ |
| FP8 | Invoice status badges: ring-1 ring-inset voor visuele consistentie | ✅ |
| FP9 | ARIA labels op checkboxes en navigatie, focus rings op filter buttons | ✅ |
| FP10 | Button sizing + error styling + unused imports opgeruimd | ✅ |

### Fase E: Verbeterpunten uit handmatige test (sessie 2, 20 feb)

| # | Feature | Complexiteit | Prioriteit | Status |
|---|---------|-------------|-----------|--------|
| E1 | "Zaken" hernoemen naar "Dossiers" in hele frontend UI | Klein | 🔴 Hoog | ✅ Gebouwd (20 feb) — puur display, code blijft `case/cases` |
| E2 | Tarieven vereenvoudigen: dropdown op dossierniveau i.p.v. aparte pagina | Klein | 🔴 Hoog | ✅ Gebouwd (20 feb) — tarieven-pagina verwijderd, rentetype blijft op dossierniveau |
| E3 | Facturen-tab op dossierdetail | Klein-Midden | 🔴 Hoog | ✅ Gebouwd (case_id filter op backend, FacturenTab met lijst/status/bedragen/empty state) |
| E4 | Documenten uploaden in dossier | Groot (storage + nieuw model) | 🔴 Hoog | ✅ Gebouwd (20 feb) — CaseFile model, drag & drop upload, download, soft-delete, Docker volume |
| E5 | Slimme facturatie-flow (onbefactureerde uren tonen, batch factureren) | Groot | 🔴 Hoog | ✅ Gebouwd (20 feb) — invoiced tracking op TimeEntry, batch import met checkboxes, Quick Bill vanuit dossierdetail |
| E6 | Debiteuren/crediteuren overzicht bij facturen | Midden | 🟡 Midden | ✅ Gebouwd (20 feb) — aging 0-30/31-60/61-90/90+ dagen, KPI-kaarten, per-relatie tabel met AgingBar, tab op facturenpagina |
| E7 | Auto-timer bij openen dossier (handmatig + automatisch modus) | Midden | 🟡 Midden | ✅ Gebouwd (20 feb) — opt-in auto-start, dossierwisseling auto-save, activity type dropdown, vergeten-timer-waarschuwing 2u, multi-tab sync |
| E8 | E-mail templates (onderwerp + body + merge fields) | Midden | 🟢 Later | ✅ Gebouwd (20 feb) — onderdeel van T3 |

**Voorgestelde bouwvolgorde:** E1 → E2 → E3 → E4 → E5 → E6 → E7 → E8

### Apart traject: Templates in workflow (na B1)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| T1 | Templates op zaakdetail (status-filtered) | Midden | ✅ Gebouwd (20 feb) — STATUS_TEMPLATE_MAP, aanbevolen/overige/verborgen secties, B2B/B2C filter |
| T2 | Workflow-suggesties bij statuswijziging | Klein-Midden | ✅ Gebouwd (20 feb) — amber suggestie-banner na statuswijziging, auto-dismiss 30s, "Ga naar documenten" knop |
| T3 | E-mail versturen vanuit Luxis (SMTP) | Groot | ✅ Gebouwd (20 feb) — compose dialog, send knop, correspondentie tab, email logs, test email, instellingen tab. **Nu via OutlookProvider (Graph API) met seidony@kestinglegal.nl op M365.** |

> Detail: zie `PROMPT-TEMPLATES-IN-WORKFLOW.md`
> E-mail templates (E8) wordt onderdeel van T3

---

## Bugs

> Detail + bestanden + fix-instructies: zie `BUGS-EN-VERBETERPUNTEN.md`

| # | Bug | Ernst | Fix-grootte | Status |
|---|-----|-------|-------------|--------|
| BUG-1 | Relatie niet automatisch gekoppeld bij nieuwe zaak vanuit relatiedetail | Hoog | Klein (URL params + form pre-fill) | ✅ Gefixt (20 feb). ✅ Heropend + gefixt (11 mrt) — opposing_party_id prefill + "Als wederpartij" link + lege-state link gefixt |
| BUG-2 | Rente-velden zichtbaar bij niet-incasso zaaktypes | Midden | Klein (conditional render) | ✅ Gefixt (20 feb) |
| BUG-3 | Renteberekening per documentdatum controleren | Hoog | Verificatie nodig | ✅ Geverifieerd — werkt correct (20 feb) |
| BUG-6 | Conflict check mist op zaakdetail Partijen tab (warning, niet blokkeren) | Midden | Klein | ✅ Gefixt (20 feb) |
| BUG-7 | Dossiergegevens niet bewerkbaar op detailpagina — `court_case_number` (F5) toont alleen als gevuld maar kan nergens ingevuld worden. Dossierdetail mist edit-modus voor alle velden (beschrijving, referentie, zaaknummer, etc.) | Hoog | Midden | ✅ Gefixt (21 feb) — Bewerken-knop + inline edit met Opslaan/Annuleren, zaaknummer altijd zichtbaar |
| BUG-8 | `court_case_number` veld ontbreekt op "Nieuw dossier" formulier — kan alleen via (niet-bestaande) edit-modus op detailpagina | Midden | Klein | ✅ Gefixt (21 feb) — veld toegevoegd aan formulier + backend CaseCreate schema |
| BUG-9 | Advocaat wederpartij niet zichtbaar/toevoegbaar in dossier — gebruiker kan niet in één oogopslag zien wie de belangrijkste contactpersonen zijn | Hoog | Midden | ✅ Gefixt (21 feb) — zoekfield toegevoegd in Dossiergegevens (view+edit) + Nieuw dossier form |
| BUG-10 | Dossier edit: velden wissen werkt niet — je kunt tekst toevoegen en opslaan, maar als je het wist en opslaat blijft de oude waarde staan. Oorzaak: `\|\| undefined` in handleSaveDetails. | Hoog | Klein | ✅ Gefixt (21 feb) — `.trim() \|\| null` stuurt lege velden als null mee |
| BUG-11 | Taken niet zichtbaar na aanmaken in dossier — `useWorkflowTasks` verwachtte paginated object maar backend retourneert array. Ook: geen `assigned_to_id` bij handmatig aanmaken → taak verscheen niet bij Mijn Taken | Hoog | Klein | ✅ Gefixt (22 feb) — hook return type gecorrigeerd, `assigned_to_id` auto-set |
| BUG-12 | Geen "Nieuwe taak" optie op Mijn Taken pagina — kon alleen vanuit dossier taken aanmaken | Midden | Klein | ✅ Gefixt (22 feb) — Nieuwe taak knop + formulier met dossier-picker |
| BUG-13 | Email-bijlage openen geeft 401 — directe `<a href>` link stuurt geen Bearer token mee. Fix: blob URL + fetch (zelfde patroon als G11 preview) | Hoog | Klein | ✅ Gefixt (23 feb) |
| BUG-14 | Email-bijlage niet opslaan als dossierbestand — geen knop/endpoint om bijlage te archiveren bij dossier. Fix: backend copy endpoint + frontend "Opslaan in dossier" knop | Midden | Klein-Midden | ✅ Gefixt (23 feb) |
| BUG-15 | Reset-password pagina hangt oneindig — browser POST naar `https://luxis.kestinglegal.nl/api/auth/reset-password` bereikt backend niet. Caddy reverse proxy draait niet, Next.js had geen rewrite. Fix: Next.js rewrite proxy `/api/*` → `backend:8000` + relatieve URLs. | Hoog | Midden | ✅ Gefixt (25 feb) |
| BUG-16 | Dashboard "Mijn Taken" widget toonde geen taken — `useMyOpenTasks` gebruikte `/api/workflow/tasks?status=due` (alleen "due" taken), terwijl taken op "pending" of "overdue" stonden. Fix: nu gebruikt hetzelfde endpoint als Mijn Taken pagina (`/api/dashboard/my-tasks`). | Midden | S (1 regel) | ✅ Gefixt (25 feb) |
| BUG-17 | Velden leegmaken + opslaan werkte niet (site-breed) — `|| undefined` in form handlers → JSON.stringify dropt de key → backend's `exclude_unset=True` slaat update over. 51 instances in 18 bestanden. | Hoog | M (18 bestanden, 86 regels gewijzigd) | ✅ Gefixt (25 feb) |
| BUG-18 | Klik op taak in dashboard/Mijn Taken navigeert niet naar het juiste dossier — taak-titel was `<p>`, nu `<Link>` naar `/zaken/{case_id}` in zowel dashboard widget als Mijn Taken pagina. | Midden | S | ✅ Gefixt (25 feb) |
| BUG-19 | Factuur aanmaken → redirect naar factuurpagina geeft "fout bij laden" — race condition: `get_db` dependency commit na response. Fix: explicit `db.commit()` in create_invoice router + `setQueryData` cache pre-populate in frontend. | Hoog | S-M | ✅ Gefixt (25 feb) |
| BUG-20 | Budget module onbekend: "Onbekende modules: budget" — `VALID_MODULES` in `settings/schemas.py` miste `"budget"`. Toegevoegd. | Hoog | S | ✅ Gefixt (25 feb) |
| BUG-21 | Advocaat wederpartij niet zichtbaar na aanmaken/bewerken dossier + budget niet opgeslagen bij aanmaken — twee oorzaken: (1) `create_case` service miste `budget` + 7 andere velden in Case constructor, (2) `get_case` en `add_case_party` hadden geen explicit `selectinload` voor nested `parties→contact` relatie (async SQLAlchemy laadt nested selectin niet automatisch). Fix: velden toegevoegd + explicit `selectinload(Case.parties).selectinload(CaseParty.contact)` in queries. | Hoog | M | ✅ Gefixt (25 feb) |
| BUG-22 | Invoice detail 500 Internal Server Error — `GET /api/invoices/{id}` crashte door circulaire `lazy="selectin"` op Invoice self-referential relationships (`credit_notes` en `linked_invoice`). | Hoog | M | ✅ Gefixt (25 feb, sessie 20) |
| BUG-23 | `/notifications` endpoints 404 — Frontend riep `/notifications` en `/notifications/unread-count` aan op elke pagina maar er bestond geen backend module. Drie sub-issues: (1) module bestond niet, (2) import path was fout (`app.auth.dependencies` i.p.v. `app.dependencies`), (3) frontend miste `/api/` prefix in API calls. | Midden | M | ✅ Gefixt (25 feb, sessie 20) |
| BUG-24 | `/api/users` endpoint 404 — Frontend riep `/api/users` aan voor dossierlijst filters maar endpoint bestond niet. | Laag | S | ✅ Gefixt (25 feb, sessie 20) |
| BUG-25 | Timer FAB z-index overlap — timer FAB overlapt met header. Fix: z-40→z-50. | Laag | S | ✅ Gefixt (27 feb, sessie 22) |
| BUG-26 | Relaties laden niet in agenda event formulier — frontend vroeg `per_page=200` maar backend had `le=100` → 422 error. Fix: backend limit verhoogd naar 200. | Midden | S | ✅ Gefixt (27 feb, sessie 22) |
| BUG-27 | 404 pagina in het Engels zonder navigatie — standaard Next.js 404. Fix: custom `not-found.tsx` met Nederlandse tekst + dashboard link. | Laag | S | ✅ Gefixt (27 feb, sessie 22) |
| BUG-28 | Batch "Stap wijzigen" toont "0 gereed" voor dossiers zonder pipeline stap — `batch_preview()` telde cases zonder `incasso_step_id` als `needs_step_assignment` i.p.v. `ready`. Fix: alle non-blocked cases tellen als ready voor advance_step. | Hoog | S | ✅ Gefixt (27 feb, sessie 24) |
| BUG-29 | Auto-advance pipeline werkt niet — `_try_auto_advance` checkte ALLE open taken (incl. 8 initiële taken uit case-aanmaak), waardoor auto-advance altijd geblokkeerd werd. Fix: (1) pipeline taken getagd via `action_config.source=pipeline`, (2) auto-advance/auto-complete scoped naar pipeline taken per stap, (3) initiële taken overgeslagen voor incasso dossiers, (4) audit trail bij stap-wijziging. | Hoog | M | ✅ Gefixt (1 mrt, sessie 26) |
| BUG-30 | test_auth.py (7 tests) — URL paden `/auth/` → `/api/auth/` | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-31 | test_integration_api.py — login helper URL pad gefixt | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-32 | test_cases.py + test_integration_api.py — workflow_data fixture toegevoegd aan conftest.py, tests gebruiken geldige transitiepaden | Midden | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-33 | test_dashboard.py — hardcoded datum → `date.today().isoformat()` | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-34 | test_documents.py — template count assertion `>= 3` + subset check | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-35 | test_relations.py — nested response pad `["contact"]["name"]` | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-36 | Anthropic API "credit balance too low" — Credits moesten apart gekocht worden via platform.claude.com. Na aankoop + propagatie werkt API correct. | Hoog (blocker) | N/A (billing) | ✅ Gefixt (6 mrt, sessie 43) |
| BUG-37 | AI classificatie GET endpoint 500 error na approve — `_classification_to_response()` gebruikte `reviewer.first_name`/`last_name` maar User model heeft alleen `full_name`. Fix: `reviewer.full_name`. | Hoog | S | ✅ Gefixt (6 mrt, sessie 43) |
| BUG-38 | Kimi API URL verkeerd: `api.moonshot.cn` → `api.moonshot.ai`. Account zit op internationaal platform (.ai), niet Chinees (.cn). | Hoog (blocker) | S | ✅ Gefixt (11 mrt, sessie 60) |
| BUG-39 | KIMI_API_KEY niet doorgegeven aan backend container — ontbrak in `docker-compose.prod.yml` environment. | Midden | S | ✅ Gefixt (11 mrt, sessie 60) |
| BUG-40 | EmailAttachment model niet geregistreerd bij SQLAlchemy mapper — standalone scripts/scheduler crashten op `SyncedEmail` relationship. Fix: import in `email/__init__.py`. | Midden | S | ✅ Gefixt (11 mrt, sessie 60) |
| BUG-41 | 120 pre-existing test errors (conftest.py) — `metadata.drop_all()` kon composite types niet droppen (FK ordering) + connection pool hield stale connections vast tussen event loops. Fix: `DROP SCHEMA CASCADE` + `NullPool`. 573 tests passen nu. | Midden | S | ✅ Gefixt (13 mrt, sessie 65) |
| BUG-42 | 196 test errors + 1 failure bij `pytest tests/ -q` — conftest.py importeerde maar 3 van 21 model modules, waardoor `Base.metadata.create_all()` de meeste tabellen niet aanmaakte. Fix: alle 21 model modules importeren via `importlib.import_module()` (vermijdt `app` name collision) + `db` fixture expliciet afhankelijk gemaakt van `setup_database`. Resultaat: 573 passed, 0 errors, 0 failures (zowel -q als -v). | Hoog | M | ✅ Gefixt (13 mrt, sessie 67) |
| BUG-43 | Timer floating button blokkeert "Volgende" en andere action buttons op meerdere pagina's — `fixed bottom-4 right-4` overlapt met knoppen onderaan. Fix: verplaatst naar `bottom-20`. | Hoog | S | ✅ Gefixt (16 mrt, sessie 75) |
| BUG-44 | API call `/api/cases?page=1&per_page=20` op login pagina voor auth check — 401 error in console. FloatingTimer component riep useCases() aan in root Providers. Fix: split in wrapper+inner component zodat hooks alleen draaien wanneer user authenticated is. | Midden | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-45 | AI-parsed partijnamen in wizard stap 2 werden als zoektekst in veld gezet maar triggeren geen selectie van bestaande contacten. Fix: useEffect auto-selecteert eerste match uit zoekresultaten wanneer AI parsing de search text heeft gezet. | Midden | M | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-46 | `case_id` URL parameter op factuur-aanmaakpagina vulde Relatie/Dossier velden niet visueel in (data werd WEL correct opgeslagen). Fix: useCase hook + useEffect om case details te laden en display fields te vullen bij pageload. | Midden | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-47 | "Vordering(optioneel)" in wizard step indicator — spatie ontbreekt voor haakje. Fix: literal space character toegevoegd. | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-48 | Stale "Selecteer een client" validatiefout bleef zichtbaar na succesvolle client selectie. Fix: error wordt gecleared in updateField wanneer client_id wordt gezet. | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-49 | Week range header in urenregistratie toonde "15 mrt — 19 mrt" maar dagen waren Ma 16 - Vr 20 mrt. Fix: gebruik lokale Date objecten i.p.v. re-parsing van ISO strings (timezone offset veroorzaakte off-by-one). | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-50 | 5 pre-existing test failures: test_refresh_token (IntegrityError), test_validate_and_clean_basic + test_validate_and_clean_decimal_precision + test_parse_invoice_pdf_success (AssertionError), test_status_workflow_happy_path (assert 400==200). Ontdekt sessie 91. | Midden | M | ✅ Gefixt (21 mrt, sessie 94) |
| BUG-50 | favicon.ico 404 op alle pagina's. Fix: SVG favicon (Scale icoon) toegevoegd in `src/app/icon.svg`. | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-51 | AI factuur parser werkte niet — KIMI_API_KEY niet doorgegeven via docker-compose env vars | Hoog | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-52 | Timer rondde af per minuut i.p.v. per 6 minuten — standaard juridische facturering | Midden | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-53 | Factuur PDF niet gekoppeld als document na AI parse + dossier aanmaken | Midden | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-54 | Renteoverzicht knop verwees naar niet-bestaande "financieel" tab | Hoog | M | ✅ Gefixt (18 mrt, sessie 78) — RenteoverzichtDialog gebouwd |
| BUG-55 | Geen delete knop voor facturen in dossier Facturen tab | Midden | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-56 | Wizard stap 3 (Vordering) overgeslagen bij incasso dossiers — Enter key + button click-through | Hoog | S | ✅ Gefixt (18 mrt, sessie 78) — handleSubmit guard + React key props |
| BUG-57 | `hourly_rate.toFixed is not a function` — zaakdetailpagina crasht bij dossiers met uurtarief. API retourneert string, `.toFixed()` verwacht number. Fix: `Number()` wrap op 3 plekken. | Hoog | S | ✅ Gefixt (21 mrt, sessie 86) |
| BUG-58 | SEC-9 RLS niet afgedwongen — policies bestonden maar `luxis` is superuser en bypast RLS. Fix: `luxis_app` non-superuser role + `FORCE ROW LEVEL SECURITY` + `SET LOCAL ROLE` in middleware. | Kritiek | M | ✅ Gefixt (21 mrt, sessie 86) |
| BUG-59 | Provisie factureren knop ontbreekt (DF-05 incompleet) — instellingen bestaan maar geen actie om factuur aan te maken met provisie pre-filled. Fix: "Provisie factureren" knop + `?provisie=true` query param. | Midden | S | ✅ Gefixt (21 mrt, sessie 86) |
| BUG-60 | Factuur uren import toont geen bedragen — `hourly_rate` niet auto-ingevuld bij time entry creatie. Fix: backend vult nu `default_hourly_rate` van user in + bestaande entries gebackfilled. | Hoog | S | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-61 | `toFixed is not a function` bij factuur uren import — zelfde type als BUG-57 maar op facturen/nieuw pagina. Decimal strings van API niet naar Number() geconverteerd. | Hoog | S | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-62 | Dark mode/Systeem knoppen in Instellingen doen niks (tonen alleen toast). Fix: knoppen verwijderd, alleen "Licht" behouden. | Laag | S | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-63 | Email matching: emails bij verkeerd dossier. Fix: thread-matching, stop-on-miss, bounce-detectie, referentie matching verwijderd, outbound dedup. QA: alle 7 scenario's PASS. Extra fixes sessie 102: Fernet key derivatie hersteld (sessie 90 regressie), outbound synthetic ID uniek gemaakt met timestamp. | Kritiek | L | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-64 | Rentetype (interest_type) niet bewerkbaar na aanmaken dossier — staat alleen in wizard stap 2, niet in DetailsTab bewerkformulier. Moet bewerkbaar zijn incl. contractuele rente velden. | Midden | S | ✅ Gefixt (sessie 104) |

### Demo Feedback Sprint 2 (afgerond, sessie 78)

| # | Feature/Fix | Ernst | Status |
|---|-------------|-------|--------|
| DF-01 | Bestede uren vs te factureren uren (standaard gelijk, aanpasbaar) | Hoog | ✅ Gebouwd (18 mrt, sessie 78) |
| DF-02 | Uren filters: maand, dag, client filter | Midden | ✅ Gebouwd (18 mrt, sessie 78) |
| DF-03 | Datum aanpassen bij uren (inline edit) | Laag | ✅ Gebouwd (18 mrt, sessie 78) |
| DF-04 | Uren-factuur koppeling zichtbaar (factuurnummer bij time entry) | Midden | ✅ Gebouwd (18 mrt, sessie 78) |

### Demo Feedback Sprint 3-4 (openstaand)

| # | Feature/Fix | Ernst | Status |
|---|-------------|-------|--------|
| DF-05 | Incasso provisie als configureerbare factuurregel | Hoog | ✅ 20 mrt |
| DF-06 | BTW toggle verbeteren (dropdown: 21%/0%/aangepast) | Midden | ✅ 18 mrt |
| DF-07 | Factuur context panel (al gefactureerd + derdengelden per dossier) | Hoog | ✅ 18 mrt |
| DF-08 | Navigatie terug naar dossier na factuur aanmaken | Laag | ✅ 18 mrt |
| DF-09 | Contractuele rente frequentie UI duidelijker | Midden | ✅ 18 mrt |
| DF-10 | Betaalregelingen: aantal termijnen → bedrag auto-berekenen | Midden | ✅ 18 mrt |
| DF-11 | Betaling auto-koppelen aan betaalregeling termijn | Midden | ✅ 20 mrt |
| DF-12 | Verschotten: file upload + belast/onbelast veld (voor Exact koppeling) | Hoog | ✅ 18 mrt |
| DF-13 | Voorschotnota: verrekening type (tussentijds / bij sluiting) | Midden | ✅ 20 mrt |

### Demo Feedback Sprint 5 (sessie 103 — 23 mrt 2026)

**Bron:** Demo met Lisanne, 23 maart 2026.

| # | Feature/Fix | Ernst | Grootte | Status |
|---|-------------|-------|---------|--------|
| DF2-01 | **Email compose uitbreiden** — Draft-in-Outlook flow: ontvanger chips, template selector (incasso templates als HTML body), bijlagen uit dossier + upload + ander dossier, draft opent in Outlook Web met alles pre-filled. | Hoog | XL | ✅ Sessie 103b |
| DF2-02 | **Incasso stappen bewerken** — bewerk-knop (potlood-icoon) toegevoegd naast bestaande inline-edit | Midden | S | ✅ Sessie 103 |
| DF2-03 | **BTW per factuurregel** — per regel btw-soort kiezen (21%/9%/0%). Per-tariegroep berekening (NL belastingwet). Smart PDF uitsplitsing. Auto-BTW bij expense import. | Hoog | M | ✅ Sessie 103 |
| DF2-04 | **Voorschotbedrag op uren** — uren × uurtarief auto-berekening op voorschotnota | Midden | S | ✅ Sessie 103 |
| DF2-05 | **Rentetype verplaatsen naar stap 3** — van stap 1 (Zaakgegevens) naar stap 3 (Vordering) | Laag | S | ✅ Sessie 103 |
| DF2-06 | **Profiel invullen bij nieuw dossier** — contactdetails standaard open bij nieuwe betrokkenen | Midden | S | ✅ Sessie 103 |
| DF2-07 | **PDF parsing verbeterd** — fallback naar Claude native PDF bij scans/afbeeldingen | Hoog | M | ✅ Sessie 103 |
| DF2-08 | **Genereer brief → mail als body** — template als mail-body versturen (met logo/handtekening/opmaak Kesting Legal), niet als bijgevoegd bestand. 5 HTML templates (aanmaning, sommatie, tweede_sommatie, 14_dagenbrief, herinnering) met Kesting Legal branding. Fallback naar PDF bijlage voor dagvaarding/renteoverzicht. | Hoog | L | ✅ Sessie 103b |
| DF2-09 | **Incasso fase vanuit dossier** — pipeline step dropdown op dossier-detail header | Midden | S | ✅ Sessie 103 |

### UX Review Fixes (sessie 79b — 18 mrt 2026)

Volledige UX review van alle 31 schermen. 5 gefixt, 13 openstaand.

| # | Issue | Prioriteit | Status |
|---|-------|-----------|--------|
| UX-1 | Uren weekdag highlight UTC vs lokale timezone | Hoog | ✅ 18 mrt |
| UX-2 | Dossier summary cards hoofdsom stale cache | Hoog | ✅ 18 mrt |
| UX-3 | Redundante "Dossiers per status" widget op dashboard | Laag | ✅ 18 mrt |
| UX-4 | Taken pagina toont alle 190 taken zonder paginering | Midden | ✅ 18 mrt |
| UX-5 | Correspondentie afzender toont alleen voornaam | Midden | ✅ 18 mrt |
| UX-6 | Dossier tabs overflow — sticky tab bar onder header | Midden | ✅ Sessie 80 |
| UX-7 | Dossier header sticky overlap — tabs sticky gemaakt | Midden | ✅ Sessie 80 |
| UX-8 | Documenten: case picker dialog voor directe generatie | Laag | ✅ Sessie 80 |
| UX-9 | Betalingen: prominente Upload knop in header | Laag | ✅ Sessie 80 |
| UX-10 | Incasso pipeline: betaalde dossiers uitgefilterd | Midden | ✅ Sessie 80 |
| UX-11 | Follow-up: uitleg toegevoegd bij lege staat | Laag | ✅ Sessie 80 |
| UX-12 | Dashboard taken: duplicaten gegroepeerd (bijv. "3x ...") | Laag | ✅ Sessie 80 |
| UX-13 | Dossier lijst: "Openstaand" kolom toegevoegd | Midden | ✅ Sessie 80 |

---

### Lisanne Feedback Sprint 3 (sessie 86, 21 maart 2026)

| # | Feature/Fix | Ernst | Grootte | Status |
|---|-------------|-------|---------|--------|
| LF-16 | Timer loopt door na sluiten programma — moet pauzeren/stoppen bij afsluiten browser | Hoog | M | ✅ 21 mrt |
| LF-17 | "Incasso/instellingen" (uurtarief, betalingstermijn) verwijderen uit dossier-aanmaak wizard — hoort in dossier zelf | Midden | S | ✅ 21 mrt |
| LF-18 | "Normaal" strategie onduidelijk bij dossier-aanmaak — hernoemen of verduidelijken | Laag | S | ✅ 21 mrt |
| LF-19 | Terugknop in dossier-wizard wist alle ingevoerde gegevens — moet state behouden | Hoog | M | ✅ 21 mrt |
| LF-20 | Te veel opties bij "type dossier" — alleen "Incasso" en "Dossier" (evt. "Advies"), insolventie/overig weg | Laag | S | ✅ 21 mrt |
| LF-21 | Filteroptie bij documenten ontbreekt — filter op bestandstype (Word, PDF, etc.) binnen dossier | Laag | S | ✅ 21 mrt |

---

## Backlog / Feature Requests

- ~~**FEATURE: Relaties — inline contactpersoon aanmaken vanuit koppeldialoog**~~ ✅ Gedaan (sessie 19) — inline aanmaken van advocaat wederpartij bij nieuw dossier
- ~~**FEATURE: Advocaat wederpartij — klikbare detailweergave**~~ ✅ Gedaan (sessie 19) — zaken zichtbaar op relatiepagina via CaseParty filter + "Partij" rol label

### Incasso Workflow Automatisering (P1)

**Doel:** Eén klik op "Verstuur brief" voor 40 dossiers → alles automatisch.

1. ✅ **Template editor UI** — Sjablonen tab in Instellingen: upload, download, bewerken, verwijderen van DOCX templates. Database-driven met disk-fallback. Incasso pipeline gebruikt dynamische template dropdown. Gebouwd sessie 24.
2. ✅ **Batch brief + email verzenden** — "Verstuur brief" genereert documenten en emailt ze naar de wederpartij via OutlookProvider (Graph API) met SMTP fallback. Sinds sessie 103b: brieven als branded HTML email body (Kesting Legal logo/kleuren/handtekening) i.p.v. PDF bijlage. Fallback naar PDF bijlage voor dagvaarding/renteoverzicht. Email toggle in PreFlightDialog, instelbare email templates per stap, email readiness check in preview. Gebouwd sessie 27, HTML body sessie 103b.
3. ✅ **Auto-complete taken** — Na document genereren: bijbehorende taken (generate_document/send_letter) automatisch afgevinkt. Gebouwd sessie 25. Bugfix sessie 26: scoped naar pipeline taken per stap (BUG-29).
4. ✅ **Auto-advance pipeline** — Na alle taken voltooid: pipeline schuift automatisch naar volgende stap, nieuwe taak + deadline aangemaakt. Bij batch advance_step worden ook taken aangemaakt. Gebouwd sessie 25. Bugfix sessie 26: blokkade door initiële taken opgelost (BUG-29).
5. ✅ **Deadline kleuren per stap** — Groen/oranje/rood kleurcodering per dossier in pipeline. Gebouwd sessie 23.
6. ✅ **Instelbare dagen per stap** — `max_wait_days` per pipeline-stap. "Min. dagen" + "Grens rood" kolommen. Gebouwd sessie 23.

**Flow:** Batch selectie → genereer brieven → email via Outlook → taken afgevinkt → pipeline doorgeschoven → deadline kleuren updaten

**QA & Testdekking (sessie 28):**
- ✅ **35 backend integration tests** — `test_incasso_pipeline.py`: deadline kleuren, email templates, auto-complete (BUG-29 regressie), auto-advance, batch preview, batch execute (met/zonder email, partial failure, edge cases), pipeline overview, queue counts. Alle 35 PASSED.
- ✅ **9 Playwright E2E tests** — `frontend/e2e/incasso-pipeline.spec.ts`: page load, deadline colors, action bar, pre-flight dialog, email toggle, queue filters, stappen beheren.
- ✅ **Smoke test checklist** — `docs/qa/p1-smoke-test-checklist.md`: 6 scenario's, 30+ handmatige checks.

---


## Volgorde van werken

> Volledige lijst van alle afgeronde items staat in `docs/completed-work.md`

**Volgende prioriteit:** Security Sprint (SEC-1 t/m SEC-15) + Code Quality Sprint (CQ-1 t/m CQ-9) — sessie 83 audits

### Pre-Launch Sprint (sessie 62 audit → uitrol)

**Doel:** Alle blokkers oplossen zodat Lisanne daadwerkelijk met Luxis kan werken.

| # | Taak | Effort | Blokkerend? | Status |
|---|------|--------|-------------|--------|
| PL-1 | **Backups activeren op VPS** — crontab instellen, backup dir aanmaken, eerste backup testen | 15 min | JA — zonder backup = dataverlies risico | ✅ Sessie 63 (13 mrt) |
| PL-2 | **Factuur-PDF generatie** — endpoint + template + download knop op factuurdetail | 4-6 uur | JA — kan geen facturen versturen | ✅ Sessie 64 (13 mrt) |
| PL-3 | **E2E auth test fixen** — URL+sidebar check i.p.v. time-dependent greeting | 30 min | Nee (test, niet productie) | ✅ Sessie 63 (13 mrt) |
| PL-4 | **Timer persistent maken** — localStorage opslag zodat page reload timer niet kwijtraakt | 1 uur | Nee maar high-impact UX | ✅ Was al geïmplementeerd |
| PL-5 | **Default uurtarief per gebruiker** — settings + auto-fill bij tijdregistratie | 1-2 uur | Nee maar dagelijkse frustratie | ✅ Sessie 63 (13 mrt) |
| PL-6 | **CSV payment import UI** — frontend pagina voor bestaand backend endpoint | 2-3 uur | Nee maar bij 20+ dossiers essentieel | ✅ Was al gebouwd (sessie 56-57) |

**Geschatte doorlooptijd:** 1.5-2 sessies

### Security Sprint (sessie 83 pentest)

**Bron:** Security audit sessie 83 (20 maart 2026). Volledige OWASP Top 10 + extra checks op advocatenkantoor-specifieke risico's.

**Positief:** Tenant isolation via JWT consistent, OAuth tokens encrypted at rest (Fernet), bcrypt correct, JWT access tokens 15 min expiry, Sentry PII disabled, Pydantic validatie op alle schemas, productie Docker ports niet exposed.

**Prioriteit legenda:** 🔴 Kritiek (direct exploiteerbaar) | 🟠 Hoog (serieus risico) | 🟡 Medium | 🟢 Laag/Info

#### Fase 1 — Kritiek (vóór volgende deploy)

| # | Issue | Ernst | Grootte | Status |
|---|-------|-------|---------|--------|
| SEC-1 | **SQL injection in tenant middleware** — f-string in `SET app.current_tenant = '{tenant_id}'`. Fix: UUID validatie vóór interpolatie. | 🔴 Kritiek | S | ✅ Sessie 83 |
| SEC-2 | **OAuth state parameter niet gesigned** — base64-encoded JSON zonder HMAC. Fix: HMAC signing + nonce + 10min expiry. | 🔴 Kritiek | M | ✅ Sessie 83 |
| SEC-3 | **XSS via email HTML** — `dangerouslySetInnerHTML` op 3 plekken zonder sanitatie. Fix: DOMPurify geïnstalleerd + sanitizeHtml helper. | 🔴 Kritiek | S | ✅ Sessie 83 |
| SEC-4 | **SECRET_KEY default waarde** — placeholder string als JWT signing key. Fix: startup check die weigert te starten met default key in productie. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-5 | **Password reset token in logs** — plaintext reset URL gelogd. Fix: URL verwijderd uit logmelding. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-6 | **API secrets roteren** — gecontroleerd: .env is NOOIT gecommit in git history. Secrets zijn veilig. | 🟠 Hoog | S | ✅ Sessie 83 |

#### Fase 2 — Hoog (binnen 1-2 sessies)

| # | Issue | Ernst | Grootte | Status |
|---|-------|-------|---------|--------|
| SEC-7 | **Rate limiting op auth endpoints** — slowapi geïnstalleerd. Login: 10/min, forgot-password: 3/uur, reset: 5/uur. | 🟠 Hoog | M | ✅ Sessie 83 |
| SEC-8 | **postMessage wildcard origin** — OAuth success popup stuurt `postMessage('*')`. Fix: specifieke origin + HTML/JS escaping. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-9 | **PostgreSQL RLS niet actief** — RLS policies bestonden maar werden niet afgedwongen (owner bypast RLS). Fix: `FORCE ROW LEVEL SECURITY` + `luxis_app` non-superuser role + `SET LOCAL ROLE` in middleware. | 🟠 Hoog | M-L | ✅ Sessie 84 + fix sessie 86 |
| SEC-10 | **Jinja2 Server-Side Template Injection** — Fix: `SandboxedEnvironment` voor alle DB-templates. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-11 | **Container draait als root** — Fix: `adduser appuser` + `USER appuser` in Dockerfile. | 🟡 Medium | S | ✅ Sessie 83 |

#### Fase 3 — Medium/Laag (hardening)

| # | Issue | Ernst | Grootte | Status |
|---|-------|-------|---------|--------|
| SEC-12 | **Refresh token rotation** — oude refresh tokens blijven geldig tot expiry (7 dagen). Fix: token blocklist of DB-opslag met rotation. | 🟡 Medium | M | ✅ Sessie 84 |
| SEC-13 | **Wachtwoord-complexiteit** — alleen min 8 chars, geen complexiteitsregels. Fix: min 12 + complexiteit voor advocatenkantoor. | 🟡 Medium | S | ✅ Sessie 84 |
| SEC-14 | **HTML-escape user input in emails** — Fix: `html.escape()` vóór newline-conversie in 3 bestanden. | 🟡 Medium | S | ✅ Sessie 83 |
| SEC-15 | **File upload hardening** — .doc/.xls (macro-gevoelig) toegestaan, geen magic byte validatie. Fix: legacy formaten verwijderen + python-magic check. | 🟡 Medium | S-M | ✅ Sessie 84 |

**Toekomstig (backlog):**
- Audit trail voor alle data-wijzigingen (AVG/GDPR compliance)
- GDPR data export + verwijdering endpoints (Art. 15/17)
- Failed login logging + monitoring

**Aanbevolen volgorde:** SEC-1 → SEC-2 → SEC-3 → SEC-4/5/6 → SEC-7 t/m SEC-11 → SEC-12 t/m SEC-15

### Mega-Audit Sprint (sessie 89, 21 maart 2026)

**Bron:** 6 parallelle audit-agents: security, backend code, frontend code, juridisch, UX/design, infra/DevOps. 100+ bevindingen geconsolideerd en gededupliceerd.

#### CRITICAL — Must-fix (juridisch/financieel/security risico)

| # | Issue | Domein | Status |
|---|-------|--------|--------|
| SEC-16 | **Fernet KDF zwak** — enkele SHA-256 zonder salt/iteraties voor OAuth token encryptie. Fix: PBKDF2HMAC met salt + 600k iteraties. | Security | ✅ Sessie 90 (al gefixt, bevestigd sessie 91) |
| SEC-17 | **DB/Redis poorten open in prod** — ports verplaatst van base naar dev override; prod heeft geen exposed ports. | Infra | ✅ Sessie 92 |
| SEC-18 | **Redis zonder wachtwoord** — geen `requirepass` in productie. | Infra | ✅ Sessie 90 (REDIS_PASSWORD ingesteld op VPS) |
| SEC-19 | **localStorage tokens** — JWT in localStorage, XSS-extractable. Interim: centraliseer in tokenStore. Later: httpOnly cookies. | Security | ✅ Sessie 91 (tokenStore module, 17 bestanden gemigreerd) |
| CQ-10 | **Missing db.commit()** — file upload, credit note, approve, send, cancel, add/remove line, expenses, payments nooit gecommit. | Backend | ✅ Sessie 90 |
| CQ-11 | **N+1 query in receivables** — 1 DB query per factuur in loop. Fix: single grouped aggregate. | Backend | ✅ Sessie 90 |
| CQ-12 | **Silent catch{} blocks** — 14+ plaatsen in frontend slikken financiële mutatie-errors. Gebruiker ziet niks. | Frontend | ✅ Sessie 91 (4 catch blocks → toast.error) |
| CQ-13 | **parseFloat voor geldbedragen** — IEEE 754 precisieverlies bij transport naar backend. Fix: string transport. | Frontend | ✅ Sessie 91 (alle parseFloat verwijderd, string transport) |

#### HIGH — Serieus risico

| # | Issue | Domein | Status |
|---|-------|--------|--------|
| SEC-20 | **Geen account lockout** — 10/min rate limit = 14.400 pogingen/dag. Fix: per-account lockout na 5 mislukte pogingen. | Security | ✅ Sessie 90 (lockout na 5 pogingen + migratie) |
| SEC-21 | **OAuth callback unauthenticated** — user_id trusted uit state parameter. Fix: server-side nonce in Redis. | Security | ✅ Sessie 91 (Redis nonce, single-use, 10min TTL) |
| SEC-22 | **Input sanitization** — user input niet gesanitized. Fix: backend + frontend sanitization. | Security | ✅ Sessie 90 (backend sanitize.py + frontend DOMPurify) |
| SEC-23 | **Filename injection Content-Disposition** — ongesanitized filename in headers. Fix: strip speciale chars. | Security | ✅ Sessie 90 (al gefixt, bevestigd sessie 91) |
| SEC-24 | **Token encryption** — OAuth tokens onvoldoende versleuteld. Fix: Fernet encryption. | Security | ✅ Sessie 90 (Fernet versterkt) |
| SEC-25 | **OAuth state parameter** — geen validatie van state parameter. Fix: server-side validatie. | Security | ✅ Sessie 90 (state parameter validatie + frontend USER directive) |
| SEC-26 | **PyJWT migratie** — python-jose niet meer onderhouden. Vervangen door PyJWT. | Backend | ✅ Sessie 90 |
| CQ-14 | **Compound interest rounding** — year_interest niet afgerond voor kapitalisatie. | Backend | ✅ Sessie 90 |
| CQ-15 | **_recalculate_totals stale** — in-memory loop i.p.v. DB aggregate voor factuur totalen. | Backend | ✅ Sessie 90 |
| CQ-16 | **list_cases missing eager loads** — MissingGreenlet crash risico bij serialisatie. | Backend | ✅ Sessie 90 |
| CQ-17 | **Factuur paid zonder payments** — status `paid` bereikbaar zonder betalingsrecords. | Backend | ✅ Sessie 90 |
| CQ-18 | **files_service uploader lazy load** — crash in async context. Fix: selectinload. | Backend | ✅ Sessie 90 |
| CQ-19 | **Float divisie betalingsregeling** — installment bedrag berekend met JS float. Fix: integer cents arithmetic. | Frontend | ✅ Sessie 91 (integer cents i.p.v. float divisie) |
| CQ-20 | **KYC/WWFT data typed als any** — compliance risico. Fix: typed KycData interface. | Frontend | ✅ Sessie 90 (KycSection getypeerd) |

#### MEDIUM — Moet gefixt, geen acuut risico

| # | Issue | Domein | Status |
|---|-------|--------|--------|
| SEC-27 | **Security headers in prod** — ontbrekende security headers in docker-compose.prod.yml. | Infra | ✅ Sessie 90 |
| SEC-28 | **Dev deps in prod image** — Changed to `uv pip install "."` (without dev extras). | Infra | ✅ Sessie 92 |
| SEC-29 | **Mass assignment setattr** — Explicit ALLOWED_FIELDS allowlist in update_profile + update_tenant. | Security | ✅ Sessie 92 |
| SEC-30 | **CSP unsafe-inline/unsafe-eval** — Removed unsafe-eval from script-src in Caddyfile. | Infra | ✅ Sessie 92 |
| CQ-21 | **Backend .dockerignore** — Created backend/.dockerignore excluding .env, tests, cache, docs. | Infra | ✅ Sessie 92 |
| CQ-22 | **Container health checks** — Added healthchecks for all 4 services in docker-compose.prod.yml. | Infra | ✅ Sessie 92 |
| CQ-23 | **Container resource limits** — Added mem_limit + cpus for all services in prod compose. | Infra | ✅ Sessie 92 |
| CQ-24 | **Off-site backups** — Updated backup.sh with rclone off-site upload support. rclone geïnstalleerd op VPS (sessie 101). Config naar Backblaze B2 nog nodig vóór soft launch. | Infra | ⏳ rclone config vóór soft launch |
| CQ-25 | **Uptime monitoring** — Self-hosted health check actief (elke 5 min, auto-restart bij downtime). /health endpoint extern beschikbaar. UptimeRobot (extern) nog opzetten vóór soft launch. | Infra | ⏳ UptimeRobot vóór soft launch |
| UX-14 | **Responsive tabellen** — overflow-x-auto + min-width op alle tab-tabellen en incasso pipeline. | Frontend | ✅ Sessie 98 |
| UX-15 | **Form validatie** — inline foutmeldingen op factuur, email compose, betaling, instellingen formulieren. | Frontend | ✅ Sessie 98 |
| UX-16 | **Unsaved changes warning** — beforeunload op nieuwe relatie (andere formulieren hadden het al). | Frontend | ✅ Sessie 98 |
| UX-17 | **Empty state guidance** — lege lijsten missen begeleiding/onboarding. EmptyState component + 7 tabs vervangen. | Frontend | ✅ Sessie 97 |
| UX-18 | **Breadcrumbs** — waren al geïmplementeerd (breadcrumb-context + useBreadcrumbs hook op alle detail pages). | Frontend | ✅ Al compleet |
| UX-19 | **Error boundaries per tab** — waren al geïmplementeerd (ErrorBoundary + TabErrorFallback op alle 10 tabs). | Frontend | ✅ Al compleet |
| UX-20 | **formatCurrency NaN** — null-safe arithmetic (??0) in dossiers pagina. | Frontend | ✅ Sessie 98 |
| UX-21 | **isError niet afgevangen** — financiële queries tonen lege lijst i.p.v. error. | Frontend | ✅ Sessie 91 (QueryError in 5 financial tabs) |
| UX-22 | **Frontend Design Audit** — alle pagina's doorlopen met Frontend Design skill en UI verbeterpunten inventariseren (anti-"AI slop", design systeem, typografie, kleurgebruik, compositie). Rapport: `docs/research/UX-22-FRONTEND-DESIGN-AUDIT.md` (score 5.5/10, 20 pagina's geaudit). | Frontend | ✅ Sessie 96 |
| UX-23 | **Design Sprint deel 1** — 8/10 UX-22 Top 10 items geïmplementeerd: Inter font, login redesign, empty states, KPI cards, sidebar secties, tabel responsiveness, microinteracties. | Frontend | ✅ Sessie 97 |
| UX-24 | **Design Sprint deel 2** — resterende 2 items: incasso pipeline collapse lege secties + correspondentie in/uit visueel + date grouping. | Frontend | ✅ Sessie 98 |

### Bugs & Issues

| # | Omschrijving | Ernst | Status |
|---|-------------|-------|--------|
| BUG-51 | **Correspondentie zoekfunctie** — zoeken op de correspondentie pagina geeft geen resultaten. | Midden | ✅ Niet reproduceerbaar (sessie 99, 22 mrt) — zoekfunctie werkt correct |

### AI UX/UI Verbetering (sessie 98 feedback)

**Bron:** Gebruiker-feedback: AI resultaten zijn niet zichtbaar genoeg BINNEN de workflow. Designkeuze blijft: geen aparte AI-pagina, AI is onzichtbaar maar de resultaten moeten wél duidelijk zijn op de plekken waar ze relevant zijn.

| # | Omschrijving | Status |
|---|-------------|--------|
| AI-UX-01 | **AI badges op email-rijen** — classificatie-badge (categorie + confidence) direct zichtbaar in de correspondentie email-lijst, niet alleen na klikken in detail-panel. | ✅ Done (sessie 99, 22 mrt) |
| AI-UX-02 | **"Wacht op review" indicator** — visuele hint op emails die nog op AI-review wachten (icoontje of kleur). | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-03 | **AI suggesties in Mijn Taken** — AI-secties met paarse AI-badge, tonen altijd (ook als lege state). Geen aparte AI-pagina. | ✅ Done (sessie 99, 22 mrt) |
| AI-UX-04 | **AI suggestion banner op dossier** — bovenaan dossier-detail een inklapbare kaart met de huidige AI-suggestie + Accepteren/Afwijzen. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-05 | **AI indicators op incasso pipeline** — AI-badge op dossier-kaarten in de pipeline ("Termijn verloopt morgen", "Actie voorgesteld"). | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-06 | **AI in activity feed** — AI-acties in dezelfde tijdlijn als menselijke acties, met AI-badge/avatar. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-07 | **Dashboard AI widget** — samenvatting "3 dossiers vereisen actie, 2 termijnen verlopen vandaag". | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-08 | **Nederlandse tekstlabels i.p.v. percentages** — "Aanbevolen" (blauw), "Mogelijk" (oranje), "Onzeker" (grijs) i.p.v. "95%". | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-09 | **AI concept-berichten klaarzetten** — bij accepteren schrijft de AI een kant-en-klaar inhoudelijk bericht. Niet een standaard afwijzing, maar een onderbouwd antwoord op basis van ALLE dossiercontext (zie AI-UX-13). Lisanne reviewt en verstuurt. Alleen voor incasso. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-10 | **Response templates tailoren** — de 6 standaard antwoord-templates moeten nog afgestemd worden op hoe Kesting Legal communiceert. Input van Arsalan nodig. | ❌ TODO — wacht op input |
| AI-UX-11 | **Algemene voorwaarden per cliënt** — upload/opslag van algemene voorwaarden per cliënt (niet van Kesting Legal). AI valt hier op terug bij betwistingen. Per dossier gekoppeld via de cliënt. | ✅ 23 maart 2026 |
| AI-UX-13 | **AI raadpleegt volledige dossiercontext** — de AI leest ALLES voordat hij een concept schrijft: (1) alle emails in+uit, (2) notities/telefoonnotities in het dossier, (3) contract/overeenkomst PDF, (4) factuur PDF, (5) algemene voorwaarden cliënt, (6) vorderingen + betalingen, (7) activity feed, (8) eerder verzonden brieven. Zonder deze context is de AI te simpel. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-14 | **Bronvermelding in concept-berichten** — AI verwijst naar specifieke artikelen uit contract/AV, berekent termijnen, citeert relevante correspondentie. Lisanne kan snel checken of het klopt. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-12 | **Correspondentie zoekfunctie** — zoeken werkt niet (BUG-51). | ✅ Niet reproduceerbaar (sessie 99, 22 mrt) |

### AI Technische Verbeteringen (sessie 98 research)

| # | Omschrijving | Status |
|---|-------------|--------|
| AI-TECH-01 | **pymupdf4llm** — vervang pdfplumber door pymupdf4llm in `backend/app/ai_agent/pdf_extract.py`. Betere tabel/layout extractie, 5-10x sneller, Markdown output voor LLM. Simpele swap (~30 min). | ✅ 23 mrt 2026 |
| AI-TECH-02 | **Claude native PDF voor contractanalyse** — bij betwistingen/zware analyse: stuur PDF direct naar Claude API i.p.v. tekst extractie. Alleen voor dure taken (1-2x/week), dagelijks werk blijft Kimi. | ✅ 23 mrt 2026 |
| AI-TECH-03 | **Claude Structured Outputs** — gebruik structured outputs bij Claude Haiku calls zodat responses gegarandeerd het juiste JSON format hebben. Elimineert parsing errors. Alleen voor Claude calls, niet Kimi. | ✅ 23 mrt 2026 |

### Tooling Upgrade (sessie 96)

**Bron:** Research sessie 95 — 1.000+ repos gescand, 20 tools geëvalueerd. Installeer tools die directe waarde toevoegen aan development en marketing.

| # | Tool | Categorie | Doel | Status |
|---|------|-----------|------|--------|
| TOOL-01 | **Codebase Memory MCP** | Dev infra | Knowledge graph van codebase, 99% minder tokens | ✅ Sessie 96 |
| TOOL-02 | **Context7 MCP** | Dev infra | Up-to-date library docs (Next.js 15, React 19, SQLAlchemy 2.0) | ✅ Sessie 96 |
| TOOL-03 | **Tavily MCP** | Search/scrape | Vervangt Perplexity + Firecrawl (gratis 1.000 calls/mnd) | ✅ Sessie 96 |
| TOOL-04 | **Systematic Debugging skill** | Dev skill | 4-fase debugging: root cause → patroon → hypothese → fix | ✅ Sessie 96 |
| TOOL-05 | **Receiving Code Review skill** | Dev skill | Regels voor feedback verwerken, anti-slijmerij, YAGNI check | ✅ Sessie 96 |
| TOOL-06 | **Verification Before Completion skill** | Dev skill | Operationeel protocol: verse output, verboden woorden, agent-verificatie | ✅ Sessie 96 |
| TOOL-07 | **Frontend Design skill** | Dev skill | Anti-"AI slop" design richtlijnen, merge met frontend/CLAUDE.md | ✅ Sessie 96 |
| TOOL-08 | **Deep Research skill** | Dev + Marketing | 8-fase research pipeline met citations | ✅ Sessie 96 |
| TOOL-09 | **Claude SEO** | Marketing | SEO audit + schema + E-E-A-T + AI Search optimalisatie voor kestinglegal.nl | ✅ Sessie 96 |
| TOOL-10 | **Marketing Skills** (Corey Haines) | Marketing | 30+ skills: SEO, copywriting, cold email, content strategie | ✅ Sessie 96 |
| TOOL-11 | **Brand Guidelines skill** | Marketing | Kesting Legal branding vastleggen voor consistent materiaal | ✅ Sessie 96 |
| TOOL-12 | **Canvas Design skill** | Marketing | Social graphics, LinkedIn visuals zonder designer | ✅ Sessie 96 |
| TOOL-13 | **Perplexity MCP verwijderen** | Opruimen | Te duur, geen free tier, geen budget | ✅ Sessie 96 |
| TOOL-14 | **Firecrawl MCP verwijderen** | Opruimen | Credits op, niet vernieuwd | ✅ Sessie 96 |

### Code Quality Sprint (sessie 83 audit)

**Bron:** Codebase audit sessie 83 (20 maart 2026). Alle bevindingen uit onafhankelijke code review.

**Prioriteit legenda:** 🔴 Kritiek (functioneel risico) | 🟡 Belangrijk (onderhoud) | 🟢 Nice-to-have

| # | Issue | Prioriteit | Grootte | Kan zonder Lisanne? | Status |
|---|-------|-----------|---------|---------------------|--------|
| CQ-1 | **Float → Decimal in cases/models.py** — 11 financiële velden (`total_principal`, `budget`, `hourly_rate`, etc.) gebruiken `Mapped[float]` i.p.v. `Mapped[Decimal]`. Database is NUMERIC(15,2) maar Python geeft floats terug. | 🔴 Kritiek | M | ✅ Ja | ✅ Sessie 84 |
| CQ-2 | **Float → Decimal in cases/schemas.py** — 15+ Pydantic schema-velden voor geld als `float` i.p.v. `Decimal` | 🔴 Kritiek | S | ✅ Ja | ✅ Sessie 84 |
| CQ-3 | **Float in relations/models.py** — `default_hourly_rate` is `Float` kolomtype (niet NUMERIC). Financieel veld in IEEE 754 floating-point. | 🔴 Kritiek | S | ✅ Ja | ✅ Sessie 84 |
| CQ-4 | **Stille no-op: "Herbereken rente" batch-actie** — `incasso/service.py` regel ~807: loop telt `processed += 1` maar doet niks. Gebruiker krijgt succesbericht terwijl er niks gebeurt. | 🔴 Kritiek | S-M | ✅ Ja | ✅ Sessie 84 |
| CQ-5 | **invoices/service.py opsplitsen** — 1292 regels, bevat CRUD + PDF + credit notes + provisie + budget tracking. Minimaal splitsen in 2-3 files. | 🟡 Belangrijk | M | ✅ Ja | ✅ Sessie 84 |
| CQ-6 | **Frontend god-components splitsen** — IncassoTab.tsx (2292r), zaken/nieuw/page.tsx (1823r), relaties/[id]/page.tsx (1545r). Moeilijk te onderhouden/debuggen. | 🟡 Belangrijk | L | ✅ Ja | ✅ Sessie 85 |
| CQ-7 | **Paginatie-duplicatie opruimen** — `pages` veld toegevoegd aan alle custom paginatie-schemas + manual dict return gefixt. | 🟢 Nice-to-have | S | ✅ Ja | ✅ Sessie 85 |
| CQ-8 | **Dead code verwijderen** — GmailProvider (364 regels verwijderd) | 🟢 Nice-to-have | S | ✅ Ja | ✅ Sessie 84 |
| CQ-9 | **Test hygiene** — 21x hardcoded datum `"2026-02-17"` → `date.today().isoformat()` in test_cases.py | 🟢 Nice-to-have | S | ✅ Ja | ✅ Sessie 84 |

**Aanbevolen volgorde:** CQ-1 + CQ-2 + CQ-3 (float→Decimal, samen doen) → CQ-4 (stille bug) → CQ-5 → CQ-6 → CQ-7/8/9

### Uitrolplan (na pre-launch sprint)

1. ✅ **QA Walkthrough** — volledige Playwright walkthrough (sessie 75, 16 mrt)
2. ✅ **QA Bugfixes** — 4 P1 + 3 P2 bugs gefixt (sessie 76, 18 mrt)
3. **AI Factuur Parsing Validatie** — LF-10 feature uitgebreid testen met echte facturen van Lisanne. Test cases: verschillende factuurtypes (B2B/B2C), incomplete facturen, meerdere vorderingen, edge cases. Doel: betrouwbaarheid valideren voor productiegebruik.
4. ✅ **Test data opschonen** — 13 rommel cases + 15 rommel contacten verwijderd (sessie 76, 18 mrt)
5. **Demo met Lisanne** — samen door hele workflow lopen, feedback verzamelen
6. **Feedback-fixes** — top-5 items fixen (1 sessie)
7. **Soft launch** — 2-3 echte dossiers in Luxis, BaseNet blijft primair (2 weken)
8. **Parallel draaien** — nieuwe dossiers in Luxis, BaseNet als backup (1 maand)
9. **M0b: Lisanne naar M365** — email migratie
10. **BaseNet opzeggen** — als alles bewezen werkt

---

### QA-traject: Systeembrede Testdekking

**Doel:** Elke module dezelfde testdekking als P1 — backend integration tests, Playwright E2E, smoke test checklist.

**Aanpak:** Per module, in prioriteitsvolgorde. Elke fase levert: pytest tests + E2E tests + smoke checklist.

| Fase | Module | Huidige dekking | Wat nodig is | Status |
|------|--------|----------------|--------------|--------|
| QA-0 | Bestaande test fixes | 20 tests stuk (BUG-30 t/m 35) | URL paden, schema's, transitions updaten | ✅ Compleet (3 mrt, sessie 29) — 380/380 tests PASSED |
| QA-1 | Auth & Permissions | 14 tests (passing) | Login, refresh, token validatie, expired JWT, inactive user, tenant isolation | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-2 | Relaties/Contacts | 23 tests (passing) | CRUD, links, conflict check, zoeken, cross-tenant isolation (5 tests) | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-3 | Zaken/Cases | 19 tests (passing) | CRUD, status workflow, partijen, activiteiten, cross-tenant isolation, terminal status lock | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-4 | Email/Sync | 11 tests | Case emails, unlinked, link/bulk-link, dismiss, detail, attachments, tenant isolation | ✅ Compleet (3 mrt, sessie 30) |
| QA-5 | Workflow/Taken | 19 tests | Statuses CRUD, transitions (B2B/B2C), tasks CRUD, rules, calendar, verjaring | ✅ Compleet (3 mrt, sessie 30) |
| QA-6 | Facturatie | 19 tests | Invoice CRUD, status workflow, BTW precision, credit notes, lines, expenses, payments | ✅ Compleet (3 mrt, sessie 30) |
| QA-7 | Tijdregistratie | 15 tests | CRUD, filters (case/billable/date), unbilled, summary, my/today, tenant isolation | ✅ Compleet (3 mrt, sessie 30) |
| QA-8 | Dashboard | 10 tests (passing) | KPI's, recente activiteit, auth checks, cross-tenant isolation | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-9 | Documents/Templates | 28 tests (passing) | Template CRUD, DOCX generatie, cross-tenant template/doc/docx isolation | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-P1 | Incasso Pipeline | 35 tests + 9 E2E | **Compleet** (sessie 28) | ✅ Gedaan |

### E2E Tests (Playwright) — Sessie-overzicht

**Doel:** Elke core flow gedekt met Playwright E2E tests naast backend pytest tests.

**Aanpak:** Opgesplitst in 3-4 sessies. Auth setup via storageState (login eenmalig, hergebruik in alle specs).

| Sessie | Scope | Tests | Status |
|--------|-------|-------|--------|
| E2E-1 | Auth + Dashboard + Sidebar + Relaties CRUD | 16 tests (1 setup + 4 auth + 3 dashboard + 3 sidebar + 5 relaties) | ✅ Compleet (4 mrt, sessie 32) |
| E2E-2 | Zaken CRUD (7 detail tabs, edit, status, delete) | 8 tests | ✅ Compleet (4 mrt, sessie 33) |
| E2E-3 | Facturen (7) + Tijdschrijven (5) | 12 tests | ✅ Compleet (5 mrt, sessie 35) |
| E2E-4 | Correspondentie (2) + Agenda (3) + Taken (3) | 8 tests | ✅ Compleet (5 mrt, sessie 36) |
| E2E-fix | Incasso pipeline tests gefixt + lint cleanup | 7 tests un-skipped | ✅ Compleet (6 mrt, sessie 37) |

**Totaal nu:** 44 E2E tests (nieuwe) + 7 incasso E2E tests (gefixt) = **51 E2E tests passing** (was 44 passing + 7 skipped)

### DevOps Enhancements (sessie 33, 4 maart) ✅

- Bekende fouten gecodificeerd: 15 → 28 items (retroactieve analyse 32 sessies)
- `/learn`, `/compact-smart`, `/verify` commands aangemaakt
- Stop hook met session-end checks (SESSION-NOTES, ROADMAP, uncommitted/unpushed)
- Security deny list (ssh, scp, dangerous rm/curl)
- `float()` → `Decimal` fix in dashboard + incasso services/schemas

**Bestanden:**
- `frontend/e2e/auth.setup.ts` — storageState setup
- `frontend/e2e/auth.spec.ts` — login, invalid creds, persistence, logout
- `frontend/e2e/dashboard.spec.ts` — greeting, KPI cards, new dossier button
- `frontend/e2e/sidebar.spec.ts` — nav items, click navigation, collapse/expand
- `frontend/e2e/relaties.spec.ts` — list, create company/person, edit, delete
- `frontend/e2e/helpers/auth.ts` + `api.ts` — shared utilities
- `frontend/e2e/facturen.spec.ts` — invoice lifecycle (create, detail, approve, send, payment, delete)
- `frontend/e2e/tijdregistratie.spec.ts` — time entry CRUD (create, verify, edit, delete)

---


> Bron: `PROMPT-BEVINDINGEN-LISANNE.md` — 10 bevindingen uit 10 min testen
> Analyse: `BEVINDINGEN-ANALYSE.md` — volledige gap-analyse met concurrent-research

**Kernprobleem:** Het dossier is niet compleet als werkhub. Bij BaseNet/Clio/Kleos doe je ALLES vanuit het dossier. Luxis mist kritieke velden en acties.

### F-Sprint 1: P0 Quick Wins — ✅ GEDAAN (commit `97e9d22`, 20 feb 2026)

| # | Bevinding | Status |
|---|-----------|--------|
| F1 | **Zoekfunctie** — `/api/search` endpoint gebouwd (global search over zaken, relaties, documenten) | ✅ Gedaan |
| F2 | **Postadres tonen** bij relaties | ✅ Gedaan |
| F3 | **Geboortedatum** bij personen | ✅ Gedaan (migration 022) |
| F4 | **Referentienummer partij** (`external_reference` op case_parties) | ✅ Gedaan (migration 022 + UI in PartijenTab) |
| F5 | **Rechtbank/rolnummer** (`court_case_number` op cases) | ✅ Gedaan (migration 022 + UI in Dossiergegevens) |

### F-Sprint 2: P1 Uitbreidingen — ✅ GEDAAN (commits `c55846b` + `821e281`, 20 feb 2026)

| # | Bevinding | Status |
|---|-----------|--------|
| F6 | **Facturatieprofiel** bij relaties (`default_hourly_rate`, `payment_term_days`, `billing_email`, `iban`) | ✅ Gedaan (migration 023 + Facturatie-sectie op relatiedetail) |
| F7 | **Afwijkende factuurrelatie** per dossier (`billing_contact_id` FK op cases) | ✅ Gedaan (migration 023) |
| F8 | **Inline contact aanmaken** bij dossier-aanmaak ("+ Nieuwe relatie" knop) | ✅ Gedaan (frontend modal op nieuw-dossier pagina) |
| F9 | **Uitgebreide filters** dossier-overzicht (assigned_to, date_from, date_to, bedrag) | ✅ Gedaan (backend + "Meer filters" panel) |
| F10 | **Telefoonnotitie-knop** met auto-timestamp template | ✅ Gedaan (quick-action knop op zaakdetail) |

### F-Sprint 3: P2 — NOG TE DOEN

| # | Bevinding | Complexiteit | Status |
|---|-----------|-------------|--------|
| F11 | **E-mail naar elke partij vanuit dossier** | L (eerst M365) of M (SMTP basis) | ✅ DONE (21 feb) |

> Detail per bevinding + concurrent-analyse + zelfkritiek: zie `BEVINDINGEN-ANALYSE.md`

**Werkwijze per feature:**
1. Onderzoek concurrenten
2. Plan voorleggen
3. Bouwen
4. `npm run build` / `pytest` + handmatig checken
5. Committen
6. Volgende feature

---

## Lisanne Feedback Sprint (LF-01 t/m LF-22)

**Bron:** `docs/research/LISANNE-FEEDBACK-13MRT.md` (13 maart 2026, eerste echte gebruik)
**Projectplan:** `.claude/plans/staged-popping-haven.md`
**Aanpak:** 8 fasen, 2 terminals parallel per fase, ~5-7 sessies doorlooptijd

### Alle items

| # | Beschrijving | Cat. | Grootte | Fase | Status |
|---|-------------|------|---------|------|--------|
| LF-01 | Contact aanmaken: adresvelden ontbreken | UX | S | 2 | ✅ 16 mrt |
| LF-02 | Dossieroverzicht: partijnamen niet zichtbaar bij smal scherm | UX/Responsive | S | 1 | ✅ 16 mrt |
| LF-03 | Afgesproken rente: geen keuze maand/jaarbasis | Feature | S-M | 2 | ✅ 16 mrt — rate_basis op Claim model |
| LF-04 | Vordering invullen bij aanmaken dossier | UX/Feature | M | 4 | ✅ 16 mrt — onderdeel wizard (LF-11) |
| LF-05 | Kenmerk client ontbreekt (veld bestaat al als `reference`) | UX/Vindbaarheid | S | 1 | ✅ 16 mrt |
| LF-06 | Vordering niet zichtbaar na invullen, hoofdsom 0, incassokosten niet zichtbaar | Bug | M | 1 | ✅ 16 mrt — Case.total_principal cache fix |
| LF-07 | Navigatie factuur → terug → facturenoverzicht i.p.v. dossier | Bug | S | 1 | ✅ 16 mrt |
| LF-08 | Vorderingen niet aanpasbaar (edit UI ontbreekt) | Bug | S-M | 1 | ✅ 16 mrt — inline edit + useUpdateClaim |
| LF-09 | Geüploade factuur niet gekoppeld aan vordering | Feature | M | 3 | ✅ 16 mrt — backend: invoice_file_id FK + PATCH endpoint |
| LF-10 | AI factuur parsing: auto-invullen bij aanmaken dossier | Feature (AI) | XL | 8 | ✅ 16 mrt |
| LF-11 | Dossier aanmaken: alles in een keer (wizard) | UX/Feature | L | 4 | ✅ 16 mrt — 3-step wizard: zaakgegevens → partijen → vordering |
| LF-12 | Incassokosten handmatig aanpasbaar + calculator | Feature | M | 2 | ✅ 16 mrt — frontend UI + backend persistence (bik_override) |
| LF-13 | Tabs "Vorderingen" en "Financieel" samenvoegen | UX | M | 3 | ✅ 16 mrt |
| LF-14 | Tabs "Betalingen" en "Derdengelden" samenvoegen | UX | M | 3 | ✅ 16 mrt |
| LF-15 | Betalingsregeling: termijnen, koppeling, meldingen | Feature (nieuw) | L-XL | 6 | ✅ 16 mrt |
| LF-16 | Email template vanuit dossier (functie bestaat, niet vindbaar) | UX/Vindbaarheid | S | 1 | ✅ 16 mrt |
| LF-17 | Dossierbestand als email bijlage + omgekeerd | Feature | M | 5 | ✅ 16 mrt |
| LF-18 | Batch-verstuurde brieven niet traceerbaar per dossier | Bug | M | 1 | ✅ 16 mrt |
| LF-19 | Uurtarief per dossier aanpasbaar | Feature | S-M | 2 | ✅ 16 mrt — hourly_rate op Case model |
| LF-20 | Incassokosten doorbelasten bij facturatie (succesprovisie) | Feature | L | 7 | ✅ 16 mrt — provisie berekening, budget tracking, advance balance |
| LF-21 | Fixed price, max uren, voorschot bij facturatie | Feature | L | 7 | ✅ 16 mrt — billing_method, voorschotnota, budget status |
| LF-22 | Debiteursinstellingen in dossier | Feature | M | 2 | ✅ 16 mrt — payment_term_days, collection_strategy, debtor_notes |

### Fase-overzicht

| Fase | Doel | Items | Terminals |
|------|------|-------|-----------|
| 1 | Bugs & Vindbaarheid | LF-02, LF-05, LF-06, LF-07, LF-08, LF-16, LF-18 | 2 parallel |
| 2 | Kleine features + velden | LF-01, LF-03, LF-12, LF-19, LF-22 | 2 parallel |
| 3 | Tab herstructurering | LF-09, LF-13, LF-14 | 2 parallel |
| 4 | Dossier wizard | LF-04, LF-11 | 2 sequentieel |
| 5 | Email verbeteringen | LF-17 | 2 sequentieel |
| 6 | Betalingsregeling | LF-15 | 2 sequentieel |
| 7 | Geavanceerde facturatie | LF-20, LF-21 | 2 parallel |
| 8 | AI factuur parsing | LF-10 | 2 sequentieel |

### Dependencies

```
LF-04 → onderdeel van LF-11
LF-06 → moet gefixt voor LF-12, LF-13
LF-08 → moet gefixt voor LF-09, LF-12
LF-16 → moet vindbaar voor LF-17
LF-19 → basis voor LF-20, LF-21
LF-10 → afhankelijk van LF-11
```

---

> **Toekomstige modules** (M365, AI Agent, Data Migratie, etc.) staan in `docs/future-modules.md`
>
> **AI Agent Masterplan** (sessie 38, 6 maart 2026): Uitgebreid onderzoeksplan in `docs/research/AI-AGENT-MASTERPLAN.md` (branch `claude/admiring-engelbart`).
>
> **AI Agent — Fase A1: MCP Tool Layer** ✅ Compleet (sessie 49, 11 maart 2026):
> 34 tools wrappen bestaande Luxis services voor Claude tool use. Fundament voor A2-A4.
> Componenten: ToolRegistry, ToolExecutor, serialize utility, 10 handler modules.
> Tools: cases (5), contacts (3), collections (5), documents (3), email (2), invoices (5),
> pipeline (3), workflow (3), time_entries (2), general (3). 26 bestaande tests passing, ruff clean.
> 57 tests voor tool layer toegevoegd in sessie 50 (registry 14, executor 8, serializer 35). Totaal: 83 AI agent tests.
> **AI Agent — Fase A2.1: Dossier Intake Agent** ✅ Compleet (sessie 52, 11 maart 2026):
> Client stuurt email met factuur → AI extraheert debiteur/factuurdata → concept-dossier → 1-klik goedkeuring.
> Kimi 2.5 primair ($0.001/call), Haiku 4.5 fallback ($0.005/call). PDF parsing via pdfplumber.
> Componenten: IntakeRequest model, kimi_client (dual AI provider), pdf_extract, intake_service (detect/process/approve/reject),
> intake_router (7 endpoints), intake_schemas, intake_prompts. Scheduler: elke 7 min. Migratie: 037_intake_requests.
> 20 tests (detection 5, processing 4, approve 3, reject 1, queries 2, multi-tenant 1, API 4). 509 totaal tests passing.
> **AI Agent — Fase A2.1 Frontend: Intake Review UI** ✅ Compleet (sessie 53, 11 maart 2026):
> Overzichtspagina (/intake) met status filter tabs + confidence bars + paginatie.
> Detail/review pagina (/intake/[id]) met inline-bewerkbare velden, approve/reject flow, AI analyse card.
> Sidebar integratie met pending count badge. 7 TanStack Query hooks. Frontend-only deploy.
>
> **AI Agent — Fase A2.2: Follow-up Advisor** ✅ Compleet (sessie 54, 11 maart 2026) — **Productietest PASS** (sessie 60):
> Rules-based workflow advisor — scant actieve incasso-dossiers, maakt aanbevelingen als min_wait_days bereikt.
> Backend: FollowupRecommendation model, scan service (30min scheduler), approve/reject/execute endpoints, 19 tests.
> Execute-flow: document genereren, email versturen, auto-advance pipeline stap. Geen AI/LLM nodig (deterministisch).
> Frontend: /followup pagina met status tabs + urgentie badges + 1-klik uitvoeren. Sidebar badge. Case detail banner.
> Productietest (sessie 60): 3/3 recommendations correct aangemaakt, urgency correct (normal/overdue), approve+execute succesvol (doc+email+auto-advance).
>
> **AI Agent — Fase A3: Betalingsmatching** ✅ Compleet (sessie 56-57, 11 maart 2026):
> CSV-import van Rabobank derdengeldrekening → auto-match aan incasso-dossiers → 1-klik goedkeuring.
> 5 matching methoden: dossiernr (95), factuurnr (90), IBAN (85), bedrag (70), naam (50).
> Execute: Derdengelden deposit + Payment record met art. 6:44 BW distributie. Volgt A2.2 patroon.
> Backend: 7 bestanden (models, csv_parsers, algorithm, schemas, service, router, migration). 15 API endpoints. 40 tests (568 totaal).
> Frontend: /betalingen pagina met CSV drag-and-drop upload, match review (confidence badges), 1-klik approve, bulk approve (≥85%), stats badges, sidebar met pending count badge.
>
> **AI Agent — Intake E2E Testpakket** (COMPLEET ✅):
> Laag 1: ✅ Seed script (`scripts/seed_intake_testdata.py`) — 18 intake_requests met diverse statussen/confidence/scenario's. --dry-run en --cleanup. (sessie 58, 11 maart)
> Laag 2: ✅ Test-factuur PDFs (`scripts/generate_test_invoices.py`) — 5 professionele Nederlandse facturen via WeasyPrint. Output: `scripts/test_invoices/`. (sessie 58, 11 maart)
> Laag 3: ✅ COMPLEET — Geautomatiseerd E2E script (`scripts/e2e_intake_test.py`) — directe service-calls met gemockte AI extractie. 4 scenario's (happy path, lege email body, edit-before-approve, reject flow). Marker-based cleanup, deterministische UUIDs, onafhankelijke DB sessies per scenario. (sessie 59, 11 maart)
> **LET OP: GEEN Gmail gebruiken — alles via OutlookProvider/Graph API met M365 account.**
>
> **AI Agent — Knowledge Base & Learning Loop** 📋 Gepland:
> De agent heeft een kennisbank nodig (algemene voorwaarden, wettelijke regels, interne richtlijnen) en een feedback/learning loop
> zodat hij leert van Lisanne's correcties en steeds beter wordt. Vereist: onderzoekssessie (hoe doen Harvey AI, CoCounsel, Clio AI dit?)
> → architectuurkeuze (RAG vs structured prompting) → knowledge base UI → feedback loop mechanisme.
> Onderdelen:
> - Knowledge base in Luxis (algemene voorwaarden Kesting Legal, wettelijke regels, standaard reacties, interne richtlijnen)
> - Feedback loop: agent voorstel → Lisanne keurt goed/corrigeert → agent onthoudt de juiste aanpak
> - Patroonherkenning: na N dossiers leert de agent welke aanpak werkt bij welk type debiteur
> - UI voor kennisbeheer (toevoegen/bewerken van kennis door Arsalan/Lisanne)
> - Meetbaarheid: success rate, aantal escalaties, verbetering over tijd
>
> **AI Email Classificatie** (sessie 39-43, 6 maart 2026): Eerste concrete AI-feature. Classificeert debiteur-emails in 8 categorieën, selecteert antwoord-template, Lisanne reviewt met 1 klik. Claude Haiku 4.5 via Anthropic SDK. Status: **Fase 1-7 COMPLEET** ✅ — E2E getest op productie.
>
> **AI Classificatie — Fase 7: Echte actie-executie** ✅ Compleet (sessie 45, 7 maart 2026):
> Alle acties in `execute_classification()` geïmplementeerd met echte side-effects:
> | Actie | Wat het doet | Status |
> |-------|-------------|--------|
> | `dismiss` | `SyncedEmail.is_dismissed = True` | ✅ |
> | `send_template` | Jinja2 template renderen + email versturen via EmailProvider/SMTP | ✅ |
> | `request_proof` | Template "verzoek betalingsbewijs" versturen via EmailProvider/SMTP | ✅ |
> | `wait_and_remind` | WorkflowTask aanmaken met due_date = vandaag + N dagen | ✅ |
> | `escalate` | WorkflowTask aanmaken (urgent, due_date=vandaag) | ✅ |
> | `no_action` | Alleen CaseActivity loggen | ✅ (was al werkend) |
> 4 nieuwe tests toegevoegd (26 totaal), ruff clean.

## Deploy

**Belangrijk:**
- `.env` moet bestaan in `/opt/luxis/`. Docker Compose leest dit automatisch. Als het ontbreekt: `cp .env.production .env`.
- `.env` bevat `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml` — hierdoor werkt gewoon `docker compose up -d` zonder `-f` flags.
- `POSTGRES_PASSWORD` in `.env` werkt ALLEEN bij eerste DB-initialisatie (volume aanmaken). Wachtwoord later wijzigen? → `docker compose exec db psql -U luxis -d luxis -c "ALTER USER luxis PASSWORD 'nieuw_wachtwoord';"` + `docker compose restart backend`
- Frontend moet ALTIJD relatieve URLs gebruiken (`""`) — NOOIT `localhost:8000`. Pre-commit hook blokkeert dit.
- Na Alembic migraties: `docker compose run --rm backend python -m alembic upgrade head` (gebruik `run` niet `exec` als backend crashed)

Frontend + backend:
```bash
cd /opt/luxis && git pull && \
docker compose build --no-cache frontend backend && \
docker compose up -d frontend backend
```

Alleen backend:
```bash
cd /opt/luxis && git pull && \
docker compose build --no-cache backend && \
docker compose up -d backend
```

Alleen frontend:
```bash
cd /opt/luxis && git pull && \
docker compose build --no-cache frontend && \
docker compose up -d frontend
```
