# Luxis — Sessie-overdracht (21 februari 2026)

> **Dit document is de overdracht voor de volgende Claude Code sessie.**
> **LUXIS-ROADMAP.md is de ENIGE source of truth voor features, bugs en status.**

---

## TL;DR — Waar staan we?

Luxis is een werkend praktijkmanagementsysteem op https://luxis.kestinglegal.nl. Login werkt, alle features t/m F10 zijn live, alle bekende bugs (BUG-1 t/m BUG-9) zijn gefixt.

**Volgende prioriteit:** F11 (e-mail naar elke partij vanuit dossier) → daarna Microsoft 365 integratie.

---

## Project

- **Wat:** PMS voor Nederlandse advocatenkantoren
- **Wie:** Arsal (eigenaar/bouwer met Claude Code), Lisanne Kesting (advocaat, enige gebruiker)
- **Stack:** FastAPI + Next.js 15 + PostgreSQL + Redis + Docker
- **Repo:** https://github.com/Apartsalan/luxis.git (branch: `main`)
- **Live:** https://luxis.kestinglegal.nl
- **VPS:** Hetzner, IP 87.106.109.66, pad: `/opt/luxis`

---

## Deployment

Claude heeft **GEEN** SSH-toegang. Geef deploy-commando's aan de gebruiker.

```bash
# Frontend only (geen migraties):
cd /opt/luxis && git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend

# Frontend + Backend (geen migraties):
cd /opt/luxis && git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend backend

# Met migraties (backend restart nodig):
cd /opt/luxis && git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend backend && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d && docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production exec backend python -m alembic upgrade head
```

**LET OP:**
- `NEXT_PUBLIC_API_URL` is BUILD-TIME → altijd `--no-cache` bij frontend rebuild
- Postgres wachtwoord: alleen bij eerste volume-creatie; daarna `ALTER USER` nodig
- Alembic revision IDs max 32 chars
- Git Bash: `MSYS_NO_PATHCONV=1` prefix bij `docker exec`

---

## Wat er gebouwd is (alles ✅)

**Backend:** 110+ endpoints, 14 routers (auth, relaties, zaken, tijdschrijven, facturatie, onkosten, documenten, workflow, KYC/WWFT, incasso, dashboard, settings, search, email)

**Frontend:** Login, Dashboard, Relaties, Zaken (9-tabs detail), Tijdschrijven, Facturatie, Documenten, Agenda, Instellingen, Taken

**Modules:** incasso, tijdschrijven, facturatie, wwft (togglebaar per tenant)

**Alle feature-fases afgerond:** A1-A7, B1-B3, C1-C3, D1/D3/D4/D5, E1-E8, T1-T3, F1-F10

**Alle bugs gefixt:** BUG-1 t/m BUG-9

> Volledig overzicht per feature: zie `LUXIS-ROADMAP.md` sectie "Wat er gebouwd moet worden"

---

## Laatste sessie (21 feb 2026) — wat er gedaan is

1. **VPS login gefixt** — DB wachtwoord mismatch opgelost via `ALTER USER`, frontend herbouwd met `--no-cache`
2. **BUG-7 gefixt** — Edit-modus toegevoegd aan Dossiergegevens (Bewerken/Opslaan/Annuleren)
3. **BUG-8 gefixt** — `court_case_number` veld toegevoegd aan Nieuw dossier form + backend CaseCreate schema
4. **BUG-9 gefixt** — Advocaat wederpartij zoekfield toegevoegd in Dossiergegevens (view+edit) + Nieuw dossier form

**Commits:**
```
a9371b0 feat(cases): add advocaat wederpartij field to case detail and new case form (BUG-9)
fde03c4 fix(frontend): editable case details + court_case_number on new case form (BUG-7, BUG-8)
```

---

## Openstaande TODO's

| Prioriteit | Wat | Context |
|-----------|-----|---------|
| 1 | **F11: E-mail naar elke partij vanuit dossier** | Backend email module bestaat al (SMTP, send endpoint, templates). Moet UI krijgen op dossierdetail. |
| 2 | **SMTP omzetten** van Gmail test-credentials naar Lisanne's Outlook | Wacht op M365 migratie (samen met Lisanne) |
| 3 | **Microsoft 365 integratie** (M0-M6) | Groot traject: OAuth, inbox sync, auto-koppeling, correspondentie tab, drafts, auto-time |

