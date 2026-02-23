# Sessie Notities — Luxis

**Laatst bijgewerkt:** 23 feb 2026 (sessie 13 — OutlookProvider)
**Laatste feature/fix:** OutlookProvider gebouwd (Microsoft Graph API)
**Volgende sessie (14):** BUG-13 + BUG-14 fixen (email-bijlagen). Daarna: document template editing UI + merge fields uitbreiden.

## Wat er gedaan is (sessie 13 — 23 feb)

### Feature: OutlookProvider — Microsoft Graph API email provider ✅

#### Backend
- **Nieuw bestand `backend/app/email/providers/outlook.py`** — Volledige Microsoft Graph API implementatie van de `EmailProvider` interface
  - OAuth 2.0: `get_authorize_url()`, `exchange_code()`, `refresh_access_token()` via Microsoft Identity Platform (tenant-specific endpoint)
  - User info: `get_user_email()` via `/me` endpoint (mail of userPrincipalName)
  - List messages: `list_messages()` via `/me/messages` met `$top`, `$orderby`, `$select`, `$search` (KQL)
  - Get message: `get_message()` met body + attachment metadata
  - Send: `send_message()` via `/me/sendMail` (202 Accepted, auto-save in Sent Items)
  - Reply: `_reply_to_message()` via `/me/messages/{id}/reply`
  - Draft: `create_draft()` via `POST /me/messages`
  - Attachments: `get_attachment()` via contentBytes (base64) of `$value` fallback
  - Attachment metadata: `_get_message_attachments()` — filtert inline images en itemAttachments
  - Pagination: `@odata.nextLink` als page_token
- **Config bijgewerkt:** `microsoft_client_id`, `microsoft_tenant_id`, `microsoft_client_secret`, `microsoft_redirect_uri` in Settings
- **Provider factory:** `get_provider("outlook")` retourneert nu `OutlookProvider()`
- **OAuth router uitgebreid:**
  - `/authorize` checkt nu Microsoft credentials als `provider=outlook`
  - `/callback/outlook` route toegevoegd (aparte redirect URI voor Azure App Registration)
  - Callback logica gerefactord naar `_handle_oauth_callback()` helper (gedeeld door Gmail + Outlook)
  - Provider-specifieke foutmeldingen bij ontbrekende refresh token

#### Infrastructure
- **docker-compose.prod.yml:** 4 Microsoft env vars toegevoegd (MICROSOFT_CLIENT_ID, MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_REDIRECT_URI)

#### Compatibiliteit
- KQL (Keyword Query Language) voor Graph `$search` is compatibel met bestaande `from:email OR to:email` query syntax in sync_service.py
- Bestaande auto-sync, matching, en compose flows werken ongewijzigd met OutlookProvider
- `EmailAccount.provider = "outlook"` wordt automatisch opgepikt door alle bestaande email-logica

### Bestanden aangemaakt/gewijzigd sessie 13

**Nieuw (backend):**
- `backend/app/email/providers/outlook.py` — OutlookProvider (~350 regels)

**Gewijzigd (backend):**
- `backend/app/config.py` — 4 Microsoft settings
- `backend/app/email/providers/__init__.py` — OutlookProvider export
- `backend/app/email/oauth_service.py` — OutlookProvider in get_provider()
- `backend/app/email/oauth_router.py` — /callback/outlook route + _handle_oauth_callback helper + credential check

**Gewijzigd (infra):**
- `docker-compose.prod.yml` — 4 Microsoft env vars

---

## Wat er gedaan is (sessie 12 — 23 feb avond)

### M0a: Microsoft 365 Setup voor Luxis Email Integratie ✅

**Doel:** Risicovrij M365 opzetten voor Arsalan's testmailbox, zodat de OutlookProvider gebouwd en getest kan worden. Lisanne's mail blijft 100% op BaseNet.

#### Stappen uitgevoerd:
1. **M365 Business Basic aangeschaft** — gratis proefversie, tenant `KestingLegal019.onmicrosoft.com`
2. **Domein `kestinglegal.nl` toegevoegd** — TXT-record `MS=ms93194745` in Wix DNS, **MX NIET gewijzigd**
3. **Mailbox `seidony@kestinglegal.nl` aangemaakt** — primair adres gewijzigd van onmicrosoft.com naar kestinglegal.nl
4. **Outlook getest** — versturen werkt ✅, ontvangen gaat naar BaseNet (verwacht, MX niet gewijzigd)
5. **Azure App Registration aangemaakt:**
   - App: `Luxis Email Integration`
   - Client ID: `8483075a-e72e-4fa9-ac0d-0994682f031b`
   - Tenant ID: `44ed7bee-37fc-4555-b2ef-b8a74c7fa28f`
   - Client Secret: opgeslagen in `.env`
   - Redirect URI: `https://luxis.kestinglegal.nl/api/email/oauth/callback/outlook`
   - Machtigingen: `Mail.Read`, `Mail.ReadWrite`, `Mail.Send`, `offline_access`, `User.Read` — alle verleend met beheerderstoestemming

#### DNS-info ontdekt:
- Domein `kestinglegal.nl` staat bij registrar **Tucows** (reseller)
- **Nameservers:** `ns10.wixdns.net`, `ns11.wixdns.net` (DNS beheerd in Wix)
- Bestaande TXT-records: SPF voor BaseNet + Lovable verificatie (niet aangeraakt)

#### Bestanden gewijzigd:
- `.env` — Microsoft 365 credentials toegevoegd (MICROSOFT_CLIENT_ID, MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_REDIRECT_URI)
- `.env.example` — Lege Microsoft 365 velden toegevoegd als template

#### Wat Lisanne merkt: NIKS
- MX-records niet gewijzigd
- Haar email blijft via BaseNet
- Geen mailbox voor haar aangemaakt in M365

### Volgende sessie: OutlookProvider bouwen
- `backend/app/email/providers/outlook.py` aanmaken
- Zelfde `EmailProvider` interface als `GmailProvider`
- Microsoft Graph API: OAuth flow, list/get/send messages, attachments
- OAuth router uitbreiden met `/callback/outlook` route
- Config updaten met Microsoft settings
- Testen met `seidony@kestinglegal.nl` account

---

