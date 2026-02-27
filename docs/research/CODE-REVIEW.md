# Luxis — Code Review

**Datum:** 19 februari 2026
**Reviewer:** Claude Code (Opus 4.6)
**Scope:** Volledige codebase — backend, frontend, infra, tests, CI/CD
**Repo:** https://github.com/Apartsalan/luxis.git (branch: main)

---

## Eindoordeel

| Categorie | Score | Toelichting |
|-----------|-------|-------------|
| **Architectuur** | 9/10 | Schone module-opzet, consistente patronen, multi-tenant ready |
| **Financiele correctheid** | 9.5/10 | Decimal door de hele stack, uitvoerig getest |
| **Security** | 8/10 | JWT + bcrypt + RLS-ready, 1 verbeterpunt (tenant middleware) |
| **Testing** | 9/10 | 5.000+ regels tests, financiele edge cases uitstekend gedekt |
| **Frontend** | 7/10 | Functioneel maar ~40% af, UX-polish nodig |
| **Infra/DevOps** | 8.5/10 | Docker Compose + CI pipeline solide, productie-ready |
| **Documentatie** | 9/10 | CLAUDE.md, DECISIONS.md, code comments — bovengemiddeld |
| **Totaal** | **8.6/10** | Productie-klaar voor Kesting Legal MVP |

---

## 1. Backend Architectuur

### 1.1 Module-structuur: UITSTEKEND

13 modules, allemaal volgens hetzelfde patroon:

```
module/
  router.py    → FastAPI endpoints (HTTP-laag)
  service.py   → Business logic (testbaar zonder HTTP)
  models.py    → SQLAlchemy ORM modellen
  schemas.py   → Pydantic request/response validatie
```

**Sterke punten:**
- Strikte scheiding HTTP ↔ business logic ↔ data
- Service-functies zijn unit-testbaar
- Elk bestand heeft een duidelijk afgebakende verantwoordelijkheid
- Consistent naming: Dutch UI labels, English code

**Modules overzicht:**

| Module | Regels | Doel | Kwaliteit |
|--------|--------|------|-----------|
| `auth` | ~200 | JWT + password | Solide |
| `relations` | ~220 | Contacten CRUD + KYC | Solide |
| `cases` | ~430 | Zaakbeheer + activities | Solide |
| `collections` | ~505 | Incasso (financieel hart) | Excellent |
| `documents` | ~405 | Document generatie | Solide |
| `invoices` | ~530 | Facturatie + onkosten | Solide |
| `time_entries` | ~190 | Tijdschrijven | Solide |
| `workflow` | ~820 | Status engine + taken | Goed (complex, maar leesbaar) |
| `dashboard` | ~170 | KPI's + samenvatting | Solide |
| `settings` | ~50 | Tenant config | Minimaal |
| `email` | ~195 | SMTP templates | Skeleton |
| `shared` | ~720 | Base models, paginatie, exceptions | Solide |
| `middleware` | ~50 | Tenant context + logging | Functioneel |

### 1.2 Entrypoint (`main.py`): GOED

93 regels, schoon en overzichtelijk:

- Health check endpoint
- Sentry integratie (optioneel via `SENTRY_DSN`)
- `send_default_pii=False` — geen PII naar Sentry
- CORS correct geconfigureerd (via comma-separated origins in `.env`)
- 13 routers geregistreerd
- Workflow scheduler met async lifespan
- Swagger docs alleen in non-production (`/docs` disabled in prod)

### 1.3 Database (`database.py`): GOED

51 regels, solide fundament:

- `create_async_engine` met `pool_pre_ping=True` (connection validation)
- `expire_on_commit=False` (voorkomt lazy-loading issues na commit)
- `TimestampMixin` met `server_default=func.now()` (DB-generated timestamps)
- Correcte session lifecycle: commit, rollback on error, close in finally

### 1.4 Configuratie (`config.py`): GOED

37 regels met `pydantic-settings`:

- Alle secrets via `.env` (niet hardcoded)
- Sensible defaults voor development
- `model_config = {"env_file": ".env", "extra": "ignore"}` — ignoreert onbekende env vars

**Verbeterpunt:** `secret_key` default is `"change-this-to-a-random-string-in-production"` — dit is goed als reminder, maar een CI-check dat de productie-key niet deze default is zou een extra safeguard zijn.

---

## 2. Financiele Correctheid

### 2.1 Decimal door de hele stack: EXCELLENT

