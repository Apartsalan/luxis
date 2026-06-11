# Plan — App als non-superuser DB-rol (RLS fail-closed)

**Status:** 📋 Gepland / gedocumenteerd — **NIET autonoom uitgevoerd** (S162).
**Reden:** infra-wijziging aan de prod-DB met reëel downtime-risico → vereist
onderhoudsvenster + go van Arsalan. PROMPT-S162 taak 3 staat dit expliciet toe
("Mag ook puur gedocumenteerd worden als het risico op prod-downtime te groot is").

---

## 1. Probleem (de latente footgun)

De app verbindt met PostgreSQL als de **superuser/owner**-rol en doet per
geauthenticeerde request `SET LOCAL ROLE luxis_app` (zie
`app/middleware/tenant.py:56`). Pas ná die role-switch is `current_user` een
non-superuser → RLS-policies worden afgedwongen.

`SET LOCAL` is **transactie-gebonden**: bij een `COMMIT` midden in een request
valt de rol terug naar de superuser. Een superuser **bypasst RLS, ook met FORCE**.
Dus elke DB-operatie ná een mid-request commit (vóór de volgende `SET LOCAL ROLE`)
draait ongefilterd als superuser.

**Nu onschadelijk:** de enige operaties ná een mid-request commit zijn
PK-refreshes van objecten die het request zélf net schreef (eigen tenant). Geen
lekpad — bevestigd in de S161-audit (SEC-5).

**Waarom toch fixen:** het is fail-**open**. Eén toekomstige code-pad dat ná een
mid-request commit een tenant-scoped read doet (RLS-only, zonder expliciet
`tenant_id`-filter) lekt stil cross-tenant. De verdediging hangt nu af van
"niemand schrijft ooit zo'n query" i.p.v. van de database. Voor een kantoor met
echte cliënt-PII van meerdere tenants willen we **fail-closed**: de DB dwingt
isolatie af, ongeacht de code.

## 2. Huidige bouwstenen (al aanwezig — S150, AUDIT-H2)

- Rol `luxis_app` bestaat: `CREATE ROLE luxis_app NOLOGIN` (idempotent),
  `GRANT luxis_app TO <connect-user>` (`app/security/rls.py:75-86`).
- Grants: SELECT/INSERT/UPDATE/DELETE op alle huidige + toekomstige tabellen,
  USAGE/SELECT op sequences, via `ALTER DEFAULT PRIVILEGES` (`rls.py:89-99`).
- Per tabel: `ENABLE` + **`FORCE` ROW LEVEL SECURITY** + policy `tenant_isolation`
  met `USING` én `WITH CHECK` op `tenant_id = current_setting('app.current_tenant')`
  (`rls.py:102-115`).
- `users` bewust uitgesloten (cross-tenant login-lookup).

De policies/grants zijn dus al klaar voor een non-superuser. Wat ontbreekt: de
**app moet als die non-superuser inloggen** i.p.v. als superuser-met-SET-ROLE.

## 3. Doel-eindtoestand

De app-DB-login is een **non-superuser** rol. Omdat de tabellen `FORCE RLS`
hebben, gelden de policies voor die rol **altijd** — ook direct na een commit,
zonder enige `SET ROLE`. Resultaat: fail-closed. `set_tenant_context` blijft de
GUC `app.current_tenant` zetten; de `SET LOCAL ROLE luxis_app`-stap kan dan
verdwijnen (de login is al non-superuser).

**Kerncomplicatie — migraties.** De deploy draait
`alembic upgrade head` **in de backend-container, met dezelfde DATABASE_URL**
(zie `deploy.yml`). DDL (CREATE/ALTER TABLE) en `apply_rls()` (CREATE ROLE, GRANT,
FORCE RLS) vereisen owner-/superuser-rechten. Een non-superuser app-login kan die
migraties **niet** draaien → de deploy breekt. Dit is de reden dat de fix
niet-triviaal is.

## 4. Opties

### Optie A — Split-rol: app-login (non-superuser) + aparte migratie-login (owner)
- Nieuwe login-rol `luxis_app_login` (NOSUPERUSER, LOGIN, wachtwoord), lid van
  `luxis_app` (erft de DML-grants), **niet** table-owner.
- App-container krijgt `DATABASE_URL` → `luxis_app_login`.
- Migraties draaien onder de **owner/superuser** via een aparte env-var
  (b.v. `MIGRATION_DATABASE_URL`); deploy-stap en `alembic env.py` gebruiken die.
- `SET LOCAL ROLE luxis_app` in middleware wordt no-op/verwijderd (login is al
  non-superuser). `set_tenant_context` blijft.
- **Voordeel:** schoonste scheiding (least privilege); app heeft nooit DDL.
- **Nadeel:** twee connection strings; `alembic env.py` + deploy moeten de
  migratie-URL kennen; meer bewegende delen.

### Optie B — App-login = table-owner maar non-superuser, met FORCE
- App-login is owner (kan dus migreren) maar **NOSUPERUSER**. FORCE RLS geldt óók
  voor de owner → policies afgedwongen, en owner kan DDL → migraties werken met
  één URL.
- **Voordeel:** één DATABASE_URL; minimale deploy-wijziging.
- **Nadeel:** de app-login kan nog steeds policies droppen/`NO FORCE` zetten
  (owner-privilege) → zwakkere garantie dan A; en `apply_rls()` doet
  `CREATE ROLE` + `GRANT role TO current_user`, wat een non-superuser owner
  alléén mag als hij `CREATEROLE` heeft. Vereist zorgvuldige privilege-tuning.