## Openstaande bugs einde sessie 12

### BUG-13: Email-bijlage openen geeft foutmelding
- **Locatie:** Correspondentie tab → email detail → bijlage download
- **Oorzaak:** Frontend maakt directe `<a href="/api/email/attachments/{id}/download">` link, maar backend vereist Bearer token auth. Een directe `<a>` tag stuurt geen auth header mee → 401 Unauthorized.
- **Fix nodig (frontend):** Zelfde blob URL + fetch aanpak als G11 document preview: `fetch()` met Bearer token → `URL.createObjectURL()` → trigger download. Dit zit in `CorrespondentieTab.tsx` regel ~88-114.
- **Bestanden:** `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx`
- **Backend endpoint:** `GET /api/email/attachments/{attachment_id}/download` in `backend/app/email/sync_router.py:432-463`
- **Ernst:** Hoog — bijlagen zijn onbruikbaar

### BUG-14: Email-bijlage niet opslaan als dossierbestand
- **Locatie:** Correspondentie tab → email detail → bijlage
- **Probleem:** Er is geen knop/optie om een email-bijlage op te slaan als bestand in het dossier (case_files). Advocaten willen belangrijke bijlagen (contracten, vonnissen, etc.) archiveren bij het dossier.
- **Fix nodig:**
  - **Backend:** Nieuw endpoint `POST /api/email/attachments/{id}/save-to-case/{case_id}` — kopieert bestand van `/app/uploads/email_attachments/` naar `/app/uploads/case_files/`, maakt `CaseFile` record aan
  - **Frontend:** "Opslaan in dossier" knop naast elke bijlage in de email detail view
- **Bestanden:** `backend/app/email/sync_router.py` (nieuw endpoint), `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx` (knop toevoegen)
- **Ernst:** Midden — workaround is handmatig downloaden + uploaden via Documenten tab
- **Provider-onafhankelijk:** Deze fix werkt ongeacht of we later naar Outlook/M365 overstappen

## Wat er gedaan is (sessie 11 — 23 feb)

### Feature: G13 — Budget Tracking per Dossier ✅

#### Backend
- **Nieuw veld `budget`** op `Case` model — `Numeric(15, 2)`, nullable
- **Schemas bijgewerkt:** `budget: float | None = None` in CaseCreate, CaseUpdate, CaseResponse, CaseSummary
- **Alembic migratie 031:** `budget` kolom op `cases` tabel
- **Service hoefde niet aangepast** — `update_case` gebruikt al dynamische `setattr` loop

#### Frontend
- **Module systeem:** "budget" toegevoegd als togglebare module (LuxisModule type + ALL_MODULES)
- **Instellingen:** Budget module verschijnt in Modules-beheer met beschrijving
- **Nieuw dossier:** Budget input veld (module-gated), type number, stap 0.01
- **Dossier edit:** Budget bewerkbaar in DetailsTab (module-gated)
- **Sidebar progress bar:** OHW (onderhanden werk) vs budget
  - Groen (<80% besteed)
  - Amber (80-100% besteed)
  - Rood (>100% — "Budget overschreden")
- **Volledig togglebaar:** Alles verborgen als budget-module uit staat

### Feature: G9 — Recurring Tasks ✅

#### Backend
- **3 nieuwe velden** op `WorkflowTask` model: `recurrence` (String(20)), `recurrence_end_date` (Date), `parent_task_id` (FK naar zichzelf)
- **Self-referential relationship:** `parent_task` relationship voor taak-keten tracking
- **Auto-create volgende taak:** Bij voltooien van recurring taak → automatisch volgende occurrence aangemaakt
- **Recurrence opties:** daily, weekly, monthly, quarterly, yearly
- **Einddatum respect:** Stopt met herhalen als `recurrence_end_date` bereikt
- **dateutil.relativedelta:** Nauwkeurige datumberekening (maandovergangen, schrikkeljaren)
- **Alembic migratie 032:** 3 kolommen + FK constraint

#### Frontend
- **Taken pagina:** Herhaling dropdown (Eenmalig/Dagelijks/Wekelijks/Maandelijks/Per kwartaal/Jaarlijks) + conditioneel "Herhalen tot" datumveld
- **Dossier taken tab:** Zelfde herhaling dropdown in taak-aanmaak
- **Recurring badge:** Blauw badge met 🔄 icoon + herhalingslabel bij taken in de lijst
- **Labels:** Nederlandse vertalingen (Eenmalig, Dagelijks, etc.)

### Feature: G11 — Inline Document Preview ✅

#### Backend
- **Nieuw endpoint `GET /api/documents/{id}/preview`:** Re-renders DOCX template met huidige case data → converteert naar PDF → retourneert inline
- **Nieuw endpoint `GET /api/cases/{case_id}/files/{file_id}/preview`:**
  - PDF/images: direct serveren met Content-Disposition: inline
  - DOCX: on-the-fly converteren naar PDF via `docx_to_pdf()`
  - Andere types: 415 Unsupported Media Type
- **PREVIEWABLE_TYPES set:** PDF, JPEG, PNG, GIF, DOCX

#### Frontend
- **`isPreviewable(contentType)` helper:** Checkt of bestand previewbaar is (PDF, images, DOCX)
- **Eye (👁) button:** Op elk previewbaar bestand en elk gegenereerd document
- **Preview dialog:** Fullscreen-achtig modal met:
  - Header: titel + "Document preview" label + sluit-knop
  - Content: iframe voor PDF rendering
  - Loading state: spinner + "Preview laden..."
  - Escape key: sluit dialog
- **Blob URL auth approach:** Fetch met Bearer token → `URL.createObjectURL()` → iframe src
- **Memory cleanup:** `URL.revokeObjectURL()` bij sluiten

### Bestanden aangemaakt/gewijzigd sessie 11

**Nieuw (backend):**
- `backend/alembic/versions/031_add_budget_to_cases.py` — Migration
- `backend/alembic/versions/032_recurring_tasks.py` — Migration

