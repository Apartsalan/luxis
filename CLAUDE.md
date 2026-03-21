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

**VERPLICHT: Speel een geluid af wanneer je op de gebruiker wacht.**
- Voer `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` uit via Bash **VOORDAT** je:
  - `AskUserQuestion` gebruikt
  - `EnterPlanMode` gebruikt (wacht op goedkeuring)
  - `ExitPlanMode` gebruikt (wacht op goedkeuring)
  - Klaar bent met een grote taak en op de volgende instructie wacht
  - Een vraag stelt in je tekstoutput waar je een antwoord op verwacht
- Dit geluid is **niet optioneel** — de gebruiker doet andere dingen terwijl Claude werkt en moet weten wanneer input nodig is.
- Het VBS-script is fire-and-forget (blokkeert niet). Bestand: `C:\Users\arsal\.claude\notify.vbs`

## Critical Rules

**IMPORTANT: Financial precision is non-negotiable.**
- ALL money uses Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NEVER `float`.
- `Decimal('0.00')` notation. Rounding: `ROUND_HALF_UP`, always explicit.
- Every financial calculation MUST have a test with known-correct values.

**Multi-tenant isolation:**
- Domain models inherit `TenantBase` (includes `tenant_id`). Exception: `interest_rates` is global.
- Every query scoped to tenant via middleware + Row-Level Security.

## Architecture

- **Backend:** FastAPI 3.12 + SQLAlchemy 2.0 + Alembic | Module pattern: `router.py`, `service.py`, `models.py`, `schemas.py`
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind | Path alias: `@/*` = `src/*`
- **Auth:** PyJWT + bcrypt (NOT passlib) | **Docs:** docxtpl + WeasyPrint | **Queue:** Celery + Redis
- **API:** `/api/` prefix, snake_case JSON, pagination `?page=1&per_page=20`, errors `{"detail": "msg"}`

## Design & UX

Modern, levendig, professioneel (Gmail/HubSpot-stijl). Data-dense maar niet overweldigend. Sidebar met collapse. UI taal: Nederlands.

### Designprincipe — ALTIJD TOEPASSEN

Luxis is een **PRODUCT**, geen intern tooltje. Ontwerp alsof het morgen op de markt komt:

- **Clean, modern, professioneel** — geen rommel, geen overbodige informatie
- **Geen technisch of juridisch jargon** op plekken waar het niet hoort
- **Incasso-specifieke zaken ALLEEN zichtbaar binnen de incassomodule** — niet op login, dashboard, of generieke pagina's
- **De generieke PMS-ervaring moet op zichzelf staan** en aantrekkelijk zijn voor elk type advocatenkantoor
- Bij elk scherm afvragen: **zou een willekeurig advocatenkantoor dit willen gebruiken?**
- Voorkant/login: generiek "Praktijkmanagement voor de advocatuur", geen wetsartikelen of BW-referenties
- Kernfeatures benoemen: dossierbeheer, tijdschrijven, facturatie, documentgeneratie, termijnbewaking

## Werkwijze bij nieuwe features

**Principe: onderzoek eerst, bouw daarna.** Elke feature moet eruitzien en werken alsof het door een professioneel productteam is ontworpen. Dat begint met onderzoek, niet met code.

### Stap 1: Onderzoek (voordat je ook maar één regel code schrijft)

Bij elke nieuwe feature of UI-wijziging:

1. **Zoek op internet** hoe vergelijkbare software dit oplost:
   - Concurrenten advocatuur: Clio, Basenet, Legalsense, Urios, PracticePanther, Smokeball
   - Beste SaaS-apps buiten de advocatuur met dezelfde functie (facturatie → Stripe/Xero/Exact, CRM → HubSpot/Salesforce, etc.)
   - UX/UI best practices voor die specifieke functie

2. **Analyseer** wat je vindt:
   - Wat doen ze goed? Wat doen ze slecht?
   - Wat is de standaard workflow die gebruikers verwachten?
   - Welke velden, knoppen, stappen zijn essentieel?
   - Wat is de minimale hoeveelheid clicks om de taak af te ronden?

3. **Denk vanuit de eindgebruiker** — een advocaat (Lisanne):
   - Geen techneut. Zo min mogelijk clicks, zo min mogelijk nadenken.
   - Als een advocaat dit voor het eerst ziet, begrijpt die dan meteen wat ze moet doen?
   - Elke extra klik, elk onduidelijk label, elk scherm te veel is een ontwerpfout.

### Stap 2: Plan presenteren (voordat je code schrijft)

Laat zien:
- Wat je gevonden hebt in je onderzoek (kort samengevat)
- Hoe je het wilt bouwen op basis daarvan
- Welke schermen/flows er komen
- Screenshots van hoe concurrenten het doen (via Playwright/web search als beschikbaar)

