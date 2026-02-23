# Luxis — Project Roadmap (Source of Truth)

**Laatst bijgewerkt:** 23 februari 2026
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
| Backend (FastAPI) | ~85% | 115+ endpoints, 15 routers, solide CRUD en business logic, correcte financial calculations. `/api/search` gebouwd. Billing profile (F6), billing_contact_id (F7), extended filters (F9), incasso pipeline (sessie 9) toegevoegd. |
| Frontend (Next.js) | ~60% | Alle Fase A-E + T1-T3 + F1-F10 features gebouwd. Status-filtered templates, workflow-suggesties, inline contact creation, telefoonnotitie, facturatieprofiel UI. |
| Infra/DevOps | ~80% | Docker Compose + Caddy reverse proxy op Hetzner VPS. Productie draait op `docker-compose.prod.yml` met `--env-file .env.production`. SSL via Caddy auto-TLS. |

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
Togglebare modules per tenant: `incasso`, `tijdschrijven`, `facturatie`, `wwft`

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
| B3 | Notities verbeteren | Klein | ✅ Gebouwd (quick note input op Overzicht tab, simple markdown, notes in timeline) |

### Fase C: Dashboard & Facturatie (kan parallel met B)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| C1 | Dashboard verbeteren (vandaag-focus, grafieken, KPI's) | Midden | ✅ Gebouwd (KPI's, pipeline bar, taken widget, weekoverzicht, recente facturen/activiteit) |
| C2 | Betalingstracking op facturen | Groot (nieuw DB model) | ✅ Volledig gebouwd (backend: model, CRUD, auto-status, 18 tests + frontend: payment tracking UI, progress bar, form, deels-betaald status) |
| C3 | Credit nota's | Midden | ✅ Gebouwd (20 feb) — invoice_type + linked_invoice_id, CN-nummering, credit nota aanmaken vanuit factuurdetail, regels pre-fill, purple styling, lijst-weergave met CN badge |

