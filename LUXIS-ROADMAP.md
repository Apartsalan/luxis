# Luxis — Project Roadmap (Source of Truth)

> ⚠️ **LEES EERST `docs/ARCHITECTUUR-KAART.md`** (2 pag.) — hoe alle systemen aan elkaar
> hangen. Wordt óók automatisch geladen bij sessiestart (SessionStart-hook, S172). Wijzig
> je een systeemkoppeling → kaart bijwerken in dezelfde sessie. Feitelijke inventaris:
> `docs/audits/inventaris-2026-07-05.md`.

**Laatst bijgewerkt:** 12 juli 2026 (sessie 204, Fable — review S203-fixes, read-only). 9 van 11 fixes bevestigd; 2 vervolg-punten: mailsync-foutpad vergiftigt volgende accounts (bewezen) + 14-dagenbrief-gate heeft 2 zijdeuren en een zwakke verstuurd-proxy. Rapport: `docs/sessions/S204-review.md`. Volgende sessie = S205 fix-sessie.
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
| Backend (FastAPI) | ~97% | ~19 modules, ~290 endpoints, ~42 models (exacte inventaris: `docs/audits/inventaris-2026-07-05.md`), 684 tests (4 skipped). Financial calcs uitstekend getest. Alle routers getest. Ruff clean ✅. CI groen ✅. Zero-BTW bug gefixt ✅. Pipeline overhaul: 21 stappen, step_transitions (branching workflow), CaseStepHistory, verweer-tracking. |
| Frontend (Next.js) | ~87% | 24 pagina's (0 stubs), 29 hooks, 29 componenten. Alle 17 backend modules hebben frontend. Skeleton loaders, error boundaries, toast notifications, mobile responsive. 65 `any` types gekilld ✅, hooks cleanup ✅. E2E: 14 spec files (incl. settings, docs). **Impeccable design-audit S155 (7 jun): 10.5→~15.5/20** — login/dashboard ont-AI'd, timer-tick + zoek-flikker gefixt, 12 modals → Radix Dialog, toetsenbord/screenreader-toegankelijkheid, Mail/Incasso mobiel, dode dark:-classes weg. Rapport: `docs/qa/impeccable-audit-2026-06-07.md`. Restwerk: zie Backlog. |
| Infra/DevOps | ~98% | Docker Compose op Hetzner VPS. Caddy ✅. GitHub-hosted CI runners ✅. Auto-deploy via SSH ✅ (S159: draait nu `alembic upgrade head` + faalt hard op health). Backup: lokaal 7d + off-site B2 90d ✅, **restore-test bewezen S159** (`docs/runbooks/restore.md`). fail2ban ✅. **ufw actief (22/80/443) S159** ✅. **uptime-cron gefixt S159** ✅. `TOKEN_ENCRYPTION_KEY` gezet ✅. Kernel 6.8.0-106 ✅. API docs + runbook ✅. CI 6/6 groen ✅. |

**Rode draad:** Backend ~97%, Frontend ~85%, Infra ~98%. Fasen 1-3 + 5 + 6 compleet. CI volledig groen (6/6 jobs).

**Strategische modus (sessie 116, 7 april 2026):** Marktonderzoek afgerond, GTM-plan voorbereid. Arsalan is nog in de **bouw/validatie-fase met Lisanne** (demos lopen). Luxis gaat de markt op zodra Lisanne's dagelijkse workflow stabiel draait. Lifestyle business met AI-leverage, doel 100-300 klanten op termijn. Het Go-To-Market plan (gearchiveerd in `docs/archief/ROADMAP-ARCHIEF.md`) is voorbereiding, niet de actieve fase.

**TODO (klein):**
- ✅ VPS kernel reboot — 6.8.0-106 (gedaan sessie 109)
- ✅ Off-site backup — Backblaze B2, **versleuteld (rclone crypt) in EU (eu-central-003 Amsterdam)** sinds S182, 90d retentie, restore-test geslaagd (oude US-bucket `Luxis-backup` wordt ~10 juli gewist)
- ✅ CI terugzetten naar GitHub-hosted runners (sessie 110 — ubuntu-latest, services blok, setup-uv)
- ✅ Zero-BTW bug gefixt (sessie 110 — lines erven nu invoice btw_percentage, xfail verwijderd)

**Roadmap naar ~98% (13-15 sessies):**
1. Infra hardening (CI/CD ✅, Caddy in repo ✅, backup ✅, security ✅) — 3 sessies — COMPLEET ✅
2. Backend test coverage (7/7 routers getest ✅, 61 nieuwe tests, email import bug gefixt) — COMPLEET ✅
3. Frontend structureel (65x `any` gekilld ✅, hooks cleanup ✅) — COMPLEET ✅
4. Stitch redesign (nieuw design, component-voor-component) — 3-5 sessies
5. Frontend E2E + polish (settings + docs E2E ✅, a11y + performance TODO) — deels compleet
6. Final hardening (API docs ✅, runbook ✅, disaster recovery ✅) — COMPLEET ✅

