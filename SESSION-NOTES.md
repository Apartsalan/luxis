# Sessie Notities — Luxis

**Laatst bijgewerkt:** 22 feb 2026 (sessie 6 — G3 procesgegevens + G5 keyboard shortcuts)
**Laatste feature/fix:** Procesgegevens sectie op dossierdetail + keyboard shortcuts

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
  └── OutlookProvider  TODO (Lisanne's M365, zelfde interface)

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
- **OutlookProvider** toevoegen wanneer Lisanne naar M365 migreert

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head
```