---

## Documentatie-overzicht

### Altijd lezen (kerncontext):
| Bestand | Doel |
|---------|------|
| `LUXIS-ROADMAP.md` | **ENIGE source of truth** — alles staat hier |
| `HANDOVER.md` | Dit document — sessie-overdracht |
| `CLAUDE.md` | AI development guide, architectuurregels, werkwijze |
| `backend/CLAUDE.md` | Backend module-patronen, financial rules |
| `frontend/CLAUDE.md` | Frontend conventies |

### Architectuur (lees bij nieuwe features):
| Bestand | Doel |
|---------|------|
| `DECISIONS.md` | Tech stack keuzes + onderbouwing |
| `FEATURE-INVENTORY.md` | Complete feature-lijst (15 modules) |
| `docs/dutch-legal-rules.md` | Nederlandse juridische regels incasso |

### Analyse/research (lees wanneer relevant):
| Bestand | Doel |
|---------|------|
| `BEVINDINGEN-ANALYSE.md` | Gap-analyse Lisanne's 10 praktijkbevindingen |
| `BUGS-EN-VERBETERPUNTEN.md` | Bug-beschrijvingen met bestanden + fix-instructies |
| `UX-REVIEW.md` | UX analyse per feature vs. concurrentie |
| `UX-VERBETERPLAN.md` | Bouw-instructies per UX feature |
| `PROMPT-TEMPLATES-IN-WORKFLOW.md` | Spec templates + email in workflow |
| `SESSION-LOG-20FEB-SESSIE3.md` | Context over email module (wat er al bestaat) |
| `UX-RESEARCH-*.md` (7 bestanden) | UX research per feature-domein |

### Archief (niet meer actief nodig):
| Bestand | Doel |
|---------|------|
| `CODE-REVIEW.md` | Point-in-time code audit |
| `CLICK-COUNT-ANALYSE.md` | UX click-count vergelijking |
| `INCASSO-VERIFICATIE.md` | Verificatie incasso-berekeningen |
| `OPTIMIZATION-LOG.md` | Claude Code workflow optimalisatie |

---

## Kernregels

1. **Dutch UI, English code** — UI-teksten Nederlands, code/comments Engels
2. **Financial precision** — `Decimal` + `NUMERIC(15,2)`, nooit `float`
3. **Multi-tenant** — `TenantBase` + `tenant_id` op alles
4. **Onderzoek eerst, bouw daarna** — 4 stappen: onderzoek → plan → bouw → check
5. **Roadmap bijwerken (HARDE REGEL)** — Na ELKE wijziging `LUXIS-ROADMAP.md` updaten
6. **Commit en push** na elke afgeronde taak
7. **Deploy-commando** altijd meegeven na push

---

## Belangrijke bestanden (quick reference)

### Backend
- `backend/app/main.py` — FastAPI app, CORS, router imports
- `backend/app/config.py` — Settings (env vars)
- `backend/app/cases/` — Dossierbeheer (router, service, models, schemas)
- `backend/app/email/` — E-mail verzenden (SMTP service)
- `backend/app/search/router.py` — Globale zoekfunctie

### Frontend
- `frontend/src/lib/api.ts` — JWT-aware fetch wrapper
- `frontend/src/hooks/use-cases.ts` — Cases CRUD + party management hooks
- `frontend/src/hooks/use-relations.ts` — Contacts CRUD + search
- `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` — Zaakdetail (groot, alle 9 tabs)
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — Nieuw dossier form

### Deployment
- `docker-compose.yml` + `docker-compose.prod.yml` + `.env.production`
- `Caddyfile` — reverse proxy (`/api/*` → backend, rest → frontend)

---

## EERSTE ACTIE IN VOLGENDE SESSIE

1. Lees `LUXIS-ROADMAP.md` — dit is de enige source of truth
2. Lees `CLAUDE.md` — werkwijze en regels
3. Vraag de gebruiker wat de prioriteit is
4. Begin met bouwen (onderzoek → plan → bouw → check)