### Fase D: Algemene UX polish

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| D1 | Wachtwoord vergeten flow | Klein-Midden | ✅ Gebouwd (forgot-password op login, reset-password pagina met token, 3-staps flow) |
| D2 | Gebruikersbeheer (rollen, rechten) | Groot | ❌ Niet relevant (Lisanne is enige gebruiker) |
| D3 | Navigatie-verbeteringen | Klein | ✅ Gebouwd (breadcrumbs met dynamische labels, nested routes) |
| D4 | Empty states en loading states | Klein | ✅ Gebouwd (skeleton loaders op alle dashboard pagina's) |
| D5 | Agenda events aanmaken | Midden (nieuw model + CRUD) | ✅ Gebouwd (20 feb) — CalendarEvent model met 7 typen, CRUD endpoints, EventDialog create/edit/delete, unifide calendar hook, case/contact pickers |

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

## Bugs — Volgende sessie fixen

> Detail + bestanden + fix-instructies: zie `BUGS-EN-VERBETERPUNTEN.md`

| # | Bug | Ernst | Fix-grootte | Status |
|---|-----|-------|-------------|--------|
| BUG-1 | Relatie niet automatisch gekoppeld bij nieuwe zaak vanuit relatiedetail | Hoog | Klein (URL params + form pre-fill) | ✅ Gefixt (20 feb) |
| BUG-2 | Rente-velden zichtbaar bij niet-incasso zaaktypes | Midden | Klein (conditional render) | ✅ Gefixt (20 feb) |
| BUG-3 | Renteberekening per documentdatum controleren | Hoog | Verificatie nodig | ✅ Geverifieerd — werkt correct (20 feb) |
| BUG-6 | Conflict check mist op zaakdetail Partijen tab (warning, niet blokkeren) | Midden | Klein | ✅ Gefixt (20 feb) |
| BUG-7 | Dossiergegevens niet bewerkbaar op detailpagina — `court_case_number` (F5) toont alleen als gevuld maar kan nergens ingevuld worden. Dossierdetail mist edit-modus voor alle velden (beschrijving, referentie, zaaknummer, etc.) | Hoog | Midden | ✅ Gefixt (21 feb) — Bewerken-knop + inline edit met Opslaan/Annuleren, zaaknummer altijd zichtbaar |
| BUG-8 | `court_case_number` veld ontbreekt op "Nieuw dossier" formulier — kan alleen via (niet-bestaande) edit-modus op detailpagina | Midden | Klein | ✅ Gefixt (21 feb) — veld toegevoegd aan formulier + backend CaseCreate schema |
| BUG-9 | Advocaat wederpartij niet zichtbaar/toevoegbaar in dossier — gebruiker kan niet in één oogopslag zien wie de belangrijkste contactpersonen zijn | Hoog | Midden | ✅ Gefixt (21 feb) — zoekfield toegevoegd in Dossiergegevens (view+edit) + Nieuw dossier form |
| BUG-10 | Dossier edit: velden wissen werkt niet — je kunt tekst toevoegen en opslaan, maar als je het wist en opslaat blijft de oude waarde staan. Oorzaak: `\|\| undefined` in handleSaveDetails. | Hoog | Klein | ✅ Gefixt (21 feb) — `.trim() \|\| null` stuurt lege velden als null mee |
| BUG-11 | Taken niet zichtbaar na aanmaken in dossier — `useWorkflowTasks` verwachtte paginated object maar backend retourneert array. Ook: geen `assigned_to_id` bij handmatig aanmaken → taak verscheen niet bij Mijn Taken | Hoog | Klein | ✅ Gefixt (22 feb) — hook return type gecorrigeerd, `assigned_to_id` auto-set |
| BUG-12 | Geen "Nieuwe taak" optie op Mijn Taken pagina — kon alleen vanuit dossier taken aanmaken | Midden | Klein | ✅ Gefixt (22 feb) — Nieuwe taak knop + formulier met dossier-picker |

---

## Volgorde van werken

**✅ Afgerond:** A1-A7, B1-B3, C1-C3, D1/D3/D4/D5, E1-E8, T1-T3, F1-F10, alle bugs t/m BUG-12
**✅ VPS login gefixt** (21 feb) — DB wachtwoord mismatch opgelost, frontend herbouwd met correcte NEXT_PUBLIC_API_URL
**✅ BUG-7/8/9 gefixt** (21 feb) — edit-modus, zaaknummer op form, advocaat wederpartij
**❌ Niet relevant:** D2 (gebruikersbeheer — Lisanne is enige gebruiker)
**TODO:** SMTP omzetten van Gmail test-credentials naar Lisanne's Outlook (wacht op M365 migratie)
**✅ F11 geïmplementeerd** (21 feb) — freestanding e-mail vanuit dossier met recipient quick-select chips
**✅ M6 gebouwd** (22 feb) — Ongesorteerde email wachtrij met split-view, suggesties, bulk link/dismiss, sidebar badge
**✅ Dossier detail refactoring** (sessie 5, 22 feb) — `zaken/[id]/page.tsx` van 4236 → ~236 regels, opgesplitst in 8 componentbestanden + types.tsx
**✅ G3 Procesgegevens** (sessie 6, 22 feb) — 5 nieuwe velden (court_name, judge_name, chamber, procedure_type, procedure_phase) + backend migration 028 + DetailsTab Procesgegevens card met NL rechtbank dropdown
**✅ G5 Keyboard shortcuts** (sessie 6, 22 feb) — T=timer, N=notitie, D=documenten, E=email, F=facturen, 1-9=tabs
**✅ G14 Dossier sidebar** (sessie 7, 22 feb) — Collapsible properties sidebar met dossierinfo, client, wederpartij, advocaat, financieel snapshot (OHW + incasso/non-incasso)
**✅ G10 Task templates** (sessie 7, 22 feb) — Automatische taak-templates bij case creation: incasso 8 taken, advies 4, insolventie 4, overig 2
**✅ BUG-11/12 gefixt** (sessie 8, 22 feb) — Taken zichtbaar na aanmaken + Nieuwe taak knop op Mijn Taken pagina
**✅ Incasso Batch Werkstroom** (sessie 9, 23 feb) — IncassoPipelineStep model + CRUD + batch actions + /incasso pagina met pipeline editor + batch werkstroom + pre-flight wizard + sidebar item. Migration 029.
**✅ Template koppeling + Documentgeneratie + Smart Work Queues** (sessie 10, 23 feb) — template_type op pipeline steps (modern docx systeem), batch "Verstuur brief" genereert documenten via render_docx(), Smart Work Queue tabs (klaar/14d verlopen/actie vereist) + sidebar badge. Migration 030.
**Volgende prioriteit (sessie 11):** Document template editing UI + merge fields uitbreiden (procesgegevens, partijen, betalingstermijn naar templates). Documenten-pagina moet templates bewerkbaar maken. Zie hieronder voor details.

### Sessie 11 Plan: Document Templates & Merge Fields

**Probleem 1: Templates niet bewerkbaar in UI**
De Documenten-pagina (`/documenten`) toont templates read-only. Lisanne kan ze niet aanpassen. De .docx bestanden moeten handmatig op de server vervangen worden. Oplossing: upload-functie voor .docx templates + preview met voorbeelddata.

**Probleem 2: Niet alle dossierdata komt in documenten terecht**
De `render_docx()` functie in `docx_service.py` bouwt context op maar mist:
- Procesgegevens: `court_name`, `court_case_number`, `judge_name`, `chamber`, `procedure_type`, `procedure_phase` (bestaan op Case model maar worden NIET doorgegeven)
- CaseParty data: deurwaarder, advocaat wederpartij (bestaan in DB maar niet in template context)
- Betalingstermijn: `Contact.payment_term_days` (beschikbaar maar niet doorgegeven)
- Advocaat wederpartij naam/kantoor (uit CaseParty of Case.opposing_party_lawyer)

**Aanpak:** Eerst templates finaliseren met Lisanne, dan merge fields uitbreiden. Beide in sessie 11.

> **Sessie-log:** Zie `SESSION-LOG-20FEB-SESSIE3.md` voor gedetailleerde context over wat er al bestaat voor email (backend email module, SMTP service, send endpoint, templates)

---

## Fase F: Bevindingen Praktijktest Lisanne (21 feb 2026)

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

## Volgende grote module: Microsoft 365 Email Integratie

**Doel:** "Best of breed" email — het beste van BaseNet, Kleos, Hammock, Smokeball en Clio combineren. Lisanne werkt in Outlook, Luxis regelt de rest automatisch op de achtergrond.

**Email strategie (beslissing 21 feb 2026):**
- **F11 (SMTP vanuit Luxis)** is een **tijdelijke brug** — werkt nu, maar emails verschijnen niet in Outlook's Verzonden map
- **M1-M6 (email integratie)** is de **eindoplossing** en wordt nu **prioriteit**
- **Abstractielaag:** `EmailProvider` interface met `GmailProvider` (dev/test) + `OutlookProvider` (Lisanne, later)
- **Test-aanpak:** Gmail API met Arsalan's account → alles bouwen en testen → later OutlookProvider toevoegen voor Lisanne
- **Azure blocker:** Gratis Outlook.com accounts kunnen geen apps meer registreren → Gmail API als dev/test provider
- **Overgangspad:** F11 blijft werken totdat M4 live is → dan vervangt de email provider de Luxis SMTP compose dialog

**Technisch fundament:** OAuth 2.0 + abstractielaag — Gmail API (dev) / Microsoft Graph API (productie)

**Prereq: Mail migratie BaseNet → Microsoft 365**
- Lisanne's mail draait nu op BaseNet (MX: `mx1.basenet.nl`)
- Microsoft 365 Business Basic aanschaffen (~€5,60/mnd)
- Oude mails migreren via IMAP migratie tool (gratis van Microsoft)
- MX records wijzigen bij domeinregistrar (kestinglegal.nl)
- Outlook instellen op laptop/telefoon
- **Moet samen met Lisanne** — zij moet inloggen, abonnement afsluiten, DNS goedkeuren

| Fase | Feature | Wat het oplevert | Status |
|------|---------|-----------------|--------|
| M0 | Mail migratie BaseNet → Microsoft 365 | Lisanne's mail draait op M365, Graph API beschikbaar | Wacht op Lisanne |
| M1 | OAuth + abstractielaag | EmailProvider interface, GmailProvider, OAuth flow, token opslag | ✅ Gebouwd (21 feb) |
| M2 | Inbox sync + auto-koppeling | Inkomende mails automatisch aan dossiers koppelen (afzender → relatie → dossier) | ✅ Gebouwd (21 feb) |
| M2+ | Dossiernummer-matching | Emails met "2026-00003" in onderwerp/body → automatisch aan juiste dossier | ✅ Gebouwd (21 feb) |
| M2+ | Klantreferentie-matching | Emails met bekende Case.reference → automatisch aan dossier | ✅ Gebouwd (21 feb) |
| M2+ | Zaaknummer rechtbank-matching | Emails met Case.court_case_number in tekst → automatisch aan dossier | ✅ Gebouwd (21 feb) |
| M2+ | body_html doorzoeken | HTML-only emails (Gmail/Outlook) worden nu ook doorzocht na HTML-stripping | ✅ Gefixt (21 feb) |
| M2+ | Bijlagen sync | Attachments downloaden van Gmail, opslaan, tonen in detail panel + download | ✅ Gebouwd (21 feb) |
| M2+ | Auto-sync (5 min) | APScheduler synct alle verbonden accounts elke 5 minuten automatisch | ✅ Gebouwd (21 feb) |
| M2+ | Re-match ongelinkte emails | Bestaande ongelinkte emails worden bij elke sync opnieuw gematcht (altijd, ook vanuit dossier-context) | ✅ Gebouwd + gefixt (21 feb) |
| M3 | Correspondentie tab (unified view) | Alle in- + uitgaande mails per dossier, split-view met detail panel + bijlagen | ✅ Gebouwd (21 feb) |
| M4 | Compose via provider | Send via Gmail API (verschijnt in Verzonden), fallback naar SMTP | ✅ Gebouwd (21 feb) |
| M5 | AutoTime op emails | Automatische tijdregistratie bij mail-activiteit (à la Smokeball) | 🔵 Backlog (bestaande timer dekt dit grotendeels) |
| M6 | "Ongesorteerd" wachtrij | Mails die niet auto-gekoppeld zijn handmatig toewijzen met suggesties | ✅ Gebouwd (22 feb) |

**Bouwvolgorde:** M0 (samen met Lisanne) → ~~M1 → M2 → M3 → M4 → M6~~ (M5 op backlog)

**Wat Lisanne ervaart na afronding:**
- Template aanklikken → opent direct in Outlook met alles pre-filled
- Inkomende mails worden automatisch aan het juiste dossier gekoppeld (op dossiernummer, referentie, of contactpersoon)
- Bijlagen worden automatisch meegesynced en zijn downloadbaar vanuit Luxis
- Op elk dossier: volledige correspondentie (in + uit) met bijlagen zichtbaar
- Email sync draait automatisch elke 5 minuten — geen handmatige actie nodig
- Tijdschrijven op email-activiteit gaat automatisch
- Ze hoeft Outlook niet te verlaten, maar alles staat ook in Luxis

---

## Toekomstige module: AI Incasso Agent

**Doel:** Een AI agent die repetitief incassowerk zelfstandig oppakt — het meeste incassowerk volgt vaste patronen met vaste templates en voorspelbare antwoorden.

**Wat de agent kan doen:**
- **Dossier aanmaken**: cliënt stuurt factuur + gegevens → agent maakt dossier aan, vult alle velden in
- **Workflow volgen**: herinnering → aanmaning → 14-dagenbrief → sommatie automatisch versturen op de juiste momenten
- **Reacties verwerken**: standaard-antwoorden herkennen ("ik betaal volgende week", "ik betwist de factuur", "ik heb al betaald") en juiste vervolgactie voorstellen
- **Betalingen matchen**: binnenkomende betalingen automatisch aan dossiers koppelen, restant berekenen, volgende stap bepalen
- **Rente berekenen**: automatisch bijwerken bij elke actie
- **Escaleren**: complexe situaties of onbekende reacties doorsturen naar Lisanne met context

**Hoe het werkt:**
1. Agent leert van Lisanne's bestaande dossiers (patronen, beslissingen, timing)
2. Nieuwe dossiers worden door de agent opgestart en gevolgd
3. Lisanne reviewt alleen: escalaties, onbekende situaties, dagvaardingen
4. Dashboard toont wat de agent heeft gedaan en wat Lisanne's aandacht nodig heeft

**Dependency:** Microsoft 365 Email Integratie (M1-M6) moet eerst af — de agent heeft email nodig om te functioneren.

**Technisch:** Claude API / Anthropic API + tool use, getraind op Lisanne's dossierpatronen en templates.

---

## Data Migratie: BaseNet → Luxis

**Doel:** Alle data uit BaseNet naadloos overzetten naar Luxis zodat Lisanne direct kan werken zonder dataverlies.

**Wat BaseNet exporteert (onderzocht 23 feb 2026):**
1. **Volledige backup** — dossiers, relaties, documenten, correspondentie als bestanden + CSV/Excel
2. **CRM/Relaties** — export naar Excel
3. **Boekhouding** — mutaties export naar Excel

**Mapping BaseNet → Luxis:**

| BaseNet Export | Luxis Tabel(len) | Complexiteit | Aanpak |
|---|---|---|---|
| Relaties (Excel/CSV) | `contacts` + `contact_links` | Laag | pandas parse → bulk insert |
| Dossiers (CSV) | `cases` + `case_parties` | Middel | ID-mapping, relatie-linking |
| Documenten (bestanden) | `generated_documents` / `case_files` + file storage | Middel | Bestanden kopiëren + metadata records |
| Correspondentie | `synced_emails` / `generated_documents` | Middel | Email parsing + dossier-linking |
| Boekhouding/mutaties | `invoices` + `payments` | Middel-Hoog | Extra validatie (totalen matchen) |
| Uren | `time_entries` | Laag | Directe mapping |

**Aanpak:**
1. **Parse-scripts** — Python scripts die BaseNet CSV/Excel inlezen met pandas
2. **Mapping & transformatie** — BaseNet velden → Luxis schema's (UUID generatie, tenant_id toewijzing, relatie-linking)
3. **ID-mapping tabel** — BaseNet ID's → Luxis UUID's zodat relaties intact blijven
4. **Dry-run modus** — rapporteert wat er geïmporteerd wordt zonder te schrijven
5. **Import** — Bulk insert via SQLAlchemy met transactie-rollback bij fouten
6. **Documenten** — Bestanden kopiëren naar Luxis storage volume, metadata records aanmaken
7. **Verificatie-rapport** — Telling per entiteit: verwacht vs geïmporteerd

**Aandachtspunten:**
- Boekhouding is het meest gevoelige deel → extra validatie
- Documentenvolume kan groot zijn → upload-tijd afhankelijk van VPS bandbreedte
- BaseNet export moet door Lisanne gedaan worden (toegangsrechten)

**Planning:** 1 sessie voor migratie-scripts + 1 sessie voor testen en uitvoeren
**Dependency:** Lisanne moet BaseNet export klaarzetten
**Status:** 📋 Gepland — wacht op BaseNet export van Lisanne

---

## Overige toekomstige modules (niet gepland, zie FEATURE-INVENTORY.md)

- Insolventiemodule (faillissement, WSNP, Recofa)
- Cliëntportaal
- Boekhoudkoppeling (Exact Online)
- Bulk operaties
- Management rapportages
- Mobiele app
- E-signing
- KvK API integratie
- Online betaling (Mollie/iDEAL)

---

## Deploy

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend
```

---

*Dit document is de enige source of truth. Alle andere .md bestanden verwijzen hiernaar voor status en prioriteit.*
