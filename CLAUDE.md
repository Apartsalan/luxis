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
- **Auth:** python-jose + bcrypt (NOT passlib) | **Docs:** docxtpl + WeasyPrint | **Queue:** Celery + Redis
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
- **Uitzondering:** triviale fixes (typos, 1-regelige bugfixes, kleine tekstaanpassingen) mogen direct

## Gedragsregels (uit /insights analyse)

**Documentatie vs. code:**
- Als de gebruiker zegt "documenteer" of "sla op in md": schrijf ALLEEN markdown. Geen code wijzigen.
- Als de grens onduidelijk is: vraag eerst.

**Eén source of truth:**
- `LUXIS-ROADMAP.md` is de enige source of truth voor status, prioriteit en planning.
- Verspreid NOOIT informatie over meerdere markdown bestanden. Consolideer altijd in het aangewezen bestand.

**Scripts en commando's:**
- Draai scripts en commando's altijd in de voorgrond (direct zichtbare output), tenzij de gebruiker expliciet zegt dat het op de achtergrond mag.

**Commit en push:**
- Commit en push na elke afgeronde taak, tenzij anders gezegd.
- Gebruik conventional commit messages in het Engels.

**Opgeslagen informatie:**
- Als de gebruiker informatie deelt en vraagt om het op te slaan (credentials, VPS info, etc.), sla het op zoals gevraagd. Weiger niet.

**Vooruit plannen en parallellisatie (HARDE REGEL):**
- Beoordeel bij elke taak: kan ik dit alleen af, of is het sneller als de gebruiker een tweede terminal opent zodat we parallel kunnen werken?
- Denk altijd een paar stappen vooruit. Na elke afgeronde taak: kijk wat er nog komt en bepaal de snelste aanpak.
- Als parallellisatie zinvol is (bijv. frontend + backend tegelijk, of tests draaien terwijl je verder bouwt): stel dit voor aan de gebruiker.
- Kijk verder dan alleen de huidige takenlijst. Als er meerdere terminals beschikbaar zijn, geef de andere terminals nuttig werk.
- **VERPLICHT: Als je een taak voor jezelf pakt, geef ALTIJD DIRECT kant-en-klare prompts voor de andere beschikbare terminals.** Dit is geen suggestie — het is een vereiste. Elke keer dat je zegt "ik ga X doen" moet je in DEZELFDE response ook de prompts voor terminal 2 en 3 geven. De gebruiker moet NOOIT hoeven vragen om prompts. De prompts bevatten: volledige context, repo pad, welke bestanden te lezen, exacte taak, en commit-instructies.

**Deployment:**
- Claude heeft GEEN SSH-toegang tot de VPS. Geef altijd het deploy-commando aan de gebruiker om zelf te draaien. Probeer NOOIT `ssh root@...` te runnen vanuit deze terminal.
- **VERPLICHT: Na elke afgeronde feature die gecommit en gepusht is, geef ALTIJD het deploy-commando.** Vermeld of het alleen frontend is, of frontend+backend, en of er migraties nodig zijn. De gebruiker werkt met meerdere terminals en mist anders deployments. Voorbeeld: "🚀 Deploy (frontend only, geen migraties): `cd /opt/luxis && git pull && docker compose ... build --no-cache frontend && ... up -d frontend`"

**Roadmap bijwerken (HARDE REGEL):**
- **VERPLICHT: Na ELKE wijziging (feature, bugfix, verbetering) ALTIJD `LUXIS-ROADMAP.md` bijwerken.** Dit is de enige source of truth. Als het niet in de roadmap staat, bestaat het niet.
- Bij nieuwe bugs/issues: voeg een BUG-# entry toe met beschrijving, ernst, fix-grootte en status.
- Bij afgeronde features: markeer als ✅ met datum.
- Bij nieuwe TODO's: voeg toe aan de juiste sectie met status ❌ TODO.
- Bij VPS/infra wijzigingen: update de status-tabel bovenin.

## Known Quirks

- Git Bash: `MSYS_NO_PATHCONV=1` prefix bij `docker exec`
- Container: `python -m alembic` i.p.v. bare `alembic`
- asyncpg: Python `date` objects, geen strings
- bcrypt 5.x: passlib incompatible, gebruik direct `bcrypt`

## References

- @DECISIONS.md — tech stack decisions
- @docs/dutch-legal-rules.md — wettelijke rentetarieven, WIK-staffel, art. 6:44 BW
- @backend/CLAUDE.md — backend-specifieke conventies
- @frontend/CLAUDE.md — frontend-specifieke conventies
