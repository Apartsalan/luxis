# AGENTS.md — Luxis (volledige werkwijze voor Codex/Sol)

> Dit is jouw permanente instructiebestand — Codex leest het automatisch. Het is een 1-op-1
> overname van de manier waarop Claude (Fable/Opus) altijd op Luxis heeft gewerkt. **Je houdt je
> hier ALTIJD aan**, ook als een opdracht het niet noemt. Arsalan is IT-recruiter, **geen
> developer**: leg alles uit in gewone taal, geen jargon, geen losse fragmenten.

Luxis = praktijkmanagementsysteem voor Nederlandse advocatenkantoren. Eerste klant: Kesting Legal
(1 advocaat, Lisanne, incasso/insolventie, Amsterdam). **Nederlandse UI, Engelse code.**

---

## 0. Hoe jij hier werkt (Codex ≠ Claude — lees dit eerst)

Je hebt **geen** Claude-slashcommando's, geen subagents en je kunt skills niet "aanroepen". Alles
wat bij Claude een commando/skill/subagent was, doe jij **handmatig door de bijbehorende
bestanden te lezen**. Vertaaltabel:

| Bij Claude | Wat jij doet |
|---|---|
| `/sessie-start` | Lees zelf: `SESSION-NOTES.md` (kop + bovenste entries), `LUXIS-ROADMAP.md` (🎯-sectie), `docs/ARCHITECTUUR-KAART.md`. Scan bestaande modules met glob vóór je "X ontbreekt" zegt. |
| `/sessie-einde` | Werk zelf `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` bij + git-tag. Regels in §6. |
| `luxis-researcher` / subagents | Lees de docs zelf (of je eigen sub-runs). |
| Skill "X" aanroepen | **Lees** `.agents/skills/X/SKILL.md` als naslag (zie §5). |
| `/premortem` | Schrijf zelf 3 faalredenen + waarom-toch bij niet-triviale plannen. |
| `/effort max` | Jij schakelt tussen Sol **Ultra** (uitzoekwerk) en Sol **High** (bouwwerk) — zie de taakprompt. |
| Geluid via `notify.vbs` | Optioneel; niet nodig. |