**Backend (Python):**
- Alle financiele velden: `Decimal` type, nergens `float`
- `NUMERIC(15, 2)` in PostgreSQL via SQLAlchemy `mapped_column(Numeric(15, 2))`
- `ROUND_HALF_UP` consequent in berekeningen
- CI-check: `grep -rn "float(" backend/app/collections/` faalt de build

**Frontend (TypeScript):**
- `Intl.NumberFormat('nl-NL')` voor valuta-weergave
- Bedragen komen als strings uit de API (Pydantic serialiseert Decimal correct)

### 2.2 Renteberekening (`interest.py`): WISKUNDIG CORRECT

339 regels, de kern van het incasso-systeem. Volledig geverifieerd in `INCASSO-VERIFICATIE.md` (score: 9.5/10).

**Wat klopt:**
- Samengestelde rente per art. 6:119 BW met jaarlijkse kapitalisatie
- Kapitalisatiejaar loopt vanaf verzuimdatum, NIET vanaf 1 januari
- Tariefwisselingen worden correct gesplitst in sub-perioden
- Pro-rata: `dagen/365` consistent (ook in schrikkeljaren)
- `_add_years(date(2024,2,29), 1)` → `date(2025,2,28)` (niet 1 maart)
- Afronding per sub-periode, daarna sommering

**Ondersteunde types:**
- `statutory` → art. 6:119 BW (compound)
- `commercial` → art. 6:119a BW (compound)
- `government` → art. 6:119b BW (compound)
- `contractual` → enkelvoudig OF samengesteld (configureerbaar)

### 2.3 WIK-staffel (`wik.py`): PERFECT

122 regels, implementeert art. 6:96 BW exact:

| Schijf | Percentage |
|--------|-----------|
| Eerste 2.500 | 15% |
| Volgende 2.500 | 10% |
| Volgende 5.000 | 5% |
| Volgende 190.000 | 1% |
| Meerdere | 0,5% |

- Minimum: 40,00
- Maximum: 6.775,00
- BTW: 21% apart berekend
- Score in verificatie: 10/10

### 2.4 Art. 6:44 BW Imputatie (`payment_distribution.py`): CORRECT

Betalingen worden correct verdeeld: kosten → rente → hoofdsom.

Score in verificatie: 10/10.

### 2.5 Service-laag (`collections/service.py`): GOED

505 regels. De `create_payment()` functie integreert alles:
1. Berekent openstaande bedragen (claims + rente + BIK)
2. Trekt eerder gealloceerde bedragen af
3. Verdeelt nieuwe betaling per art. 6:44 BW
4. Slaat allocatie op per payment record
5. Triggert workflow hook voor auto-transitie naar 'betaald'

**Let op:** De `INCASSO-VERIFICATIE.md` rapporteerde eerder een bug waar `distribute_payment()` niet werd aangeroepen. Dit is inmiddels verholpen — de service-laag roept `distribute_payment()` correct aan in `create_payment()` (regels 196-201).

---

## 3. Security

### 3.1 Authenticatie: GOED

**JWT-implementatie:**
- Access token: 15 minuten expiry (configureerbaar)
- Refresh token: 7 dagen (configureerbaar)
- Algorithm: HS256
- `tenant_id` in JWT payload (multi-tenant isolation)
- Token type validatie (`"access"` vs `"refresh"`)

**Password hashing:**
- bcrypt (niet passlib — passlib 1.7.4+ is incompatibel met bcrypt 5.x)
- Automatische salt via `bcrypt.gensalt()`

### 3.2 Autorisatie: GOED

`require_role()` factory in `dependencies.py`:
- Rollen: `admin`, `advocaat`, `medewerker`
- Decorator-patroon: `dependencies=[Depends(require_role("admin"))]`
- Duidelijke foutmelding bij onvoldoende rechten

### 3.3 Multi-tenant isolatie: GOED MET 1 VERBETERPUNT

**Drie lagen bescherming:**
1. Application layer: elke query filtert op `tenant_id`
2. JWT layer: `tenant_id` zit in het token
3. Database layer: PostgreSQL sessie-variabele voor RLS

**VERBETERPUNT — SQL string formatting:**

In `middleware/tenant.py`:
```python
await db.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
```

Dit is technisch een SQL injection vector. Het risico is **laag** omdat `tenant_id` een UUID is die uit het JWT komt (en dus gevalideerd), maar de best practice is:

