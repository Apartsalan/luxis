# Audit 4 — Multi-Tenant Isolation

**Datum:** 2026-04-22
**Scope:** `backend/app/*` + `backend/alembic/versions/*`
**Auditor:** security-reviewer subagent (Opus 4.7)

## Verdict: RISKY

Twee lagen van isolatie bestaan (service-level `tenant_id` filter + PostgreSQL RLS met forced role), beide consistent geïmplementeerd in de hand-geschreven services. **Geen werkend cross-tenant data leak gevonden in HTTP endpoints.** Echter, vier productietabellen met gevoelige data (OAuth tokens, bank transacties via indirect link, notifications, product catalogus) **ontbreken in de RLS policy list**, en één daarvan (`exact_online_connections`) bevat **encrypted refresh tokens voor accounting systemen** — defense-in-depth is afwezig op exact de tabellen waar het telt. Twee HIGH-sensitivity patterns (scheduler bypass RLS volledig, tenant_id trust op FK velden bij create flows) vullen het risico aan.

## Severity counts
- **CRITICAL:** 0 werkende leaks
- **HIGH:** 4
- **MEDIUM:** 6
- **LOW/INFO:** 5

---

## Top findings (volgorde op risico)

### HIGH #1 — RLS policies ontbreken op 4 tenant-scoped tabellen
**Locatie:** `backend/alembic/versions/sec9_row_level_security.py:35-74` + `sec9b_force_rls.py:28-67`

Ontbrekende tabellen: **`products`**, **`exact_online_connections`**, **`exact_sync_log`**, **`notifications`**. Toegevoegd na de RLS migratie en nooit bijgewerkt. `exact_online_connections` bevat Exact Online OAuth refresh tokens (accounting-system access) — de meest gevoelige van de vier.

**Impact:** Een regressie in service-layer filtering (of een nieuw endpoint dat `.where(tenant_id=...)` vergeet) zou direct leaks geven: product catalog, Exact Online credentials, cross-tenant notifications, sync logs.

**Fix:** Migratie `sec14_rls_remainder` die voor alle vier de tabellen uitvoert:
```sql
ALTER TABLE ... ENABLE ROW LEVEL SECURITY;
ALTER TABLE ... FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON ... USING (tenant_id = current_setting('app.current_tenant')::uuid);
GRANT SELECT, INSERT, UPDATE, DELETE ON ... TO luxis_app;
```

### HIGH #2 — Scheduler bypass RLS volledig
**Locatie:** `backend/app/workflow/scheduler.py:33, 58, 177, 230, 271, 308, 363, 404, 552`

Alle scheduled jobs draaien als superuser (`async_session()` direct, geen `set_tenant_context`). `SET ROLE luxis_app` wordt nooit uitgevoerd → RLS policies gelden NIET in de scheduler. Elke job leunt 100% op hand-geschreven `tenant_id=...` filters.

**Risico:** Jobs `email_auto_sync` (alle accounts), `daily_deadline_notifications` (schrijft notifications), `ai_email_classification` (leest inkomende emails), `followup_scan` (maakt action items). Eén gemist filter = silent cross-tenant write.

**Fix:** Wrap elke per-tenant loop-body met `await set_tenant_context(session, tenant.id)` in een nested transactie `async with session.begin_nested()`. Outer cross-tenant loop blijft op superuser.

### HIGH #3 — `mark_overdue_installments` cross-tenant update zonder scoping
**Locatie:** `backend/app/collections/service.py:785-800`

Aangeroepen vanuit scheduler zonder `tenant_id` argument — update installments **over alle tenants in één query** als superuser. Functioneel correct vandaag, maar patroon van cross-tenant writes zonder scoping is gevaarlijk als dit per ongeluk vanuit een authenticated request path aangeroepen wordt.

**Fix:** Docstring-banner "CROSS-TENANT — scheduler only". Beter: signature wijzigen naar `tenant_id: uuid.UUID | None = None` en wanneer gezet ook RLS context zetten.

### HIGH #4 — `secret_key` default + production guard gap
**Locatie:** `backend/app/config.py:12` + `backend/app/main.py:54-60`

`secret_key` default is hardcoded `"change-this-to-a-random-string-in-production"`. Production guard in `main.py` blokkeert startup ALS `app_env=="production"` exact, maar bij `APP_ENV` unset of typo (`prod`, `PRODUCTION`) wordt de default geaccepteerd en **kan elke attacker JWTs forgen voor elke tenant_id**.

