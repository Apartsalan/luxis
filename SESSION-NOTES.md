# Sessie Notities — Luxis

**Laatst bijgewerkt:** 21 feb 2026
**Laatste feature/fix:** M1-M4 Email integratie via Gmail API gebouwd

## Wat er gedaan is (deze sessie)

### M1: OAuth + EmailProvider abstractielaag
- `EmailProvider` abstract class met volledige interface (authorize, exchange, refresh, list, get, send, draft)
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
- Email detail panel met Van/Aan/CC/Datum headers + HTML body rendering
- Sync inbox knop direct op de tab

### M4: Compose via Gmail
- Send via provider endpoint (POST /api/email/compose/cases/{id})
- Draft endpoint (POST /api/email/compose/draft)
- Frontend: automatische routing — als OAuth verbonden → Gmail API, anders → SMTP fallback
- Verzonden emails worden direct opgeslagen als SyncedEmail (verschijnen meteen in correspondentie tab)
- Activity logging op het dossier

## Wat de volgende stap is

### Testen (handmatig)
1. `docker compose up` lokaal
2. Alembic migraties draaien (024 + 025)
3. Ga naar Instellingen → E-mail → "Verbind met Gmail"
4. Google OAuth consent doorlopen
5. Open een dossier → Correspondentie tab → "Sync inbox"
6. Stuur een test email vanuit het dossier

### Later bouwen
- **M5:** AutoTime op emails (automatische tijdregistratie bij mail-activiteit)
- **M6:** "Ongesorteerd" wachtrij UI (endpoint is al klaar: GET /api/email/unlinked)
- **OutlookProvider** toevoegen wanneer Lisanne naar M365 migreert

## Bestanden die zijn aangemaakt/aangepast (deze sessie)

### Nieuw aangemaakt (backend)
- `backend/app/email/providers/__init__.py` — provider exports
- `backend/app/email/providers/base.py` — EmailProvider abstract class
- `backend/app/email/providers/gmail.py` — GmailProvider (Gmail REST API)
- `backend/app/email/oauth_models.py` — EmailAccount model
- `backend/app/email/oauth_service.py` — OAuth business logic (state, tokens, refresh)
- `backend/app/email/oauth_router.py` — OAuth endpoints (/authorize, /callback, /status, /disconnect)
- `backend/app/email/token_encryption.py` — Fernet encryption voor tokens
- `backend/app/email/synced_email_models.py` — SyncedEmail model
- `backend/app/email/sync_service.py` — Sync + matching business logic
- `backend/app/email/sync_router.py` — Sync + inbox endpoints
- `backend/app/email/compose_router.py` — Send/draft via provider
- `backend/alembic/versions/024_email_accounts.py` — Migration
- `backend/alembic/versions/025_synced_emails.py` — Migration

### Nieuw aangemaakt (frontend)
- `frontend/src/hooks/use-email-oauth.ts` — OAuth status/connect/disconnect hooks
- `frontend/src/hooks/use-email-sync.ts` — Sync/inbox/compose hooks

### Aangepast
- `backend/app/config.py` — Google OAuth settings toegevoegd
- `backend/app/main.py` — 3 nieuwe routers geregistreerd
- `backend/pyproject.toml` — httpx, cryptography, python-dateutil dependencies
- `backend/alembic/env.py` — EmailAccount + SyncedEmail model imports
- `frontend/src/app/(dashboard)/instellingen/page.tsx` — EmailTab herschreven met OAuth UI
- `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` — CorrespondentieTab unified view + provider compose
- `.env` — Google OAuth credentials ingevuld
- `.env.example` — Google OAuth velden toegevoegd
- `LUXIS-ROADMAP.md` — M1-M4 status bijgewerkt
- `SESSION-NOTES.md` — deze update

## Architectuur

```
EmailProvider (abstract interface)
  ├── GmailProvider    ✅ Gebouwd (Arsalan's test account)
  └── OutlookProvider  TODO (Lisanne's M365, zelfde interface)

OAuth Flow:
  Frontend "Verbind met Gmail" → GET /authorize → Google consent popup
  → Google redirects to /callback → exchange code → encrypt + store tokens
  → postMessage naar opener → frontend toont "Verbonden"

Email Sync:
  POST /sync → GmailProvider.list_messages() → voor elke email:
    1. Dedup check (provider_message_id)
    2. Email adressen → Contact lookup → Case match
    3. Opslaan als SyncedEmail (met case_id als 1 match)

Compose via Provider:
  Frontend stuurt naar /api/email/compose/cases/{id}
  → GmailProvider.send_message() (verschijnt in Gmail Verzonden)
  → EmailLog + SyncedEmail + CaseActivity aangemaakt
```

## Openstaande issues
- Migraties 024 + 025 moeten nog gedraaid worden (lokaal + productie)
- pip install nodig voor httpx, cryptography, python-dateutil
- Google OAuth test: arsalanseidony@gmail.nl moet als test user staan in Google Cloud Console
- Dossier detail page is nu 50K+ regels — refactoring wenselijk

## Beslissingen genomen
- OAuth tokens encrypted at rest (Fernet via SECRET_KEY)
- Popup OAuth flow (niet redirect) zodat gebruiker op settings pagina blijft
- Auto-matching: alleen als precies 1 case matcht, anders "ongesorteerd"
- SMTP fallback: als geen provider verbonden, bestaande SMTP flow blijft werken
- Sent emails via provider worden direct opgeslagen als SyncedEmail (geen re-sync nodig)

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend
```

Vergeet niet: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` toevoegen aan `.env.production` op de VPS.