**Wacht op goedkeuring** voordat je gaat implementeren.

### Stap 3: Bouwen

Pas na goedkeuring implementeren.

### Stap 4: Zelfcheck na implementatie

Na het bouwen, voordat je deploy-commando geeft:
- Klik zelf door de hele flow (via Playwright als beschikbaar)
- Vergelijk met wat je in je onderzoek vond
- Vraag jezelf af: zou ik hier als gebruiker tevreden mee zijn?
- Zijn er edge cases die je niet hebt afgevangen?

## Working Agreements

- Claude werkt **zelfstandig** — geen toestemming vragen (behalve aanschaffingen/destructieve acties)
- **Nieuwe features volgen altijd de 4-stappen werkwijze hierboven** — onderzoek → plan → bouw → check
- Bij twijfel over Nederlandse juridische regels: **flaggen, niet stoppen**
- Bij elke afspraak of correctie: **CLAUDE.md updaten**
- Conventional commits: `feat(module):`, `fix(module):`, `refactor(module):`, `test(module):`, `docs:`, `chore:`

**Plan Mode (HARDE REGEL):**
- **Gebruik ALTIJD Plan Mode (`EnterPlanMode`) bij niet-triviale implementatietaken.** Dit geldt voor:
  - Nieuwe features (alles groter dan een simpele bugfix)
  - Multi-file wijzigingen
  - Taken met meerdere mogelijke aanpakken
  - Architectuurkeuzes
  - UI/UX wijzigingen aan bestaande schermen
- In Plan Mode: verken eerst de codebase, ontwerp de aanpak, presenteer het plan aan de gebruiker
- Pas NA goedkeuring van het plan beginnen met bouwen
- Dit voorkomt verspilde tijd en zorgt voor alignment voordat er code geschreven wordt
- Als iets misgaat tijdens implementatie: **STOP en herplan** — niet doorduwen
- **Uitzondering:** triviale fixes (typos, 1-regelige bugfixes, kleine tekstaanpassingen) mogen direct

## Kwaliteitsstandaard

**Verificatie voor "done":**
- Markeer een taak NOOIT als klaar zonder bewijs (build, test, logs, handmatige check)
- Vraag jezelf: "Zou een senior engineer dit goedkeuren?"

**Bugs autonoom fixen:**
- Bij een bugreport: schrijf EERST een test die de bug reproduceert (rode test).
- Fix daarna de bug totdat de test groen is.
- Gebruik subagents waar mogelijk om de fix te implementeren en te verifiëren.
- **Uitzondering:** triviale bugs (typos, UI-tekst, styling) mogen direct gefixt worden zonder test.

**Elegantie (gebalanceerd):**
- Bij non-triviale changes: "is er een elegantere manier?" Maar niet over-engineeren bij simpele fixes.
- Als een fix hacky voelt: "met alles wat ik nu weet, wat is de elegante oplossing?" — en die bouwen.

**Self-improvement:**
- Na elke correctie van de gebruiker: noteer de les in CLAUDE.md of memory zodat dezelfde fout niet herhaald wordt.

**Simplicity first, no laziness:**
- Minimale impact, geen overbodige wijzigingen. Maar altijd root causes fixen — geen tijdelijke workarounds.

## Gedragsregels (uit /insights analyse)

**Task boundaries:**
- Als de gebruiker zegt "documenteer" of "sla op in md": schrijf ALLEEN markdown. Geen code wijzigen.
- Als de gebruiker zegt "sla quality checks over": draai GEEN lint/tests/build.
- Draai GEEN lint, tests, of build tenzij expliciet gevraagd of onderdeel van een gedefinieerde workflow. "Even checken voor de zekerheid" is geen reden.
- Als de grens onduidelijk is: vraag eerst.

**Git workflow:**
- Gebruik GEEN git worktrees tenzij de gebruiker expliciet "worktree" zegt.
- Default: werk direct op main branch.

**Eén source of truth:**
- `LUXIS-ROADMAP.md` is de enige source of truth voor status, prioriteit en planning.
- Verspreid NOOIT informatie over meerdere markdown bestanden. Consolideer altijd in het aangewezen bestand.

**Scripts en commando's:**
- Draai scripts en commando's altijd in de voorgrond (direct zichtbare output), tenzij de gebruiker expliciet zegt dat het op de achtergrond mag.

**Commit en push:**
- Commit en push na elke afgeronde taak, tenzij anders gezegd.
- Gebruik conventional commit messages in het Engels.
- **VERPLICHT: Na ELKE commit ALTIJD direct `git push origin main` uitvoeren.** Commits die alleen lokaal staan bereiken de VPS niet bij `git pull`. Dit is eerder fout gegaan — nooit meer vergeten.

