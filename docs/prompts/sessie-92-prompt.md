Sessie 92 — Mega-audit Sprint 3: MEDIUM infra + security hardening
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-Audit Sprint') en SESSION-NOTES.md (sessie 91). Geef compacte samenvatting."

## Taak
Fix ALLE MEDIUM infra/security issues:

**Security (3 items):**
- SEC-28: Dev deps in prod image — `backend/Dockerfile` gebruikt `uv pip install ".[dev]"`. Fix: aparte prod install zonder dev deps
- SEC-29: Mass assignment setattr — user profile update itereert `model_dump()`. Fix: explicit allowlist van velden
- SEC-30: CSP unsafe-inline/unsafe-eval — Caddyfile. Fix: verwijder unsafe-eval in prod, behoud alleen wat nodig is

**Infra (5 items):**
- CQ-21: Backend .dockerignore — .env en test files worden meegekopieerd in image. Maak/update `.dockerignore`
- CQ-22: Container health checks — voeg HEALTHCHECK toe aan backend + frontend Dockerfiles of compose
- CQ-23: Container resource limits — voeg mem_limit + cpus toe aan prod compose
- CQ-24: Off-site backups — configureer pg_dump cron + upload naar externe opslag (S3/Backblaze)
- CQ-25: Uptime monitoring — configureer UptimeRobot of vergelijkbaar voor luxis.kestinglegal.nl

## Verificatie
- Docker build test: `docker compose build` (geen errors)
- Health checks: `docker compose ps` (alle containers healthy)
- Backup test: handmatige pg_dump draaien en verifiëren

## Constraints (wat NIET doen)
- Geen code changes aan app logica
- Geen frontend UI wijzigingen
- Geen LOW items

## Commit
Commit + push na ALLE fixes. Deploy via SSH automatisch.