---

## 🎯 Huidige prioriteit (bijgewerkt 12 juli 2026, S204)

Eén prioriteit-sectie tegelijk — afgeronde sprints/audits/bug-logs staan in `docs/archief/ROADMAP-ARCHIEF.md`.

> ✅ **MAILSLOT is nu een KNOP (S197):** Instellingen → E-mail → schakelaar "Mailverzending"
> (DB-vlag, fail-safe dicht). **Mail staat op UIT** — Arsalan zet het zelf aan wanneer nodig; niet
> autonoom openzetten. Ontvangen/sync werkt altijd door.

1. ✅ **S204 Fable-review AFGEROND (12 juli).** 9 van 11 S203-fixes bevestigd; batch-gate #5 zelf
   correct. Twee vervolg-punten met bewijs in `docs/sessions/S204-review.md` (§Beslislijst):
   14-dagenbrief-gate ontbreekt in follow-up "Uitvoeren" én in het AI-concept-verzendpad (🔴 juridisch),
   verstuurd-proxy = stap-binnenkomst (🟠), mailsync-foutpad vergiftigt volgende accounts (🟠, bewezen),
   heartbeat ziet "draait maar faalt" niet (🟡), dagenbrief-stap heeft geen sjabloon op prod (besluit).
2. **Volgende sessie = S205 fix-sessie** (`docs/sessions/PROMPT-S205-gate-zijdeuren.md`): de
   beslislijst hierboven, juridische punten eerst. Checklist: dagelijkse-job-rijen in `scheduler_heartbeat`.
3. **Openstaand ná S205 (kies één spoor):**
   - **S201 facturatie-import** — 439 conflict-vrije facturen; recept + droogloop-poorten klaar in
     `docs/research/S201-facturatie-recept.md`. Aparte, naar-buiten-gerichte schrijfactie → apart akkoord.
   - **S203-restpunten** — 35-route backend-sloop (eigen per-route-verificatie), #7 document-audittrail,
     #15 regeling-badge, log-persistentie VPS.
   - **S202 security-fixes (Fase D)** — H1 cross-tenant CaseFile, H2 fail-open "betaald"-guard, H3
     "Geïnd" telt verwijderde betalingen, M1/M2 + mailhardening. Rapport `docs/security/S202-delta-audit.md`.
     M3 (DB-superuser/RLS Fase 2) bewust apart.