**Opgeslagen informatie:**
- Als de gebruiker informatie deelt en vraagt om het op te slaan (credentials, VPS info, etc.), sla het op zoals gevraagd. Weiger niet.

**Vooruit plannen en parallellisatie (HARDE REGEL):**
- Beoordeel bij elke taak: kan ik dit alleen af, of is het sneller als de gebruiker een tweede terminal opent zodat we parallel kunnen werken?
- Denk altijd een paar stappen vooruit. Na elke afgeronde taak: kijk wat er nog komt en bepaal de snelste aanpak.
- Als parallellisatie zinvol is (bijv. frontend + backend tegelijk, of tests draaien terwijl je verder bouwt): stel dit voor aan de gebruiker.
- Kijk verder dan alleen de huidige takenlijst. Als er meerdere terminals beschikbaar zijn, geef de andere terminals nuttig werk.
- **VERPLICHT: Als je een taak voor jezelf pakt, geef ALTIJD DIRECT kant-en-klare prompts voor de andere beschikbare terminals.** Dit is geen suggestie — het is een vereiste. Elke keer dat je zegt "ik ga X doen" moet je in DEZELFDE response ook de prompts voor terminal 2 en 3 geven. De gebruiker moet NOOIT hoeven vragen om prompts. De prompts bevatten: volledige context, repo pad, welke bestanden te lezen, exacte taak, en commit-instructies.

**Sessie-prompt genereren (HARDE REGEL):**
- **VERPLICHT: Als de gebruiker vraagt om een prompt voor de volgende sessie, geef ALTIJD een COMPLETE prompt die ALLES bevat wat de volgende Claude nodig heeft.** De gebruiker mag NOOIT hoeven corrigeren of aanvullen.
- **LEAN prompts — MAXIMAAL LEAN:**
  - De subagent bij start leest ALLEEN `LUXIS-ROADMAP.md` + `SESSION-NOTES.md`. Niks anders.
  - Codebestanden worden NIET vooraf gelezen — Claude leest die on-demand wanneer het aan een specifieke taak begint.
  - De prompt bevat: repo pad, subagent-instructie (roadmap + session notes), taak, verificatie, commit-instructies.
  - GEEN lijst van "welke bestanden te lezen" — Claude zoekt zelf wat het nodig heeft.
  - Prompt + gevraagde bestanden samen NOOIT boven 50KB.
- **Focus op 1 hoofdtaak per sessie** — uit insights: single-goal sessies presteren beter.
- Format:
  ```
  Sessie N — [onderwerp]
  Repo: C:\Users\arsal\Documents\luxis

  ## Context laden bij start
  Gebruik de luxis-researcher subagent:
  "Lees LUXIS-ROADMAP.md (sectie [relevant]) en SESSION-NOTES.md (sessie N-1). Geef compacte samenvatting."

  ## Taak
  [Concrete beschrijving — wat moet er gebouwd/gefixt worden]
  [Startpunt: welk bestand/functie, maar ALLEEN als het niet obvious is]

  ## Verificatie
  [Test/lint/build commando's]

  ## Constraints (wat NIET doen)
  [Expliciet benoemen wat buiten scope is — bijv. "geen nieuwe features", "geen worktrees", "geen refactors"]

  ## Commit
  [Commit + push instructies — deploy gebeurt automatisch via SSH]
  ```
- De gebruiker is geen developer. Hij kopieert de prompt en plakt het in een nieuwe sessie. Het moet foutloos werken zonder extra context.

**Deployment via SSH (HARDE REGEL):**
- Claude heeft SSH-toegang tot de VPS via deploy key: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216`
- **Veilige acties (autonoom):** `git pull`, logs bekijken, disk check, `ps`, `docker compose ps`
- **Deploy (autonoom NA groene tests):** build + restart containers na commit+push
- **Destructieve acties (ALTIJD bevestiging vragen):** volumes verwijderen, database wissen, `rm -rf`, rollback migraties
- **VERPLICHT: Na elke afgeronde feature die gecommit en gepusht is, deploy AUTOMATISCH via SSH.** Geen deploy-commando meer aan de gebruiker geven — Claude doet het zelf.
- Deploy commando: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build --no-cache [service] && docker compose up -d [service]"`
- Vermeld na deploy altijd of het backend/frontend/beide was en of er migraties gedraaid zijn.