**Gewijzigd (backend):**
- `backend/app/cases/models.py` — `budget` field
- `backend/app/cases/schemas.py` — `budget` in 4 schemas
- `backend/app/workflow/models.py` — `recurrence`, `recurrence_end_date`, `parent_task_id`
- `backend/app/workflow/schemas.py` — Velden in 3 schemas + RECURRENCE_OPTIONS
- `backend/app/workflow/service.py` — Auto-create next recurring task + _RECURRENCE_DELTAS
- `backend/app/documents/router.py` — Preview endpoint
- `backend/app/cases/router.py` — File preview endpoint + PREVIEWABLE_TYPES

**Gewijzigd (frontend):**
- `frontend/src/hooks/use-modules.ts` — "budget" module
- `frontend/src/hooks/use-cases.ts` — `budget` in interfaces
- `frontend/src/hooks/use-workflow.ts` — recurrence fields + RECURRENCE_LABELS
- `frontend/src/hooks/use-case-files.ts` — `isPreviewable()` helper
- `frontend/src/app/(dashboard)/instellingen/page.tsx` — Budget module info
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — Budget input (module-gated)
- `frontend/src/app/(dashboard)/zaken/[id]/components/DetailsTab.tsx` — Budget edit (module-gated)
- `frontend/src/app/(dashboard)/zaken/[id]/components/DossierSidebar.tsx` — Budget progress bar (module-gated)
- `frontend/src/app/(dashboard)/taken/page.tsx` — Recurrence dropdown + badge
- `frontend/src/app/(dashboard)/zaken/[id]/components/TijdregistratieTab.tsx` — Recurrence dropdown
- `frontend/src/app/(dashboard)/zaken/[id]/components/DocumentenTab.tsx` — Preview dialog + eye buttons

---

## Wat er gedaan is (sessie 10 — 23 feb)

### Feature: Template koppeling + Documentgeneratie + Smart Work Queues ✅

#### Backend
- **Nieuw veld `template_type`** op `IncassoPipelineStep` — koppelt stap aan modern docx-template systeem (string key i.p.v. deprecated FK)
- **Nieuw veld `step_entered_at`** op `Case` — timestamp wanneer dossier in huidige pipeline-stap is geplaatst
- **Alembic migratie 030:** `template_type` kolom op `incasso_pipeline_steps` + `step_entered_at` kolom op `cases`
- **Seed defaults bijgewerkt:** Aanmaning→"aanmaning", Sommatie→"sommatie", 2e Sommatie→"tweede_sommatie", Dagvaarding→"dagvaarding"
- **Documentgeneratie bij batch "Verstuur brief":** `batch_execute(action=generate_document)` roept nu `render_docx()` aan per dossier, slaat `GeneratedDocument` op in database
- **Smart Work Queue counts:** Nieuw endpoint `GET /api/incasso/queues/counts` — retourneert `{ ready_next_step, wik_expired, action_required }`
- **Queue logica:** `ready_next_step` = cases waar `days_in_step >= min_wait_days` van volgende stap; `wik_expired` = cases in eerste stap ≥ 14 dagen; `action_required` = combinatie van beide + onzugeassigneerde cases

#### Frontend
- **Template dropdown** in pipeline editor: per stap een "Briefsjabloon" dropdown met alle 7 docx-templates (Aanmaning, Sommatie, 2e Sommatie, etc.)
- **Smart Work Queue tabs** op werkstroom: "Alle dossiers" (default) | "Klaar voor volgende stap (X)" | "14d verlopen (X)" | "Actie vereist (X)"
- **Client-side filtering** op queue selectie (ready_next_step, wik_expired, action_required filters)
- **Sidebar badge** op Incasso nav item: rode teller met "actie vereist" count (auto-refresh 5 min)
- **Hooks:** `useIncassoQueueCounts()` (5-min auto-refresh), `template_type` in alle pipeline step hooks

### Commits sessie 10

| Hash | Beschrijving |
|------|-------------|
| TBD | feat(incasso): template coupling, batch document generation, smart work queues |

### Bestanden aangemaakt/gewijzigd

**Nieuw (backend):**
- `backend/alembic/versions/030_incasso_template_type_and_step_entered_at.py` — Migration

**Gewijzigd (backend):**
- `backend/app/incasso/models.py` — `template_type` field
- `backend/app/incasso/schemas.py` — `template_type` in schemas + `QueueCounts` schema
- `backend/app/incasso/service.py` — seed defaults, document generation, queue counts, step_entered_at tracking
- `backend/app/incasso/router.py` — queue counts endpoint + user_id passing
- `backend/app/cases/models.py` — `step_entered_at` field

**Gewijzigd (frontend):**
- `frontend/src/app/(dashboard)/incasso/page.tsx` — template dropdown + Smart Work Queue tabs
- `frontend/src/hooks/use-incasso.ts` — `template_type`, `QueueCounts`, `useIncassoQueueCounts`
- `frontend/src/components/layout/app-sidebar.tsx` — incasso badge

---

## Wat er gedaan is (sessie 9 — 23 feb)

### Feature: Incasso Batch Werkstroom ✅

#### Backend
- **Nieuw model `IncassoPipelineStep`** (tenant_id, name, sort_order, min_wait_days, template_id, is_active) in `backend/app/incasso/models.py`
- **CRUD endpoints:** GET/POST/PUT/DELETE `/api/incasso/pipeline-steps` + POST `/api/incasso/pipeline-steps/seed` voor default stappen
- **Pipeline overview:** GET `/api/incasso/pipeline` — alle incasso-dossiers gegroepeerd per stap
- **Batch preview:** POST `/api/incasso/batch/preview` — pre-flight check met blockers + status info
- **Batch execute:** POST `/api/incasso/batch` — batch-actie uitvoeren (advance_step, generate_document, recalculate_interest)
- **Case model uitbreiding:** `incasso_step_id` FK (nullable) op cases tabel
- **Alembic migratie 029:** `incasso_pipeline_steps` tabel + `incasso_step_id` kolom op cases
- **Case schemas:** `incasso_step_id` toegevoegd aan CaseResponse en CaseSummary

#### Frontend
- **Sidebar item "Incasso"** (Gavel icoon, module-gated op "incasso")
- **`/incasso` pagina** met twee tabs: Werkstroom (default) + Stappen beheren
- **Pipeline Editor (Stappen beheren tab):**
  - Lijst van stappen met naam, volgorde, wachtdagen, template
  - Toevoegen, verwijderen, herordenen (up/down knoppen)
  - Inline editing (klik op naam → edit, opslaan/annuleren)
  - Seed-knop voor standaardstappen als er geen zijn
