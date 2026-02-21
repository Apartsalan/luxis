# Sessie Notities — Luxis

**Laatst bijgewerkt:** 21 feb 2026
**Laatste feature/fix:** VPS deploy fix + email strategie beslissing

## Wat er gedaan is
- VPS deploy gefixt: 5 issues opgelost (Pydantic int crash, DATABASE_URL `!` in wachtwoord, Sentry BadDsn, docker-compose leest .env.production niet, NEXT_PUBLIC_API_URL niet in frontend build)
- **KRITIEK geleerd:** `--env-file .env.production` is VERPLICHT bij alle docker compose commando's. `NEXT_PUBLIC_API_URL` is een build-time arg — runtime env heeft geen effect.
- Email strategie beslissing genomen: F11 (SMTP) is tijdelijke brug → M1-M6 (Outlook) is eindoplossing
- LUXIS-ROADMAP.md bijgewerkt met email strategie + infra status
- Beslissing: M1-M4 (Outlook integratie) wordt nu prioriteit, testen met Arsalan's gratis Outlook.com account

## Wat de volgende stap is

### PRIORITEIT: M1 — Microsoft Graph API OAuth koppeling

**Voordat de sessie begint moet Arsalan dit doen (10 min):**

1. **Maak een gratis Outlook.com account aan** (of gebruik een bestaand @outlook.com / @hotmail.com account)
2. **Ga naar https://entra.microsoft.com** (login met dat Outlook account)
   - Klik "Identity" → "Applications" → "App registrations" → "+ New registration"
   - Name: `Luxis Dev`
   - Supported account types: **"Personal Microsoft accounts only"**
   - Redirect URI: Web → `http://localhost:8000/api/email/oauth/callback`
   - Klik "Register"
3. **Kopieer deze 2 waarden** (staan op de Overview pagina):
   - **Application (client) ID** → bewaar dit
   - Ga naar "Certificates & secrets" → "+ New client secret" → beschrijving: `luxis-dev` → Add
   - **Client Secret Value** → bewaar dit (verdwijnt na het scherm!)
4. **Voeg permissions toe:**
   - Ga naar "API permissions" → "+ Add a permission" → "Microsoft Graph" → "Delegated permissions"
   - Zoek en vink aan: `Mail.Read`, `Mail.Send`, `Mail.ReadWrite`, `User.Read`, `offline_access`
   - Klik "Add permissions"
5. **Voeg extra redirect URI toe** (voor productie):
   - Ga naar "Authentication" → "+ Add URI"
   - Voeg toe: `https://luxis.kestinglegal.nl/api/email/oauth/callback`
   - Klik "Save"

**Geef de Client ID + Client Secret aan Claude bij de volgende sessie.**

### Daarna (in de sessie):
- **M1:** Backend OAuth flow bouwen (authorize URL → callback → token opslag)
- **M2:** Inbox sync (emails ophalen via Graph API, koppelen aan dossiers)
- **M3:** Correspondentie tab (unified view van alle emails per dossier)
- **M4:** Compose via Outlook (draft aanmaken in Outlook vanuit Luxis)

### Later:
- G3 (procesgegevens), G5 (keyboard shortcuts), G14 (sidebar), G10 (task templates)

## Bestanden die zijn aangepast (deze sessie)
- `docker-compose.prod.yml` — env var defaults (ACCESS_TOKEN, REFRESH_TOKEN, SENTRY_DSN)
- `LUXIS-ROADMAP.md` — infra status fix, email strategie notitie
- `DOSSIER-WERKPLEK-RESEARCH.md` — G2 als done, email strategie notitie bij Fase 1
- `SESSION-NOTES.md` — deze update

## Openstaande issues
- Geen bekende bugs
- SMTP gebruikt nog Gmail test-credentials (wordt vervangen door Graph API)
- Dossier detail page is 47K+ regels — refactoring naar losse componenten gewenst (lage prio)

## Beslissingen genomen
- **Email strategie:** F11 (SMTP) = tijdelijke brug, M1-M6 (Outlook) = eindoplossing
- **Test-aanpak:** Arsalan's gratis Outlook.com account als test → alles bouwen en testen → daarna Lisanne overzetten
- **Geen M365 abonnement nodig voor dev:** Gratis Outlook.com account werkt met Graph API (Mail.Read, Mail.Send, offline_access)
- **Deploy:** ALTIJD `docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml` gebruiken

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && \
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml up -d
```