**Nieuwe lessen/feedback van Arsalan sla je hier op** (§4: voeg een regel toe aan "Geleerde
lessen"), zodat de werkwijze net als bij Claude meegroeit. Dat is jouw "memory".

---

## 1. Twee gedragsmodi die ALTIJD aanstaan

### Ponytail (lui = efficiënt, niet slordig)
De beste code is code die je niet schrijft. Vóór je iets bouwt, loop de ladder af en stop bij de
eerste tree die houdt: (1) moet dit überhaupt bestaan? speculatief = overslaan; (2) bestaat het al
in deze codebase? hergebruik; (3) doet de stdlib het? (4) native platform-feature? (5) een al
geïnstalleerde dependency? (6) kan het één regel zijn? (7) pas dán: minimale code die werkt. Geen
ongevraagde abstracties, geen scaffolding "voor later", verwijderen boven toevoegen. **Maar:** de
ladder verkort de oplossing, nooit het begrip — lees eerst de hele flow die je raakt, fix bij de
root (grep alle callers), pas dán lui. Nooit lui over: input-validatie op vertrouwensgrenzen,
foutafhandeling die dataverlies voorkomt, security, of iets dat expliciet gevraagd is. Niet-triviale
logica laat één runbare check achter (kleine `assert`/test).

### Fable-discipline (meet, weerleg, hek af, rond af)
- **Diepte:** bij onderzoek/audit/debug — meet in de bron, kwantificeer, ga één stap dieper. Nooit
  redeneren vanaf notities als je het kunt meten (SQL op prod, code-regel, log).
- **Tegenspreker:** na elk plan/fix/conclusie en vóór elke prod-schrijfactie — probeer jezelf te
  weerleggen. Wat zou dit onwaar maken?
- **Scope-hek:** vóór elke schrijfactie — wijs de zin in de opdracht aan die dit vraagt. Extra's =
  voorstel, niet doen.
- **Afronding:** vóór "klaar" — bewijs-audit per claim; rapporteer alleen wat je met een resultaat
  uit déze sessie kunt bewijzen. **"Niet geverifieerd" is een geldig en verplicht label.**
- **Kern:** handel als je genoeg weet; heropen geen genomen besluiten; bij een keuze geef één
  aanbeveling, geen catalogus. Eindig een beurt nooit op een belofte/plan — doe het werk eerst, of
  benoem de blokkade die alleen Arsalan kan opheffen.

---

## 2. Kritieke projectregels (HARD)

- **Geld = Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NOOIT float.** `ROUND_HALF_UP` expliciet.
  Elke geldberekening krijgt een test met bekend-correcte waarden uit de juridische bron.
- **Multi-tenant:** modellen erven `TenantBase` (heeft `tenant_id`). Uitzondering: `interest_rates`
  is globaal. **Elke query filtert óók zelf op `tenant_id`** — vertrouw niet alleen op RLS/middleware.
- **Security (audit S183 — gelden ALTIJD):**
  - Nieuwe tabel met `tenant_id` → RLS in **dezelfde** migratie: `apply_rls(op.get_bind())`. Vergeet
    je het, dan faalt de opstartcontrole (`app.main.lifespan`) + drift-guard-test de deploy.
    Uitzondering: `users` (`app/security/rls.py`).
  - Nieuwe route → auth verplicht: `Depends(get_current_user)` of `require_role(...)`. Publiek
    (login/OAuth) = expliciet + rate-limit.
  - Na een `db.commit()` binnen één request worden tenant+rol her-toegepast (`after_begin`-event) —
    filter tóch altijd zelf op `tenant_id`.
  - Nooit secrets in code — alleen uit env (`app/config.py`). OAuth-tokens versleuteld. Geen
    `NEXT_PUBLIC_*` met secrets (alle AI/externe calls lopen server-side).
  - Uploads alleen via de bestaande gevalideerde helpers (extensie-whitelist + grootte-cap +
    magic-byte-check).
  - Rollen-matrix: `docs/security/rollen.md`.

---

## 3. Toegang & omgeving (geverifieerd 12 juli 2026 — jij kunt dit)

Je draait op Arsalans Windows-machine in `C:\Users\arsal\Documents\luxis`. Je hebt shell-toegang,
dus git/docker/ssh werken. **Verifieer toegang één keer aan het begin** met een onschuldige check
voordat je erop leunt.

### Git (commit + push werkt)
- Remote: `origin https://github.com/Apartsalan/luxis.git` (fetch+push). Identity: `Arsalan
  <arsalanseidony@gmail.com>`.
- **Na ELKE afgeronde taak: `git commit` + `git push origin main`.** Conventional commits:
  `feat(module):`, `fix(module):`, `docs:`, `refactor(module):`, etc. Klein committen, niet één berg.
- Verifieer bij twijfel: `git remote -v` en `git push` (de laatste push slaagde).
- Commit alleen wat bij je taak hoort. Losse bestanden in de repo-root (PDF's, bank-CSV,
  Word-lockbestanden `~$…`) NIET meecommitten.

### Server / SSH / deploy (VPS)
- Host: `root@46.225.115.216`, key: `~/.ssh/luxis_deploy` (passphrase-vrij, ligt op de machine).
  Prod-URL: `https://luxis.kestinglegal.nl`. App-pad op VPS: `/opt/luxis`.
- Verifieer toegang: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "echo ok"`.
- **Read-only prod-query (voor uitzoekwerk):**
  `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose exec -T db psql -U luxis -d luxis -c \"<SELECT ...>\""`
- **Deploy na commit+push** (autonoom, Claude deed dit ook zelf):
  - Backend: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend && docker compose up -d backend && docker image prune -f"`
  - Backend + migratie: idem, met `&& docker compose run --rm backend python -m alembic upgrade head` **ná** de build, vóór `up -d`. **Volgorde cruciaal: eerst build, dán migreren.**
  - Frontend: vervang `backend` door `frontend`.
  - Verifieer: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose ps && docker compose logs backend --tail 5"`
  - **Geen `--no-cache`** standaard (vreet VPS-schijf); wel na `pyproject.toml`/`package-lock.json`-wijziging.
- **Destructief (volumes/DB wissen, migraties terugdraaien, `rm -rf`, rollback): NOOIT zonder
  expliciete toestemming van Arsalan.** Read-only/logs/ps/deploy-na-groene-tests mag autonoom.

### Dev-commando's
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up   # dev, hot reload
docker compose exec backend pytest tests/ -v                        # tests (of -k "keyword" gericht)
docker compose exec backend ruff check app/                         # lint
docker compose exec backend python -m alembic upgrade head          # migraties
cd frontend && npm run build                                        # frontend build / npx tsc --noEmit
```

---

## 4. Geleerde lessen & feedback van Arsalan (staande regels — vul aan)

Dit is de overgenomen "memory". Elke nieuwe correctie van Arsalan zet je hier bij als regel.

- **Test-recipient (KRITIEK):** bij ELKE e-mailtest recipient ALTIJD overschrijven naar
  `arsalanir@hotmail.com`. NOOIT klanten/wederpartij/`lisanne@`.
- **Mailslot NIET aanzetten:** `app_config.outbound_mail_locked` staat bewust op `true`. Arsalan
  zet het zelf aan. Ontvangen/sync werkt altijd door.
- **Geen destructieve DB-acties** zonder toestemming (volumes/DB, incident 2026-03-30).
- **Parallelle terminals:** nooit committen/pushen vóór alle terminals klaar zijn (data-loss sessie 70).
  Bij parallelle sessies: eigen entry toevoegen bij merge-conflict, niets weggooien; `git pull` vlak
  vóór de afsluiting.
- **Bij twijfel ALTIJD eerst vragen of onderzoeken**, niet gokken.
- **Onderzoek (juridisch, concurrenten, best practices) doe JIJ zelf**, delegeer het nooit naar Arsalan.
- **Kritisch zijn** bij ideeën/tools/voorstellen — geen ja-knikker.
- **Elk bestand naar wederpartij/cliënt = PDF**, nooit DOCX of bewerkbaar formaat.
- **UI-benamingen:** gebruik de letterlijke teksten uit de frontend, nooit synoniemen/parafrases.
- **Kwaliteit output:** professioneel advocatenkantoor-niveau — geen dubbele symbolen, nette tabellen.
- **"Grondig checken" = ook visueel + functioneel in de browser**, niet alleen tests + tsc/build.
- **AI-resultaten prominent** tonen, techniek onzichtbaar; output in-your-face, niet verstopt.
- **Agent-autonomie:** pipeline op schema = auto OK; reactie op inkomende e-mail = ALTIJD Lisanne beslist.
- **UI schoonhouden:** bij een nieuwe feature de legacy-UI verbergen, geen parallelle systemen naast elkaar.
- **Gewone taal, geen "caveman"/fragmenten** — Arsalan is geen developer.
- **Login:** `seidony@kestinglegal.nl` (NIET `lisanne@`).
- **Kesting-specifieke kennis hoort in data** (DB/ContactTerms), niet in code.

---

## 5. Skills = naslag om te LEZEN (in `.agents/skills/<naam>/SKILL.md`)

Je roept ze niet aan; je **leest** ze wanneer relevant:
- **deploy-regels** — VPS-deploy, disk-pressure, valkuilen (de deploy-commando's in §3 komen hiervandaan).
- **bekende-fouten** — valkuilen uit 30+ sessies. **Lees bij elke niet-triviale taak.**
- **incasso-workflow** — pipeline (21 stappen), batch, deadlines.
- **template-systeem** — DOCX-rendering, ManagedTemplate, de 4 sjabloon-opslagplaatsen.
- **premortem** — hoe je een strategische premortem draait (positionering/pricing/architectuur).
- **systematic-debugging / verification-before-completion / receiving-code-review** — werkhouding
  bij debuggen, afronden en het verwerken van review-feedback.
- **impeccable / frontend-design / brand-guidelines / canvas-design / deep-research** — design- en
  onderzoeksnaslag; gebruik bij UI-werk of groot onderzoek.

De incasso-domeinregels staan ook in `docs/dutch-legal-rules.md` (wettelijke rente, WIK-staffel,
art. 6:44 BW, 14-dagenbrief) en de officiële workflow in `docs/lisanne-incasso-workflow.md`.

**Volledige skill-set:** alle 13 project-skills staan in `.agents/skills/` (bekende-fouten,
brand-guidelines, canvas-design, deep-research, deploy-regels, frontend-design, impeccable,
incasso-workflow, premortem, receiving-code-review, systematic-debugging, template-systeem,
verification-before-completion) — lees de betreffende `SKILL.md` wanneer relevant. De
**gedrags**-skills (Ponytail-luiheid + de fable-discipline) zijn geen bestanden die je aanroept;
hun kern staat in §1 en staat dus altijd aan. Arsalans globale skill-bibliotheek
(`~/.claude/skills/`: ads-*, seo-*, recruitment, copywriting…) is voor **andere projecten** —
negeer die, ze horen niet bij Luxis.

### MCP-servers (Codex heeft zijn eigen set — niet Claude's)
MCP's zijn tool-koppelingen per client; ze gaan **niet** automatisch 1-op-1 van Claude naar Codex.
- **Codex heeft al geconfigureerd** (`.codex/config.toml`) en jij mag gebruiken:
  `context7` (actuele library-/framework-docs — gebruik bij twijfel over een API i.p.v. gokken),
  `tavily` (web-onderzoek — voor concurrenten/best-practices in stap 1), `claude-context` +
  `codebase-memory` (semantisch zoeken door de repo), `stitch` (design), `youtube-transcript`.
- **Werken NIET in Codex** (hangen aan claude.ai-login): Gmail, Google Calendar/Drive,
  claude.ai-Supabase, claude-in-chrome, telegram, playwright. Heb je een browser/mail nodig, doe
  het handmatig of vraag Arsalan.
- **Voor de vier fasen (mailpad-audit, facturatie, voorkant-fixes, security-fixes) is geen enkele
  MCP strikt nodig** — code lezen + prod-SQL + git + deploy volstaat. Wil Arsalan een specifieke
  MCP erbij, dan is dat een `.codex/config.toml`-instelklus, los van het huidige werk.

---

## 6. Werkwijze, sessie-start/einde, kwaliteit

### Nieuwe feature = 4 stappen (Onderzoek eerst, bouw daarna)
1. **Onderzoek:** hoe lossen concurrenten (Clio, BaseNet, Legalsense, Urios, PracticePanther,
   Smokeball) + beste SaaS dit op? Standaard-workflow, essentiële velden, minimale clicks. Denk
   vanuit Lisanne.
2. **Plan presenteren** + wacht op goedkeuring. Bij elk niet-triviaal plan: premortem (3 faalredenen
   + waarom-toch). Triviale fixes mogen direct.
3. **Bouwen** na goedkeuring.
4. **Verificatie-loop:** build (`tsc --noEmit`/`pytest`) → visueel → functioneel doorklikken. Pas
   "done" als alle drie groen. NOOIT doorgaan met een kapotte taak.

### Bugs
Eerst een rode test → fix → groen. Triviale bugs direct. Fix chirurgisch (alleen de kapotte zaak,
root cause, geen workarounds; nooit features/security breed terugdraaien voor één symptoom).

### Sessie-start (handmatig)
Lees `SESSION-NOTES.md` (kop + bovenste entries) + `LUXIS-ROADMAP.md` (🎯-sectie) +
`docs/ARCHITECTUUR-KAART.md`. Scan modules met glob (`frontend/src/app/(dashboard)/**/page.tsx`,
`backend/app/*/router.py`) vóór je "X ontbreekt" concludeert — nooit gokken over wat bestaat.

### Sessie-einde (handmatig)
- **SESSION-NOTES.md:** nieuwe entry bovenaan (Samenvatting / Gewijzigde bestanden / Bekende issues /
  Volgende sessie) + de 4 kopregels bijwerken (kort, max 1-2 zinnen). **Max 10 entries** — de oudste
  verbatim naar `docs/archief/SESSION-ARCHIVE.md` (verplaatsen, nooit weggooien).
- **LUXIS-ROADMAP.md:** precies één "🎯 Huidige prioriteit"-sectie + één "Laatst bijgewerkt"-regel.
  Afgerond → ✅ met datum; nieuwe bugs → BUG-#. Afgeronde sprints → `docs/archief/ROADMAP-ARCHIEF.md`.
- Git-tag `sessie-N`. Commit + push.
- Volgende-sessie-prompt LEAN (<50KB), 1 hoofdtaak, verwijs naar docs i.p.v. inline.

### Kwaliteitsstandaard
Nooit "done" zonder bewijs. "Migration completed" is fout als records geskipt zijn; "tests pass" is
fout als tests geskipt zijn. Onzekerheid tonen, niet verbergen. Elegantie overwegen bij niet-triviale
changes, niet over-engineeren. Conflicterende patronen niet middelen — kies één (recentste/meest
getest), licht toe, flag de andere.

### Gedragsregels
- "Documenteer/sla op in md" = ALLEEN markdown, geen code. "Sla checks over" = geen lint/tests/build.
- Geen lint/tests/build tenzij gevraagd of in de workflow. Geen git worktrees tenzij Arsalan "worktree" zegt.
- Scripts/commando's altijd in de voorgrond. Juridische twijfel: flaggen, niet stoppen.
- `LUXIS-ROADMAP.md` = enige source of truth.

---

## 7. Architectuur & bekende valkuilen

- **Backend:** FastAPI 3.12 + SQLAlchemy 2.0 + Alembic. Module = `router.py` (endpoints) →
  `service.py` (logica, geen HTTP) → `models.py` → `schemas.py`. Async overal (`AsyncSession`,
  `async def`, `await`). Auth: PyJWT + **bcrypt (NIET passlib)**.
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind + TanStack Query. `@/*` =
  `src/*`. UI-tekst Nederlands. `null` vs `undefined`: nooit `|| undefined` → `|| null` wijzigen.
- **API:** `/api/`-prefix, snake_case JSON, paginatie `?page=1&per_page=20`, errors `{"detail": "msg"}`.
  Geld serialiseert als **string** (frontend: `Number()`).
- **Design:** modern, data-dense, professioneel (Gmail/HubSpot). Luxis is een **product** —
  incasso-jargon alleen in de incassomodule; bij elk scherm: "zou een willekeurig advocatenkantoor
  dit willen?".
- **Prod = image-baked (S170):** code wijzigen ⇒ rebuild (git pull alleen ververst code NIET). Alleen
  `templates/` is live gemount.
- **Quirks:** Git Bash `MSYS_NO_PATHCONV=1` vóór `docker exec`; container `python -m alembic` (niet
  bare); asyncpg wil Python `date`-objecten (geen strings); docker-commando's altijd vanuit de
  hoofdrepo; falende tests → check eerst stale DB / ontbrekende migraties; RLS is FORCE +
  `SET LOCAL ROLE luxis_app` (alles tenant-scoped behalve `interest_rates`).

## 8. Referenties
`DECISIONS.md` (tech stack) · `backend/CLAUDE.md` + `frontend/CLAUDE.md` (module-detail — óók geldig
voor jou) · `docs/dutch-legal-rules.md` · `docs/qa/` (QA-checklists) · `docs/research/` (UX) ·
`docs/future-modules.md` (M365, AI-agent, migratie) · `docs/ARCHITECTUUR-KAART.md` (verbindingskaart).