- **Batch Werkstroom (hoofdscherm):**
  - Tabel met incasso-dossiers gegroepeerd per pipeline-stap
  - Kolommen: checkbox, dossiernr., cliënt, wederpartij, hoofdsom, openstaand, dagen in stap
  - "Zonder stap" sectie voor niet-toegewezen dossiers (amber highlight)
  - Checkboxes + "Selecteer alles" per stap
  - Floating action bar: "Wijzig stap", "Verstuur brief", "Herbereken rente"
  - Pre-flight wizard dialog met blocker-overzicht en bevestiging
- **Hooks:** `useIncassoPipelineSteps`, `useCreatePipelineStep`, `useUpdatePipelineStep`, `useDeletePipelineStep`, `useSeedPipelineSteps`, `useIncassoPipeline`, `useBatchPreview`, `useBatchExecute`

### Commits sessie 9

| Hash | Beschrijving |
|------|-------------|
| `4c12b48` | feat(incasso): add incasso batch workflow — pipeline model, CRUD, batch actions, and full UI |

### Bestanden aangemaakt/gewijzigd

**Nieuw (backend):**
- `backend/app/incasso/__init__.py`
- `backend/app/incasso/models.py` — IncassoPipelineStep model
- `backend/app/incasso/schemas.py` — Pydantic schemas
- `backend/app/incasso/service.py` — Business logic
- `backend/app/incasso/router.py` — FastAPI endpoints
- `backend/alembic/versions/029_incasso_pipeline.py` — Migration

**Nieuw (frontend):**
- `frontend/src/app/(dashboard)/incasso/page.tsx` — Incasso pagina (~650 regels)
- `frontend/src/hooks/use-incasso.ts` — TanStack Query hooks

**Gewijzigd:**
- `backend/alembic/env.py` — IncassoPipelineStep model import
- `backend/app/cases/models.py` — incasso_step_id FK + relationship
- `backend/app/cases/schemas.py` — incasso_step_id in CaseResponse + CaseSummary
- `backend/app/main.py` — incasso_router registratie
- `frontend/src/components/layout/app-sidebar.tsx` — Incasso nav item

---

## Plan voor sessie 9 — Incasso Batch Werkstroom

### Wat het is
Een nieuw scherm "Incasso" in de sidebar waarmee Lisanne batch-acties kan uitvoeren op meerdere incasso-dossiers tegelijk (brieven sturen, status wijzigen, rente herberekenen). Plus een pipeline editor om de incasso-stappen zelf te configureren.

### Waarom
In BaseNet heet dit "Workflow" — je stuurt bijv. 15 dossiers tegelijk een 2e sommatie. Maar BaseNet's aanpak werkt niet optimaal: geen preview, geen self-service configuratie, geen compliance-handhaving. Luxis kan dit beter.

### Navigatie
Eén sidebar-item **"Incasso"** (`/incasso`) met twee views:
1. **Werkstroom** (default) — pipeline-overzicht van alle incasso-dossiers per status-kolom
2. **Stappen beheren** — pipeline editor (naam, volgorde, wachtdagen, template)

### Feature-details

#### A. Pipeline Editor (Stappen beheren)
- Lijst van incasso-stappen: naam, volgorde, minimum wachtdagen, gekoppelde documenttemplate
- Stappen toevoegen, verwijderen, herordenen (drag-and-drop of up/down knoppen)
- Default stappen: Aanmaning → Sommatie (14d) → 2e Sommatie → Ingebrekestelling → Dagvaarding → Executie
- Per stap: wachtperiode instellen, template koppelen
- Backend: nieuw model `IncassoPipelineStep` (tenant_id, name, sort_order, min_wait_days, template_id, is_active)

#### B. Batch Werkstroom (hoofdscherm)
- Tabel met alle incasso-dossiers, gegroepeerd per huidige incasso-status
- Kolommen: checkbox, dossiernummer, cliënt, wederpartij, hoofdsom, openstaand, dagen in huidige stap, laatst verzonden brief
- Checkboxes voor selectie + "Selecteer alle X in dit stadium"
- Floating action bar bij selectie: "Verstuur brief", "Wijzig status", "Herbereken rente"
- **Pre-flight wizard** bij batch-actie:
  - Toont hoeveel dossiers worden bewerkt
  - Toont welke dossiers eerst een statuswijziging nodig hebben (en biedt aan dit automatisch te doen)
  - Toont welke dossiers blockers hebben (betalingsregeling actief, adres onbekend)
  - Preview van de actie → bevestig → uitvoer

#### C. Smart Work Queues (later, P2)
- Voorgedefinieerde filters als tabs: "Klaar voor sommatie", "14 dagen verlopen", "Klaar voor escalatie"
- Badge-tellingen in de sidebar

### Backend-werk nodig
1. Nieuw model `IncassoPipelineStep` + CRUD endpoints
2. Nieuw veld op cases: `incasso_step_id` (FK naar huidige stap in de pipeline)
3. Endpoint: `GET /api/incasso/pipeline` — alle dossiers gegroepeerd per stap
4. Endpoint: `POST /api/incasso/batch` — batch-actie uitvoeren (status wijzigen, brief genereren)
5. Pre-flight endpoint: `POST /api/incasso/batch/preview` — preview zonder uitvoering

### Frontend-werk nodig
1. Sidebar-item "Incasso" toevoegen
2. `/incasso` pagina met twee tabs (Werkstroom + Stappen)
3. Pipeline editor component
4. Batch tabel met checkboxes + floating action bar
5. Pre-flight wizard dialog

### Research gedaan
Grondig onderzoek naar BaseNet, CreditDevice, Onguard, TAGOR, iFlow, Aryza, Buckaroo, Straetus. Plus UX-patronen van Stripe Workflows, Linear, Jira bulk wizard, HubSpot. Conclusie: combineer CreditDevice's dagelijkse automatisering met Linear/Jira's batch-selectie UX, plus compliance-handhaving die geen concurrent goed doet.

### Commits sessie 8