**Fix:** Default wegnemen: `secret_key: str = Field(...)` (required). Ook `app_env.lower() in {"production","prod"}` normaliseren. Verifieer `.env.production` zet SECRET_KEY.

### MEDIUM #5 — `create_invoice` / `add_line` / `create_expense` / `create_payment` accepteren FK's zonder cross-tenant check
**Locatie:** `backend/app/invoices/service.py:225-298`

Accepteert `contact_id`, `case_id`, `time_entry_id`, `expense_id`, `product_id`, `line_data.product_id` van de client zonder cross-tenant existence check. RLS voorkomt dat een cross-tenant FK resolved op read, maar een attacker met gelekte UUID van tenant B kan tenant A's invoice vervuilen met FK references naar foreign rows.

**Fix:** `_assert_tenant_owns()` helper die elke FK valideert tegen `tenant_id`, aanroepen vóór `db.add(invoice)`.

### MEDIUM #6 — `save_attachment_to_case` geen case ownership check
**Locatie:** `backend/app/email/sync_router.py:486-559`

`case_id` komt uit URL path. Service kopieert file naar `uploads/<user.tenant_id>/<case_id>/` en schrijft `CaseFile` met `tenant_id = user.tenant_id`. Als user een `case_id` van tenant B meegeeft, wordt een file record aangemaakt onder tenant A gekoppeld aan een case die de user niet mag zien — orphan data.

**Fix:** Case ownership valideren voor write: `await cases_service.get_case(db, user.tenant_id, case_id)` — raises NotFoundError bij cross-tenant.

### MEDIUM #7 — `get_user_by_id` assert tenant_id match ontbreekt
**Locatie:** `backend/app/auth/service.py:94-97`

Fetcht user puur op UUID — gebruikt in `get_current_user` na JWT decode. Als een user tussen tenants verplaatst wordt (soft-delete + recreate), zou de oude JWT nog steeds resolven naar een user record waarvan `tenant_id` niet meer match met de JWT's `tenant_id` claim. Dependency zet RLS context vanuit JWT tenant_id, zoekt user op zonder asserten dat user nog bij die tenant hoort → queries draaien onder een stale context.

**Fix:** Na de lookup: `assert user.tenant_id == uuid.UUID(tenant_id_from_jwt)`; raise 401 anders.

### MEDIUM #8 — Tenant middleware gebruikt f-string interpolatie
**Locatie:** `backend/app/middleware/tenant.py:36`

`SET LOCAL app.current_tenant = '<uuid>'` via f-string na `uuid.UUID()` validatie. Validatie is correct, maar patroon van interpolatie in raw SQL is fragile — een toekomstige refactor die UUID-coercion drop zou een SQLi zijn.

**Fix:** Regex guard toevoegen `^[a-f0-9-]{36}$` voor belt-and-braces + code comment over de f-string.

### MEDIUM #9 — RLS enforcement niet in staging
**Locatie:** `backend/app/middleware/tenant.py:40-53`

In non-production waarschuwt `luxis_app` role check met log en **gaat zonder RLS-enforcement door**. Als een staging/dev environment per ongeluk op internet staat, is RLS volledig uit.

**Fix:** RLS enforcement ook verplicht in staging (`APP_ENV in {"staging","production"}`). Fail fast.

### MEDIUM #10 — Inconsistente tenant context na JWT decode
**Locatie:** `backend/app/dependencies.py:47-50`

`set_tenant_context(db, tenant_id)` gebruikt de JWT claim. User wordt NA RLS setting opgezocht. Als een JWT `tenant_id=B` heeft maar `sub` wijst naar user in tenant A: RLS context = B, User object.tenant_id = A. Service calls filteren op A maar RLS sessie is B → elke query geeft 0 rows.

**Fix:** Na user lookup: assert `str(user.tenant_id) == tenant_id` OF reset RLS context vanuit `user.tenant_id` (DB is source of truth).

### MEDIUM #11 — Email uniqueness GLOBAL = info-leak
**Locatie:** `backend/app/auth/service.py:116-118`

`User.email unique=True` globaal. Tenant B kan geen user onboarden met email die al in tenant A bestaat → bestaansbewijs van user in concurrerend kantoor. Blokkeert ook real-world cases (iemand werkt bij twee advocatenkantoren).