```python
await db.execute(text("SET app.current_tenant = :tid"), {"tid": str(tenant_id)})
```

Of met PostgreSQL's `set_config()`:
```python
await db.execute(text("SELECT set_config('app.current_tenant', :tid, true)"), {"tid": str(tenant_id)})
```

**Ernst:** Laag (UUID-validatie voorkomt misbruik), maar fix is eenvoudig en elimineert de categorie volledig.

### 3.4 CORS: CORRECT

```python
allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()]
```

Geen wildcard `*`, origins configureerbaar per environment.

### 3.5 CI Security Checks: GOED

- Check op `.env` bestanden in de repo
- Check op `float()` in financiele code

**Suggestie:** Voeg toe:
- Check dat `SECRET_KEY` niet de default value is in productie-config
- Dependency scanning (bijv. `pip-audit` of `safety`)

---

## 4. Testing

### 4.1 Overzicht: UITSTEKEND

13 testbestanden, 5.000+ regels:

| Testbestand | Regels | Focus |
|-------------|--------|-------|
| `conftest.py` | 137 | Fixtures: DB, client, tenant, user |
| `test_interest.py` | 409 | Basis renteberekeningen |
| `test_interest_edge_cases.py` | 558 | Schrikkeljaren, tariefwisselingen |
| `test_payment_distribution.py` | 160 | Art. 6:44 BW basisverdeling |
| `test_payment_distribution_extended.py` | 522 | Meerdere claims, complexe scenario's |
| `test_payment_allocation.py` | 289 | Volledige betalingsflow |
| `test_wik.py` | 142 | WIK-staffel basis |
| `test_wik_edge_cases.py` | 359 | Min/max grenzen, BTW |
| `test_auth.py` | 102 | JWT, wachtwoord, token refresh |
| `test_relations.py` | 459 | Contact CRUD, tenant-isolatie |
| `test_cases.py` | 410 | Zaakbeheer, workflow transities |
| `test_documents.py` | 752 | Document generatie (Word/PDF) |
| `test_dashboard.py` | 158 | Dashboard KPI's |
| `test_integration_api.py` | 668 | End-to-end API flows |

### 4.2 Test-infrastructuur: GOED

- Async test database met `pytest-asyncio`
- Schema wordt per test aangemaakt en opgeruimd
- Fixtures voor tenant, user, contacts, auth headers
- CI draait met echte PostgreSQL 16 + Redis 7

### 4.3 Financiele edge cases: UITSTEKEND

Geteste scenario's:
- 0 dagen rente
- 1 dag rente
- Exact 1 jaar (compound = simple)
- 1 jaar + 1 dag (eerste kapitalisatie + 1 dag)
- 2, 3, 10 jaar samengestelde rente
- Schrikkeljaar (29 feb + 1 jaar = 28 feb)
- Tariefwissel halverwege periode
- Meerdere tariefwisselingen in 1 jaar
- WIK minimum (40) en maximum (6.775)
- Negatieve hoofdsom (wiskundig correct: negatieve rente)
- Nul hoofdsom

### 4.4 Wat ontbreekt (suggesties)

- **Performance tests:** Geen load testing. Voor Kesting Legal (1 gebruiker) niet urgent, maar voor multi-tenant later wel.
- **Frontend tests:** Geen automatische frontend tests (geen Vitest/Jest/Playwright). Handmatig testen is nu acceptabel, maar bij groei risicovol.

---

## 5. Frontend

### 5.1 Architectuur: GOED

- Next.js 15 met App Router (file-based routing)
- React 19
- shadcn/ui + Tailwind CSS (consistent design system)
- TanStack Query voor data fetching
- React Hook Form + Zod voor formulieren

### 5.2 API Client (`lib/api.ts`): GOED

65 regels, doet precies wat het moet:
- JWT token automatisch meegestuurd
- Bij 401: refresh token proberen, retry
- Bij refresh failure: redirect naar `/login`
- `Content-Type: application/json` standaard

### 5.3 State Management: GOED

- **Auth:** `AuthContext` via `use-auth.ts` (React Context)
- **Timer:** `TimerContext` via `use-timer.ts` (localStorage persistent)
- **Data:** TanStack Query voor server state (17 hooks)
- **Forms:** React Hook Form met Zod validatie

Patroon per hook:
```typescript
export function useCases() {
  return useQuery({
    queryKey: ["cases"],
    queryFn: async () => {
      const res = await api("/api/cases");
      if (!res.ok) throw new Error("...");
      return res.json();
    },
  });
}
```