| Hash | Beschrijving |
|------|-------------|
| `01741b5` | fix: task visibility and add create task to Mijn Taken page |
| `7cad57b` | docs: update session notes and roadmap for session 8 (BUG-11, BUG-12) |

## Wat er gedaan is (sessie 8 — 22 feb)

### BUG-FIX: Taken niet zichtbaar na aanmaken in dossier ✅
- **Oorzaak:** `useWorkflowTasks` hook verwachtte `PaginatedTasks` object (`{ items, total, ... }`) maar backend `GET /api/workflow/tasks` retourneert een plain `WorkflowTask[]` array. Daardoor was `tasksData?.items` altijd `undefined` → lege takenlijst.
- **Fix `use-workflow.ts`:** `useWorkflowTasks` return type van `PaginatedTasks` → `WorkflowTask[]`, pagination params verwijderd (backend ondersteunt het niet)
- **Fix `use-workflow.ts`:** `useMyOpenTasks` zelfde probleem — return type van `PaginatedTasks` → `WorkflowTask[]`, `.slice(0, limit)` in de hook
- **Fix `TijdregistratieTab.tsx`:** `tasksData?.items ?? []` → `tasksData ?? []`
- **Fix `page.tsx` (dashboard):** `data?.items ?? []` → `data ?? []`, `data?.total` → `tasks.length`

### BUG-FIX: Taken verschijnen niet bij "Mijn Taken" na handmatig aanmaken ✅
- **Oorzaak:** `TijdregistratieTab` stuurde geen `assigned_to_id` mee bij aanmaken → taak werd niet aan gebruiker toegewezen → `/api/dashboard/my-tasks` (filtert op `assigned_to_id = user.id`) toonde ze niet
- **Fix:** `useAuth()` toegevoegd + `assigned_to_id: user.id` meegeven bij `createTask.mutateAsync()`

### Feature: "Nieuwe taak" knop op Mijn Taken pagina ✅
- **Knop:** "Nieuwe taak" naast de filter-knoppen in de header
- **Formulier:** Dossier dropdown (alle actieve dossiers), titel, type, deadline, omschrijving
- **Auto-assign:** Taak wordt automatisch aan de ingelogde gebruiker toegewezen
- **Imports:** `useCreateTask`, `useAuth`, `useCases` hooks + `Plus`, `Loader2`, `X` icons

### Commits sessie 8

| Hash | Beschrijving |
|------|-------------|
| `01741b5` | fix: task visibility and add create task to Mijn Taken page |

---

## Wat er gedaan is (sessie 7 — 22 feb)

### G14: Collapsible properties sidebar op dossierdetail ✅
- **Nieuw bestand:** `zaken/[id]/components/DossierSidebar.tsx`
- **Secties:** Dossierinfo (type, status, datum, debiteur, rente, referentie, zaaknr.), Client (link + email), Wederpartij (link + email), Advocaat wederpartij (indien aanwezig), Financieel snapshot
- **Financieel:** OHW uit `useTimeEntrySummary`, incasso-details uit `useFinancialSummary` (hoofdsom, betaald, openstaand, derdengelden, progress bar), non-incasso basic (hoofdsom, betaald)
- **Collapsible:** localStorage persistence (`luxis_sidebar_open`), fixed reopen-knop bij collapsed
- **Layout:** `page.tsx` omgebouwd naar flex layout (content + sidebar)

### G10: Task templates per dossiertype ✅
- **Backend:** `backend/app/cases/service.py` — `_create_initial_tasks()` helper
- **Templates per type:**
  - **Incasso:** 8 taken (dossier controleren, herinnering, 14-dagenbrief, betaling controleren, sommatie, betaling controleren, beoordeel dagvaarding, verjaring controleren)
  - **Advies:** 4 taken (controleren, juridisch onderzoek, concept advies, advies versturen)
  - **Insolventie:** 4 taken (controleren, beoordeel aanvraag, verzoekschrift, indienen)
  - **Overig:** 2 taken (controleren, plan van aanpak)
- **Deadlines:** Relatief t.o.v. `date_opened` (1-180 dagen afhankelijk van type taak)
- **Werking:** Taken worden automatisch aangemaakt bij `create_case()`, verschijnen direct op de Taken-tab
- **Geen migratie nodig** — gebruikt bestaande WorkflowTask tabel

### Commits sessie 7

| Hash | Beschrijving |
|------|-------------|
| `288f568` | feat: add dossier sidebar and task templates (G14, G10) |

---

## Wat er gedaan is (sessie 6 — 22 feb)

### G3: Procesgegevens sectie op dossierdetail ✅
- **Backend:** 5 nieuwe velden op Case model: `court_name`, `judge_name`, `chamber`, `procedure_type`, `procedure_phase`
- **Migration:** `028_procesgegevens` — alle kolommen nullable
- **Schemas:** Velden toegevoegd aan CaseCreate, CaseUpdate, CaseResponse
- **Frontend CaseDetail interface:** 5 velden toegevoegd
- **DetailsTab:** Nieuwe "Procesgegevens" card met Gavel-icoon
  - **View mode:** 5 velden in 2-koloms grid
  - **Edit mode:** Rechtbank dropdown (alle 16 NL rechtbanken + gerechtshoven + Hoge Raad), rechter tekstveld, kamer tekstveld, type procedure dropdown (9 opties), procesfase dropdown (12 opties)
  - Edit/save deelt dezelfde state als Dossiergegevens card (1 Bewerken-knop voor alles)

### G5: Keyboard shortcuts ✅
- **Locatie:** `zaken/[id]/page.tsx` — useEffect met keydown listener
- **Shortcuts:** T=timer start/stop, N=notitie (switch naar overzicht + focus textarea), D=documenten tab, E=email compose dialog, F=facturen tab, 1-9=tab switching
- **Guards:** Niet actief bij typing in input/textarea/select/contenteditable, niet bij Ctrl/Meta/Alt modifiers

### Commits sessie 6

| Hash | Beschrijving |
|------|-------------|
| `fb70487` | feat: add procesgegevens section and keyboard shortcuts (G3, G5) |

---

## Wat er gedaan is (sessie 5 — 22 feb)