**Fix:** Composite unique `(tenant_id, email)`. Migratie met data-check eerst.

### LOW #12 — AI Agent tool executor: prompt injection van tenant_id
**Locatie:** `backend/app/ai_agent/tools/executor.py:28-70`

Tool executor geeft `tenant_id` en `user_id` door als kwargs. Handlers scope correct. LLM-controlled inputs komen via `**tool_input` — bij prompt-injectie `{"tenant_id": "<B>"}` als field name raised Python `TypeError: multiple values for keyword argument`. Veilig vandaag maar brittle.

**Fix:** Pop `tenant_id` / `user_id` uit `tool_input` voor unpacking: `tool_input.pop("tenant_id", None); tool_input.pop("user_id", None)`.

### LOW #13 — Email sync case number regex tenant-agnostic
**Locatie:** `backend/app/email/sync_service.py:77-123`

Case number regex `20\d{2}-\d{4,6}` is tenant-agnostic; function scoped DB lookup op `account.tenant_id`, dus "2026-00005" in subject van externe sender kan niet tussen tenants hoppen. Verified safe.

**Fix:** Geen actie.

### LOW #14 — `get_file_path()` uses stored tenant_id
**Locatie:** `backend/app/cases/files_service.py:138-142`

Bouwt path uit `case_file.tenant_id / case_file.case_id / stored_filename`. Correct — gebruikt stored tenant_id, niet request's. Stored_filename UUID-based, geen user input → geen path traversal risk.

**Fix:** `Path.resolve()` check tegen `UPLOADS_BASE` als extra hardening.

### LOW #15 — `list_users` — check `UserResponse` serialization
**Locatie:** `backend/app/auth/router.py:316-323`

Filters by tenant_id correct. Verifieer dat `UserResponse` niet `hashed_password` serialiseert.

### INFO #16 — `reset_password` token globaal uniek, veilig
**Locatie:** `backend/app/auth/router.py:237-251`

Token is random en SHA-256 hashed in DB; lookup zonder tenant filter is correct — random token is globally unique by construction. Rate-limited 5/hour.

### INFO #17 — RLS roles architectuur correct
`luxis_app` is `NOLOGIN` en granted naar `luxis` (owner). App `SET LOCAL ROLE luxis_app` per request. `FORCE ROW LEVEL SECURITY` zorgt dat zelfs owner (na `SET ROLE`) gefilterd wordt. Correct.

### INFO #18 — CORS
`main.py:91-97`: origins uit `settings.cors_origins`, comma-split. `allow_credentials=True` + `allow_methods=["*"]`. Prima **mits** env var strikt `https://luxis.kestinglegal.nl` is in prod. Controleer `.env.production`.

---

## Quick wins (vandaag te doen)

1. **RLS-gap migratie** voor `products`, `exact_online_connections`, `exact_sync_log`, `notifications` (finding #1)
2. **Assert `user.tenant_id == jwt.tenant_id`** in `get_current_user` (finding #7 & #10)
3. **Verwijder `secret_key` default** (finding #4)
4. **Pop tenant_id/user_id** uit AI tool inputs vóór kwargs expansion (finding #12)

## Tests om toe te voegen

- `test_cross_tenant_rls.py` — seed 2 tenants, RLS context voor tenant A, SELECT van elke tenant-scoped tabel, assert 0 rows van tenant B — loop over ALLE tabelnamen (incl. `products`, `notifications`, `exact_online_connections`, `exact_sync_log`)
- `test_cross_tenant_api.py` — login als tenant A, GET `/api/cases/<B-case-uuid>` → 404, POST `/api/invoices` met `contact_id` van B → 400 nadat finding #5 gefixt is

---

## Positieve bevindingen

Hand-written service layer is consistent — elke `.where(...)` filtert op `tenant_id`. AI agent tool executor threadt `tenant_id` correct. File downloads reconstrueren path uit de stored tenant_id (niet de request's). Search, dashboard, trust_funds, invoices, cases, email sync — alle geverifieerd om te scopen per tenant. OAuth state is HMAC-signed met single-use nonces. RLS gebruikt `FORCE ROW LEVEL SECURITY` met non-superuser `luxis_app` role — architectuur is correct, alleen incompleet toegepast.

**Bottom line:** Geen exploitable leak gevonden, maar defense-in-depth heeft meetbare gaten. Fix #1 en #2 deze week — elk een 30-minuten migratie.