4. **Beslissingen voor Lisanne/Arsalan:** 14-dagenbrief versturen vanuit Luxis (sjabloon op de stap
   zetten — bestaat al in code) óf buiten Luxis + handmatige registratie (S204 beslispunt 5);
   derdengelden-werkwijze (272 betalingen buiten derdengeldenkanaal — S200 #18); kantoorrekening
   `NL79KNAB0606569456` 1× tegen bankpas checken (1 cijfer gereconstrueerd).
5. **Heropening werkvoorraad:** volgende batch per opdrachtgever mét stap 4b —
   `docs/plans/PLAN-heropening-werkvoorraad.md` + `docs/sessions/S181-werkvoorraad-recept.csv`.

**Backlog-gedachte (Arsalan, 9 juli — plan voor later, niet nu bouwen):** de 13 lopende
betalingsregelingen zijn alleen zinvol te bewaken als Luxis ook *ziet* dat er betaald is —
en er is (nog) geen koppeling met de derdengeldrekening/bank. Denkrichtingen voor het plan:
(a) periodieke MT940/CSV-bankexport inlezen via de bestaande Bankimport-pagina (D-C kijkt of
die af is), (b) een bankkoppeling (PSD2-dienst zoals Enable Banking/Ponto) als structurele
oplossing, (c) tot die tijd: termijn-alarm behandelen als "check de bank handmatig"-taak
i.p.v. "debiteur heeft niet betaald". Meenemen in de fase-2-beslislijst na D-C.

---

## Projectdocumenten

### In de Git repo (`C:\Users\arsal\Documents\luxis\`)

| Document | Doel | Status |
|----------|------|--------|
| `LUXIS-ROADMAP.md` | **Dit document** — overzicht van alles. Status, prioriteit, bugs, features | **ENIGE source of truth** — alle andere docs verwijzen hiernaar |
| `docs/ARCHITECTUUR-KAART.md` | **Verbindingskaart** — hoe alle systemen aan elkaar hangen (2 pag.) | **Elke sessie eerst lezen** (auto via SessionStart-hook); bijwerken bij elke koppeling-wijziging |
| `docs/audits/inventaris-2026-07-05.md` | Feitelijke feature-inventaris + dubbele systemen + verweer-woordenschat (audit S172) | Referentie — wat er ÍS |
| `CLAUDE.md` | AI development guide, architectuurregels, werkwijze | Actief |
| `backend/CLAUDE.md` / `frontend/CLAUDE.md` | Backend/frontend-conventies | Actief |
| `docs/DECISIONS.md` | Tech stack keuzes + onderbouwing | Deels stale (Celery/Nginx/jose — zie audit S172); paden gecorrigeerd S172 (stonden op repo-root) |
| `docs/archief/` | Historie: oude sessie-entries, roadmap-secties, prompts, audits, afgeronde plannen | Archief — verplaatsen, nooit verwijderen |
| `docs/FEATURE-INVENTORY.md` | Markt-checklist: wat een PMS zou kúnnen (concurrent-onderzoek) | Referentie — de "wat zou kunnen" lijst (NIET wat er is) |
| `docs/research/UX-REVIEW.md` / `UX-VERBETERPLAN.md` / `BUGS-EN-VERBETERPUNTEN.md` / `PROMPT-TEMPLATES-IN-WORKFLOW.md` | Historische detail-docs (feb-mrt 2026) | Archief — status staat in deze roadmap |

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
- **Auth:** Custom JWT (PyJWT + bcrypt — python-jose vervangen S90)
- **Docs:** docxtpl + WeasyPrint
- **Scheduling:** APScheduler (géén Celery — dode dependency, verwijderen; audit S172). Redis alleen voor rate-limiting/OAuth-nonce
- **Hosting:** Hetzner VPS (CX33) + Docker Compose + Caddy + Let's Encrypt
- **Monitoring:** Sentry nog NIET actief (DSN leeg — actiepunt Arsalan sinds S159); self-hosted uptime-cron draait wel

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

## Backlog / Feature Requests

### Uit "Volgorde van werken" overgenomen bij archivering (9 juli 2026) — enig open punt

- **AI Factuur Parsing Validatie** — LF-10 feature uitgebreid testen met echte facturen van Lisanne. Test cases: verschillende factuurtypes (B2B/B2C), incomplete facturen, meerdere vorderingen, edge cases. Doel: betrouwbaarheid valideren voor productiegebruik.

- ~~**FEATURE: Relaties — inline contactpersoon aanmaken vanuit koppeldialoog**~~ ✅ Gedaan (sessie 19) — inline aanmaken van advocaat wederpartij bij nieuw dossier
- ~~**FEATURE: Advocaat wederpartij — klikbare detailweergave**~~ ✅ Gedaan (sessie 19) — zaken zichtbaar op relatiepagina via CaseParty filter + "Partij" rol label

### Frontend design-audit S155 — restwerk (bewuste backlog, zie `docs/qa/impeccable-audit-2026-06-07.md`)

- **AUDIT-FE-1: hard-coded palette-classes → semantic varianten** — 🔶 Top-5 gedaan (sessie 156): `lib/tones.ts` als centrale bron + incasso/dashboard/facturen/DossierHeader/facturen-detail gemigreerd (192→1 classes, screenshots pixel-identiek). **Restant: ~57 bestanden / ~620 classes** (ergste: correspondentie, agenda, taken) — nu mechanisch via tones.ts-patroon, zelfde recept (screenshot vóór/na, tsc, commit per pagina). NIET via blinde sed.
- **AUDIT-FE-2: touch targets < 44px** (±73 `p-1`/`p-1.5` icon-buttons). Per scherm beoordelen — bulk-vergroting vervormt data-dense tabellen. Verkenning sessie 156: DocumentenTab 12×, incasso 8×, uren 6×, sjablonen-tab 6×; voorgestelde aanpak `max-sm:p-2` per component (groter alleen op touch).
- ~~**AUDIT-FE-3: per-veld `aria-invalid`/`aria-describedby`**~~ ✅ Gedaan (sessie 156) — gekoppeld in relaties/nieuw (7 velden), zaken/nieuw (3), facturen/nieuw (3), BetalingenTab (2); error-`<p>` kreeg id + role=alert; functioneel geverifieerd. **Let op:** `form-field-error.tsx`-component zelf heeft nog 0 consumers — adopteren (unificeert error-styling) of verwijderen.
- *(Bewust behouden, géén werk: agenda event side-stripes = Google Calendar-idioom; credit-nota paars als functionele type-kleur (`CREDIT_NOTE_TONE`); DossierSidebar verborgen <lg; DossierHeader `text-orange-500` rente-icoon als one-off accent.)*

### Incasso Workflow Automatisering (P1)

**Doel:** Eén klik op "Verstuur brief" voor 40 dossiers → alles automatisch.

1. ✅ **Template editor UI** — Sjablonen tab in Instellingen: upload, download, bewerken, verwijderen van DOCX templates. Database-driven met disk-fallback. Incasso pipeline gebruikt dynamische template dropdown. Gebouwd sessie 24.
2. ✅ **Batch brief + email verzenden** — "Verstuur brief" genereert documenten en emailt ze naar de wederpartij via OutlookProvider (Graph API) met SMTP fallback. Sinds sessie 103b: brieven als branded HTML email body (Kesting Legal logo/kleuren/handtekening) i.p.v. PDF bijlage. Fallback naar PDF bijlage voor dagvaarding/renteoverzicht. Email toggle in PreFlightDialog, instelbare email templates per stap, email readiness check in preview. Gebouwd sessie 27, HTML body sessie 103b.
3. ✅ **Auto-complete taken** — Na document genereren: bijbehorende taken (generate_document/send_letter) automatisch afgevinkt. Gebouwd sessie 25. Bugfix sessie 26: scoped naar pipeline taken per stap (BUG-29).
4. ✅ **Auto-advance pipeline** — Na alle taken voltooid: pipeline schuift automatisch naar volgende stap, nieuwe taak + deadline aangemaakt. Bij batch advance_step worden ook taken aangemaakt. Gebouwd sessie 25. Bugfix sessie 26: blokkade door initiële taken opgelost (BUG-29).
5. ✅ **Deadline kleuren per stap** — Groen/oranje/rood kleurcodering per dossier in pipeline. Gebouwd sessie 23.
6. ✅ **Instelbare dagen per stap** — `max_wait_days` per pipeline-stap. "Min. dagen" + "Grens rood" kolommen. Gebouwd sessie 23.
7. ✅ **Step Transitions (branching workflow)** — `step_transitions` tabel: elke stap kan meerdere uitgangen hebben op basis van trigger (timeout/verweer/betaling/handmatig). 21 standaard overgangen geseeded. UI in expanded step row. Nieuwe stap "Verweer beantwoorden". Gebouwd sessie 131.
8. ✅ **Pivot naar lineair pipeline + automation rules** — Sessie 133. Branching state-machine vervangen door Lisanne's officiele 14 stappen (5 hoofdpad + 6 tussenstappen + 1 verweer + 2 afsluit). 6 .eml sjablonen + verzoekschrift DOCX geïmporteerd. AI-prompt module + defense_library voor verweer-respons. Manual + scheduled draft-generation. Bron: `docs/lisanne-incasso-workflow.md`.
9. ✅ **End-to-end AI draft flow** — Sessie 133. "Concept genereren" knop in dossier → AI draft → `/taken` queue → klik "Bekijk concept" → opent in dossier → versturen via Outlook → auto step-advance.
10. ✅ **Mail-pagina** — Sessie 133. Sidebar `Correspondentie` → `Mail`. "Nieuwe mail" knop voor free-compose zonder dossier-context.

**Flow:** Batch selectie → genereer brieven → email via Outlook → taken afgevinkt → pipeline doorgeschoven → deadline kleuren updaten

### Geplande verbeteringen (P2, niet bouwen tot expliciet groen licht)

- ✅ **Mail-pagina dossier-zoekveld in compose-dialog** — Search bovenaan compose, klik dossier → koppelt + recipient pre-fill van opposing_party/client, sjablonen/files/library beschikbaar via dropdowns. "Ontkoppel" link maakt binding ongedaan. `useRenderTemplate` accepteert nu `string | undefined`. Gebouwd sessie 137 (13 mei).
- ✅ **Email-trigger detectie** — Inkomende mail van debiteur → auto status "Verweer beantwoorden" + AI draft via verweer-bibliotheek. Gebouwd sessie 134.
- ✅ **Tenant-instelling UI** — `pipeline_auto_drafts_enabled` flag aan/uit per tenant via Instellingen → Workflow → Automatiseringsregels. Gebouwd sessie 137.
- ✅ **TransitionsSection vervangen** — UI in pipeline-page hernaamd naar "Automatische regels" paneel. Gebouwd sessie 137.

**QA & Testdekking (sessie 28):**
- ✅ **35 backend integration tests** — `test_incasso_pipeline.py`: deadline kleuren, email templates, auto-complete (BUG-29 regressie), auto-advance, batch preview, batch execute (met/zonder email, partial failure, edge cases), pipeline overview, queue counts. Alle 35 PASSED.
- ✅ **9 Playwright E2E tests** — `frontend/e2e/incasso-pipeline.spec.ts`: page load, deadline colors, action bar, pre-flight dialog, email toggle, queue filters, stappen beheren.
- ✅ **Smoke test checklist** — `docs/qa/p1-smoke-test-checklist.md`: 6 scenario's, 30+ handmatige checks.

---


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