### Refactoring: Dossier detail page.tsx opsplitsen ✅
- **Probleem:** `zaken/[id]/page.tsx` was 4236 regels — alles in één bestand
- **Oplossing:** Opgesplitst in 8 componentbestanden + 1 shared types bestand
- **Resultaat:** `page.tsx` is nu ~236 regels (data loading + tabs + state als props)
- **Geen functionaliteitswijzigingen** — puur code-organisatie

### Nieuwe bestanden
- `zaken/[id]/types.tsx` — gedeelde constanten (STATUS_LABELS, STATUS_BADGE, PIPELINE_STEPS, etc.), activity/task constanten, renderSimpleMarkdown helper
- `zaken/[id]/components/DossierHeader.tsx` — header, pipeline stepper, workflow-suggestie banner, quick stats, quick actions bar
- `zaken/[id]/components/DetailsTab.tsx` — OverzichtTab (dossiergegevens, bewerkformulier, partijen inline, notitie-invoer, recente activiteit)
- `zaken/[id]/components/IncassoTab.tsx` — 4 named exports: VorderingenTab, BetalingenTab, FinancieelTab, DerdengeldenTab
- `zaken/[id]/components/DocumentenTab.tsx` — 2 named exports: DocumentenTab (template generatie + bestandsuploads) + FacturenTab
- `zaken/[id]/components/CorrespondentieTab.tsx` — email correspondentie + EmailDetailPanel
- `zaken/[id]/components/TijdregistratieTab.tsx` — workflow taakbeheer (was TakenTab)
- `zaken/[id]/components/PartijenTab.tsx` — partijenoverzicht met conflict detectie
- `zaken/[id]/components/ActiviteitenTab.tsx` — activiteitentijdlijn met paginatie

### Commits sessie 5

| Hash | Beschrijving |
|------|-------------|
| `0914e37` | refactor(zaken): split dossier detail page into 8 tab components |

---

## Wat er gedaan is (sessie 4 — 22 feb)

### Feature: M6 — Ongesorteerde email wachtrij ✅
- **Nieuwe pagina `/correspondentie`** met split-view: email lijst + detail + koppel-panel
- **Dossier-suggesties** per email op basis van contact-match, dossiernummer, referentie, zaaknummer rechtbank
- **1-click koppelen** aan voorgesteld dossier of handmatig zoeken
- **Negeer-functie** (`is_dismissed` boolean) — email uit wachtrij, niet verwijderd
- **Bulk acties** — checkboxes, selecteer alles, bulk koppelen/negeren
- **Sidebar badge** — rode counter met aantal ongesorteerde emails (auto-refresh 5 min)
- **Zoekbalk** — client-side filter op afzender, onderwerp, snippet, ontvanger
- **Empty state** als alles gesorteerd is

### Backend wijzigingen
- `is_dismissed` boolean op `SyncedEmail` model
- Alembic migratie `027_email_dismissed` (kolom + partial index)
- `POST /api/email/dismiss` — bulk dismiss
- `POST /api/email/bulk-link` — bulk link meerdere emails aan 1 dossier
- `GET /api/email/suggest-cases/{id}` — dossier-suggesties
- `GET /api/email/unlinked/count` — lichtgewicht count voor sidebar badge
- `get_unlinked_emails` filtert nu `is_dismissed = False`

### Frontend wijzigingen
- `frontend/src/app/(dashboard)/correspondentie/page.tsx` — volledige pagina (~720 regels)
- `frontend/src/hooks/use-email-sync.ts` — 5 nieuwe hooks (useUnlinkedCount, useBulkLinkEmails, useDismissEmails, useSuggestCases, CaseSuggestion type)
- `frontend/src/components/layout/app-sidebar.tsx` — Correspondentie nav item + badge

### Roadmap update
- M5 (AutoTime) → backlog (bestaande timer dekt dit)
- M6 → ✅ gebouwd

### Commits sessie 4

| Hash | Beschrijving |
|------|-------------|
| `ffdc9d1` | feat(email): M6 ongesorteerd email wachtrij — triage pagina + backend |
| `8a44800` | feat(email): add search filter to ongesorteerd email queue |

---

## Wat er gedaan is (sessie 3 — 21 feb, avond)

### Fix: Dossier edit — velden wissen werkte niet ✅ BEVESTIGD WERKEND
- **Probleem:** Als je een veld (Beschrijving, Referentie, Zaaknummer rechtbank) leegmaakte en opsloeg, bleef de oude waarde staan.
- **Oorzaak:** `handleSaveDetails` gebruikte `|| undefined` → `JSON.stringify` dropte het → backend sloeg het over.
- **Fix:** `|| undefined` → `.trim() || null`. Lege strings worden als `null` meegestuurd.
- **Bestanden:** `frontend/src/app/(dashboard)/zaken/[id]/page.tsx`, `frontend/src/hooks/use-cases.ts`
- **Commit:** `58c5cc0`

### Fix: Email matching op zaaknummer rechtbank (court_case_number) ✅
- **Probleem:** `_find_case_by_case_number()` scande niet op `Case.court_case_number`.
- **Fix:** Method 3 toegevoegd — zoekt `court_case_number` in email tekst.
- **Bestand:** `backend/app/email/sync_service.py`
- **Commit:** `9c94585`

### Fix: body_html doorzoeken bij email matching ✅
- **Probleem:** Veel emails (Gmail, Outlook) sturen alleen HTML, geen text/plain. De matching zocht alleen in `body_text` → HTML-only emails werden gemist.
- **Fix:** `_build_searchable_text()` functie: stript HTML tags, doorzoekt body_html + body_text + subject + snippet.
- **Bestand:** `backend/app/email/sync_service.py`
- **Commit:** `896d48f`

### Fix: Rematch altijd uitvoeren, ook bij dossier-context sync ✅
- **Probleem:** `_rematch_unlinked_emails()` werd overgeslagen als `force_case_id` was gezet (sync vanuit dossier). Oude ongelinkte emails werden nooit herscand.
- **Fix:** `if not force_case_id:` guard verwijderd — rematch draait nu altijd.
- **Bestand:** `backend/app/email/sync_service.py`
- **Commit:** `d995dea`