Consistent door alle 17 hooks.

### 5.4 Providers (`providers.tsx`): GOED

Nette provider-hiërarchie:
```
QueryClientProvider
  └─ AuthProvider
       └─ TimerProvider
            ├─ {children}
            ├─ CommandPalette
            ├─ FloatingTimer
            └─ Toaster
```

Globale componenten (CommandPalette, FloatingTimer) worden correct buiten de page tree gerenderd.

### 5.5 Pagina's (18 stuks)

| Pagina | Status |
|--------|--------|
| Login | Werkend |
| Dashboard | Basis (verbetering gepland: C1) |
| Relaties lijst/detail/nieuw | Werkend |
| Zaken lijst/detail/nieuw | Werkend, met 9-tab interface |
| Uren | Werkend, met globale timer |
| Facturen lijst/detail/nieuw | Werkend |
| Incasso | Werkend |
| Agenda | Basis kalender |
| Documenten | Template catalogus |
| Instellingen | Kantoorgegevens |

### 5.6 Gebouwd maar nog niet in roadmap

- **Command Palette (Ctrl+K):** Zoeken + quick actions
- **Floating Timer:** Persistent, globale context, rechtsonder
- **9-tab zaakdetail:** Overzicht, Taken, Vorderingen, Betalingen, Financieel, Derdengelden, Documenten, Activiteiten, Partijen

### 5.7 Verbeterpunten frontend

| # | Issue | Ernst | Waar |
|---|-------|-------|------|
| F1 | Geen automatische tests | Midden | Heel frontend |
| F2 | Geen error boundaries per page | Laag | App-level error.tsx bestaat wel |
| F3 | Loading states inconsistent | Laag | Sommige pagina's spinners, andere skeletons |
| F4 | Empty states ontbreken | Laag | Lege lijsten tonen niks |
| F5 | Breadcrumbs inconsistent | Laag | Niet overal aanwezig |

---

## 6. Infrastructure & DevOps

### 6.1 Docker Compose: GOED

3 compose bestanden:
- `docker-compose.yml` — basis services (db, redis, backend, frontend)
- `docker-compose.dev.yml` — development overrides (hot reload, volume mounts)
- `docker-compose.prod.yml` — production (geen debug, optimized builds)

Services:
- PostgreSQL 16 Alpine (met healthcheck)
- Redis 7 Alpine (met healthcheck)
- Backend (FastAPI + uvicorn)
- Frontend (Next.js)

### 6.2 CI/CD Pipeline: GOED

GitHub Actions met 5 jobs:

1. **Backend Lint** — Ruff check + format
2. **Backend Tests** — pytest met echte PostgreSQL + Redis
3. **Frontend Lint** — ESLint
4. **Frontend Build** — `npm run build`
5. **Security Checks** — .env bestanden + float in financiele code

Alles draait op push naar `main` en pull requests.

**Sterk:** `uv` als Python package manager (sneller dan pip/poetry).

### 6.3 Deployment: FUNCTIONEEL

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d frontend backend
```

**Suggesties:**
- Voeg `alembic upgrade head` toe aan het deploy-script (database migraties)
- Overweeg een health-check na deployment (`curl https://luxis.kestinglegal.nl/health`)
- Blue-green deployment is overkill voor 1 gebruiker, maar `--remove-orphans` is handig

### 6.4 Hosting plan: REDELIJK

- Hetzner VPS CX33: 4 vCPU, 8GB RAM, 80GB NVMe — 5,49/mnd
- SSL via Let's Encrypt + Nginx
- Backups naar Hetzner Storage Box
- Sentry voor error tracking (~26/mnd)
- Totaal: ~35/mnd

---

## 7. Documentatie

### 7.1 Overzicht

| Document | Kwaliteit | Doel |
|----------|-----------|------|
| `CLAUDE.md` (root) | Excellent | AI development guide, architectuurregels |
| `backend/CLAUDE.md` | Goed | Backend conventies |
| `frontend/CLAUDE.md` | Goed | Frontend conventies |
| `DECISIONS.md` | Excellent | Tech stack onderbouwing (553 regels!) |
| `LUXIS-ROADMAP.md` | Excellent | Centrale roadmap, prioriteiten, status |
| `FEATURE-INVENTORY.md` | Goed | Complete featurelijst |
| `UX-REVIEW.md` | Goed | Kritische UX analyse |
| `UX-VERBETERPLAN.md` | Goed | Geprioriteerde werklijst |
| `INCASSO-VERIFICATIE.md` | Excellent | Wiskundige verificatie van alle berekeningen |
| Code comments | Goed | Vooral in `interest.py` en `wik.py` |

