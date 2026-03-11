# Luxis — Project Roadmap (Source of Truth)

**Laatst bijgewerkt:** 11 maart 2026 (sessie 53)
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
| Backend (FastAPI) | ~90% | 120+ endpoints, 15 routers, solide CRUD en business logic, correcte financial calculations. Budget tracking, recurring tasks, document preview endpoints. |
| Frontend (Next.js) | ~65% | Alle Fase A-E + T1-T3 + F1-F10 + G3/G5/G9/G10/G11/G13/G14 features gebouwd. Budget module, recurring tasks, inline document preview, status-filtered templates, workflow-suggesties, keyboard shortcuts. |
| Infra/DevOps | ~85% | Docker Compose op Hetzner VPS. Caddy reverse proxy. SSH deploy key geïnstalleerd (sessie 46) — Claude deployt nu autonoom via SSH. Frontend gebruikt relatieve URLs + Next.js rewrites `/api/*` → `backend:8000`. |

**Rode draad:** De backend is vaak verder dan de frontend. ~40% van de verbeteringen vereist geen backend-werk.

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
| T3 | E-mail versturen vanuit Luxis (SMTP) | Groot | ✅ Gebouwd (20 feb) — compose dialog, send knop, correspondentie tab, email logs, test email, instellingen tab. **SMTP werkend met Gmail test-credentials. Later omzetten naar Lisanne's Outlook.** |

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

---

## Backlog / Feature Requests

- ~~**FEATURE: Relaties — inline contactpersoon aanmaken vanuit koppeldialoog**~~ ✅ Gedaan (sessie 19) — inline aanmaken van advocaat wederpartij bij nieuw dossier
- ~~**FEATURE: Advocaat wederpartij — klikbare detailweergave**~~ ✅ Gedaan (sessie 19) — zaken zichtbaar op relatiepagina via CaseParty filter + "Partij" rol label

### Incasso Workflow Automatisering (P1)

**Doel:** Eén klik op "Verstuur brief" voor 40 dossiers → alles automatisch.

1. ✅ **Template editor UI** — Sjablonen tab in Instellingen: upload, download, bewerken, verwijderen van DOCX templates. Database-driven met disk-fallback. Incasso pipeline gebruikt dynamische template dropdown. Gebouwd sessie 24.
2. ✅ **Batch brief + email verzenden** — "Verstuur brief" genereert documenten, converteert naar PDF, en emailt ze als bijlage naar de wederpartij via provider (Gmail/Outlook) met SMTP fallback. Email toggle in PreFlightDialog, instelbare email templates per stap, email readiness check in preview. Gebouwd sessie 27.
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

**Volgende prioriteit:** Frontend polish afgerond (sessie 48). Bepaal volgende prioriteit: P2 features, Lisanne-feedback, of QA uitbreiden.

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
