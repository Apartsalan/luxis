# CLAUDE.md — Luxis

Practice management system for Dutch law firms. First client: Kesting Legal (1 lawyer, collections/insolvency law, Amsterdam).

**Dutch UI, English code.**

## Commands

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up   # Dev with hot reload
docker compose exec backend pytest tests/ -v                         # Tests
docker compose exec backend ruff check app/                          # Lint
docker compose exec backend python -m alembic upgrade head           # Migrations
docker compose exec backend python -m alembic revision --autogenerate -m "desc"  # New migration
```

## Notificatiegeluid (HARDE REGEL)

**Speel geluid af bij wacht op gebruiker:** `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` via Bash VOORDAT je `AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode` gebruikt, klaar bent met grote taak, of een vraag stelt.

## Critical Rules

**Financial precision:** ALL money = Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NEVER float. `Decimal('0.00')`, `ROUND_HALF_UP` explicit. Every calc needs test.

**Multi-tenant:** Models inherit `TenantBase` (has `tenant_id`). Exception: `interest_rates` is global. Every query scoped via middleware + RLS.

## Security-regels (HARD — audit S183)

Deze gelden ALTIJD, ook zonder dat de opdracht ze noemt. Ze bestaan omdat de audit
bewees dat ze wegdriften zodra iemand ze vergeet.

- **Nieuwe tabel met `tenant_id` → RLS in DEZELFDE migratie.** Roep `apply_rls(op.get_bind())`
  aan (idempotent, dekt de nieuwe tabel). Vergeet je het, dan blokkeert de opstartcontrole
  (`app.main.lifespan`, faalt dicht in productie) + de drift-guard-test
  (`tests/test_rls_isolation.py::test_drift_guard_flags_tenant_table_without_rls`) de deploy.
  `learned_answers` ontsnapte hier ooit aan (S183-1). Enige uitzondering: `users` (zie
  `app/security/rls.py`).
- **Nieuwe route → auth verplicht.** `Depends(get_current_user)` (of `require_role(...)`),
  tenzij het echt publiek moet (login/OAuth-callback) — dan expliciet + rate-limit.
- **Geld/tenant-mutatie na een `db.commit()` binnen één request:** de tenant + rol worden
  automatisch her-toegepast (`after_begin`-event, S183-2) — vertrouw daar niet blind op,
  filter altijd óók op `tenant_id` in de query zelf.
- **Nooit secrets/sleutels in code.** Alleen uit env (`app/config.py`). Sleutels van
  gebruikers (OAuth) versleuteld opslaan. Geen `NEXT_PUBLIC_*` met secrets — sleutels blijven
  server-side (alle AI/externe calls lopen via de backend).
- **Uploads:** alleen via de bestaande gevalideerde helpers (extensie-whitelist + grootte-cap
  + magic-byte-check). Geen rauwe bestandsopslag.
- **Rollen-matrix:** zie `docs/security/rollen.md` (wat admin/advocaat/medewerker mogen).

## Architecture

- **Backend:** FastAPI 3.12 + SQLAlchemy 2.0 + Alembic | Module: `router.py`, `service.py`, `models.py`, `schemas.py`
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind | `@/*` = `src/*`
- **Auth:** PyJWT + bcrypt (NOT passlib) | **Docs:** docxtpl + WeasyPrint | **Queue:** Celery + Redis
- **API:** `/api/` prefix, snake_case JSON, pagination `?page=1&per_page=20`, errors `{"detail": "msg"}`

## Design & UX

Modern, professioneel (Gmail/HubSpot-stijl). Data-dense, niet overweldigend. Sidebar met collapse. UI: Nederlands.

Luxis is een **PRODUCT**. Clean, modern, geen jargon buiten vakmodules. Incasso-specifiek ALLEEN in incassomodule. Bij elk scherm: "zou een willekeurig advocatenkantoor dit willen?"

## Werkwijze bij nieuwe features

**Onderzoek eerst, bouw daarna.** 4 stappen:

### Stap 1: Onderzoek
Zoek hoe concurrenten (Clio, Basenet, Legalsense, Urios, PracticePanther, Smokeball) + beste SaaS-apps dit oplossen. Analyseer: standaard workflow, essentiële velden, minimale clicks. Denk vanuit Lisanne (advocaat, geen techneut).

### Stap 2: Plan presenteren
Samenvatting onderzoek + hoe je het bouwt + welke schermen. **Wacht op goedkeuring.**

**Pre-mortem (bij elk niet-triviaal plan):** 3 faalredenen + waarom toch juiste aanpak. Niet bij triviale fixes.

**Strategische premortem:** Bij positionering/pricing/architectuur die toekomst bepaalt → draai `/premortem` automatisch.

### Stap 3: Bouwen
Na goedkeuring.

### Stap 4: Verificatie-loop
1. Build check — `tsc --noEmit` of `pytest`. Rood → fix → opnieuw.
2. Visuele check — preview/screenshot.
3. Functionele check — klik door flow.
4. Pas "done" als alle 3 groen. NOOIT doorgaan met kapotte taak.

## Working Agreements

- Zelfstandig werken, geen toestemming (behalve destructieve acties)
- Nieuwe features: altijd 4-stappen werkwijze
- Juridische twijfel: flaggen, niet stoppen
- Correcties: CLAUDE.md of memory updaten
- Conventional commits: `feat(module):`, `fix(module):`, etc.

**Plan Mode:** ALTIJD bij niet-triviale taken (features, multi-file, architectuur, UI/UX). Verken → ontwerp → presenteer → goedkeuring → bouw. Misgaat → STOP en herplan. Triviale fixes mogen direct.

## Kwaliteitsstandaard

- Nooit "done" zonder bewijs (build/test/handmatige check). "Migration completed" is fout als records geskipt zijn. "Tests pass" is fout als tests geskipt zijn. Surface uncertainty, niet verbergen.
- Bugs: EERST rode test → fix → groen. Triviale bugs direct.
- Elegantie overwegen bij non-triviale changes, niet over-engineeren
- Conflicterende patronen niet middelen — kies één (recentste/meest getest), licht toe waarom, flag andere voor cleanup.
- Na correctie: les noteren in CLAUDE.md of memory
- Minimale impact, root causes fixen, geen workarounds

## Geen aannames — eerst zeker weten (HARDE REGEL)

- **Maak GEEN aannames.** Verifieer alles met de code, git-historie, logs of database vóór je iets aanpast. Twijfel je → eerst onderzoeken, nooit gokken.
- **Bij regressies** (iets dat eerder werkte, nu niet): zoek in git-historie/SESSION-NOTES wánneer het werkte en wélke commit het brak. Vergelijk oude vs huidige code.
- **Fix chirurgisch:** alleen de kapotte regressie herstellen. NOOIT features of security-verbeteringen breed terugdraaien om één los symptoom te fixen.
- **Presenteer bevindingen + voorgestelde fix vóór je wijzigt** (Plan Mode); pas aan na bevestiging.

## Gedragsregels

- "Documenteer/sla op in md" = ALLEEN markdown, geen code
- "Sla checks over" = geen lint/tests/build
- Geen lint/tests/build draaien tenzij expliciet gevraagd of in workflow
- Geen git worktrees tenzij gebruiker "worktree" zegt
- `LUXIS-ROADMAP.md` = enige source of truth; levende docs klein houden: SESSION-NOTES max 10 entries, roadmap één prioriteit-sectie, historie → `docs/archief/` (verplaatsen, nooit weggooien — archief-regels in `/sessie-einde`)
- Scripts/commands altijd in voorgrond
- Commit + push na elke taak. **Na ELKE commit ALTIJD `git push origin main`.**
- Bij parallelle terminals: **ALTIJD kant-en-klare prompts meegeven**

**Deploy:** Na commit+push → deploy automatisch via SSH. Details in skill `deploy-regels`.

**Sessie-einde:** SESSION-NOTES.md + LUXIS-ROADMAP.md updaten + git tag. Details in `/sessie-einde` command.

**Sessie-prompt:** LEAN (<50KB), 1 hoofdtaak, format in `/sessie-einde` command.

## Context Management

- Gebruik `luxis-researcher` subagent voor grote docs (roadmap, session notes)
- Skills laden on-demand (incasso-workflow, deploy-regels, template-systeem, bekende-fouten)
- `/clear` tussen onafhankelijke taken
- `/compact` met focus als context vol raakt
- Delegeer onderzoek naar subagents
- **`/effort max` aan begin van elke sessie** voor maximale reasoning

### Subagents
- **luxis-researcher** — leest grote docs, geeft compacte samenvattingen
- **code-reviewer** — checkt financial precision, multi-tenant, async, URLs

### Skills (on-demand)
- **incasso-workflow** — pipeline, batch, deadlines
- **deploy-regels** — VPS deploy, disk-pressure, valkuilen
- **template-systeem** — DOCX rendering, ManagedTemplate
- **bekende-fouten** — valkuilen uit 32 sessies (LEES bij niet-triviale taken)

## Known Quirks

- Git Bash: `MSYS_NO_PATHCONV=1` prefix bij `docker exec`
- Container: `python -m alembic` niet bare `alembic`
- asyncpg: Python `date` objects, geen strings
- bcrypt 5.x: passlib incompatible, direct bcrypt
- Docker commands ALTIJD vanuit hoofdrepo (`C:\Users\arsal\Documents\luxis`)
- Falende tests: check eerst stale DB / ontbrekende migraties

## References

- @DECISIONS.md — tech stack | @backend/CLAUDE.md — backend | @frontend/CLAUDE.md — frontend
- @docs/dutch-legal-rules.md — wettelijke rente, WIK, art. 6:44 BW
- @docs/qa/ — QA checklists | @docs/research/ — UX research | @docs/future-modules.md — M365, AI, migratie
