# Sessie Notities — Luxis

**Laatst bijgewerkt:** 21 feb 2026
**Laatste feature/fix:** VPS deploy fix + email strategie beslissing

## Wat er gedaan is
- VPS deploy gefixt: 5 issues opgelost (Pydantic int crash, DATABASE_URL `!` in wachtwoord, Sentry BadDsn, docker-compose leest .env.production niet, NEXT_PUBLIC_API_URL niet in frontend build)
- Email strategie beslissing genomen: F11 (SMTP) = tijdelijke brug, M1-M6 = eindoplossing
- Beslissing: Gmail API als dev/test provider, later Outlook toevoegen voor Lisanne
- Abstractielaag: `EmailProvider` interface met `GmailProvider` (nu) + `OutlookProvider` (later)

## Wat de volgende stap is

### PRIORITEIT: M1-M4 — Email integratie via Gmail API (dev/test)

**Voordat de sessie begint moet Arsalan dit doen (10 min):**

1. **Ga naar https://console.cloud.google.com** (login met je Gmail)
2. **Maak een project aan:**
   - Project-dropdown bovenin → "New Project" → Name: `Luxis Dev` → Create
3. **Zet Gmail API aan:**
   - Zoekbalk: "Gmail API" → klik erop → **Enable**
4. **OAuth consent screen invullen:**
   - "APIs & Services" → "OAuth consent screen"
   - User type: **External** → Create
   - App name: `Luxis Dev`, support email: jouw Gmail, developer email: jouw Gmail
   - Save and Continue (rest mag leeg, klik door tot klaar)
5. **Maak OAuth credentials:**
   - "APIs & Services" → "Credentials" → **"+ Create Credentials"** → "OAuth client ID"
   - Application type: **Web application**
   - Name: `Luxis`
   - Authorized redirect URIs:
     - `http://localhost:8000/api/email/oauth/callback`
     - `https://luxis.kestinglegal.nl/api/email/oauth/callback`
   - Klik **Create**
6. **Kopieer Client ID + Client Secret** (verschijnen direct na aanmaken)
7. **Voeg jezelf toe als test user:**
   - "OAuth consent screen" → "Test users" → "+ Add users" → jouw Gmail adres

**Geef de Client ID + Client Secret aan Claude bij de volgende sessie.**

### Bouwvolgorde (in de sessie):
- **M1:** Backend OAuth flow (authorize URL → callback → token opslag + auto-refresh)
- **M2:** Inbox sync (emails ophalen via Gmail API, koppelen aan dossiers via afzender → relatie → dossier)
- **M3:** Correspondentie tab (unified chronologische view: emails + brieven + notities + telefoonnotities per dossier)
- **M4:** Compose via email provider (draft aanmaken vanuit Luxis)

### Architectuur:
```
EmailProvider (abstract interface)
  ├── GmailProvider    (Arsalan's test - nu bouwen)
  └── OutlookProvider  (Lisanne - later toevoegen, zelfde interface)
```
Zo hoeft de frontend + correspondentie tab maar 1x gebouwd te worden.

### Later:
- OutlookProvider toevoegen wanneer Lisanne naar M365 migreert
- G3 (procesgegevens), G5 (keyboard shortcuts), G14 (sidebar), G10 (task templates)

## Bestanden die zijn aangepast (deze sessie)
- `docker-compose.prod.yml` — env var defaults (ACCESS_TOKEN, REFRESH_TOKEN, SENTRY_DSN)
- `LUXIS-ROADMAP.md` — infra status fix, email strategie notitie
- `DOSSIER-WERKPLEK-RESEARCH.md` — G2 als done, email strategie notitie bij Fase 1
- `SESSION-NOTES.md` — deze update

## Openstaande issues
- Geen bekende bugs
- SMTP gebruikt nog Gmail test-credentials (wordt vervangen door OAuth Gmail API)
- Dossier detail page is 47K+ regels — refactoring gewenst (lage prio)

## Beslissingen genomen
- **Email strategie:** F11 (SMTP) = tijdelijke brug, M1-M6 = eindoplossing
- **Dev/test provider:** Gmail API (Arsalan's account) → later Outlook toevoegen voor Lisanne
- **Abstractielaag:** EmailProvider interface zodat Gmail en Outlook inwisselbaar zijn
- **Azure blocker:** Gratis Outlook.com accounts kunnen geen apps meer registreren zonder Azure subscription → daarom Gmail als test
- **Deploy:** ALTIJD `docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml` gebruiken

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && \
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml up -d
```