**Aanbeveling:** **Optie A** (least privilege, DB dwingt af, app raakt DDL nooit
aan). Optie B alleen als de split-URL in alembic/deploy te bewerkelijk blijkt.

## 5. Concrete stappen (Optie A, in onderhoudsvenster, mét Arsalan)

> Alle stappen eerst op een **wegwerp-kopie** van de prod-DB (of een Postgres-
> branch) dry-runnen. Nooit blind op prod.

1. **Backup** (cron `backup.sh` + handmatige `pg_dump` vlak vóór de wijziging).
2. **Login-rol aanmaken** (als owner/superuser):
   ```sql
   CREATE ROLE luxis_app_login LOGIN PASSWORD '<sterk>' NOSUPERUSER NOCREATEDB NOCREATEROLE;
   GRANT luxis_app TO luxis_app_login;     -- erft DML + default privileges
   ```
3. **Verifiëren** dat `luxis_app` (en dus de login) op álle tenant-tabellen kan
   lezen/schrijven mét policy (test cross-tenant read → 0 rijen) op de kopie.
4. **Migratie-pad scheiden:** `alembic/env.py` leest `MIGRATION_DATABASE_URL`
   (fallback naar `DATABASE_URL`); deploy zet die var op de owner-connectie.
5. **Middleware:** `SET LOCAL ROLE luxis_app` verwijderen/condition-eel maken
   (overbodig zodra de login non-superuser is); `set_tenant_context` behoudt de
   GUC. Rode→groene test: `tests/test_rls_isolation.py` aanpassen zodat het
   scenario "non-superuser login, geen SET ROLE, post-commit read → 0 cross-tenant
   rijen" bewijst (dekt precies de footgun af).
6. **Prod `.env`:** `DATABASE_URL` → `luxis_app_login`; `MIGRATION_DATABASE_URL`
   → huidige owner. Backup `.env.bak-s1xx-rolesplit`.
7. **Deploy** in venster: migraties (owner) → app recreate (app-login) →
   health-checks intern + extern → 6× fout-login lockout-rooktest + 1 normale
   login → cross-tenant smoke.
8. **Observeren** (Sentry, logs) 24-48u.

## 6. Premortem — "het is 6 maanden later en de fix brak prod"

1. **Migraties draaiden als de non-superuser app-login → deploy faalde / DDL
   geweigerd.** Meest waarschijnlijke faalmodus. Mitigatie: stap 4 (aparte
   `MIGRATION_DATABASE_URL`) is hárd vereist en wordt eerst op de kopie bewezen;
   deploy.yml-stap `alembic upgrade head` expliciet op de owner-URL pinnen.
2. **Ontbrekende grant op een nieuwe tabel → app kan niet lezen/schrijven →
   500's.** Een toekomstige migratie maakt een tabel terwijl `ALTER DEFAULT
   PRIVILEGES` net niet greep (verkeerde grantor). Mitigatie: default privileges
   zetten als de **owner die de tabellen maakt**; na elke migratie een
   `GRANT ... ON ALL TABLES`-sweep in `apply_rls()` houden (bestaat al); coverage-
   guard-test die élke tenant-tabel op leesbaarheid-voor-luxis_app checkt.
3. **`apply_rls()` zelf brak** omdat het `CREATE ROLE`/`GRANT role TO current_user`
   doet en `current_user` tijdens migratie nu de owner (niet superuser) is zonder
   `CREATEROLE`. Mitigatie: migratie-owner krijgt `CREATEROLE`, óf de role-creatie
   wordt een eenmalige out-of-band bootstrap (niet elke migratie).
4. **Stille regressie: een code-pad deed tóch `SET ROLE` of verwachtte superuser**
   (b.v. scheduler `SET app.current_tenant` zonder role). Mitigatie: grep op alle
   `SET ROLE`/`current_user`-aannames (scheduler.py:632, oauth_router, exact_online
   al geïnventariseerd); scheduler draait als owner of krijgt eigen non-superuser
   pad met FORCE-test.
5. **Rollback bleek lastig** omdat `.env` + rol + middleware samen wijzigen.
   Mitigatie: rollback = `.env` terug naar owner-`DATABASE_URL` + container
   recreate (rol en grants mogen blijven staan; ze zijn additief en breken de
   superuser-modus niet). 1-regel terugzetten, geen DB-restore nodig.

**Waarom toch de juiste aanpak:** alle faalmodi zitten in de *uitrol*, niet in het
*eindmodel*. Het eindmodel (DB dwingt isolatie af, app heeft nooit DDL) is strikt
veiliger dan de huidige "code mag nooit een fout maken"-garantie. De risico's zijn
beheersbaar met een kopie-dry-run + onderhoudsvenster.

## 7. Aanbeveling voor uitvoering

- **Niet autonoom / niet blind op prod.** Inplannen met Arsalan in een rustig
  venster, ná een verse backup, eerst volledig op een DB-kopie of Supabase-branch
  bewezen.
- Inschatting: ~1 sessie voor de kopie-dry-run + alembic-split + tests, ~1 kort
  venster voor de prod-cutover.
- Tot die tijd blijft de huidige superuser+SET-ROLE-modus **veilig** (latent, geen
  lekpad) — dit is hardening, geen acuut gat.