### 7.2 Sterk punt: CLAUDE.md systeem

Het project gebruikt een gelaagd `CLAUDE.md`-systeem:
- Root: projectbrede regels en architectuur
- Backend: Python conventies, Decimal regel, module-patroon
- Frontend: Next.js conventies, hook-patronen, shadcn/ui regels

Dit maakt het mogelijk voor AI (of nieuwe developers) om consistent code te produceren.

---

## 8. Bevindingen & Aanbevelingen

### Kritiek (moet gefixt)

| # | Bevinding | Ernst | Locatie | Fix |
|---|-----------|-------|---------|-----|
| K1 | SQL string formatting in tenant middleware | Laag-Midden | `middleware/tenant.py:16` | Gebruik parameterized query |

### Aanbevelingen (zou moeten)

| # | Bevinding | Ernst | Toelichting |
|---|-----------|-------|-------------|
| A1 | Secret key default check in CI | Laag | Voorkom dat default key in productie draait |
| A2 | Dependency scanning | Laag | `pip-audit` of `safety` in CI pipeline |
| A3 | `alembic upgrade head` in deploy script | Midden | Voorkomt vergeten migraties |
| A4 | Health check na deployment | Laag | `curl /health` als validatie |
| A5 | Frontend error boundaries per section | Laag | Nu alleen app-level |
| A6 | Rate limiting op auth endpoints | Midden | Voorkomt brute force |

### Nice-to-have (toekomst)

| # | Bevinding | Toelichting |
|---|-----------|-------------|
| N1 | Audit logging tabel | Wie deed wat wanneer (GDPR, tuchtrecht) |
| N2 | Frontend test suite | Vitest + Playwright voor kritieke flows |
| N3 | Database connection pooling tuning | `pool_size`, `max_overflow` configureerbaar |
| N4 | API rate limiting | Algemeen, niet alleen auth |
| N5 | Structured logging (JSON) | Makkelijker te parsen in productie |

---

## 9. Samenvatting per domein

### Wat werkt GOED

1. **Financiele precision** — Decimal door de hele stack, geen float, CI-geguard
2. **Module-structuur** — 13 modules, consistent router → service → model patroon
3. **Multi-tenant** — Application + JWT + RLS-ready (3 lagen)
4. **Testing** — 5.000+ regels, financiele edge cases uitstekend
5. **Documentation** — CLAUDE.md systeem, DECISIONS.md, code comments
6. **CI/CD** — Automatische lint, tests, build, security checks
7. **Auth** — JWT met refresh, bcrypt, role-based access

### Wat aandacht nodig heeft

1. **Frontend completeness** — ~40% af, veel UX polish nodig
2. **Frontend tests** — Geen automatische tests
3. **Tenant middleware** — SQL string formatting (eenvoudige fix)
4. **Rate limiting** — Ontbreekt op auth endpoints
5. **Audit trail** — Geen logging van wie-wat-wanneer

### Productie-gereedheid

| Criterium | Status |
|-----------|--------|
| Financiele correctheid | ✅ Geverifieerd |
| Security basis | ✅ JWT + bcrypt + tenant isolation |
| Data integriteit | ✅ Decimal + NUMERIC + constraints |
| Error tracking | ✅ Sentry geconfigureerd |
| Backup plan | ✅ PostgreSQL dump naar Storage Box |
| CI/CD | ✅ GitHub Actions |
| SSL/TLS | ✅ Let's Encrypt via Nginx |
| Monitoring | ✅ Sentry + health endpoint |
| Multi-tenant isolation | ✅ Application + JWT + RLS-ready |
| Compliance (Nederlands recht) | ✅ Art. 6:119, 6:96, 6:44 BW |

**Conclusie:** De codebase is productie-klaar voor de Kesting Legal MVP. De architectuur is solide, de financiele berekeningen zijn wiskundig geverifieerd, en de security-basis is goed. De frontend heeft meer werk nodig (dat staat gepland in UX-VERBETERPLAN.md), maar de backend en infra zijn op een hoog niveau.

---

*Review uitgevoerd op 19 februari 2026 door Claude Code (Opus 4.6)*