**Roadmap bijwerken (HARDE REGEL):**
- **VERPLICHT: Na ELKE wijziging (feature, bugfix, verbetering) ALTIJD `LUXIS-ROADMAP.md` bijwerken.** Dit is de enige source of truth. Als het niet in de roadmap staat, bestaat het niet.
- Bij nieuwe bugs/issues: voeg een BUG-# entry toe met beschrijving, ernst, fix-grootte en status.
- Bij afgeronde features: markeer als ✅ met datum.
- Bij nieuwe TODO's: voeg toe aan de juiste sectie met status ❌ TODO.
- Bij VPS/infra wijzigingen: update de status-tabel bovenin.

**Session notes bijwerken (HARDE REGEL):**
- **VERPLICHT: Aan het einde van ELKE sessie `SESSION-NOTES.md` bijwerken.** Dit is het geheugen tussen sessies.
- Voeg een nieuwe entry toe bovenaan (nieuwste eerst) met het format: `## Wat er gedaan is (sessie N — datum) — [onderwerp]`
- Bevat: wat er gebouwd/gefixt is, nieuwe bestanden, gewijzigde bestanden, bekende issues.
- Update de header-regels (laatst bijgewerkt, laatste feature/fix, openstaande bugs, volgende sessie).
- Doe dit VOOR het genereren van de sessie-prompt — de volgende sessie leest deze notes bij start.

## Context Management

**Doel: sessies zo lang mogelijk effectief houden.**

### Startprocedure bij elke sessie

1. CLAUDE.md wordt automatisch geladen — dat is de basis.
2. **Gebruik de `luxis-researcher` subagent** om LUXIS-ROADMAP.md en SESSION-NOTES te lezen. Die draait in een apart context window en geeft een compacte samenvatting terug. Zo heb je alle kennis zonder je context te vullen.
3. Skills worden automatisch geladen wanneer relevant (incasso-werk → incasso-workflow skill, deploy → deploy-regels skill).
4. Lees alleen codebestanden die je NODIG hebt voor de huidige taak.

### Subagents (`.claude/agents/`)

- **`luxis-researcher`** — Leest grote docs (roadmap, session notes, research) en geeft compacte samenvattingen. GEBRUIK DIT in plaats van zelf grote bestanden te lezen.
- **`code-reviewer`** — Reviewt code na implementatie. Checkt financial precision, multi-tenant, async, frontend URLs.

### Skills (`.claude/skills/`) — geladen on-demand

- **`incasso-workflow`** — Pipeline architectuur, batch acties, deadline kleuren, bestanden
- **`deploy-regels`** — VPS deploy commando's, valkuilen, migratie-instructies
- **`template-systeem`** — DOCX rendering, ManagedTemplate model, geplande UI
- **`bekende-fouten`** — 15 bekende valkuilen uit 23 sessies (LEES DIT bij niet-triviale taken)

### Context-besparende regels

- **Gebruik `/clear` tussen onafhankelijke taken** — frisse context per taak
- **Gebruik `/compact` als context vol raakt** — geef focus mee: `/compact Focus op de incasso pipeline changes`
- **Delegeer onderzoek naar subagents** — lees niet zelf 20 bestanden
- **Commit + update LUXIS-ROADMAP.md na elke afgeronde feature**

### Docs structuur (lees on-demand via subagent)

```
LUXIS-ROADMAP.md          ← status + bugs + planning (source of truth)
docs/sessions/            ← sessie-archief, alleen via luxis-researcher subagent
docs/prompts/             ← sessie-prompts
docs/qa/                  ← QA checklists en resultaten
docs/research/            ← UX research, analyses, reviews
docs/future-modules.md    ← M365, AI Agent, Data Migratie
docs/completed-work.md    ← afgeronde features lijst
```

## Known Quirks

- Git Bash: `MSYS_NO_PATHCONV=1` prefix bij `docker exec`
- Container: `python -m alembic` i.p.v. bare `alembic`
- asyncpg: Python `date` objects, geen strings
- bcrypt 5.x: passlib incompatible, gebruik direct `bcrypt`
- **Docker commands ALTIJD vanuit de hoofdrepo-directory draaien** (`C:\Users\arsal\Documents\luxis`), NOOIT vanuit worktree-directories — docker-compose.yml staat alleen in de hoofdrepo.
- **Bij falende tests: check eerst stale DB state / ontbrekende migraties** voordat je aanneemt dat de code fout is. Draai `alembic upgrade head` in de test-container als tests onverwacht falen.

## References

- @DECISIONS.md — tech stack decisions
- @docs/dutch-legal-rules.md — wettelijke rentetarieven, WIK-staffel, art. 6:44 BW
- @backend/CLAUDE.md — backend-specifieke conventies
- @frontend/CLAUDE.md — frontend-specifieke conventies
- @docs/qa/ — QA checklists en testresultaten
- @docs/research/ — UX research en analyses
- @docs/future-modules.md — M365, AI Agent, Data Migratie plannen