### Regel toegevoegd aan CLAUDE.md ✅
- **VERPLICHT: Na ELKE commit ALTIJD direct `git push origin main` uitvoeren.** Eerder waren commits lokaal blijven staan waardoor VPS stale code pulde.
- **Commit:** `c4953cd`

### Commits sessie 3

| Hash | Beschrijving |
|------|-------------|
| `58c5cc0` | fix(cases): clearing dossier edit fields now persists on save |
| `9c94585` | fix(email): add court_case_number matching to email sync |
| `c4953cd` | docs: enforce git push after every commit in CLAUDE.md |
| `896d48f` | fix(email): search body_html for reference matching |
| `0ff70cb` | debug(email): add match-debug logging (tijdelijk) |
| `d995dea` | fix(email): always run rematch on unlinked emails |
| `e92ab50` | chore(email): remove debug logging from email matching |

---

## Wat er gedaan is (sessie 2 — 21 feb, namiddag)

### Fix: Google OAuth env vars niet doorgegeven aan Docker
- `docker-compose.prod.yml` miste `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` in de backend environment block
- Ook `SMTP_*` variabelen ontbraken in de prod override
- **Commit:** `57326c8`

### Fix: Dossier-context sync ("Sync inbox" vanuit dossier)
- Probleem: "Sync inbox" haalde de hele inbox op, matching was te streng, emails bleven ongesorteerd
- Fix: Als je vanuit een dossier synct, worden automatisch de emailadressen van alle contacten (client, wederpartij, case parties) opgezocht
- Gmail query wordt gebouwd: `from:contact@email.com OR to:contact@email.com`
- Alle gevonden emails worden automatisch aan dat dossier gelinkt
- Eerder gesynced maar ongelinkte emails worden ook alsnog gekoppeld
- Frontend stuurt nu `caseId` mee bij sync vanuit correspondentie tab
- **Commit:** `a2e66d6`

### Feature: Dossiernummer + klantreferentie matching
- Elke email wordt gescand op dossiernummers (regex: `\b(20\d{2}-\d{4,6})\b`)
- Matcht "2026-00003" in onderwerp/body automatisch aan dossier 2026-00003
- Scant ook op bekende klantreferenties (Case.reference veld, min. 3 tekens)
- **Prioriteit matching:** dossiernummer > klantreferentie > email-contact matching

### Feature: Bijlagen (attachments) downloaden en tonen
- `EmailAttachment` model (tenant_id, synced_email_id, filename, stored_filename, content_type, file_size)
- Alembic migration 026 (email_attachments tabel)
- Gmail provider: `get_attachment()` methode — download attachment bytes via Gmail API
- `AttachmentInfo` dataclass op `EmailMessage` — parsed uit Gmail payload parts
- Opslag: `/app/uploads/email_attachments/{tenant_id}/{synced_email_id}/{uuid}{ext}`
- API endpoints:
  - `GET /api/email/messages/{id}/attachments` — lijst bijlagen per email
  - `GET /api/email/attachments/{id}/download` — download bijlage (FileResponse)
- Frontend: bijlagen zichtbaar in email detail panel met bestandsnaam, grootte en download-knop
- `SyncedEmailDetail.attachments[]` en `SyncedEmailSummary.attachment_count` toegevoegd

### Feature: Auto-sync elke 5 minuten
- APScheduler `IntervalTrigger(minutes=5)` toegevoegd aan workflow scheduler
- `email_auto_sync()` job: synct alle verbonden email accounts automatisch
- Per account: max 50 emails per cycle, matching + bijlagen download
- Logs naar stdout: "Scheduler: email auto-sync klaar — X accounts, Y nieuw, Z gekoppeld"

### Fix: Re-match ongelinkte emails bij elke sync
- Probleem: emails gesynced voor de dossiernummer-matching feature werden nooit opnieuw gescand
- Fix 1: Bij skip van bestaande ongelinkte email → alsnog case number matching draaien
- Fix 2: `_rematch_unlinked_emails()` na elke sync — scant ALLE ongelinkte emails opnieuw
- Matching: dossiernummer → klantreferentie → email-contact → case

### Commits sessie 2

| Hash | Beschrijving |
|------|-------------|
| `57326c8` | fix(deploy): add Google OAuth + SMTP env vars to prod compose |
| `a2e66d6` | fix(email): smart dossier-context sync met auto-linking |
| `fa1a979` | feat(email): dossiernummer-matching, bijlagen sync, auto-sync elke 5 min |
| `2684272` | fix(email): re-match ongelinkte emails op dossiernummer bij elke sync |

---

## Wat er gedaan is (sessie 1 — 21 feb, ochtend)

### M1: OAuth + EmailProvider abstractielaag
- `EmailProvider` abstract class met volledige interface (authorize, exchange, refresh, list, get, send, draft, get_attachment)
- `GmailProvider` implementatie (Gmail REST API v1, alle methoden)
- `EmailAccount` model met encrypted token opslag (Fernet via SECRET_KEY)
- OAuth flow: authorize URL → Google consent → callback → token opslag
- Auto-refresh: bij expired token automatisch vernieuwd via refresh_token
- Alembic migration 024 (email_accounts tabel)
- Frontend: OAuth connect/disconnect UI op Instellingen → E-mail tab
- Popup OAuth flow met postMessage callback

### M2: Inbox sync + auto-koppeling aan dossiers
- `SyncedEmail` model voor opslag van inbox emails
- Sync service: haalt emails op via Gmail API, slaat op in DB
- Auto-matching: email adres → Contact → Case (client/opposing_party/case_party)
- Deduplicatie: zelfde email wordt niet twee keer opgeslagen
- Endpoints: POST /sync, GET /cases/{id}/emails, GET /unlinked, POST /link
- Alembic migration 025 (synced_emails tabel met indices)
- Frontend hooks: useSyncEmails, useCaseEmails, useUnlinkedEmails, useLinkEmail

### M3: Correspondentie tab (unified view)
- Correspondentie tab op dossierdetail volledig herschreven
- Unified timeline: synced inbox emails + verzonden email logs, samengevoegd en chronologisch gesorteerd
- Filter tabs: Alles / Ontvangen / Verzonden
- Split-view: email lijst links, detail panel rechts
- Direction icons (blauw = ontvangen, groen = verzonden)
- Email detail panel met Van/Aan/CC/Datum headers + HTML body rendering + bijlagen
- Sync inbox knop direct op de tab

