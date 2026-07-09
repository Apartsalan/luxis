Sessie 92 — Mega-audit Sprint 3: infra + Docker + security hardening
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-Audit Sprint') en SESSION-NOTES.md (sessie 90). Geef compacte samenvatting."

## Taak
Fix ALLE infra/Docker/security-config issues (GEEN app code, GEEN frontend componenten):

**CRITICAL (uit sessie 91 verplaatst — hoort bij infra):**
- SEC-17: DB/Redis poorten open in prod — `docker-compose.prod.yml`. Voeg `ports: []` override toe voor db en redis services zodat ze niet extern bereikbaar zijn

**Security config (3 items):**
- SEC-28: Dev deps in prod image — `backend/Dockerfile` gebruikt `uv pip install ".[dev]"`. Fix: aparte prod install zonder dev deps
- SEC-29: Mass assignment setattr — `backend/app/auth/router.py` user profile update itereert `model_dump()`. Fix: explicit allowlist van velden
- SEC-30: CSP unsafe-inline/unsafe-eval — Caddyfile. Fix: verwijder unsafe-eval in prod, behoud alleen wat nodig is

**Infra (5 items):**
- CQ-21: Backend .dockerignore — .env en test files worden meegekopieerd in image. Maak/update `.dockerignore`
- CQ-22: Container health checks — voeg HEALTHCHECK toe aan backend + frontend in docker-compose.prod.yml
- CQ-23: Container resource limits — voeg mem_limit + cpus toe aan docker-compose.prod.yml
- CQ-24: Off-site backups — configureer pg_dump cron + upload naar externe opslag (S3/Backblaze)
- CQ-25: Uptime monitoring — configureer UptimeRobot of vergelijkbaar voor luxis.kestinglegal.nl

## Verificatie
- Docker build test: `docker compose -f docker-compose.yml -f docker-compose.prod.yml config` (geen errors)
- Controleer dat .dockerignore werkt: `docker compose build backend` bevat geen .env/tests
- SEC-29: check dat alleen toegestane velden geüpdatet worden

## Constraints (wat NIET doen)
- Geen frontend component/hook wijzigingen (dat doen sessie 91 en 93)
- Geen app logica wijzigingen
- Alleen config/infra bestanden: Dockerfiles, compose files, Caddyfile, .dockerignore, VPS scripts
- Uitzondering: SEC-29 mag auth/router.py wijzigen (alleen de update profile endpoint)
- NIET committen of pushen — meld dat je klaar bent (andere terminals draaien parallel)

## Commit
NIET zelf committen. Terminal A regelt commit + push voor alle terminals.
