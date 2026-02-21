# Sessie Notities — Luxis

**Laatst bijgewerkt:** 21 feb 2026
**Laatste feature/fix:** VPS deploy fix + email strategie beslissing

## Wat er gedaan is
- VPS deploy gefixt: 5 issues opgelost (Pydantic int crash, DATABASE_URL `!` in wachtwoord, Sentry BadDsn, docker-compose leest .env.production niet, NEXT_PUBLIC_API_URL niet in frontend build)
- **KRITIEK geleerd:** `--env-file .env.production` is VERPLICHT bij alle docker compose commando's. `NEXT_PUBLIC_API_URL` is een build-time arg — runtime env heeft geen effect.
- Email strategie beslissing genomen: F11 (SMTP) is tijdelijke brug → M1-M6 (Outlook) is eindoplossing
- G1 (Correspondentie Tab) wordt gebouwd met abstractielaag zodat SMTP-data en Outlook-data allebei werken
- LUXIS-ROADMAP.md bijgewerkt met email strategie + infra status

## Wat de volgende stap is
- **G1: Unified Correspondentie Tab** — bouw met abstractielaag (`source: 'smtp' | 'outlook'`), chronologisch overzicht van emails + brieven + notities + telefoonnotities
- Daarna: G3 (procesgegevens), G5 (keyboard shortcuts), G14 (sidebar), G10 (task templates)
- SMTP migratie van Gmail test-credentials naar Lisanne's Outlook (wacht op M365)

## Bestanden die zijn aangepast (deze sessie)
- `docker-compose.prod.yml` — env var defaults (ACCESS_TOKEN, REFRESH_TOKEN, SENTRY_DSN)
- `LUXIS-ROADMAP.md` — infra status fix, email strategie notitie
- `SESSION-NOTES.md` — deze update

## Openstaande issues
- Geen bekende bugs
- SMTP gebruikt nog Gmail test-credentials (werkt, maar moet naar Outlook na M0)
- Dossier detail page is 47K+ regels — refactoring naar losse componenten gewenst (lage prio)

## Beslissingen genomen
- **Email strategie:** F11 (SMTP) = tijdelijke brug, M1-M6 (Outlook) = eindoplossing. G1 wordt gebouwd met abstractielaag die beide ondersteunt. Na M4 vervangt "Open in Outlook" de Luxis compose dialog.
- **Deploy:** ALTIJD `docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml` gebruiken. Frontend MOET rebuilden bij NEXT_PUBLIC_API_URL wijzigingen.

## Deploy commando (copy-paste ready)
```bash
cd /opt/luxis && git pull && \
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && \
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml up -d
```
