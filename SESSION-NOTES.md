# Sessie Notities — Luxis

**Laatst bijgewerkt:** 21 feb 2026 (sessie 2 — email sync verbeteringen)
**Laatste feature/fix:** Dossiernummer-matching, bijlagen sync, auto-sync, re-match fix

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

## Alle bestanden aangemaakt/aangepast (beide sessies)

### Nieuw aangemaakt (backend)
- `backend/app/email/providers/__init__.py` — provider exports
- `backend/app/email/providers/base.py` — EmailProvider abstract class + AttachmentInfo
- `backend/app/email/providers/gmail.py` — GmailProvider (Gmail REST API)
- `backend/app/email/oauth_models.py` — EmailAccount model
- `backend/app/email/oauth_service.py` — OAuth business logic (state, tokens, refresh)
- `backend/app/email/oauth_router.py` — OAuth endpoints (/authorize, /callback, /status, /disconnect)
- `backend/app/email/token_encryption.py` — Fernet encryption voor tokens
- `backend/app/email/synced_email_models.py` — SyncedEmail model + attachments relationship
- `backend/app/email/sync_service.py` — Sync + matching + re-match + bijlagen download
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
- `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` — CorrespondentieTab unified view + bijlagen + provider compose
- `.env` — Google OAuth credentials ingevuld
- `.env.example` — Google OAuth velden toegevoegd

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
  2. Klantreferentie: Case.reference in subject/body (min 3 chars)
  3. Contact email: from/to/cc → Contact.email → Case (client/wederpartij/party)
  4. Re-match: elke sync scant ook bestaande ongelinkte emails opnieuw

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

## Openstaande issues
- Migration 026 moet gedraaid worden op VPS
- Dossier detail page is nu 55K+ regels — refactoring wenselijk
- Google OAuth test: arsalanseidony@gmail.nl moet als test user staan in Google Cloud Console
- Auto-sync zal bij grote inboxen de eerste keer langzaam zijn (max 50 per cycle)

## Wat de volgende stap is

### Later bouwen
- **M5:** AutoTime op emails (automatische tijdregistratie bij mail-activiteit)
- **M6:** "Ongesorteerd" wachtrij UI (endpoint is al klaar: GET /api/email/unlinked)
- **OutlookProvider** toevoegen wanneer Lisanne naar M365 migreert

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head
```
