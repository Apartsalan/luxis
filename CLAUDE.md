# CLAUDE.md — Luxis

Practice management system for Dutch law firms. First client: Kesting Legal (1 lawyer, collections/insolvency law, Amsterdam).

**Dutch UI, English code.**

> 🆕 **Nieuwe computer of nieuw account? LEES EERST `HANDOVER-NIEUWE-MACHINE.md`.** Daarna:
> 📌 **`WERKWIJZE.md`** — hoe er aan Luxis gewerkt wordt: communicatiestijl (gewoon Nederlands,
> geen jargon — harde regel), werkdiscipline en veiligheidsregels. Geldt voor iedere Claude Code
> die in deze map werkt.

## Notificatiegeluid (HARDE REGEL)

**Speel geluid af bij wacht op gebruiker:** `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` via Bash VOORDAT je `AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode` gebruikt, klaar bent met grote taak, of een vraag stelt.

## Critical Rules

**Financial precision:** ALL money = Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NEVER float. `Decimal('0.00')`, `ROUND_HALF_UP` explicit. Every calc needs test.

**Multi-tenant:** Models inherit `TenantBase` (has `tenant_id`). Exception: `interest_rates` is global. Every query scoped via middleware + RLS.

## Security-regels (HARD — audit S183)

Deze gelden ALTIJD, ook zonder dat de opdracht ze noemt. Ze bestaan omdat de audit
bewees dat ze wegdriften zodra iemand ze vergeet.

- **Nieuwe tabel met `tenant_id` → RLS in DEZELFDE migratie.** Roep `apply_rls(op.get_bind())`
  aan (idempotent). Vergeet je het, dan blokkeert de opstartcontrole (`app.main.lifespan`) +
  de drift-guard-test de deploy. Enige uitzondering: `users` (zie `app/security/rls.py`).
- **Nieuwe route → auth verplicht.** `Depends(get_current_user)` (of `require_role(...)`),
  tenzij het echt publiek moet (login/OAuth-callback) — dan expliciet + rate-limit.
- **Geld/tenant-mutatie na een `db.commit()` binnen één request:** tenant + rol worden
  her-toegepast (`after_begin`-event, S183-2) — vertrouw daar niet blind op, filter altijd
  óók op `tenant_id` in de query zelf.
- **Nooit secrets/sleutels in code.** Alleen uit env (`app/config.py`). OAuth-sleutels
  versleuteld opslaan. Geen `NEXT_PUBLIC_*` met secrets — alle AI/externe calls via backend.
- **Uploads:** alleen via de bestaande gevalideerde helpers (whitelist + grootte-cap +
  magic-byte-check).
- **Rollen-matrix:** `docs/security/rollen.md`.

## Architecture (niet-afleidbare keuzes)

- Backend-module: `router.py` (dun) → `service.py` (businesslogica) → `models.py` → `schemas.py`
- **Auth: PyJWT + direct bcrypt — NIET passlib** (bcrypt 5.x incompatible)
- API: `/api/` prefix, snake_case JSON, pagination `?page=1&per_page=20`, errors `{"detail": "msg"}`
- Frontend: `@/*` = `src/*`; details in `frontend/CLAUDE.md` en `backend/CLAUDE.md`

## Design & UX

Modern, professioneel (Gmail/HubSpot-stijl). Data-dense, niet overweldigend. UI: Nederlands.
Luxis is een **PRODUCT**: incasso-specifiek ALLEEN in de incassomodule. Bij elk scherm:
"zou een willekeurig advocatenkantoor dit willen?"

## Werkwijze

**KOERSREGEL (Arsalan, 30-7):** geen nieuwe features — afmaken en verbeteren. Nieuwbouw
alleen op expliciete vraag. Twijfel → adviseer "niets doen".

**Nieuwe features (als er tóch om gevraagd wordt), 4 stappen:** (1) onderzoek hoe
concurrenten (Clio, Basenet, Legalsense, e.a.) het oplossen, denk vanuit Lisanne;
(2) plan presenteren + pre-mortem, **wacht op goedkeuring**; (3) bouwen; (4) verificatie-loop.

**Verificatie-loop (elke taak):** build check (`tsc --noEmit`/`pytest`) → visuele check →
functionele check → **kruispunt-check via skill `breed-testen` (HARD, S223)**: raakt de taak
een gedeeld effect (mail, stapwissel, geld, zaak sluiten)? → route×huisregel-matrix, elke
gevonden fout krijgt een wachter-test voor zijn SOORT. Pas "done" als alles groen, met bewijs —
geskipte records/tests melden, niet verbergen.