### M4: Compose via Gmail
- Send via provider endpoint (POST /api/email/compose/cases/{id})
- Draft endpoint (POST /api/email/compose/draft)
- Frontend: automatische routing — als OAuth verbonden → Gmail API, anders → SMTP fallback
- Verzonden emails worden direct opgeslagen als SyncedEmail (verschijnen meteen in correspondentie tab)
- Activity logging op het dossier

---

## Architectuur

```
EmailProvider (abstract interface)
  ├── GmailProvider    ✅ Gebouwd + bijlagen + auto-sync
  └── OutlookProvider  ✅ Gebouwd (Graph API, OAuth, mail CRUD, bijlagen)

OAuth Flow:
  Frontend "Verbind met Gmail" → GET /authorize → Google consent popup
  → Google redirects to /callback → exchange code → encrypt + store tokens
  → postMessage naar opener → frontend toont "Verbonden"

Email Sync Matching (prioriteit):
  1. Dossiernummer regex: "2026-00003" in subject/body → Case.case_number match
  2. Klantreferentie: Case.reference in subject/body/html (min 3 chars)
  3. Zaaknummer rechtbank: Case.court_case_number in subject/body/html (min 3 chars)
  4. Contact email: from/to/cc → Contact.email → Case (client/wederpartij/party)
  5. Re-match: elke sync scant ook bestaande ongelinkte emails opnieuw (altijd, ook vanuit dossier-context)

Searchable text wordt opgebouwd via _build_searchable_text():
  subject + body_text + _strip_html(body_html) + snippet
  → Dit vangt HTML-only emails op (Gmail, Outlook sturen vaak alleen HTML)

Dossier-context sync:
  "Sync inbox" vanuit dossier → haalt contactemails op → bouwt Gmail query
  → filtert op from/to van contacten → linkt alles aan dat dossier

Bijlagen:
  Gmail API → get_attachment(message_id, attachment_id) → bytes
  → /app/uploads/email_attachments/{tenant}/{email_id}/{uuid}.ext
  → EmailAttachment record in DB
  → Frontend toont in detail panel met download link

Auto-sync:
  APScheduler IntervalTrigger(minutes=5)
  → email_auto_sync() → alle connected EmailAccounts
  → sync_emails_for_account(max_results=50) per account
  → matching + bijlagen + re-match ongelinkte emails

Compose via Provider:
  Frontend stuurt naar /api/email/compose/cases/{id}
  → GmailProvider.send_message() (verschijnt in Gmail Verzonden)
  → EmailLog + SyncedEmail + CaseActivity aangemaakt
```

## Alle bestanden aangemaakt/aangepast (alle sessies)

### Nieuw aangemaakt (backend)
- `backend/app/email/providers/__init__.py` — provider exports
- `backend/app/email/providers/base.py` — EmailProvider abstract class + AttachmentInfo
- `backend/app/email/providers/gmail.py` — GmailProvider (Gmail REST API)
- `backend/app/email/oauth_models.py` — EmailAccount model
- `backend/app/email/oauth_service.py` — OAuth business logic (state, tokens, refresh)
- `backend/app/email/oauth_router.py` — OAuth endpoints (/authorize, /callback, /status, /disconnect)
- `backend/app/email/token_encryption.py` — Fernet encryption voor tokens
- `backend/app/email/synced_email_models.py` — SyncedEmail model + attachments relationship
- `backend/app/email/sync_service.py` — Sync + matching + re-match + bijlagen download + _build_searchable_text
- `backend/app/email/sync_router.py` — Sync + inbox + attachment endpoints
- `backend/app/email/compose_router.py` — Send/draft via provider
- `backend/app/email/attachment_models.py` — EmailAttachment model
- `backend/alembic/versions/024_email_accounts.py` — Migration
- `backend/alembic/versions/025_synced_emails.py` — Migration
- `backend/alembic/versions/026_email_attachments.py` — Migration

### Nieuw aangemaakt (frontend)
- `frontend/src/hooks/use-email-oauth.ts` — OAuth status/connect/disconnect hooks
- `frontend/src/hooks/use-email-sync.ts` — Sync/inbox/compose hooks + attachment types

### Aangepast
- `backend/app/config.py` — Google OAuth settings toegevoegd
- `backend/app/main.py` — 3 nieuwe routers geregistreerd
- `backend/pyproject.toml` — httpx, cryptography, python-dateutil dependencies
- `backend/alembic/env.py` — EmailAccount + SyncedEmail + EmailAttachment model imports
- `backend/app/workflow/scheduler.py` — email_auto_sync() elke 5 min
- `docker-compose.prod.yml` — Google OAuth + SMTP env vars
- `frontend/src/app/(dashboard)/instellingen/page.tsx` — EmailTab herschreven met OAuth UI
- `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` — CorrespondentieTab unified view + bijlagen + provider compose + edit form fix
- `frontend/src/hooks/use-cases.ts` — useUpdateCase type fix (Record<string, unknown>)
- `.env` — Google OAuth credentials ingevuld
- `.env.example` — Google OAuth velden toegevoegd
- `CLAUDE.md` — git push regel toegevoegd

---

## Openstaande issues
- ~~Dossier detail page is nu 4236 regels in één bestand~~ ✅ Opgesplitst in sessie 5
- Google OAuth test: arsalanseidony@gmail.nl moet als test user staan in Google Cloud Console
- Auto-sync zal bij grote inboxen de eerste keer langzaam zijn (max 50 per cycle)
- M6 + migratie 027 + G3 migratie 028 moeten nog gedeployed worden op de VPS (deploy commando staat hieronder)

## Wat de volgende stap is

### Sessie 6 — Volgende prioriteit
- **Dossier workspace verbeteringen** (G3-G15 uit DOSSIER-WERKPLEK-RESEARCH.md)
- Of andere features uit UX-RESEARCH-A6-A7.md

### Later bouwen
- **M5:** AutoTime op emails (backlog — bestaande timer dekt dit grotendeels)
- ~~**OutlookProvider** toevoegen wanneer Lisanne naar M365 migreert~~ ✅ Gebouwd (sessie 13)

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head
```