**Bugs:** EERST rode test → fix → groen (triviale bugs direct). Root cause, geen workaround.
**Regressies:** zoek in git-historie/SESSION-NOTES wanneer het werkte en welke commit het brak;
fix chirurgisch — nooit features of security breed terugdraaien voor één symptoom.

**Plan Mode** bij niet-triviale taken (features, multi-file, architectuur, UI/UX). Triviale
fixes mogen direct.

## Working Agreements

- **Agent-laag-compatibel bouwen (S237):** businesslogica in de service-laag, router dun.
  Toekomst-triggers: `docs/TOEKOMST-REPOS.md` — raakt een sessie zo'n trigger, meld het vóór
  het bouwen.
- **Rolverdeling (S240):** deze sessies BOUWEN; Lisanne doet inhoudelijk werk (mails,
  dossierbeslissingen). Inhoudelijke vondsten signaleren, niet zelf oppakken.
- Zelfstandig werken, geen toestemming vragen (behalve destructieve acties)
- Juridische twijfel: flaggen, niet stoppen
- Correcties van Arsalan: CLAUDE.md of memory updaten
- Conventional commits: `feat(module):`, `fix(module):`, etc.

## Gedragsregels

- "Documenteer/sla op in md" = ALLEEN markdown, geen code
- "Sla checks over" = geen lint/tests/build; geen lint/tests/build draaien tenzij gevraagd
  of in workflow
- Geen git worktrees tenzij gebruiker "worktree" zegt
- `LUXIS-ROADMAP.md` = enige source of truth; SESSION-NOTES max 10 entries; historie →
  `docs/archief/` (verplaatsen, nooit weggooien — regels in `/sessie-einde`)
- Scripts/commands altijd in voorgrond
- Commit + push na elke taak. **Na ELKE commit ALTIJD `git push origin main`.**
- **NOOIT `git add -A` of `git add .`** — stage expliciete paden. De repo bevat
  bewust-untracked bestanden (bank-CSV, AV-PDF's, tmp-SQL); één `git add -A` veegde ze in
  S203 de historie in (history-rewrite nodig). Zie `.gitignore`.
- Bij parallelle terminals: ALTIJD kant-en-klare prompts meegeven

**Deploy:** na commit+push → deploy automatisch via SSH. Details in skill `deploy-regels`.
**Sessie-einde:** SESSION-NOTES.md + LUXIS-ROADMAP.md updaten + git tag — zie `/sessie-einde`.
**Sessie-prompt:** LEAN (<50KB), 1 hoofdtaak.

## Commands

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up   # Dev with hot reload
docker compose exec backend pytest tests/ -v                         # Tests
docker compose exec backend ruff check app/                          # Lint
docker compose exec backend python -m alembic upgrade head           # Migrations
```

## Context Management

- `luxis-researcher` subagent voor grote docs (roadmap, session notes); onderzoek delegeren
- Skills on-demand: **incasso-workflow** (pipeline/batch/deadlines), **deploy-regels** (VPS,
  valkuilen), **template-systeem** (DOCX rendering), **bekende-fouten** (valkuilen uit 32
  sessies — LEES bij niet-triviale taken)
- `/effort max` aan het begin van elke sessie
- `/clear` tussen onafhankelijke taken; `/compact` met focus als context vol raakt

## Known Quirks

- Git Bash: `MSYS_NO_PATHCONV=1` prefix bij `docker exec`
- Container: `python -m alembic`, niet bare `alembic`
- asyncpg: Python `date` objects, geen strings
- Docker commands ALTIJD vanuit hoofdrepo (`C:\Users\arsal\Documents\luxis`)
- Falende tests: check eerst stale DB / ontbrekende migraties
- Compound interest year runs from **verzuimdatum**, NOT January 1
- `alembic stamp head` voor pre-existing databases, niet `upgrade head`

## References

- @backend/CLAUDE.md — backend | @frontend/CLAUDE.md — frontend
- @docs/dutch-legal-rules.md — wettelijke rente, WIK, art. 6:44 BW
- docs/qa/ — QA checklists | docs/research/ — UX research | docs/future-modules.md — M365, AI, migratie (op afroep lezen, niet meer altijd geladen)
