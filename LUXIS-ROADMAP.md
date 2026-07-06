# Luxis — Project Roadmap (Source of Truth)

> ⚠️ **LEES EERST `docs/ARCHITECTUUR-KAART.md`** (2 pag.) — hoe alle systemen aan elkaar
> hangen. Wordt óók automatisch geladen bij sessiestart (SessionStart-hook, S172). Wijzig
> je een systeemkoppeling → kaart bijwerken in dezelfde sessie. Feitelijke inventaris:
> `docs/audit/inventaris-2026-07-05.md`.

**Laatst bijgewerkt:** 6 juli 2026 (sessie 175 — **Onafhankelijke review S174: GO.** Alle draaiboek-checks doorlopen (diff regel voor regel, 89 tests zelf gedraaid, prod-rooktest: Slim-leren-UI + concept op verweer-dossier + logs + PII-steekproef; relabel-verdeling exact de dryrun, goedgekeurde rijen onaangeraakt). Eén must-fix gevonden + direct live: `get_learned_examples` keek maar naar de 12 nieuwste goedkeuringen → V4-type-matching zou stil falen zodra Lisanne >12 kandidaten goedkeurt; cap → 200 (rode test eerst, commit `5fa4592`, gedeployed). Next: Lisanne's beoordeling begeleiden / K2-meting, `docs/sessions/PROMPT-S176.md`.)
**Vorige:** 6 juli 2026 (sessie 174 — **Verbind-sprint 2 LIVE**: staleness-gate (de `created_at`-selectiebug op 3 plekken weg), audience-gate voor client-updates, de 13-types-verweer-woordenschat + deterministische pre-labeler (`defense_types.py`), en **type-matching bij het genereren** (classificatie kiest `defense_type` → `get_learned_examples` geeft matchend type voorrang, verweer-categorieën als één pool). Prod-relabel toegepast (87 kandidaten, verdeling exact als de dryrun); goedgekeurde rijen ongemoeid. 139 relevante tests groen. 2 commits (`0ec6852`+`8817ada`) + migratie `s174` gedeployed. **S175 = verplichte Fable-review.**)
**Vorige:** 5 juli 2026 (sessie 172 — **Fable-audit code↔roadmap**: feature-inventaris opgeleverd (`docs/audit/inventaris-2026-07-05.md`), KERNBEVINDING: 3 AI-conceptservices met 3 verschillende geheugens (alleen het verweer-pad ziet AV+geleerde voorbeelden; compose-dialog ziet NIETS) → verbind-sprint gepland (PROMPT-S173, daarna Fable-review in S174). ±20 van de 110 "Overig"-kandidaten = vervuiling (debiteur-tekst/lege fragmenten, in prod geverifieerd); verweer-woordenschat van 13 types uit de echte data gedestilleerd. `docs/ARCHITECTUUR-KAART.md` gemaakt + SessionStart-hook. Stale roadmap-regels gefixt (Celery/Nginx/jose/Sentry/doc-paden/FEAT-MAIL-01).)
**Vorige:** 5 juli 2026 (sessie 171 — **Algemene voorwaarden LIVE voor de 7 opdrachtgevers**: ontdekt dat de geversioneerde AV-upload per cliënt (`ContactTerms`, S140) al bestond incl. AI-injectie in de verweer-prompt → 3 AV-sets gekoppeld + end-to-end geverifieerd (AI laadt nu per zaak de echte voorwaarden). **K1-kennisbank dus grotendeels al gebouwd → alleen gevuld.** + Slim-leren layout-bug gefixt (grid `min-w-0`, live). Audit-opdracht code↔roadmap voor Fable klaargezet. K0-gate poot 2 rond; poot 1 = Lisanne's review loopt (12 goedgekeurd). Volgende: `docs/sessions/PROMPT-AUDIT-code-vs-roadmap.md` / `PROMPT-S172.md`.)
**Vorige:** 5 juli 2026 (sessie 170 — FIN-2 dossier-afwikkelflow LIVE + Fable-review 3 fixes + source-mount-lek gefixt) · 4 juli (S169 — Slim leren geschaald naar 130 + kennisbank-onderzoek) · 3 juli (S168 — BaseNet-import uitgevoerd)
**Product:** Praktijkmanagementsysteem voor Nederlandse advocatenkantoren
**Eerste klant:** Kesting Legal (Lisanne Kesting, 1 advocaat, incasso/insolventie, Amsterdam)
**Productie:** https://luxis.kestinglegal.nl
**Repo:** https://github.com/Apartsalan/luxis.git (branch: main)

---

## Over het team

**Arsalan** — geen developer. IT-recruitment + business development voor Kesting Legal. Bouwt volledig samen met AI (Claude Code). Beschikbare tijd: 6-10 uur per week. Kan geen code reviewen — het systeem moet zelfcontrolerend zijn.

**Lisanne Kesting** — mr., advocaat, beëdigd 14-02-2018, arrondissement Amsterdam. VIA-lid. Enige advocaat bij Kesting Legal. Specialisatie: incasso en insolventierecht. MKB-cliënten, incassobureaus, deurwaarders. 250+ procedures gevoerd. Kantoor: IJsbaanpad 9, 1076 CV Amsterdam. KvK: 88601536.

**Huidig systeem:** Basenet (wordt pas opgezegd als Luxis de dagelijkse workflow volledig overneemt)
**Boekhouding:** Exact Online (gekoppeld aan Basenet)
**E-mail:** Outlook/365

---

## Huidige status

| Laag | Volwassenheid | Toelichting |
|------|--------------|-------------|
| Backend (FastAPI) | ~97% | ~19 modules, ~290 endpoints, ~42 models (exacte inventaris: `docs/audit/inventaris-2026-07-05.md`), 684 tests (4 skipped). Financial calcs uitstekend getest. Alle routers getest. Ruff clean ✅. CI groen ✅. Zero-BTW bug gefixt ✅. Pipeline overhaul: 21 stappen, step_transitions (branching workflow), CaseStepHistory, verweer-tracking. |
| Frontend (Next.js) | ~87% | 24 pagina's (0 stubs), 29 hooks, 29 componenten. Alle 17 backend modules hebben frontend. Skeleton loaders, error boundaries, toast notifications, mobile responsive. 65 `any` types gekilld ✅, hooks cleanup ✅. E2E: 14 spec files (incl. settings, docs). **Impeccable design-audit S155 (7 jun): 10.5→~15.5/20** — login/dashboard ont-AI'd, timer-tick + zoek-flikker gefixt, 12 modals → Radix Dialog, toetsenbord/screenreader-toegankelijkheid, Mail/Incasso mobiel, dode dark:-classes weg. Rapport: `docs/qa/impeccable-audit-2026-06-07.md`. Restwerk: zie Backlog. |
| Infra/DevOps | ~98% | Docker Compose op Hetzner VPS. Caddy ✅. GitHub-hosted CI runners ✅. Auto-deploy via SSH ✅ (S159: draait nu `alembic upgrade head` + faalt hard op health). Backup: lokaal 7d + off-site B2 90d ✅, **restore-test bewezen S159** (`docs/runbooks/restore.md`). fail2ban ✅. **ufw actief (22/80/443) S159** ✅. **uptime-cron gefixt S159** ✅. `TOKEN_ENCRYPTION_KEY` gezet ✅. Kernel 6.8.0-106 ✅. API docs + runbook ✅. CI 6/6 groen ✅. |

**Rode draad:** Backend ~97%, Frontend ~85%, Infra ~98%. Fasen 1-3 + 5 + 6 compleet. CI volledig groen (6/6 jobs).

**Strategische modus (sessie 116, 7 april 2026):** Marktonderzoek afgerond, GTM-plan voorbereid. Arsalan is nog in de **bouw/validatie-fase met Lisanne** (demos lopen). Luxis gaat de markt op zodra Lisanne's dagelijkse workflow stabiel draait. Lifestyle business met AI-leverage, doel 100-300 klanten op termijn. Het Go-To-Market plan hieronder is voorbereiding, niet de actieve fase.

**TODO (klein):**
- ✅ VPS kernel reboot — 6.8.0-106 (gedaan sessie 109)
- ✅ Off-site backup — Backblaze B2, bucket `Luxis-backup`, 90d retentie
- ✅ CI terugzetten naar GitHub-hosted runners (sessie 110 — ubuntu-latest, services blok, setup-uv)
- ✅ Zero-BTW bug gefixt (sessie 110 — lines erven nu invoice btw_percentage, xfail verwijderd)

**Roadmap naar ~98% (13-15 sessies):**
1. Infra hardening (CI/CD ✅, Caddy in repo ✅, backup ✅, security ✅) — 3 sessies — COMPLEET ✅
2. Backend test coverage (7/7 routers getest ✅, 61 nieuwe tests, email import bug gefixt) — COMPLEET ✅
3. Frontend structureel (65x `any` gekilld ✅, hooks cleanup ✅) — COMPLEET ✅
4. Stitch redesign (nieuw design, component-voor-component) — 3-5 sessies
5. Frontend E2E + polish (settings + docs E2E ✅, a11y + performance TODO) — deels compleet
6. Final hardening (API docs ✅, runbook ✅, disaster recovery ✅) — COMPLEET ✅

---

## 🎯 VERBIND-SPRINT (na audit S172) — HUIDIGE PRIORITEIT

**Kern:** even geen nieuwe features — eerst verbinden. De audit bewees dat de AI-laag uit
losse, half-verbonden stukken bestaat (3 conceptservices / 3 geheugens; 4 sjabloonplekken).
Volledige onderbouwing: `docs/audit/inventaris-2026-07-05.md`.

| # | Stap | Sessie | Status |
|---|------|--------|--------|
| V1 | **Gedeelde AI-kennis-bouwer** — AV + geleerde voorbeelden + bibliotheek in álle 3 draft-paden (lost ook `draft_service` legacy-AV op) | S173 (Opus) | ✅ live (`resolve_case_terms`, commit bc8923e) |
| V2 | **Leer-wachtrij schoonmaken** — ±20 vervuilde kandidaten afwijzen + 2 extractie-guards | S173 (Opus) | ✅ live (16 afgewezen, 118→102) |
| V3 | **Verweer-woordenschat 13 types** + trefwoord-labeling + relabel 'overig' + dropdown | S174 (Opus) | ✅ live (`defense_types.py`, commit 0ec6852; prod-relabel 87 kandidaten, verdeling = dryrun) |
| V3b | **Review-punten S173b** — staleness-gate (created_at-bug ×3 weg), audience-gate client-updates, skip-logging, unified Engels vb. | S174 (Opus) | ✅ live (`last_inbound_defense`, commit 0ec6852) |
| V4 | **Type-matching bij genereren** — classificatie kiest `defense_type`, `get_learned_examples` geeft matchend type voorrang (één pool) | S174 (Opus) | ✅ live (migratie s174, commit 8817ada) |
| V4-review | **Verplichte onafhankelijke Fable-review op S174** | S175 (Fable) | ✅ GO — 1 must-fix (12-cap in `get_learned_examples`) direct live, commit `5fa4592` |
| V5 | Met/zonder-meting edit-rate (K1-vlag) | later | 📋 |
| V6 | Later: sjablonen→DB (DF122-04), 3 services→1 motor, `kimi_client` hernoemen, Celery-dep weg, `terms_file_path` uitfaseren, H25-besluit | backlog | 📋 |

**Parallel (mensen, kritiek pad):** Lisanne's review van de 130 kandidaten · open beslissingen
S157 (verdienmodel/BTW, 2e stichtingsbestuurder, 14-dagenbrief-akkoord H6 — advies ligt klaar).

---

## 🔴 SYSTEEM-AUDIT 2026-06-01 — Fix-backlog (PRIORITEIT)

**Methode:** read-only audit (API+DB+code, parallel agents) + serieel visuele sweep, op lokale wegwerp-stack met Mailpit-zinkput. Elke bevinding onafhankelijk geverifieerd; high-severity adversarieel her-gecheckt. Geld onafhankelijk nagerekend tegen wettelijke ijkpunten.
**Volledige rapporten (lokaal, gitignored — bevatten data):** `.audit/AUDIT-REPORT.md` (techniek) + `.audit/UI-FINDINGS.md` (visueel) + `.audit/PASS1-FINDINGS.md` (geld-orakel).
**Telling:** 3 blocker · 25 high · 48 medium · 31 low · 4 polish (111 na dedup).
**Positief referentiepunt:** rekenkern (rente/WIK/art. 6:44/nakosten) onafhankelijk nagerekend = **correct**. UI consistent professioneel, geen render-crashes.
**Werkwijze fixen:** op volgorde, blockers eerst, elk rood→groen geverifieerd. NIET alles in één sessie.

**Voortgang S162 (2026-06-11, Opus) — reproduceerbare builds + dep-scanning + VPS-drift (S161-residuals afgehecht):** **(2) Reproduceerbare builds:** `backend/uv.lock` gegenereerd (110 pinned pkgs); Dockerfile + CI installeren nu uit de gepinde+hashte `uv export` i.p.v. `>=`-floors → deterministisch. Nieuwe **blocking** CI-job `pip-audit` op de locked runtime-closure (pip/setuptools zitten niet in de export → géén pip-self-ruis), plus **non-blocking** `npm audit --audit-level=high` (resterende moderates leven in Next 15's eigen dep-tree). Lokaal volledige image-build + import-smoke-test vóór push; CI 8/8 groen; prod live op de pinned versies (PyJWT 2.13.0 / starlette 1.3.0 / multipart 0.0.32 / cryptography 48.0.1). `2dff131`. **(4) VPS-drift opgeruimd:** de 'ongecommitte' scripts bleken enkel een **mode-drift** (chmod +x op de VPS, inhoud identiek) die elke deploy-`git pull` deed afbreken (S161-Caddyfile-patroon) → exec-bit nu in git getrackt (`9611d06`), VPS verzoend, `git status` volledig schoon. Zwerf-`test_followup.py` (root + `app/` + `build/`, mét hardcoded prod-wachtwoord) verwijderd op de VPS; de **échte** `tests/test_followup.py`-suite (A2.2 follow-up advisor) intact (bijna per ongeluk meegenomen → hersteld via git checkout). `.gitignore` dekt nu `.env.bak*` (secret-backups konden bij een `git add` lekken — nu beschermd, bestanden als rollback-net op de VPS gelaten) + nieuwe `.gitattributes` pint LF op `.sh`/`uv.lock`/yml/Dockerfile (autocrlf-veiligheid; CRLF zou `#!/bin/bash` op de Linux-VPS breken). **(3) App als non-superuser owner (RLS fail-closed):** bewust **niet** blind op prod — plan + premortem in `docs/security/rls-nonsuperuser-owner-plan.md`. Kerncomplicatie: alembic-migraties draaien in de backend-container mét dezelfde DATABASE_URL → een non-superuser app-login kan geen DDL → aparte migratie-owner nodig. Aanbeveling: split-rol (app-login NOSUPERUSER + migratie-owner, Optie A), uit te voeren in een onderhoudsvenster mét Arsalan na kopie-dry-run. Huidige superuser+SET-ROLE-modus blijft veilig (latent, geen lekpad). **Open residual:** `deploy.yml` bouwt `--no-cache` op élke push (ook docs-only) — botst met de deploy-regels-skill ('standaard geen --no-cache'); `disk_guard`+weekly builder-prune vangen het op (disk 43%), maar ooit conditioneel maken. Volledige details: SESSION-NOTES S162-entry. **Voortgang S161 (2026-06-10, Opus) — SECURITY-DIEPTE vóór livegang met echte cliënt-PII:** SEC-3 (secrets) was al schoon (S160); SEC-1/2/4/5/6/7/8 nu gedekt. **SEC-5 tenant-isolatie = ROBUUST** — RLS FORCE + WITH CHECK + adversariële test (geforceerde cross-tenant read→0 rijen + future-table coverage-guard) ÉN app-laag `tenant_id`-filtering overal; geen lekpad. **4 echte fixes** (rode→groen, gedeployed + live geverifieerd): **SEC-7** account-lockout was STIL KAPOT in prod (`authenticate_user` flush'te de teller, maar de 401 rolt `get_db` terug → teller bleef altijd 0; live bewezen) → nu commit (`2b499fb`) + regressietest; **SEC-1** wachtwoord-wijziging/-reset trekken nu refresh-tokens in (`978eaee`) (rest SEC-1 al goed: HS256 vastgepind, 15-min tokens, refresh-rotatie+reuse-detection); **SEC-6** upload gecapt aan de edge (Caddy `request_body 55MB`) + backend pre-read check (`e3124dd`) — IDOR was al veilig, XSS geneutraliseerd (nosniff); **SEC-4** npm audit fix (picomatch ReDoS + postcss XSS, `9817da5`) + PyJWT/multipart floors (`c323774`) — prod bouwt `--no-cache`, fresh build geverifieerd pip-audit 30→5 (alle 5 in `pip` zélf). **SEC-2** schoon (geen rauwe SQL met user-input). **SEC-8** schoon (volledige Caddy header-set, geen stacktrace-lek; live `curl -I` bevestigd). **DEPLOY-BLOKKADE opgelost:** VPS had ongecommitte `mcp.bespoke…`-Caddyblock → elke `git pull` brak af → géén fix was live (VPS hing op `39ec4ba`); mcp-block in git (`15ee7b7`), VPS verzoend, alles gebouwd+gedeployed, Caddy reload. **Residuals (laag/hardening, gedocumenteerd):** harness `override_get_db` maskeert transactie-bugs · geen lockfile + voeg pip-audit aan CI · app als superuser (latente RLS-bypass na mid-request commit) · CSP `unsafe-inline` · VPS-drift (ongecommitte scripts + zwerf-`test_followup.py`). Volledige bevindingen: SESSION-NOTES S161-entry. **Voortgang S159 (2026-06-10, Opus):** S158-audits (readiness + connectie) uitgevoerd — puur uitvoeren, keuzes lagen vast. **READY-B3** deploy draait nu `alembic upgrade head` + faalt hard op intern+extern health (`3194939`, deploy groen mét zichtbare alembic-stap). **READY-B1** Kimi/Gemini volledig uit code → 100% Claude; debiteur-PII niet langer naar Moonshot/China (AVG); compose-env + fallback-ketens gestript, 80 AI-tests groen (`4f9879c`). **READY-B2** restore-test bewezen op prod-VPS (nieuwste dump → wegwerp-DB, 0 fouten, counts exact = live: cases 48/contacts 44/invoices 21/trust 9), runbook `docs/runbooks/restore.md` (`d0f4eb7`). **CONN-6** ongeldige `?tab=` deep-link → `safeTab`-fallback naar overzicht, browser-geverifieerd (`db9b429`). **CONN-1** dagelijkse job `sent→overdue` + notificatie per vervallen declaratie, rode test→groen (`ef21ba6`). **CONN-2** vier-ogen-notificatie bij pending trust-uitbetaling/verrekening (alle users behalve creator), test→groen (`c09b4e2`). **CONN-3/4/14** Intake + Follow-up sidebar-items met pending-badges (ai-pending eindelijk gekoppeld), browser-geverifieerd badge=10 (`d119153`). **CONN-5** notificatie-tab-context (email→correspondentie, deadline→taken, trust→betalingen, invoice→facturen), browser-geverifieerd (`fe0804a`). **VPS-hardening:** H2 uptime-cron gefixt (script miste execute-bit → cron `Permission denied`; nu `/bin/bash` + chmod +x, logt 200), H3 `TOKEN_ENCRYPTION_KEY` gegenereerd+gezet in prod-`.env` + doorgegeven via compose (`88c9364`; **Outlook 1× opnieuw koppelen**), H5 ufw actief (22/80/443, SSH+site geverifieerd). **Openstaand voor Arsalan:** H1 Sentry (gratis account → DSN), Outlook her-koppelen, B2-bucket EU-regio verifiëren, ufw beschermt geen Docker-published poorten (3100). **Voortgang S154 (2026-06-03):** 3 bounded crash-guards + row 59 opgelost — elk rood→groen, los gecommit, CI+auto-deploy. (1) malformed JWT `sub`/`tenant_id` → 401 i.p.v. 500 (`dependencies.py` UUID-validatie binnen auth-try, `c10e7c5`) · (2) `_determine_direction` None-guard op `from_email` (`a098a09`) · (3) `distribute_payment` weigert negatief bedrag (`< 0`; nul blijft toegestaan — auditvoorstel `<= 0` afgekeurd want breekt `test_zero_payment`; `63385f9`) · (4) **row 59** 14-dagenbrief rente-label neutraal "Rente"/"verschuldigde rente" zoals de sommatie (B2C+B2B correct; bewoording met gebruiker bevestigd; `9fa3de7`). **Voortgang S153 (2026-06-03):** **H4** (openstaand incl. rente+BIK) + **H5/griffierecht** (officiële 2026-staffel + eiser-logica + onvermogenden) + 6 bounded MEDIUM (#1–#6) + row 55 (factuur delete/cancel geeft items vrij) opgelost — elk rood→groen, deels live in browser/API bevestigd. **Nog open high:** H6 (14-dagenbrief tekst — juridisch), H14-H19 (derdengelden cluster), H25 (modules_enabled). **Voortgang S149 (2026-06-01):** 3 blockers (B1 deels, B2, B3) + 8 high opgelost (H1, H3, H8, H10, H20, H21, H23, H24), elk rood→groen + lint + push + CI/deploy groen. **Voortgang S150 (2026-06-02):** AUDIT-H2 + B1-restant opgelost — `luxis_app`-rol + FORCE RLS op alle 45 tenant-tabellen, afgedwongen via SET ROLE, adversariële test rood→groen, volledige suite 904 passed, CI/deploy groen. **Nog open:** H4 (openstaand excl. rente/BIK — niet-triviaal: geen cache, O(N) live-herberekening of nieuwe cache-kolommen, vereist keuze), H5 (griffierecht-tarieven — juridisch onderzoek), H6 (14-dagenbrief tekst — juridisch), H7 (kantoorgegevens in brieven), H9 (email_logs), H11/H12/H13 (pipeline), H14-H19 (derdengelden cluster — deels feature), H22 (taak effective-status in lijst/agenda — gedeelde root met H23/H24, alleen reports-deel gedaan), H25 (modules_enabled server-side — te breed, vereist JWT-claim + gefaseerde uitrol). Plus 48 medium / 31 low / 4 polish.

### BLOCKERS (eerst)
| ID | Bevinding | Module | Aanpak |
|----|-----------|--------|--------|
| AUDIT-B1 | Placeholder `SECRET_KEY` = auth-bypass (admin-token namaakbaar) + RLS feitelijk uit | Auth/security | ✅ **Opgelost (S149 + S150)** — SECRET_KEY-deel S149 (`cfb942b`): guard gehardend (default-secure, `config.secret_key_status()`, unset/typo APP_ENV = enforced); prod-key bewezen sterk. **RLS-deel S150** (`d2e6ce2`+`6ea1d0f`): `luxis_app`-rol + FORCE RLS op alle 45 tenant-tabellen, afgedwongen via SET ROLE, adversariële test (zie AUDIT-H2). |
| AUDIT-B2 | `/api/reports/kpis` crasht (500) — `.days` op `Decimal` | Rapportages | ✅ **Opgelost (2026-06-01, S149)** — `int(round(float(avg_interval)))` + rode→groene test met gesloten zaak. Commit `0e049fc` |
| AUDIT-B3 | Bankimport-betaling negeert dossier-instellingen → verkeerde rente/BIK/BTW | Betalingen | ✅ **Opgelost (2026-06-01, S149)** — centrale helper `case_payment_kwargs()` + `create_payment_for_case()`; bankimport, AI-handler én router delen nu één bron. Lost AUDIT-H20 mee op. Commit `db2c767` |

### HIGH (25)
| ID | Bevinding | Module |
|----|-----------|--------|
| AUDIT-H1 | ✅ **Opgelost (S149, `c4c79f1`)** Status 'betaald' zonder financiële guard — guard in validate_transition blokkeert 'betaald' bij openstaand saldo | Dossiers/Rekenkern/Pipeline |
| AUDIT-H2 | ✅ **Opgelost (S150, `d2e6ce2`+`6ea1d0f`)** RLS no-op — `luxis_app`-rol ontbrak (app draaide als bypassrls-superuser), 2/46 tabellen FORCE. Idempotente migratie `h2_rls_complete` maakt rol aan + FORCE RLS + `tenant_isolation` (USING+WITH CHECK) op alle 45 tenant-tabellen (dynamische tenant_id-discovery, gedeelde `app/security/rls.py`); app dwingt af via `SET LOCAL ROLE luxis_app`. Adversariële test bewijst cross-tenant SELECT/INSERT geblokkeerd (rood→groen). Fase 2 (app verbindt ALS luxis_app) bewust uitgesteld. | Auth/security |
| AUDIT-H3 | ✅ **Opgelost (S149, `9471713`)** XFF-spoofing omzeilt login rate-limit; `/refresh` ongelimiteerd — key_func gebruikt nu laatste XFF-entry (Caddy-peer) + /refresh 20/min | Auth/security |
| AUDIT-H4 | ✅ **Opgelost (S153, `f40152e`)** Openstaand op dashboard/reports sloot rente+BIK uit (onderschat) — `get_portfolio_outstanding()` sommeert per actief dossier de `get_financial_summary`-`total_outstanding` (zelfde grand_total-logica als dossierdetail); claimloze dossiers vallen terug op cache `principal − paid` (skipt rentecalc). Live: dashboard+rapportages €5.000→€5.818,27 = dossierdetail. Caveat: O(N) live (rente is datumafhankelijk) — prima op kantoorschaal, herzien met cache-kolommen bij honderden actieve dossiers. | Rapportages |
| AUDIT-H5 | ✅ **Opgelost (S153, `7758f5d`)** Griffierecht-staffel volledig verouderd → vervangen door officiële 2026-tabel (Stcrt. 2025, 39855) kanton (≤€25k) + civiel, 3 kolommen (rechtspersoon/natuurlijk/onvermogend). Lost tevens de twee griffierecht-MEDIUMs op: tarief volgt nu de **eiser** (`case.client.contact_type`) i.p.v. `debtor_type`, en het onvermogenden-tarief is toegevoegd (optionele `?onvermogend`, default uit). 15 tests pinnen officiële bedragen + eiser-logica. Eenmanszaak-nuance (`company`→rechtspersoon) later met rechtsvorm-vlag. | Rekenkern |
| AUDIT-H6 | 🟡 **Advies klaar (S157) — wacht op Lisanne.** Twee tegenstrijdige betaalinstructies (2 bedragen + 2 rekeningen; HTML-variant zelfs zonder enig IBAN). Rechtspraak geverifieerd: HR 2016:2704 (verwarrend = géén BIK) + RBROT:2020:5202 (twee bedragen = fataal). Volledig advies + concreet tekstvoorstel + 4 beslispunten in `docs/research/14-dagenbrief-advies.md`. Implementatie ½ sessie na akkoord. Let op: `termijn_14_dagen` (+15) moet sowieso naar +16 (HR-ervaringsregel bezorging). | Documenten |
| AUDIT-H7 | ✅ **Opgelost (S151, `2bdd6dc`)** Betaalbrieven tonen leeg kantoor-IBAN/adres/telefoon — templates lazen `kantoor.iban/telefoon/email` al, maar Kantoor-tab had geen invulvelden → kolommen bleven leeg. Telefoon/E-mail/IBAN (kantoorrekening) toegevoegd aan Kantoor-tab (apart van Stichting Derdengelden-IBAN); end-to-end geverifieerd (UI→API→DB round-trip). Regressietest op `_tenant_ctx`-mergevelden. | Documenten/Instellingen |
| AUDIT-H8 | ✅ **Opgelost (S149, `91a5c0b`)** Managed-template preview crasht (ImportError → 500) — verkeerde import `_build_base_context` → `build_base_context` | Documenten |
| AUDIT-H9 | ✅ **Opgelost (S151, `4b45361`)** `email_logs`-tabel ontbreekt → verzonden mails onzichtbaar (500) — migratie 011 was gestampt maar nooit uitgevoerd op gedrifte DB's (restore-dumps); `sec13` gokte dit al ("may not exist on all environments"). Idempotente self-healing migratie `s151_heal_email_logs` (CREATE TABLE IF NOT EXISTS + indexes + RLS/policy/grant) heelt dev+prod, no-op waar tabel al bestaat. Rood→groen geverifieerd op gedrifte lokale DB + endpoint-regressietest. | Correspondentie |
| AUDIT-H10 | ✅ **Opgelost (S149, `91a5c0b`)** Verweer-switch schrijft naar niet-bestaand attribuut (teller reset niet) — `incasso_step_entered_at` → `step_entered_at` | Pipeline |
| AUDIT-H11 | ✅ **Opgelost (S151, `4fc4655`)** Pipeline negeert `case.status` — gesloten zaken (terminal-stap) bleven op het bord/queue staan omdat `move_case_to_step` `case.status` nooit schrijft en de filters daarop leunden. `get_pipeline_overview` + `get_queue_counts` sluiten nu zaken op een `is_terminal`-stap uit aan de bron (robuust, geen slug-afhankelijkheid, geen H1-guard-omzeiling). **Bewust NIET** pipeline→workflow-`case.status` gekoppeld (aparte productkeuze: "Afgesloten" heeft geen status-slug; "Betaald" moet H1-guard respecteren) → follow-up. Rood→groen test. | Pipeline |
| AUDIT-H12 | ✅ **Opgelost (S151, `4795f6e`, conservatief opgeschoond)** Payment-/debtor_response-automation-rules nergens geëvalueerd — rule-evaluator leest alleen `timeout`. `debtor_response` wordt al door de email-classificatie-hook afgehandeld (dode dubbele config); `payment` werd nergens gelezen. Seed maakt ze niet meer aan; migratie `s151_dead_pipeline_rules` deactiveert bestaande (5→0 actief elk, soft/omkeerbaar). **Bewust geen** nieuwe automatisering bedraad (flow ongetest). Rood→groen test. | Pipeline |
| AUDIT-H13 | ✅ **Opgelost (S151, `349e0ec`, conservatief opgeschoond)** Batch 'document genereren' werkt nooit op actieve stappen (template_type leeg → altijd geblokkeerd) — alle actieve stappen gebruiken de AI/HTML-route. `batch_preview`/`batch_execute` verwijzen nu naar de AI-conceptflow i.p.v. dood "geen briefsjabloon"; modal toont eerlijke empty-state. Actie blijft werken voor stappen mét DOCX-sjabloon. **Bewust geen** massa-AI-generatie aangezet (flow ongetest). Rood→groen test + tsc/build. | Pipeline |
| AUDIT-H14 | ✅ **Opgelost (S157, `1f66206`)** Vier-ogen: env-flag → tenant-setting `trust_allow_self_approval` + harde regel 2+ actieve users = altijd strikt (Voda 6.22 lid 8). Toggle + uitleg in Instellingen → Stichting Derdengelden. | Derdengelden |
| AUDIT-H15 | ✅ **Opgelost (S157, `aed1c10`)** Storno via tegenboeking: `reverse_transaction()` (type `reversal` + `reverses_id`); storting-storno direct met saldo-guard, debit-storno via vier-ogen; verrekening-storno heropent factuur. Storno-knop in DossierTab. | Derdengelden |
| AUDIT-H16 | ✅ **Opgelost (S157, `aed1c10`)** `undo_match()`: uitgevoerde match terugdraaien — trust-storno eerst (faalt veilig als geld al weg), betaling soft-delete + financials-refresh, transactie weer koppelbaar. 'Terugdraaien'-knop met verplichte reden. NB: deposit+payment dubbel boeken is juridisch correct (geld stáát op stichtingsrekening; payment = vorderingsadministratie). | Derdengelden/Betalingen |
| AUDIT-H17 | ✅ **Opgelost (S157, `c76f80d`)** Dedup op IBAN+Volgnr (fallback inhouds-hash) + unique constraint per tenant; her-import/dubbele rijen overgeslagen + geteld (`duplicate_count`, badge in importhistorie). | Betalingen |
| AUDIT-H18 | ✅ **Opgelost (S157, `c76f80d`)** Overbetaling: deposit vol bedrag, betaling gecapt op openstaand (`cap_to_outstanding`), overschot zichtbaar als saldo + melding. Bulk per-match in savepoint → geen wees-stortingen; respons `{executed, failed}`. Bonus: trust-deposit krijgt échte bankdatum + betalingskenmerk. | Betalingen |
| AUDIT-H19 | ✅ **Opgelost (S157, `d371b2b`)** Tab 'Ongekoppeld' (tenant-breed endpoint) + dialoog 'Koppel aan dossier' (koppelt + verwerkt direct). KPI 'Wachten op goedkeuring' klikbaar → drill-down met dossier-links. | Betalingen |
| AUDIT-H20 | ✅ **Opgelost (S149, `db2c767`)** AI-tool registreert betaling óók zonder dossier-instellingen — via gedeelde helper (zie AUDIT-B3) | Betalingen |
| AUDIT-H21 | ✅ **Opgelost (S149, `93c7968`)** Soft-delete guard negeert open facturen/derdengelden → wees-tegenpartij — delete_contact blokkeert nu op open facturen + niet-nul trust-saldo | Relaties |
| FIN-1 | ✅ **Opgelost (S158, `8965322`)** Geldstromen liepen uiteen: handmatige 'Via derdengelden'-betaling boekte géén trust-storting; bankimport-storting wel. Gedeelde helper `record_trust_debtor_payment()` boekt nu altijd trust-deposit **én** 6:44-betaling (gecapt) — bankimport gerefactored, handmatig idem. Derdengelden-verrekening krijgt eigen methode `verrekening_derdengelden` (vervuilt voorschotsaldo niet). DerdengeldenTab-storting blijft trust-only + hint. Onderzoek: `docs/research/financiele-samenhang.md`. | Betalingen/Derdengelden/Facturen |
| FIN-2 | ✅ **Opgelost (S170, `fc8b471`+`1ee1265`)** Afwikkel-paneel op de derdengelden-tab: routekeuze per dossier (verrekenen/doorbetalen) + checklist die de bestaande factuur-/verrekening-/uitbetaal-flows aanstuurt. Verschijnt op basis van het **saldo** i.p.v. een status → de "welke klaar-status"-ontwerpvraag omzeild. Afsluit-guard `requires_settled` op de "Afgesloten"-stap in `move_case_to_step` (Voda 6.19; "Betaald" blokkeert bewust niet) + dagelijkse talm-job (saldo >7 dagen stil). Archive-guard (S158) blijft. Fable-gereviewd (3 fixes). Ontwerp: `docs/research/afwikkel-flow-ontwerp-2026-07-05.md`. | Derdengelden/Dossier |
| READY-B1…B3 | 📋 **Readiness-audit (S158, Fable)** — VPS live geverifieerd. **3 blockers vóór echte data:** B1 debiteur-PII naar Moonshot/Kimi in AI-fallback-keten (AVG; Kimi strippen, besluit nodig) · B2 restore nooit getest (backups zelf draaien perfect + off-site) · B3 deploy zonder `alembic upgrade` + health-fail die niet faalt. Hoog: Sentry-DSN leeg, uptime-cron logt nooit, TOKEN_ENCRYPTION_KEY niet gezet (#95 = 10-min fix), ufw inactive, RLS fase 2. Rapport: `docs/research/readiness-audit.md`. | Infra/Security/AVG |
| CONN-1…14 | ◐ **Connectie-audit (S158, Fable)** — link-graaf + 6 journeys, 14 signalerings-/navigatiegaten. **✅ S159:** CONN-1 factuur-overdue-job+notif (`ef21ba6`) · CONN-2 vier-ogen-notif (`c09b4e2`) · CONN-3/4/14 Intake+Follow-up sidebar+badges (`d119153`) · CONN-5 notif-tab-context (`fe0804a`) · CONN-6 `?tab=`-fallback (`db9b429`). **✅ S160 (polish-batch):** CONN-8 rapportages drill-down + zaken-filters uit URL (`b82901e`, fixt ook de stille dashboard-`?status=`-link) · CONN-9 relatie→facturen-link (`d15d56a`) · CONN-10 uren→factureer-CTA (`abb09b1`) · CONN-11 zoek facturen+e-mails (`24c9893` backend + `64a5481` palette) · CONN-12 palette quick-actions (`64a5481`). **✅ S170:** CONN-7 (=FIN-2 afwikkel-wizard) gebouwd (zie FIN-2). **Open:** CONN-13 (Exact-sync-status, pas na Exact-activatie). Rapport: `docs/research/connectie-audit.md`. | App-breed |
| AI-AGENT | 🛑 **Besluit S160: GEEN autonome incasso-agent bouwen** (premortem-onderbouwd, `docs/premortem-ai-incasso-agent-2026-06-10.{html,md}`). 4 van 7 faalmodi komen uit autonomie zelf (onomkeerbare verkeerde brief → tuchtklacht; "omkeerbaar" juridisch een mythe; advocaat schaalt nooit op voorbij L1). De **assistent** blijft de eindvorm: AI leest dossier → maakt concept-bericht, **Lisanne beslist + handelt**. Als ooit tóch autonomie: eerst shadow-mode + pre-send legal-check, nooit één aan/uit-knop. | AI/Strategie |
| SECURITY | ◐ **Security-diepte (gestart S160).** ✅ **SEC-3 secrets schoon:** geen secrets in repo/git-historie; SECRET_KEY-guard `sys.exit(1)` op prod-boot; prod `.env` correct (production/debug-off/CORS-domein/86-char key). **Open (S161, multi-agent):** SEC-5 tenant-isolatie/IDOR (belangrijkste, vóór echte cliëntdata), SEC-1 auth/JWT, SEC-2 injectie, SEC-6 file-upload, SEC-7 rate-limit-dekking, SEC-8 exposure/headers, SEC-4 deps (npm audit: 4 build-tooling-vulns + pip-audit). Plan: `docs/sessions/PROMPT-S161.md`. | Security/AVG |
| AUDIT-H22 | ✅ **Opgelost (S151, `c7ba8f7`)** Taakstatus batch-gematerialiseerd — 324 taken tonen niet als 'overdue' — effectieve status nu afgeleid uit `due_date` op leestijd (zelfde root als H23/H24): helper `effective_task_status` + `WorkflowTaskResponse`-validator (takenlijst/my-tasks) + `get_calendar_events` (agenda status+kleur). Pydantic-laag, DB-kolom ongemoeid. Rood→groen test. | Taken/Agenda |
| AUDIT-H23 | ✅ **Opgelost (S149, `1c95843`)** Reports-KPI 'overdue_tasks' hangt aan stale status-veld — overdue/upcoming nu afgeleid uit due_date | Taken |
| AUDIT-H24 | ✅ **Opgelost (S149, `308fb13`)** Open taken blijven hangen op gearchiveerde dossiers — delete_case zet open taken op 'skipped' | Taken |
| AUDIT-H25 | `modules_enabled` niet server-side afgedwongen (per-module pricing) | Instellingen |

### MEDIUM (48) · LOW (31) · POLISH (4)
Volledige lijst met symptoom→oorzaak→bewijs→advies staat in `.audit/AUDIT-REPORT.md` (lokaal). Hoofdthema's: BTW-/credit-nota-/Exact-randgevallen (grotendeels latent, 0 live-data), agenda timezone/all-day, factuur-totaal-integriteit, dode/ongebruikte code, UX-polish. Visuele-laag extra's (tabel-overflow, stille KPI-degradatie, omgekeerd BTW-label) in `.audit/UI-FINDINGS.md`.

**✅ MEDIUM gefixt in S151 (4):** verjaring schrikkeldag-crash (`relativedelta`, `33a0ee9`) · `create_case` liet `nakosten_type`/`provisie_base` vallen (`30d3bf7`) · maandgrafiek negeerde `is_active` — 215 i.p.v. 2 (`000293a`) · agenda-event ongeldig/cross-tenant `case_id` → 404 i.p.v. 500 (`7d6b8ed`). _NB: deze 48 audit-MEDIUMs staan (bewust) niet als losse rows — bron blijft `.audit/AUDIT-REPORT.md`._

**✅ MEDIUM gefixt in S152 (4):** TASK_TYPES miste `verjaring_warning`/`review_ai_draft` die scheduler/automation al aanmaken (`bdef23e`) · producten geen unieke `(tenant_id, code)` → `MultipleResultsFound`-crash; partial-unique index actieve rijen + lookup op `is_active` (`b37c24f`) · `manual_match` blokkeert nu (409) bij bestaande PENDING-match → geen dubbele betaling (`c5a4547`) · `(bulk-)link emails` valideert doel-dossier-tenant → cross-tenant koppeling dicht (`9e70e6c`). **Niet gefixt:** C1 (CaseActivity bij mislukte SMTP) = non-issue (`get_db` rollbackt op raise); C4 (agenda timezone-grens) = niet schoon bounded (frontend). **~40 medium resterend** — lijst bevat non-issues + design/feature/legal, verifieer elk tegen code.

**✅ MEDIUM/HIGH gefixt in S153 (8):** #1 GET dossier-detail idempotent — refresh-on-read weg (`1523c67`) · #2 PUT factuur `btw_percentage` herberekent BTW (propageert naar geërfde regels, `3c01127`) · #3 "Verdeling type debiteur" op `Case.debtor_type` i.p.v. crediteur (`2d0eef9`) · #6 cross-tenant `product_id` op factuurregel geweigerd (`b026ef6`) · #5 batch `recalculate_interest` ressynct financiële cache i.p.v. no-op (`5e3ff02`) · #4 dossiernummer-regex ≥5 cijfers (factuurnr blokkeert contact-koppeling niet meer, `b2e58d1`) · **H4** openstaand incl. rente+BIK (zie boven) · **row 55** delete/cancel factuur geeft gelinkte uren+verschotten vrij (`1db7432`). Plus **H5 + griffierecht-MEDIUMs** (zie AUDIT-H5 hierboven).

**🔬 Griffierecht (H5) — ✅ GEFIXT S153** (was onderzocht S152, "samen met Lisanne"): officiële bron rechtspraak.nl gevonden → volledige 2026-tabel verwerkt; eiser-logica + onvermogenden bevestigd met gebruiker. Zie AUDIT-H5. **NB:** AUDIT-H6 (14-dagenbrief tegenstrijdige instructies) is een ánder item (Documenten/juridisch) en nog open.

**✅ Bounded crash-guards + row 59 — GEFIXT S154:** malformed JWT 500→401 (`c10e7c5`) · `_determine_direction` None-crash (`a098a09`) · `distribute_payment` negatief bedrag (`63385f9`) · row 59 14-dagenbrief rente-label neutraal zoals de sommatie (`9fa3de7`) · dead 'Standaard rente-instellingen'-blok op Kantoor-tab verwijderd (placeholder uit maart, sloeg niks op + fout BTW-label; `ee382f3`). Elk rood→groen / tsc-schoon.
**Audit-triage S154 (al opgelost / non-issue, geverifieerd tegen code):** #48 maandgrafiek `is_active`, #63 `create_case` nakosten/provisie, #84 verjaring schrikkeldag (`relativedelta` + `day=28`-fallback), #81 event cross-tenant `case_id` (al geguard → 404). **#93 Exact-sync `float()` op geld → ONDERZOCHT, NON-ISSUE:** Exact's REST API-reference typeert UnitPrice/Quantity/AmountDC als **Edm.Double** → OData v3 JSON vereist een JSON-**getal**, geen string. Auditadvies ("Decimal-string") was fout; `float()` is de juiste grensconversie. Code-comment toegevoegd tegen her-flaggen. Interne calc/opslag blijft `Decimal`.
**✅ Derdengelden-cluster H14–H19 — GEFIXT S157** (onderzoek: juridisch Voda/NOvA + concurrenten Clio/Smokeball/Actionstep/LEAP/BaseNet + code-audit; vastgelegd in `docs/research/derdengelden-regels.md`). Extra's: verrekening-bevestigingstaak (art. 6.19 lid 5 — wettelijk verplicht), reject-audit (`rejected_by/at/reason`), begunstigde verplicht bij uitbetaling, bankdatum/referentie op trust-deposits. **Vragen voor Lisanne** (vóór livegang, zie research-doc §5): wie is 2e stichtingsbestuurder + als approver in Luxis? · verrekenclausule in opdrachtbevestiging? · debiteuren betalen op stichtingsrekening?
**✅ MEDIUM-triage compleet — S157** (alle 52 rows beoordeeld, verdict per item in `.audit/TRIAGE-S157.md`): 20 waren al opgelost, 3 non-issue, **4 gefixt in S157** (#52 rente negeerde deelbetalingen · #61 hardcoded stichtings-IBAN ×16 → tenant-settings (betaalbrieven-IBAN dus klaar) · #69 mod-97 IBAN-validatie · #83 verjaring vanaf opeisbaarheid i.p.v. date_opened), 4 latent geparkeerd (credit-nota/EU-BTW-cluster), 16 design/feature → backlog.
**✅ MEDIUM gefixt in S163 (4 bounded, elk rood→groen + eigen commit):** #66 relatie-validatie (Pydantic KvK/e-mail/BTW/IBAN-validators op ContactCreate/Update, mod-97 IBAN naar gedeelde `app/shared/validators.py`) · #70 saldo row-lock (`_lock_case_for_balance` SELECT…FOR UPDATE in álle saldo-verlagende derdengelden-paden; race-test met 2 sessies + statement_timeout; ook #71-tautologie gefixt → `total_balance`-check) · #73 bedrag-match op totale schuld (payment-matcher gebruikt nu `get_financial_summary` grand_total incl. rente/BIK i.p.v. hoofdsom-restant, met fallback + cent-tolerantie) · #97 verweer-switch + advance-after-send via `move_case_to_step` (CaseStepHistory + pipeline_change-activity i.p.v. losse attribuut-write; dood `incasso_step_entered_at`-veld verwijderd). Plus `build(deps)` starlette 1.3.0→1.3.1 (CVE-2026-54283 blokkeerde de pip-audit-gate → deploy).
**✅ ook gefixt in S163 (na go gebruiker, `cd21c97`):** `update_case` step-wijziging (case-detail dropdown) loopt nu óók via `move_case_to_step` → history + pipeline_change-activity + `step_entered_at`-reset; de 3e step-bypass dicht (na #97's verweer-switch + advance).
**Resterend uit audit:** H25 (modules_enabled) · ~~#95 Fernet-key los van SECRET_KEY~~ → **token-re-encrypt UITGEVOERD in S164** (key staat los van SECRET_KEY; opgeslagen Outlook/IMAP-tokens her-versleuteld met `TOKEN_ENCRYPTION_KEY`; mail werkt weer) · BTW-op-rente (juridisch, samen met #54).

**S164-demosessie backlog (volgende sessie — zie `docs/sessions/PROMPT-S165.md`):** (1) cliënt-kenmerk/dossiernummer in Luxis bij factuur-upload (staat niet op factuur) · (2) particulier-naam (voor/achternaam) auto in wederpartij-veld bij factuur-upload · (3) staphistorie: verzonden brieven bijhouden (verstuurde 1e sommatie ontbreekt) · (4) 14-dagenbrief bij particulier (B2C) meenemen in gegenereerde brieven · (5) verweer-escalatie: na 2 inhoudelijke reacties → afsluitend ultimatum-bericht → volgende fase (patroon herkennen) · (6) **shadow-learning Optie A** (RAG uit Lisanne's echte verzonden antwoorden, door Arsalan goedgekeurd — plan + premortem, dan bouwen) · (7) H25 nog open.
**✅ Gefixt + live in S164 (demosessie):** e-mail dood door token (InvalidToken → re-encrypt) · "Sync inbox"-knop (Graph `$search`+`$orderby` 400-bug) · dossier-sync trok vreemde dossiers binnen (`force_case_id` nu fallback + bounce-guard) · concept opnieuw openen (CaseActionFeed + algemene takenlijst + dossier-taken-tab via `?draft=latest`) · nieuw-dossier-wizard verkeerde partij (stale `keepPreviousData` auto-match) + leesbare 422-fouten (`parseApiError`) · verweer-reactie (dubbel → simpel → Lisanne's exacte sjabloontekst, + auto-retry op 'XXX'-plaatshouder-flakiness).

---

## Go-To-Market Plan (voorbereid sessie 116, 7 april 2026)

**Status:** Voorbereid, nog niet actief. Arsalan is nog in bouw/validatie-fase met Lisanne. Dit plan wordt actief zodra Lisanne's dagelijkse workflow stabiel draait zonder blokkerende issues.

**Bron:** Marktonderzoek in `docs/research/marktonderzoek-2026-04/` (7 deep research rapporten + synthese). Strategische beslissing: lifestyle business met AI-leverage.

### Strategische positionering

- **Model:** Lifestyle business. Geen venture, geen investeerders, geen exit. Doel = duurzame cashflow voor Arsalan.
- **Realistisch ambitieniveau (met AI-leverage):** 100-300 klanten op termijn, €150K-400K/jaar winst.
- **Moat:** Velocity (uren-niveau response) + Nederlandse incasso-specialisatie + persoonlijke service.
- **Niet concurreren op:** Feature-breedte vs Clio/Kleos, AI-breedte vs Wolters Kluwer, marktaandeel vs Basenet.
- **Wel concurreren op:** Incasso-diepte (niemand heeft dit), iteratie-snelheid, persoonlijke support, transparante pricing, anti-lock-in (data-export als feature).

### ICP (Ideal Customer Profile)

**Primair segment:** Solo incasso-advocaten in de Randstad (Amsterdam, Rotterdam, Utrecht, Den Haag)

Waarom dit segment:
- 3.298 eenpitters in NL totaal, ~35% in Amsterdam
- Incasso is Luxis' unieke technische moat
- Solo-advocaten hebben korte beslis-cycli (geen commissie, geen RFP)
- Randstad = waar Lisanne's netwerk zit (warme intro's)
- 20-35% werkt nog met Excel/Word (Lexxyn 2021, n=128) → greenfield prospects

**Secundair segment (later):** Ex-Kleos/AdvocaatCentraal gebruikers (trauma-groep, actief zoekend)

### Pricing

| Pakket | Prijs | Doelgroep |
|--------|-------|-----------|
| **Founding customer** | €59/mnd per gebruiker, "voor altijd" | Eerste 10 klanten, in ruil voor case study + referentie + feedback |
| **Standaard** | €79/mnd per gebruiker | Alle klanten daarna |

Positionering:
- Onder Basenet Essentials (€69) + geen module-kosten
- Onder Kleos Advanced (€99)
- Boven "budget" perceptie (niet onder €50)
- Maandelijks opzegbaar (Basenet heeft 3 maanden opzegtermijn)
- Alle AI-features inbegrepen (niet apart bijkopen zoals BaseGPT €10/mnd)

### Distributie-strategie (voor wanneer GTM-fase start)

| Week | Actie | Target |
|------|-------|--------|
| 1-2 | Lisanne's netwerk: 5 introducties via warme intro | 1-2 klanten |
| 3-4 | LinkedIn persoonlijke outreach (50/week, geen mass templates) | 5 gesprekken/week |
| 5-6 | Advocatenblad/Advocatie.nl artikel over PMS-gaten voor incasso | Naambekendheid |
| 7-8 | Recht & ICT beurs OF NOvA event (netwerken, geen stand) | 10 gesprekken → 2 demo's |

**Geen paid ads, geen funnels, geen marketing automation.** Puur persoonlijk contact tot 10 klanten binnen.

### Werkverdeling

Geen vaste percentage-regel. Arsalan bepaalt per sessie wat nodig is. Tijdens de bouw/validatie-fase met Lisanne ligt de focus op bouwen en feedback verwerken. Zodra de GTM-fase actief wordt, verschuift de verdeling naar meer verkopen.

### Concrete actielijst (sessie 117+)

| # | Actie | Effort | Status |
|---|-------|--------|--------|
| GTM-01 | Lisanne vraagt om lijst van 10 introductie-namen | 30 min | ❌ TODO |
| GTM-02 | Simpele landingspagina luxis.nl (demo-only, geen features-lijst) | 2-4 uur | ❌ TODO |
| GTM-03 | Pitch van 3 zinnen schrijven en oefenen | 1 uur | ❌ TODO |
| GTM-04 | LinkedIn outreach template (persoonlijk, geen mass) | 1 uur | ❌ TODO |
| GTM-05 | 15-min demo-script voor eerste gesprekken | 2 uur | ❌ TODO |
| GTM-06 | Agenda blokkeren: 4 uur/dag verkopen voor 6 weken | 15 min | ❌ TODO |
| GTM-07 | Check of Fidura nog bestaat als advocaten-PMS | 30 min | ❌ TODO |
| GTM-08 | Kleos-migratie landingspagina (wedge voor trauma-groep) | 4-6 uur | ❌ TODO |
| GTM-09 | Basenet-migratie landingspagina (wedge voor prijsschok) | 4-6 uur | ❌ TODO |
| GTM-10 | Advocatenblad artikel schrijven over incasso-PMS gaten | 1 dag | ❌ TODO |
| GTM-11 | 5 advocaten interviewen (niet-Lisanne) voor validatie | 2 weken | ❌ TODO |

### Team-uitbreiding (wanneer)

- **Niet voor 50+ klanten** (€45K+/jaar ARR)
- **Volgorde:** virtueel assistent (admin, €500-800/mnd) → customer success part-time (bij 100+) → developer pas bij 300+
- **Niet eerst een developer** — klassieke solo-founder val

### Gedescoped (bewust NIET doen)

- Stitch UI redesign — overbodig pre-PMF
- Externe security audit — later, bij 50+ klanten
- Urios/Legalsense/Fidura herdraaien marktonderzoek — wachten tot na 10 echte gesprekken
- Feature race met Kleos/Clio AI — niet winbaar, niet nodig
- Aanverwante markten (notarissen, deurwaarders) — venture-denken, blijf bij advocaten
- Mass email marketing / ads / funnels — niet nodig tot 50+ klanten

### Marktonderzoek: belangrijkste vondsten samengevat

| Vondst | Implicatie voor Luxis |
|--------|----------------------|
| 20-35% NL kantoren zonder PMS (~1.500-2.000) | Greenfield = primaire doelgroep, nul switchkosten |
| Incassomodule is markt-brede witte vlek | Luxis' moat is echt, niet theoretisch |
| Basenet prijsstijging 73-148% (Blinqx) | Actief ontevreden klanten, wedge moment |
| Kleos Trustpilot 1,5/5 + "Hotel California" | Trauma-groep actief zoekend, 4 concurrenten hebben al migratiepagina's |
| Clio heeft geen NL-compliance | Clio geen directe concurrent (tenzij ze lokaliseren) |
| Fidura mogelijk niet-bestaand als advocaten-PMS | Uit concurrent-lijst schrappen, checken |
| Luxis TAM ~€3-6M/jaar | Klein voor venture, perfect voor lifestyle |

**Eerlijke caveats (bus-factor, 24/7 support, compliance updates):** bekend en manageable, geen dealbreakers voor gekozen ICP (solo incasso-advocaten).

---

## Audit 124 — 4-assige Opus 4.7 audit (22 april 2026)

Volledige rapporten: `docs/audits/audit-{1-financial,3-templates,4-multitenant,5-security}.md`. Rendered brieven: `docs/audits/rendered-samples/index.html`. Totaal: **11 Critical, 18 High, 29 Medium, 14 Low**.

### ✅ Opgelost in sessie 124 (commit `6fee872`)
- 14-dagenbrief laatste alinea "na dagtekening" → "na ontvangst" (HR Arno/RS Bekking — BIK-forfeit risico)
- `_fmt_currency` / `_format_currency`: "EUR 1.234,56" → "€ 1.234,56" (Nederlandse standaard)
- IBAN + Stichting Beheer Derdengelden + zaaknummer direct in betaalzin 14-dagenbrief

### ❌ Open — financieel-juridisch (audit 1 + 3)
| ID | Bevinding | Sev | Tijd |
|----|-----------|-----|------|
| AUD124-01 | ✅ BIK zonder BTW voor niet-BTW-plichtige cliënten — `Contact.is_btw_plichtig` veld | Critical | 2-3u |
| AUD124-02 | ✅ Rente op originele hoofdsom na deelbetaling — art. 6:44 BW (sessie 125, 22 apr) | Critical | 3-4u |
| AUD124-03 | ✅ Nakosten (€189/€287) toegevoegd — dropdown op case detail (sessie 125, 22 apr) | High | 2u |
| AUD124-04 | ✅ `bik_override_percentage` nu in payment + financial summary (sessie 125, 22 apr) | High | 1u |
| AUD124-05 | ✅ 14-dagen termijn 14→15 in workflow (sessie 125, 22 apr) | High | 0.5u |
| AUD124-06 | ✅ Factuur-PDF auto-attach uitgebreid naar alle sommatie-varianten + 14-dagenbrief (sessie 125, 22 apr) | High | 0.5u |
| AUD124-07 | ✅ `_fmt_currency` consistent — 14-dagenbrief letter was al €; gefixt: 3x EUR→€ + Dutch format in workflow/hooks.py CaseActivity (sessie 137, 13 mei) | Low | 0.2u |

### ✅ Afgerond — multi-tenant (audit 4, sessie 125, 22 apr)
| ID | Bevinding | Sev | Status |
|----|-----------|-----|--------|
| AUD124-08 | ✅ RLS policies toegevoegd op 4 ontbrekende tables | High | Gefixt |
| AUD124-09 | ⚪ Scheduler bypass RLS — by design (cross-tenant queries, expliciet tenant_id filter) | High | By design |
| AUD124-10 | ✅ APP_ENV guard case-insensitive + "prod"/"prd" varianten | High | Gefixt |
| AUD124-11 | ✅ tenant_id assertion in get_current_user | Med | Gefixt |
| AUD124-12 | ✅ Cross-tenant FK validatie in create_invoice | Med | Gefixt |

### ✅ Afgerond — security (audit 5, sessie 125, 22 apr)
| ID | Bevinding | Sev | Status |
|----|-----------|-----|--------|
| AUD124-13 | ✅ SECRET_KEY guard: blacklist + min 32 chars | Critical | Gefixt |
| AUD124-14 | ✅ Login timing equalization: dummy bcrypt | Critical | Gefixt |
| AUD124-15 | ✅ Workflow + template write endpoints admin-only | High | Gefixt |
| AUD124-16 | ✅ Email compose HTML gesanitized via DOMPurify | High | Gefixt |
| AUD124-17 | ⚪ File encryption at rest — mitigated door Hetzner disk encryption | High | Deferred |
| AUD124-18 | ✅ Separate TOKEN_ENCRYPTION_KEY (fallback SECRET_KEY) | High | Gefixt |
| AUD124-19 | ✅ JWT algorithm hardcoded HS256 | High | Gefixt |
| AUD124-20 | ✅ WeasyPrint SSRF: url_fetcher blokkeert externe URLs | Med | Gefixt |
| AUD124-21 | ✅ /api/auth/logout endpoint (revokes all refresh tokens) | Med | Gefixt |
| AUD124-22 | ⚪ forgot-password timing — mitigated (constant response + 3/hour + background task) | Med | Mitigated |
| AUD124-23 | ⚪ Audit trail — feature, apart plannen | Med | Deferred |

### Nuances (geen bug, overwogen)
- Finding "handelsrente niet auto-B2B" = geen bug; `cases/service.py:399` gebruikt `client.default_interest_type` als gezet.
- Finding "dubbel valutasymbool €&nbsp;EUR" niet reproduceerbaar in sample-render.

### Volgorde van aanpak (afgerond)
**Batch 2 (sessie 125):** ✅ AUD124-01 t/m AUD124-06 (financieel-juridisch). Afgerond 22 apr.
**Batch 3 (sessie 125):** ✅ AUD124-08, 13, 14 (security Criticals + RLS). Afgerond 22 apr.
**Batch 4 (sessie 125):** ✅ AUD124-15, 16, 19 (access control + XSS). Afgerond 22 apr.
**Batch 5 (sessie 125):** ✅ AUD124-10, 11, 12, 18, 20, 21 (remaining High/Med). Afgerond 22 apr.
**Deferred:** AUD124-17 (file encryption), AUD124-23 (audit trail). Niet urgent voor huidige fase.

### 📋 Gepland — /ultrareview (Claude Code multi-agent cloud review)

3 gratis reviews beschikbaar (geldig tot 5 mei 2026, daarna $5-20 per run). Prioriteit:
1. **Financiele module** — interest.py, wik.py, payment_distribution.py (meest kritisch)
2. **Auth + multi-tenant isolatie** — RLS, JWT, tenant scoping
3. **Incasso pipeline** — 20 stappen, batch acties, state machine

### ✅ Gefixt — BUG-70: AI smart replies / drafts niet persistent (sessie 129)

AIDraft model + `ai_drafts` tabel. Drafts worden nu persistent opgeslagen in DB met status workflow (generated → reviewed → approved → sent / discarded). CRUD endpoints: POST generate, GET list/detail, PATCH status. Auto-draft via orchestrator gebouwd maar DISABLED (kwaliteit onvoldoende, kost API credits). Handmatige draft generatie werkt en persisteert.

---

## Audit 110 — Actiepunten (28 maart 2026)

Volledige audit: `docs/FULL-AUDIT-110.md`. Score: **7.2/10**. Testplan: Bijlage E (100+ testcases).

### P0 — Blokkerend voor productie

| # | Item | Effort | Status |
|---|------|--------|--------|
| AUDIT-01 | Uptime monitoring instellen (UptimeRobot, gratis) | 1 sessie | ✅ Health endpoint bevestigd, user moet UptimeRobot account aanmaken |
| AUDIT-02 | Backup restore test — bewijs dat restore werkt | 0.5 sessie | ✅ Restore getest: 43 tabellen, alle data intact (sessie 110) |
| AUDIT-03 | Uitgebreid testen — alle features top-tot-teen (zie testplan Bijlage E) | 6-8 sessies | ✅ Alle 9 secties getest sessie 110. Alle endpoints werken. Geen blokkers gevonden. |
| AUDIT-04 | Basenet export opvragen bij Lisanne + formaat analyseren | 1 sessie | ✅ **S166** — XML-export ontvangen (`Xml_02-07-2026_2400.zip`), formaat gekraakt (137 bestanden, per-record parser), mapping ontworpen. Documenten-backup (11,5 GB, apart deel) aangevraagd |
| AUDIT-05 | Data-migratie script bouwen + dry-run | 3-5 sessies | ✅ **UITGEVOERD S168** — schone-lei-wipe (backup+restore bewezen) → fase 1 (1168 relaties/607 dossiers/1563 vorderingen, 0 mismatch) + fase 2 (`import_emails.py`, 6393 .eml→synced_emails onder import-account) + fase 3 (`classify_and_backfill.py`, 344 gericht op Haiku → 131 verweer-kandidaten). Dossiers = passief archief. **Fase 1b (betalingen + persoon↔bedrijf ContactLinks) bewust overgeslagen** (peripheer, geen AI-kost) — optioneel S169+ |

### P1 — Belangrijk voor werkbaarheid

| # | Item | Effort | Status |
|---|------|--------|--------|
| AUDIT-06 | Compose dialog: "Verstuur" als primaire knop (direct send via Graph API), "Open in Outlook" als backup | 1 sessie | ✅ Sessie 110 |
| AUDIT-07 | Outlook agenda sync via Graph API (CalendarEvents) | 2-3 sessies | ✅ Sessie 111 (28 mrt) |
| AUDIT-08 | Database indices op veelgebruikte filterkolommen (synced_emails.email_date, workflow_tasks.due_date, cases.status+tenant_id) | 1 sessie | ✅ Alle indices bestaan al (sessie 110 geverifieerd) |
| AUDIT-09 | 14-dagentermijn berekening verifieren (dag NA ontvangst, niet na verzending) | 0.5 sessie | ✅ Gefixt sessie 110 (today+15) |
| AUDIT-10 | Verjarings-waarschuwing automatiseren (90/60/30 dagen alert) | 1 sessie | ✅ Sessie 110 — scheduler maakt taken aan |
| AUDIT-11 | Rollback procedure documenteren + testen | 1 sessie | ✅ Gedocumenteerd in RUNBOOK.md sessie 110 |
| AUDIT-12 | unattended-upgrades installeren op VPS | 0.5 sessie | ✅ Was al actief, geverifieerd sessie 110 |
| AUDIT-13 | Follow-up advisor: 1-klik approve+execute (doc genereren + email + pipeline advance) | 1-2 sessies | ✅ Was al geïmplementeerd |
| AUDIT-14 | Classification flow: 1-klik "Goedkeuren en uitvoeren" | 0.5 sessie | ✅ Sessie 110 — approve-and-execute endpoint + UI |

### P2 — Nice-to-have / toekomst

| # | Item | Effort | Status |
|---|------|--------|--------|
| AUDIT-15 | Exact Online integratie (boekhouding sync) | 1 sessie (vereenvoudigd) | ✅ Sessie 112 — OAuth + sync module gebouwd |
| AUDIT-16 | ~~Online betalen via Mollie/iDEAL~~ | — | ❌ Geschrapt — niet relevant voor advocatenkantoor |
| AUDIT-17 | Rapport-pagina (management overzichten, omzet, incasso-KPIs) | 2-3 sessies | ✅ Sessie 111 (28 mrt) |
| AUDIT-18 | Betalingsbelofte-extractie uit debiteur-emails (AI) | 2 sessies | ✅ Backend sessie 111 + Frontend sessie 112 |
| AUDIT-19 | Aangetekend Mailen API integratie (Aangetekend B.V., eIDAS) | 2-3 sessies | ⏸️ Pas bij hoog volume |
| AUDIT-20 | Pre-send compliance check (14-dagenbrief validatie, WIK check) | 2 sessies | ✅ Sessie 110 — 6 checks (14-dagen, BIK, debiteur, vorderingen, verzuimdatum, verjaring) |
| AUDIT-21 | ~~Email analytics (open rate, click rate)~~ | — | ❌ Geschrapt — juridische brieven, geen marketing |
| AUDIT-22 | Auto-update naar opdrachtgever (AI draft bij betaling/statuswijziging) | 1-2 sessies | ✅ Sessie 110 — /client-update endpoint |
| AUDIT-23 | BIK override validatie — mag niet hoger dan WIK-staffel bij B2C | 0.5 sessie | ✅ Sessie 110 |
| AUDIT-24 | Griffierechten-tabel integreren | 1 sessie | ✅ Sessie 110 — kanton + rechtbank tarieven 2026 |
| AUDIT-25 | AI smart replies — incasso-specifieke suggesties bij debiteur-emails (3 opties: betalingsregeling/betwisting afhandelen/escaleren) | 2 sessies | ✅ Backend sessie 111 + Frontend sessie 112 |
| AUDIT-26 | ~~iDEAL payment link in incasso-emails~~ | — | ❌ Geschrapt — duplicaat van AUDIT-16 |
| AUDIT-27 | ~~Closed-loop betaling~~ | — | ❌ Geschrapt — vereist bankfeed, te vroeg |
| AUDIT-28 | Sentiment/toon analyse op debiteur-emails — boos/meewerkend/wanhopig detectie voor triage | 1 sessie | ✅ Sessie 110 — AI prompt + model + schema + migratie |
| AUDIT-29 | Workflow auto-email bij statuswijziging — nu alleen taken, optioneel ook email versturen | 1 sessie | ✅ Was al geïmplementeerd (auto_execute send_email hooks) |
| AUDIT-30 | ~~Client portal~~ | — | ❌ Geschrapt — debiteuren gebruiken dit niet |

### Volgorde van aanpak

```
1. AUDIT-01 + AUDIT-02 + AUDIT-12  (infra basics, 1 sessie)
2. AUDIT-03                         (uitgebreid testen, 6-8 sessies)
3. AUDIT-06                         (compose dialog fix, 1 sessie)
4. AUDIT-04 + AUDIT-05              (data-migratie, 4-6 sessies)
5. GO LIVE — Lisanne begint met nieuwe dossiers in Luxis
6. P1 items (AUDIT-07 t/m AUDIT-14) na go-live
7. P2 items op basis van Lisanne's feedback
```

---

## Projectdocumenten

### In de Git repo (`C:\Users\arsal\Documents\luxis\`)

| Document | Doel | Status |
|----------|------|--------|
| `LUXIS-ROADMAP.md` | **Dit document** — overzicht van alles. Status, prioriteit, bugs, features | **ENIGE source of truth** — alle andere docs verwijzen hiernaar |
| `docs/ARCHITECTUUR-KAART.md` | **Verbindingskaart** — hoe alle systemen aan elkaar hangen (2 pag.) | **Elke sessie eerst lezen** (auto via SessionStart-hook); bijwerken bij elke koppeling-wijziging |
| `docs/audit/inventaris-2026-07-05.md` | Feitelijke feature-inventaris + dubbele systemen + verweer-woordenschat (audit S172) | Referentie — wat er ÍS |
| `CLAUDE.md` | AI development guide, architectuurregels, werkwijze | Actief (staat ongecommit gewijzigd — eerst met Arsalan afstemmen) |
| `backend/CLAUDE.md` / `frontend/CLAUDE.md` | Backend/frontend-conventies | Actief |
| `docs/DECISIONS.md` | Tech stack keuzes + onderbouwing | Deels stale (Celery/Nginx/jose — zie audit S172); paden gecorrigeerd S172 (stonden op repo-root) |
| `docs/FEATURE-INVENTORY.md` | Markt-checklist: wat een PMS zou kúnnen (concurrent-onderzoek) | Referentie — de "wat zou kunnen" lijst (NIET wat er is) |
| `docs/research/UX-REVIEW.md` / `UX-VERBETERPLAN.md` / `BUGS-EN-VERBETERPUNTEN.md` / `PROMPT-TEMPLATES-IN-WORKFLOW.md` | Historische detail-docs (feb-mrt 2026) | Archief — status staat in deze roadmap |

### Op Bureaublad (`C:\Users\arsal\OneDrive\Bureaublad\Kesting Legal\Luxis\`)

| Document | Doel | Status |
|----------|------|--------|
| `LUXIS-PROJECT-PROMPT.md` | Oorspronkelijk projectbriefing (wie, wat, waarom, fasering) | Verwerkt in deze roadmap — bewaren als archief |
| `TECH-STACK-DECISION-PROMPT.md` | Opdracht die leidde tot DECISIONS.md | Verwerkt — bewaren als archief |


---

## Tech Stack (samenvatting)

> Volledige onderbouwing: zie `DECISIONS.md`

- **Backend:** FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic + PostgreSQL 16
- **Frontend:** Next.js 15 (React 19, App Router) + shadcn/ui + Tailwind CSS
- **Auth:** Custom JWT (PyJWT + bcrypt — python-jose vervangen S90)
- **Docs:** docxtpl + WeasyPrint
- **Scheduling:** APScheduler (géén Celery — dode dependency, verwijderen; audit S172). Redis alleen voor rate-limiting/OAuth-nonce
- **Hosting:** Hetzner VPS (CX33) + Docker Compose + Caddy + Let's Encrypt
- **Monitoring:** Sentry nog NIET actief (DSN leeg — actiepunt Arsalan sinds S159); self-hosted uptime-cron draait wel

---

## Kernregels

1. **Financial precision:** ALL money = Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NEVER float.
2. **Multi-tenant isolation:** `TenantBase` + `tenant_id` op alles. Row-Level Security.
3. **Dutch UI, English code.**
4. **Onderzoek eerst, bouw daarna.** Elke feature: onderzoek → plan → bouw → check.
5. **Lisanne-toets:** "Zou ze dit begrijpen zonder uitleg?" Zo nee, versimpel.
6. **Product, geen tooltje.** Elk scherm alsof het morgen gelanceerd wordt.

---

## Wat er al gebouwd is

### Backend (110+ endpoints, 13 routers)
- **Auth:** Login, refresh, registration, password change, user/tenant CRUD
- **Relaties:** CRUD, zoeken, typefilter, contact links (persoon-bedrijf)
- **Zaken:** CRUD, status workflow (enforced transitions), activities, parties, conflict check
- **Tijdschrijven:** CRUD, dagfilter, zaakfilter, summary, `/my/today` endpoint
- **Facturatie:** CRUD, lifecycle (concept→goedgekeurd→verzonden→betaald), PDF generatie, BTW
- **Onkosten:** CRUD, billable/uninvoiced tracking
- **Documenten:** Templates beheer, document generatie (docx/pdf), merge fields
- **Workflow:** Rules, taken CRUD, status transities, scheduler, verjaring bewaking
- **KYC/WWFT:** Identificatie, UBO, PEP/sanctie, risicoclassificatie, review scheduling
- **Incasso:** Claims, betalingen, arrangementen, derdengelden, wettelijke rente (compound), WIK/BIK, art. 6:44 BW imputatie, financieel overzicht
- **Dashboard:** Summary, recent activity, my-tasks
- **Settings:** Tenant CRUD, module management
- **Health:** Health check endpoint

### Frontend (pagina's)
- Login
- Dashboard (statistieken, recente zaken, deadlines, KYC warnings, incasso pipeline)
- Relaties (lijst, detail, aanmaken, bewerken)
- Zaken (lijst, detail, aanmaken, status wijzigen, workflow taken)
- Tijdschrijven (lijst, invoer, bewerken)
- Facturatie (lijst, aanmaken, PDF download, status transities)
- Documenten (template catalogus, generatie)
- Agenda (maand/week view, kleurcodering)
- Instellingen (kantoorgegevens, modules)

### Module systeem
Togglebare modules per tenant: `incasso`, `tijdschrijven`, `facturatie`, `wwft`, `budget`

---

## Wat er gebouwd moet worden

### Fase A: Quick Wins — Backend is al klaar (puur frontend)

| # | Feature | API klaar? | Complexiteit | Status |
|---|---------|-----------|-------------|--------|
| A1 | Timer voor tijdschrijven | ✅ `/my/today` | Klein | ✅ Gebouwd (floating timer, persistent via localStorage, globale context) |
| A2 | Global search (Ctrl+K) | ✅ `/api/search` endpoint gebouwd (F1, commit `97e9d22`) | Klein-Midden | ✅ Gebouwd (backend search router + frontend werkt) |
| A3 | "Mijn Taken" pagina | ✅ `/dashboard/my-tasks` | Klein | ✅ Gebouwd (dedicated pagina, groepering op datum, filter, complete/skip met 1 klik) |
| A4 | Activity timeline op zaakdetail | ✅ `/cases/{id}/activities` | Klein-Midden | ✅ Gebouwd (timeline met gekleurde iconen, relatieve tijden, inline notitie, paginatie, user info) |
| A5 | Contact-bedrijf koppelingen UI | ✅ `/relations/links` | Klein | ✅ Gebouwd (ContactLinks component, zoek-dropdown, rol selectie, CRUD) |
| A6 | Derdengelden UI verbeteren | ✅ Complete API | Klein | ✅ Gebouwd (saldokaarten, approval workflow, storting/uitbetaling forms, twee-directeurengoedkeuring) |
| A7 | Financieel overzicht zaak verbeteren | ✅ `/cases/{id}/financial-summary` | Klein | ✅ Gebouwd (KPI-kaarten, betalingsvoortgang progress bar, breakdown-tabel met mini-bars) |

### Fase B: Zaakdetail transformatie (kan parallel met C)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| B1 | Tabbed interface op zaakdetail | Groot | ✅ Gebouwd (9 tabs: Overzicht, Taken, Vorderingen, Betalingen, Financieel, Derdengelden, Documenten, Activiteiten, Partijen) |
| B2 | Quick actions bar op zaakdetail | Klein | ✅ Gebouwd (Uren loggen, Notitie, Document, Factuur, Renteoverzicht — contextueel) |
| B3 | Notities verbeteren | Klein | ✅ Gebouwd (rich text editor met Tiptap — bold/italic/bullets toolbar, WYSIWYG, backward compat met plain text, 11 mrt) |

### Fase C: Dashboard & Facturatie (kan parallel met B)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| C1 | Dashboard verbeteren (vandaag-focus, grafieken, KPI's) | Midden | ✅ Gebouwd (KPI's, pipeline bar, taken widget, weekoverzicht, recente facturen/activiteit) |
| C2 | Betalingstracking op facturen | Groot (nieuw DB model) | ✅ Volledig gebouwd (backend: model, CRUD, auto-status, 18 tests + frontend: payment tracking UI, progress bar, form, deels-betaald status) |
| C3 | Credit nota's | Midden | ✅ Gebouwd (20 feb) — invoice_type + linked_invoice_id, CN-nummering, credit nota aanmaken vanuit factuurdetail, regels pre-fill, purple styling, lijst-weergave met CN badge |

### Fase D: Algemene UX polish

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| D1 | Wachtwoord vergeten flow | Klein-Midden | ✅ Gebouwd (forgot-password op login, reset-password pagina met token, 3-staps flow, email sending via SMTP ✅). ✅ BUG-15 gefixt (25 feb). |
| D2 | Gebruikersbeheer (rollen, rechten) | Groot | ❌ Niet relevant (Lisanne is enige gebruiker) |
| D3 | Navigatie-verbeteringen | Klein | ✅ Gebouwd (breadcrumbs met dynamische labels, nested routes) |
| D4 | Empty states en loading states | Klein | ✅ Gebouwd (skeleton loaders op alle dashboard pagina's) |
| D5 | Agenda events aanmaken | Midden (nieuw model + CRUD) | ✅ Gebouwd (20 feb) — CalendarEvent model met 7 typen, CRUD endpoints, EventDialog create/edit/delete, unifide calendar hook, case/contact pickers |

### Frontend Polish (sessie 48, 11 maart)

| # | Verbetering | Status |
|---|-------------|--------|
| FP1 | Status badge constants geconsolideerd → `lib/status-constants.ts` (was gedupliceerd in 4+ pagina's) | ✅ |
| FP2 | Instellingen pagina opgesplitst: 2113-regels monoliet → 9 tab componenten + thin shell | ✅ |
| FP3 | Documenten pagina hernoemd naar "Sjablonen" met duidelijkere beschrijving | ✅ |
| FP4 | BUG-1 refix: wederpartij prefill bij nieuw dossier vanuit relatie detailpagina | ✅ |

### Frontend UX Polish (sessie 61, 13 maart)

| # | Verbetering | Status |
|---|-------------|--------|
| FP5 | Delete confirmations toegevoegd aan uren, documenten, factuurregels | ✅ |
| FP6 | Empty states gestandaardiseerd (taken, uren, documenten → standaard patroon) | ✅ |
| FP7 | Mobile responsive tables: non-essentiële kolommen hidden op sm: breakpoint | ✅ |
| FP8 | Invoice status badges: ring-1 ring-inset voor visuele consistentie | ✅ |
| FP9 | ARIA labels op checkboxes en navigatie, focus rings op filter buttons | ✅ |
| FP10 | Button sizing + error styling + unused imports opgeruimd | ✅ |

### Fase E: Verbeterpunten uit handmatige test (sessie 2, 20 feb)

| # | Feature | Complexiteit | Prioriteit | Status |
|---|---------|-------------|-----------|--------|
| E1 | "Zaken" hernoemen naar "Dossiers" in hele frontend UI | Klein | 🔴 Hoog | ✅ Gebouwd (20 feb) — puur display, code blijft `case/cases` |
| E2 | Tarieven vereenvoudigen: dropdown op dossierniveau i.p.v. aparte pagina | Klein | 🔴 Hoog | ✅ Gebouwd (20 feb) — tarieven-pagina verwijderd, rentetype blijft op dossierniveau |
| E3 | Facturen-tab op dossierdetail | Klein-Midden | 🔴 Hoog | ✅ Gebouwd (case_id filter op backend, FacturenTab met lijst/status/bedragen/empty state) |
| E4 | Documenten uploaden in dossier | Groot (storage + nieuw model) | 🔴 Hoog | ✅ Gebouwd (20 feb) — CaseFile model, drag & drop upload, download, soft-delete, Docker volume |
| E5 | Slimme facturatie-flow (onbefactureerde uren tonen, batch factureren) | Groot | 🔴 Hoog | ✅ Gebouwd (20 feb) — invoiced tracking op TimeEntry, batch import met checkboxes, Quick Bill vanuit dossierdetail |
| E6 | Debiteuren/crediteuren overzicht bij facturen | Midden | 🟡 Midden | ✅ Gebouwd (20 feb) — aging 0-30/31-60/61-90/90+ dagen, KPI-kaarten, per-relatie tabel met AgingBar, tab op facturenpagina |
| E7 | Auto-timer bij openen dossier (handmatig + automatisch modus) | Midden | 🟡 Midden | ✅ Gebouwd (20 feb) — opt-in auto-start, dossierwisseling auto-save, activity type dropdown, vergeten-timer-waarschuwing 2u, multi-tab sync |
| E8 | E-mail templates (onderwerp + body + merge fields) | Midden | 🟢 Later | ✅ Gebouwd (20 feb) — onderdeel van T3 |

**Voorgestelde bouwvolgorde:** E1 → E2 → E3 → E4 → E5 → E6 → E7 → E8

### Apart traject: Templates in workflow (na B1)

| # | Feature | Complexiteit | Status |
|---|---------|-------------|--------|
| T1 | Templates op zaakdetail (status-filtered) | Midden | ✅ Gebouwd (20 feb) — STATUS_TEMPLATE_MAP, aanbevolen/overige/verborgen secties, B2B/B2C filter |
| T2 | Workflow-suggesties bij statuswijziging | Klein-Midden | ✅ Gebouwd (20 feb) — amber suggestie-banner na statuswijziging, auto-dismiss 30s, "Ga naar documenten" knop |
| T3 | E-mail versturen vanuit Luxis (SMTP) | Groot | ✅ Gebouwd (20 feb) — compose dialog, send knop, correspondentie tab, email logs, test email, instellingen tab. **Nu via OutlookProvider (Graph API) met seidony@kestinglegal.nl op M365.** |

> Detail: zie `PROMPT-TEMPLATES-IN-WORKFLOW.md`
> E-mail templates (E8) wordt onderdeel van T3

---

## Bugs

> Detail + bestanden + fix-instructies: zie `BUGS-EN-VERBETERPUNTEN.md`

| # | Bug | Ernst | Fix-grootte | Status |
|---|-----|-------|-------------|--------|
| BUG-1 | Relatie niet automatisch gekoppeld bij nieuwe zaak vanuit relatiedetail | Hoog | Klein (URL params + form pre-fill) | ✅ Gefixt (20 feb). ✅ Heropend + gefixt (11 mrt) — opposing_party_id prefill + "Als wederpartij" link + lege-state link gefixt |
| BUG-2 | Rente-velden zichtbaar bij niet-incasso zaaktypes | Midden | Klein (conditional render) | ✅ Gefixt (20 feb) |
| BUG-3 | Renteberekening per documentdatum controleren | Hoog | Verificatie nodig | ✅ Geverifieerd — werkt correct (20 feb) |
| BUG-6 | Conflict check mist op zaakdetail Partijen tab (warning, niet blokkeren) | Midden | Klein | ✅ Gefixt (20 feb) |
| BUG-7 | Dossiergegevens niet bewerkbaar op detailpagina — `court_case_number` (F5) toont alleen als gevuld maar kan nergens ingevuld worden. Dossierdetail mist edit-modus voor alle velden (beschrijving, referentie, zaaknummer, etc.) | Hoog | Midden | ✅ Gefixt (21 feb) — Bewerken-knop + inline edit met Opslaan/Annuleren, zaaknummer altijd zichtbaar |
| BUG-8 | `court_case_number` veld ontbreekt op "Nieuw dossier" formulier — kan alleen via (niet-bestaande) edit-modus op detailpagina | Midden | Klein | ✅ Gefixt (21 feb) — veld toegevoegd aan formulier + backend CaseCreate schema |
| BUG-9 | Advocaat wederpartij niet zichtbaar/toevoegbaar in dossier — gebruiker kan niet in één oogopslag zien wie de belangrijkste contactpersonen zijn | Hoog | Midden | ✅ Gefixt (21 feb) — zoekfield toegevoegd in Dossiergegevens (view+edit) + Nieuw dossier form |
| BUG-10 | Dossier edit: velden wissen werkt niet — je kunt tekst toevoegen en opslaan, maar als je het wist en opslaat blijft de oude waarde staan. Oorzaak: `\|\| undefined` in handleSaveDetails. | Hoog | Klein | ✅ Gefixt (21 feb) — `.trim() \|\| null` stuurt lege velden als null mee |
| BUG-11 | Taken niet zichtbaar na aanmaken in dossier — `useWorkflowTasks` verwachtte paginated object maar backend retourneert array. Ook: geen `assigned_to_id` bij handmatig aanmaken → taak verscheen niet bij Mijn Taken | Hoog | Klein | ✅ Gefixt (22 feb) — hook return type gecorrigeerd, `assigned_to_id` auto-set |
| BUG-12 | Geen "Nieuwe taak" optie op Mijn Taken pagina — kon alleen vanuit dossier taken aanmaken | Midden | Klein | ✅ Gefixt (22 feb) — Nieuwe taak knop + formulier met dossier-picker |
| BUG-13 | Email-bijlage openen geeft 401 — directe `<a href>` link stuurt geen Bearer token mee. Fix: blob URL + fetch (zelfde patroon als G11 preview) | Hoog | Klein | ✅ Gefixt (23 feb) |
| BUG-14 | Email-bijlage niet opslaan als dossierbestand — geen knop/endpoint om bijlage te archiveren bij dossier. Fix: backend copy endpoint + frontend "Opslaan in dossier" knop | Midden | Klein-Midden | ✅ Gefixt (23 feb) |
| BUG-15 | Reset-password pagina hangt oneindig — browser POST naar `https://luxis.kestinglegal.nl/api/auth/reset-password` bereikt backend niet. Caddy reverse proxy draait niet, Next.js had geen rewrite. Fix: Next.js rewrite proxy `/api/*` → `backend:8000` + relatieve URLs. | Hoog | Midden | ✅ Gefixt (25 feb) |
| BUG-16 | Dashboard "Mijn Taken" widget toonde geen taken — `useMyOpenTasks` gebruikte `/api/workflow/tasks?status=due` (alleen "due" taken), terwijl taken op "pending" of "overdue" stonden. Fix: nu gebruikt hetzelfde endpoint als Mijn Taken pagina (`/api/dashboard/my-tasks`). | Midden | S (1 regel) | ✅ Gefixt (25 feb) |
| BUG-17 | Velden leegmaken + opslaan werkte niet (site-breed) — `|| undefined` in form handlers → JSON.stringify dropt de key → backend's `exclude_unset=True` slaat update over. 51 instances in 18 bestanden. | Hoog | M (18 bestanden, 86 regels gewijzigd) | ✅ Gefixt (25 feb) |
| BUG-18 | Klik op taak in dashboard/Mijn Taken navigeert niet naar het juiste dossier — taak-titel was `<p>`, nu `<Link>` naar `/zaken/{case_id}` in zowel dashboard widget als Mijn Taken pagina. | Midden | S | ✅ Gefixt (25 feb) |
| BUG-19 | Factuur aanmaken → redirect naar factuurpagina geeft "fout bij laden" — race condition: `get_db` dependency commit na response. Fix: explicit `db.commit()` in create_invoice router + `setQueryData` cache pre-populate in frontend. | Hoog | S-M | ✅ Gefixt (25 feb) |
| BUG-20 | Budget module onbekend: "Onbekende modules: budget" — `VALID_MODULES` in `settings/schemas.py` miste `"budget"`. Toegevoegd. | Hoog | S | ✅ Gefixt (25 feb) |
| BUG-21 | Advocaat wederpartij niet zichtbaar na aanmaken/bewerken dossier + budget niet opgeslagen bij aanmaken — twee oorzaken: (1) `create_case` service miste `budget` + 7 andere velden in Case constructor, (2) `get_case` en `add_case_party` hadden geen explicit `selectinload` voor nested `parties→contact` relatie (async SQLAlchemy laadt nested selectin niet automatisch). Fix: velden toegevoegd + explicit `selectinload(Case.parties).selectinload(CaseParty.contact)` in queries. | Hoog | M | ✅ Gefixt (25 feb) |
| BUG-22 | Invoice detail 500 Internal Server Error — `GET /api/invoices/{id}` crashte door circulaire `lazy="selectin"` op Invoice self-referential relationships (`credit_notes` en `linked_invoice`). | Hoog | M | ✅ Gefixt (25 feb, sessie 20) |
| BUG-23 | `/notifications` endpoints 404 — Frontend riep `/notifications` en `/notifications/unread-count` aan op elke pagina maar er bestond geen backend module. Drie sub-issues: (1) module bestond niet, (2) import path was fout (`app.auth.dependencies` i.p.v. `app.dependencies`), (3) frontend miste `/api/` prefix in API calls. | Midden | M | ✅ Gefixt (25 feb, sessie 20) |
| BUG-24 | `/api/users` endpoint 404 — Frontend riep `/api/users` aan voor dossierlijst filters maar endpoint bestond niet. | Laag | S | ✅ Gefixt (25 feb, sessie 20) |
| BUG-25 | Timer FAB z-index overlap — timer FAB overlapt met header. Fix: z-40→z-50. | Laag | S | ✅ Gefixt (27 feb, sessie 22) |
| BUG-26 | Relaties laden niet in agenda event formulier — frontend vroeg `per_page=200` maar backend had `le=100` → 422 error. Fix: backend limit verhoogd naar 200. | Midden | S | ✅ Gefixt (27 feb, sessie 22) |
| BUG-27 | 404 pagina in het Engels zonder navigatie — standaard Next.js 404. Fix: custom `not-found.tsx` met Nederlandse tekst + dashboard link. | Laag | S | ✅ Gefixt (27 feb, sessie 22) |
| BUG-28 | Batch "Stap wijzigen" toont "0 gereed" voor dossiers zonder pipeline stap — `batch_preview()` telde cases zonder `incasso_step_id` als `needs_step_assignment` i.p.v. `ready`. Fix: alle non-blocked cases tellen als ready voor advance_step. | Hoog | S | ✅ Gefixt (27 feb, sessie 24) |
| BUG-29 | Auto-advance pipeline werkt niet — `_try_auto_advance` checkte ALLE open taken (incl. 8 initiële taken uit case-aanmaak), waardoor auto-advance altijd geblokkeerd werd. Fix: (1) pipeline taken getagd via `action_config.source=pipeline`, (2) auto-advance/auto-complete scoped naar pipeline taken per stap, (3) initiële taken overgeslagen voor incasso dossiers, (4) audit trail bij stap-wijziging. | Hoog | M | ✅ Gefixt (1 mrt, sessie 26) |
| BUG-30 | test_auth.py (7 tests) — URL paden `/auth/` → `/api/auth/` | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-31 | test_integration_api.py — login helper URL pad gefixt | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-32 | test_cases.py + test_integration_api.py — workflow_data fixture toegevoegd aan conftest.py, tests gebruiken geldige transitiepaden | Midden | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-33 | test_dashboard.py — hardcoded datum → `date.today().isoformat()` | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-34 | test_documents.py — template count assertion `>= 3` + subset check | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-35 | test_relations.py — nested response pad `["contact"]["name"]` | Laag | S | ✅ Gefixt (3 mrt, sessie 29) |
| BUG-36 | Anthropic API "credit balance too low" — Credits moesten apart gekocht worden via platform.claude.com. Na aankoop + propagatie werkt API correct. | Hoog (blocker) | N/A (billing) | ✅ Gefixt (6 mrt, sessie 43) |
| BUG-37 | AI classificatie GET endpoint 500 error na approve — `_classification_to_response()` gebruikte `reviewer.first_name`/`last_name` maar User model heeft alleen `full_name`. Fix: `reviewer.full_name`. | Hoog | S | ✅ Gefixt (6 mrt, sessie 43) |
| BUG-38 | Kimi API URL verkeerd: `api.moonshot.cn` → `api.moonshot.ai`. Account zit op internationaal platform (.ai), niet Chinees (.cn). | Hoog (blocker) | S | ✅ Gefixt (11 mrt, sessie 60) |
| BUG-39 | KIMI_API_KEY niet doorgegeven aan backend container — ontbrak in `docker-compose.prod.yml` environment. | Midden | S | ✅ Gefixt (11 mrt, sessie 60) |
| BUG-40 | EmailAttachment model niet geregistreerd bij SQLAlchemy mapper — standalone scripts/scheduler crashten op `SyncedEmail` relationship. Fix: import in `email/__init__.py`. | Midden | S | ✅ Gefixt (11 mrt, sessie 60) |
| BUG-41 | 120 pre-existing test errors (conftest.py) — `metadata.drop_all()` kon composite types niet droppen (FK ordering) + connection pool hield stale connections vast tussen event loops. Fix: `DROP SCHEMA CASCADE` + `NullPool`. 573 tests passen nu. | Midden | S | ✅ Gefixt (13 mrt, sessie 65) |
| BUG-42 | 196 test errors + 1 failure bij `pytest tests/ -q` — conftest.py importeerde maar 3 van 21 model modules, waardoor `Base.metadata.create_all()` de meeste tabellen niet aanmaakte. Fix: alle 21 model modules importeren via `importlib.import_module()` (vermijdt `app` name collision) + `db` fixture expliciet afhankelijk gemaakt van `setup_database`. Resultaat: 573 passed, 0 errors, 0 failures (zowel -q als -v). | Hoog | M | ✅ Gefixt (13 mrt, sessie 67) |
| BUG-43 | Timer floating button blokkeert "Volgende" en andere action buttons op meerdere pagina's — `fixed bottom-4 right-4` overlapt met knoppen onderaan. Fix: verplaatst naar `bottom-20`. | Hoog | S | ✅ Gefixt (16 mrt, sessie 75) |
| BUG-44 | API call `/api/cases?page=1&per_page=20` op login pagina voor auth check — 401 error in console. FloatingTimer component riep useCases() aan in root Providers. Fix: split in wrapper+inner component zodat hooks alleen draaien wanneer user authenticated is. | Midden | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-45 | AI-parsed partijnamen in wizard stap 2 werden als zoektekst in veld gezet maar triggeren geen selectie van bestaande contacten. Fix: useEffect auto-selecteert eerste match uit zoekresultaten wanneer AI parsing de search text heeft gezet. | Midden | M | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-46 | `case_id` URL parameter op factuur-aanmaakpagina vulde Relatie/Dossier velden niet visueel in (data werd WEL correct opgeslagen). Fix: useCase hook + useEffect om case details te laden en display fields te vullen bij pageload. | Midden | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-47 | "Vordering(optioneel)" in wizard step indicator — spatie ontbreekt voor haakje. Fix: literal space character toegevoegd. | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-48 | Stale "Selecteer een client" validatiefout bleef zichtbaar na succesvolle client selectie. Fix: error wordt gecleared in updateField wanneer client_id wordt gezet. | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-49 | Week range header in urenregistratie toonde "15 mrt — 19 mrt" maar dagen waren Ma 16 - Vr 20 mrt. Fix: gebruik lokale Date objecten i.p.v. re-parsing van ISO strings (timezone offset veroorzaakte off-by-one). | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-50 | 5 pre-existing test failures: test_refresh_token (IntegrityError), test_validate_and_clean_basic + test_validate_and_clean_decimal_precision + test_parse_invoice_pdf_success (AssertionError), test_status_workflow_happy_path (assert 400==200). Ontdekt sessie 91. | Midden | M | ✅ Gefixt (21 mrt, sessie 94) |
| BUG-50 | favicon.ico 404 op alle pagina's. Fix: SVG favicon (Scale icoon) toegevoegd in `src/app/icon.svg`. | Laag | S | ✅ Gefixt (18 mrt, sessie 76) |
| BUG-51 | AI factuur parser werkte niet — KIMI_API_KEY niet doorgegeven via docker-compose env vars | Hoog | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-52 | Timer rondde af per minuut i.p.v. per 6 minuten — standaard juridische facturering | Midden | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-53 | Factuur PDF niet gekoppeld als document na AI parse + dossier aanmaken | Midden | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-54 | Renteoverzicht knop verwees naar niet-bestaande "financieel" tab | Hoog | M | ✅ Gefixt (18 mrt, sessie 78) — RenteoverzichtDialog gebouwd |
| BUG-55 | Geen delete knop voor facturen in dossier Facturen tab | Midden | S | ✅ Gefixt (18 mrt, sessie 78) |
| BUG-56 | Wizard stap 3 (Vordering) overgeslagen bij incasso dossiers — Enter key + button click-through | Hoog | S | ✅ Gefixt (18 mrt, sessie 78) — handleSubmit guard + React key props |
| BUG-57 | `hourly_rate.toFixed is not a function` — zaakdetailpagina crasht bij dossiers met uurtarief. API retourneert string, `.toFixed()` verwacht number. Fix: `Number()` wrap op 3 plekken. | Hoog | S | ✅ Gefixt (21 mrt, sessie 86) |
| BUG-58 | SEC-9 RLS niet afgedwongen — policies bestonden maar `luxis` is superuser en bypast RLS. Fix: `luxis_app` non-superuser role + `FORCE ROW LEVEL SECURITY` + `SET LOCAL ROLE` in middleware. | Kritiek | M | ✅ Gefixt (21 mrt, sessie 86) |
| BUG-59 | Provisie factureren knop ontbreekt (DF-05 incompleet) — instellingen bestaan maar geen actie om factuur aan te maken met provisie pre-filled. Fix: "Provisie factureren" knop + `?provisie=true` query param. | Midden | S | ✅ Gefixt (21 mrt, sessie 86) |
| BUG-60 | Factuur uren import toont geen bedragen — `hourly_rate` niet auto-ingevuld bij time entry creatie. Fix: backend vult nu `default_hourly_rate` van user in + bestaande entries gebackfilled. | Hoog | S | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-61 | `toFixed is not a function` bij factuur uren import — zelfde type als BUG-57 maar op facturen/nieuw pagina. Decimal strings van API niet naar Number() geconverteerd. | Hoog | S | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-62 | Dark mode/Systeem knoppen in Instellingen doen niks (tonen alleen toast). Fix: knoppen verwijderd, alleen "Licht" behouden. | Laag | S | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-63 | Email matching: emails bij verkeerd dossier. Fix: thread-matching, stop-on-miss, bounce-detectie, referentie matching verwijderd, outbound dedup. QA: alle 7 scenario's PASS. Extra fixes sessie 102: Fernet key derivatie hersteld (sessie 90 regressie), outbound synthetic ID uniek gemaakt met timestamp. | Kritiek | L | ✅ Gefixt + QA pass (sessie 101+102) |
| BUG-64 | Rentetype (interest_type) niet bewerkbaar na aanmaken dossier — staat alleen in wizard stap 2, niet in DetailsTab bewerkformulier. Moet bewerkbaar zijn incl. contractuele rente velden. | Midden | S | ✅ Gefixt (sessie 104) |
| BUG-65 | Geen "Markeer verweer" knop in floating action bar — backend endpoint + useSetVerweer hook bestaan, geen UI-knop op /incasso bij selectie | Midden | S | ✅ Gefixt (24 apr, sessie 127) |
| BUG-66 | Staphistorie niet op zaakdetail — useCaseStepHistory hook + API bestaan, geen timeline UI op /zaken/[id] | Midden | S | ✅ Gefixt (24 apr, sessie 127) |
| BUG-67 | Seed voegt geen stappen toe als er al stappen bestaan — `if existing: return existing` skipt alle nieuwe default stappen | Midden | S | ✅ Gefixt (24 apr, sessie 127) |
| BUG-68 | Add form mist eindstap/pauzeerstap checkboxes + email template velden | Laag | S | ✅ Gefixt (24 apr, sessie 127) |
| BUG-69 | Briefsjabloon dropdown mist seed template_types — bestaande waarden niet in dropdown, reset naar "Geen" bij edit | Laag | S | ✅ Gefixt (24 apr, sessie 127) |
| BUG-71 | `s126a_pipeline_overhaul.py` migratie gebruikt `app.current_tenant_id` i.p.v. `app.current_tenant` — latent risico bij DB from scratch | Laag | S | ✅ Gefixt (13 mei, sessie 137) — origineel file + nieuwe data-migratie `bug71_csh` recreëert policy op prod |
| BUG-72 | 4 tests in `test_incasso_router.py` falen door stale DB state (duplicate tenant slug `kesting-legal`) — test-infra issue, niet code | Laag | S | ✅ Niet meer reproduceerbaar (13 mei, sessie 137) — conftest DROP SCHEMA CASCADE dekt het al |
| SEC-01 | AgentShield security scan (`npx ecc-agentshield scan`) — one-time audit van Claude Code config + MCP permissions + hook veiligheid | Laag | S | ✅ Uitgevoerd (13 mei, sessie 137) — deny-list uitgebreid, 3 sub-agents model frontmatter; 28 HIGH zijn inherent aan dev workflow (Bash docker/python/ssh broad permissions), accept |
| BUG-73 | "Concept genereren" knop opende compose-dialog niet | Hoog | S-M | ✅ Gefixt (7 mei, sessie 134) — bleek 5 keten-bugs: useSearchParams stale na router.replace → direct setState; AI fallback chain (Sonnet voor draft, Gemini retry); endpoint path `/api/ai-agent` ipv `/api/ai`; AIDraftResponse.sources schema dict\|list; EmailComposeDialog reset alleen op Radix onOpenChange |
| BUG-74 | "Bekijk concept" knop ontbrak in dossier-Taken-tab — review_ai_draft tasks niet heropenbaar binnen dossier | Middel | S | ✅ Gefixt (7 mei, sessie 134) — TijdregistratieTab krijgt onOpenDraft callback van page.tsx |
| FEAT-EML-01 | HTML email-templates met logo + handtekening + genormaliseerde tabel-layout over alle 6 sjablonen — server-side renderer ipv AI voor HTML opmaak | Middel | M | ✅ Gebouwd (7 mei, sessie 134) |
| FEAT-EML-02 | Email-trigger detectie voor verweer-flow — inkomende mail → classify → als juridisch_verweer/betwisting + dossier in hoofdpad → auto-switch naar 'Verweer beantwoorden' + AI draft via verweer-bibliotheek | Hoog | M | ✅ Gebouwd (7 mei, sessie 134) — moet nog end-to-end getest |
| BUG-75 | Tijdstempels overal alleen datum, geen tijd in HH:MM (Lisanne demo S140) | Laag | S | ✅ Gefixt (14 mei, sessie 141 — S142) — `formatDateTime` helper, 7 componenten gemigreerd waar backend timestamp levert |
| BUG-76 | Sync-toast geeft "0 nieuw, 0 gekoppeld" zonder context (Lisanne ervaart als kapot) | Midden | S | ✅ Gefixt (14 mei, sessie 141 — S142) — `buildSyncToastMessage` helper toont nu nuttige melding incl. verwijzing naar Ongesorteerd |
| BUG-77 | Disclaimer (schuldhulpblok + juridisch) staat in incasso-templates boven handtekening i.p.v. eronder (Lisanne demo S140) | Hoog | M | ✅ Gefixt (14 mei, sessie 141 — S142) — `_BASE_EMAIL` heeft nieuwe `{{ disclaimer }}` slot na `{{ afsluiting }}`, 19 call sites gerefactord, regression-test toegevoegd |
| BUG-78 | `create_case` zet `incasso_step_id` nooit op stap 1 — 42 van 45 incasso-cases bleven zonder pipeline-stap, blokkeerden batch + auto-advance | Hoog | M | ✅ Gefixt (14 mei, sessie 141 — S143) — auto-toewijzen aan eerste pipeline-stap voor `case_type='incasso'` + backfill-script 42 cases hersteld |
| BUG-79 | Batch_execute completeerde alleen `generate_document`/`send_letter` tasks — open `review_ai_draft` tasks blokkeerden `_try_auto_advance` (Lisanne "status blijft op 1e sommatie") | Hoog | S | ✅ Gefixt (14 mei, sessie 141 — S143) — nieuwe `_skip_review_drafts_for_step` helper marks open review-tasks als 'skipped' na succesvolle send |
| BUG-80 | Dossiernummer-matching scant alleen onderwerp, mist nummers in mail-body (replies waar wederpartij `Re:` zonder kenmerk hergebruikt) | Midden | S | ✅ Gefixt (14 mei, sessie 141 — S144) — `_find_case_by_case_number` neemt `text` parameter, callers passeren `_build_searchable_text(subject, body_text, body_html, snippet)` |
| BUG-81 | Ongesorteerd-mails niet zichtbaar voor Lisanne — sidebar-badge te subtiel bij hogere aantallen, geen dashboard-prompt | Midden | S | ✅ Gefixt (14 mei, sessie 141 — S144) — badge vol rood bij >5, "Ongesorteerd"-row bovenaan dashboard "Actie nodig"-widget |
| BUG-82 | Backend restart-loop na deploy: Alembic `df140a_invoice_lines_btw` migration nooit gestamped, kolom bestond al → `DuplicateColumnError` elke startup | Hoog | XS | ✅ Gefixt (14 mei, sessie 141) — `alembic stamp df140a_invoice_lines_btw` op productie uitgevoerd |
| BUG-83 | Bel-icon toont 403 ongelezen notifications (productie-DB) niet in UI | Midden | XS-S | ✅ Gefixt (20 mei, sessie 146) — root cause was niet rendering maar notifications die niet voor alle tenant-users werden aangemaakt. `_notify_all_tenant_users` helper + backfill + cleanup van 468 duplicate deadline-records resulteerde in correcte badge (480 → 16 ongelezen, bel toont "9+"). |
| BUG-84 | Notification-types beperkt — alleen `deadline_overdue` wordt aangemaakt. Geen `email_received`, `draft_ready`, `classification_done` → Lisanne ervaart "geen meldingen" | Midden | M | ✅ Gefixt (20 mei, sessie 146) — 3 nieuwe types met hooks in sync_service/unified_draft_service/ai_agent service, dedup per (user, case, title) met type-afhankelijke windows. 6 unit tests groen. |
| FEAT-AI-01 | UnifiedDraftService: één endpoint POST /api/ai/draft met intents `next_step`/`reply_to_email`/`free_compose`. Alle 3 flows routeren via `incasso_templates._render_branded()` | Hoog | L | ✅ Gebouwd (15 mei, sessie 145) — `unified_draft_service.py` + `unified_router.py`, 13 unit tests groen, parallel met oude `/api/ai-agent/draft` tot frontend migratie in S146-147 |
| FEAT-AI-02 | Email-adres in `_signature()` dynamisch op `Case.case_type` — incasso → `Incasso@kestinglegal.nl`, dossier/advies → `kesting@kestinglegal.nl` | Midden | S | ✅ Gebouwd (15 mei, sessie 145) — `_signature` leest `ctx[zaak][type]`, hoofdletter I (BaseNet stijl), beide NL+EN takken |
| FEAT-AI-03 | Logo embedden als data-URL via `templates/lisanne/_kesting_logo.b64` i.p.v. externe URL — voorkomt mailclient remote-image blocking | Laag | S | ✅ Gebouwd (15 mei, sessie 145) — `_LOGO_DATA_URL` constante, robuuste pad-lookup voor Docker/CI/lokaal |
| FEAT-AI-04 | CaseActionFeed widget op Overzicht-tab — één plek met kaart-types: concept klaar, antwoord van wederpartij, volgende pipeline-stap. Vervangt 3 verspreide plekken | Hoog | L (2 sessies) | ✅ Gebouwd (20 mei, sessie 146) — 4 kaart-types (DraftReady/EmailReceived/Classification/Deadline), filter Wachtend/Afgehandeld/Alles, max 3 zichtbaar + Toon-alle toggle, refresh-knop, vriendelijke lege staat, deadlines bovenaan. Mount op zaken/[id] Overzicht-tab. 30s polling + window-focus refetch. End-to-end getest op productie via Playwright. |
| FEAT-AI-05 | Snooze-functionaliteit op CaseActionFeed kaarten (24u/3d/1w). Vereist `snooze_until` veld op notifications + migratie + UI menu per kaart | Midden | M | ✅ Gebouwd (1 jun, sessie 147) — `notifications.snoozed_until` (TIMESTAMPTZ) + migratie `s147a`, `PUT /api/notifications/{id}/snooze {hours}` (server-berekend, whitelist 24/72/168u, `hours=0`=unsnooze, houdt is_read=False), `useSnoozeFeedItem` hook + klok-dropdown per kaart, "Sluimert tot …" + "Nu tonen" onder Alles. 4 service-tests. Live getest op productie (dossier 2026-00049). Ontwerp: `docs/design/feat-ai-05-snooze.md`. |
| CLEAN-AI-01 | Deprecatie oude AI-endpoints: `/api/ai-agent/draft` + smart-replies UI. Memory feedback_s141: geen parallelle entries. Backend hooks blijven via UnifiedDraftService | Midden | M | ✅ Afgerond (1 jun, sessie 147) — smart-replies UI verwijderd (SmartReplyCard + `useSmartReplies` + panel), routes `POST /api/ai-agent/draft/{case_id}` + `GET /classifications/{id}/smart-replies` + `smart_reply_service.py` hard verwijderd. `draft_service.generate_and_persist_draft` behouden (orchestrator/CaseActionFeed). "Concept genereren"-knop (incasso pipeline-stap) bewust behouden — geen duplicaat. App boot OK, 45 tests groen. |
| CLEAN-TEST-01 | Conftest `setup_database` doet `DROP SCHEMA CASCADE` per test → asyncpg statement-cache out-of-sync → ~13 tests geskipt (KNOWN-002 SEPA/verrekening, KNOWN-003 docx) | Midden | M | ✅ Afgerond (1 jun, sessie 147) — schema 1× per proces + per-test `TRUNCATE ... RESTART IDENTITY CASCADE`. 13 tests unskipped + groen. 2 verstopte oorzaken gefixt: stale `sepaxml` in dev-container (staat in pyproject), stale assertions `"EUR"`→`"€"`. Volledige suite 879 passed, geen regressie. KNOWN-002/003 OPGELOST in `KNOWN_BUGS.md`. |
| BUG-85 | Outbound mails (Microsoft Graph API) tonen mojibake bij ontvanger — `€` → `â,¬`, `cliënte` → `cliÃ«nte`. Graph genereert eml met `charset=Windows-1252` ondanks UTF-8 JSON body. | Hoog | S | ✅ Gefixt (15 mei, sessie 145) — `_to_html_entities()` in OutlookProvider zet non-ASCII naar numeric HTML entities vóór send/draft. 7 unit tests. |
| BUG-86 | CI faalde op alle template-tests + invoice-tests: `factuur.html` en `_kesting_logo.b64` staan op repo-root `templates/`, niet `backend/templates/`. Docker mount maskeerde dit. Auto-deploy was skipped door rode CI. | Hoog | S | ✅ Gefixt (15 mei, sessie 145) — directory-lookup checkt nu op specifieke bestand-aanwezigheid i.p.v. directory bestaan. Auto-deploy weer functioneel. |
| FEAT-EMAIL-01 | Templates pixel-perfect BaseNet-stijl — Lisanne wil dat alle sjablonen exact eruit zien als BaseNet origineel (Verdana 12px overal, geen gouden header, handtekening met logo onderaan, schuldhulp+disclaimer 12px zwart cursief) | Hoog | M | ✅ Gebouwd (15 mei, sessie 145) — `_BASE_EMAIL` herontwerp, `_signature` met "Mevr. mr.", `_vordering_table_basenet` BaseNet structuur, schuldhulp+disclaimer 12px zwart, alle 25 templates compliant |
| FEAT-EMAIL-02 | Schuldhulp+disclaimer in ALLE incasso-mails inclusief Engelse templates | Midden | S | ✅ Gebouwd (15 mei, sessie 145) — `_schuldhulp_disclaimer_en` vertaling toegevoegd, `bevestiging_sluiting` + 5 EN templates krijgen disclaimer |
| OPS-01 | Tenant-data Kesting Legal op productie ingevuld (address/postal_code/city/phone/email/iban waren NULL — kantoor-info ontbrak in templates) | Hoog | XS | ✅ Gefixt (15 mei, sessie 145) — handmatige SQL via SSH: IJsbaanpad 9 / 1076 CV Amsterdam / etc. |
| FEAT-MAIL-01 | Slimmere mail-matching: bij multi-dossier afzender niet weigeren maar suggereren — suggest-endpoint + confidence-sortering | Hoog | M | ✅ Gebouwd (geverifieerd audit S172: `email/sync_router.py` suggest_cases_for_email + confidence-sort; roadmap-regel stond onterecht op "Gepland") |

### Demo Feedback Sprint 2 (afgerond, sessie 78)

| # | Feature/Fix | Ernst | Status |
|---|-------------|-------|--------|
| DF-01 | Bestede uren vs te factureren uren (standaard gelijk, aanpasbaar) | Hoog | ✅ Gebouwd (18 mrt, sessie 78) |
| DF-02 | Uren filters: maand, dag, client filter | Midden | ✅ Gebouwd (18 mrt, sessie 78) |
| DF-03 | Datum aanpassen bij uren (inline edit) | Laag | ✅ Gebouwd (18 mrt, sessie 78) |
| DF-04 | Uren-factuur koppeling zichtbaar (factuurnummer bij time entry) | Midden | ✅ Gebouwd (18 mrt, sessie 78) |

### Demo Feedback Sprint 3-4 (openstaand)

| # | Feature/Fix | Ernst | Status |
|---|-------------|-------|--------|
| DF-05 | Incasso provisie als configureerbare factuurregel | Hoog | ✅ 20 mrt |
| DF-06 | BTW toggle verbeteren (dropdown: 21%/0%/aangepast) | Midden | ✅ 18 mrt |
| DF-07 | Factuur context panel (al gefactureerd + derdengelden per dossier) | Hoog | ✅ 18 mrt |
| DF-08 | Navigatie terug naar dossier na factuur aanmaken | Laag | ✅ 18 mrt |
| DF-09 | Contractuele rente frequentie UI duidelijker | Midden | ✅ 18 mrt |
| DF-10 | Betaalregelingen: aantal termijnen → bedrag auto-berekenen | Midden | ✅ 18 mrt |
| DF-11 | Betaling auto-koppelen aan betaalregeling termijn | Midden | ✅ 20 mrt |
| DF-12 | Verschotten: file upload + belast/onbelast veld (voor Exact koppeling) | Hoog | ✅ 18 mrt |
| DF-13 | Voorschotnota: verrekening type (tussentijds / bij sluiting) | Midden | ✅ 20 mrt |

### Demo Feedback Sprint 5 (sessie 103 — 23 mrt 2026)

**Bron:** Demo met Lisanne, 23 maart 2026.

| # | Feature/Fix | Ernst | Grootte | Status |
|---|-------------|-------|---------|--------|
| DF2-01 | **Email compose uitbreiden** — Draft-in-Outlook flow: ontvanger chips, template selector (incasso templates als HTML body), bijlagen uit dossier + upload + ander dossier, draft opent in Outlook Web met alles pre-filled. | Hoog | XL | ✅ Sessie 103b |
| DF2-02 | **Incasso stappen bewerken** — bewerk-knop (potlood-icoon) toegevoegd naast bestaande inline-edit | Midden | S | ✅ Sessie 103 |
| DF2-03 | **BTW per factuurregel** — per regel btw-soort kiezen (21%/9%/0%). Per-tariegroep berekening (NL belastingwet). Smart PDF uitsplitsing. Auto-BTW bij expense import. | Hoog | M | ✅ Sessie 103 |
| DF2-04 | **Voorschotbedrag op uren** — uren × uurtarief auto-berekening op voorschotnota | Midden | S | ✅ Sessie 103 |
| DF2-05 | **Rentetype verplaatsen naar stap 3** — van stap 1 (Zaakgegevens) naar stap 3 (Vordering) | Laag | S | ✅ Sessie 103 |
| DF2-06 | **Profiel invullen bij nieuw dossier** — contactdetails standaard open bij nieuwe betrokkenen | Midden | S | ✅ Sessie 103 |
| DF2-07 | **PDF parsing verbeterd** — fallback naar Claude native PDF bij scans/afbeeldingen | Hoog | M | ✅ Sessie 103 |
| DF2-08 | **Genereer brief → mail als body** — template als mail-body versturen (met logo/handtekening/opmaak Kesting Legal), niet als bijgevoegd bestand. 5 HTML templates (aanmaning, sommatie, tweede_sommatie, 14_dagenbrief, herinnering) met Kesting Legal branding. Fallback naar PDF bijlage voor dagvaarding/renteoverzicht. | Hoog | L | ✅ Sessie 103b |
| DF2-09 | **Incasso fase vanuit dossier** — pipeline step dropdown op dossier-detail header | Midden | S | ✅ Sessie 103 |

### UX Review Fixes (sessie 79b — 18 mrt 2026)

Volledige UX review van alle 31 schermen. 5 gefixt, 13 openstaand.

| # | Issue | Prioriteit | Status |
|---|-------|-----------|--------|
| UX-1 | Uren weekdag highlight UTC vs lokale timezone | Hoog | ✅ 18 mrt |
| UX-2 | Dossier summary cards hoofdsom stale cache | Hoog | ✅ 18 mrt |
| UX-3 | Redundante "Dossiers per status" widget op dashboard | Laag | ✅ 18 mrt |
| UX-4 | Taken pagina toont alle 190 taken zonder paginering | Midden | ✅ 18 mrt |
| UX-5 | Correspondentie afzender toont alleen voornaam | Midden | ✅ 18 mrt |
| UX-6 | Dossier tabs overflow — sticky tab bar onder header | Midden | ✅ Sessie 80 |
| UX-7 | Dossier header sticky overlap — tabs sticky gemaakt | Midden | ✅ Sessie 80 |
| UX-8 | Documenten: case picker dialog voor directe generatie | Laag | ✅ Sessie 80 |
| UX-9 | Betalingen: prominente Upload knop in header | Laag | ✅ Sessie 80 |
| UX-10 | Incasso pipeline: betaalde dossiers uitgefilterd | Midden | ✅ Sessie 80 |
| UX-11 | Follow-up: uitleg toegevoegd bij lege staat | Laag | ✅ Sessie 80 |
| UX-12 | Dashboard taken: duplicaten gegroepeerd (bijv. "3x ...") | Laag | ✅ Sessie 80 |
| UX-13 | Dossier lijst: "Openstaand" kolom toegevoegd | Midden | ✅ Sessie 80 |

---

### Lisanne Feedback Sprint 3 (sessie 86, 21 maart 2026)

| # | Feature/Fix | Ernst | Grootte | Status |
|---|-------------|-------|---------|--------|
| LF-16 | Timer loopt door na sluiten programma — moet pauzeren/stoppen bij afsluiten browser | Hoog | M | ✅ 21 mrt |
| LF-17 | "Incasso/instellingen" (uurtarief, betalingstermijn) verwijderen uit dossier-aanmaak wizard — hoort in dossier zelf | Midden | S | ✅ 21 mrt |
| LF-18 | "Normaal" strategie onduidelijk bij dossier-aanmaak — hernoemen of verduidelijken | Laag | S | ✅ 21 mrt |
| LF-19 | Terugknop in dossier-wizard wist alle ingevoerde gegevens — moet state behouden | Hoog | M | ✅ 21 mrt |
| LF-20 | Te veel opties bij "type dossier" — alleen "Incasso" en "Dossier" (evt. "Advies"), insolventie/overig weg | Laag | S | ✅ 21 mrt |
| LF-21 | Filteroptie bij documenten ontbreekt — filter op bestandstype (Word, PDF, etc.) binnen dossier | Laag | S | ✅ 21 mrt |

---

## Backlog / Feature Requests

- ~~**FEATURE: Relaties — inline contactpersoon aanmaken vanuit koppeldialoog**~~ ✅ Gedaan (sessie 19) — inline aanmaken van advocaat wederpartij bij nieuw dossier
- ~~**FEATURE: Advocaat wederpartij — klikbare detailweergave**~~ ✅ Gedaan (sessie 19) — zaken zichtbaar op relatiepagina via CaseParty filter + "Partij" rol label

### Frontend design-audit S155 — restwerk (bewuste backlog, zie `docs/qa/impeccable-audit-2026-06-07.md`)

- **AUDIT-FE-1: hard-coded palette-classes → semantic varianten** — 🔶 Top-5 gedaan (sessie 156): `lib/tones.ts` als centrale bron + incasso/dashboard/facturen/DossierHeader/facturen-detail gemigreerd (192→1 classes, screenshots pixel-identiek). **Restant: ~57 bestanden / ~620 classes** (ergste: correspondentie, agenda, taken) — nu mechanisch via tones.ts-patroon, zelfde recept (screenshot vóór/na, tsc, commit per pagina). NIET via blinde sed.
- **AUDIT-FE-2: touch targets < 44px** (±73 `p-1`/`p-1.5` icon-buttons). Per scherm beoordelen — bulk-vergroting vervormt data-dense tabellen. Verkenning sessie 156: DocumentenTab 12×, incasso 8×, uren 6×, sjablonen-tab 6×; voorgestelde aanpak `max-sm:p-2` per component (groter alleen op touch).
- ~~**AUDIT-FE-3: per-veld `aria-invalid`/`aria-describedby`**~~ ✅ Gedaan (sessie 156) — gekoppeld in relaties/nieuw (7 velden), zaken/nieuw (3), facturen/nieuw (3), BetalingenTab (2); error-`<p>` kreeg id + role=alert; functioneel geverifieerd. **Let op:** `form-field-error.tsx`-component zelf heeft nog 0 consumers — adopteren (unificeert error-styling) of verwijderen.
- *(Bewust behouden, géén werk: agenda event side-stripes = Google Calendar-idioom; credit-nota paars als functionele type-kleur (`CREDIT_NOTE_TONE`); DossierSidebar verborgen <lg; DossierHeader `text-orange-500` rente-icoon als one-off accent.)*

### Incasso Workflow Automatisering (P1)

**Doel:** Eén klik op "Verstuur brief" voor 40 dossiers → alles automatisch.

1. ✅ **Template editor UI** — Sjablonen tab in Instellingen: upload, download, bewerken, verwijderen van DOCX templates. Database-driven met disk-fallback. Incasso pipeline gebruikt dynamische template dropdown. Gebouwd sessie 24.
2. ✅ **Batch brief + email verzenden** — "Verstuur brief" genereert documenten en emailt ze naar de wederpartij via OutlookProvider (Graph API) met SMTP fallback. Sinds sessie 103b: brieven als branded HTML email body (Kesting Legal logo/kleuren/handtekening) i.p.v. PDF bijlage. Fallback naar PDF bijlage voor dagvaarding/renteoverzicht. Email toggle in PreFlightDialog, instelbare email templates per stap, email readiness check in preview. Gebouwd sessie 27, HTML body sessie 103b.
3. ✅ **Auto-complete taken** — Na document genereren: bijbehorende taken (generate_document/send_letter) automatisch afgevinkt. Gebouwd sessie 25. Bugfix sessie 26: scoped naar pipeline taken per stap (BUG-29).
4. ✅ **Auto-advance pipeline** — Na alle taken voltooid: pipeline schuift automatisch naar volgende stap, nieuwe taak + deadline aangemaakt. Bij batch advance_step worden ook taken aangemaakt. Gebouwd sessie 25. Bugfix sessie 26: blokkade door initiële taken opgelost (BUG-29).
5. ✅ **Deadline kleuren per stap** — Groen/oranje/rood kleurcodering per dossier in pipeline. Gebouwd sessie 23.
6. ✅ **Instelbare dagen per stap** — `max_wait_days` per pipeline-stap. "Min. dagen" + "Grens rood" kolommen. Gebouwd sessie 23.
7. ✅ **Step Transitions (branching workflow)** — `step_transitions` tabel: elke stap kan meerdere uitgangen hebben op basis van trigger (timeout/verweer/betaling/handmatig). 21 standaard overgangen geseeded. UI in expanded step row. Nieuwe stap "Verweer beantwoorden". Gebouwd sessie 131.
8. ✅ **Pivot naar lineair pipeline + automation rules** — Sessie 133. Branching state-machine vervangen door Lisanne's officiele 14 stappen (5 hoofdpad + 6 tussenstappen + 1 verweer + 2 afsluit). 6 .eml sjablonen + verzoekschrift DOCX geïmporteerd. AI-prompt module + defense_library voor verweer-respons. Manual + scheduled draft-generation. Bron: `docs/lisanne-incasso-workflow.md`.
9. ✅ **End-to-end AI draft flow** — Sessie 133. "Concept genereren" knop in dossier → AI draft → `/taken` queue → klik "Bekijk concept" → opent in dossier → versturen via Outlook → auto step-advance.
10. ✅ **Mail-pagina** — Sessie 133. Sidebar `Correspondentie` → `Mail`. "Nieuwe mail" knop voor free-compose zonder dossier-context.

**Flow:** Batch selectie → genereer brieven → email via Outlook → taken afgevinkt → pipeline doorgeschoven → deadline kleuren updaten

### Geplande verbeteringen (P2, niet bouwen tot expliciet groen licht)

- ✅ **Mail-pagina dossier-zoekveld in compose-dialog** — Search bovenaan compose, klik dossier → koppelt + recipient pre-fill van opposing_party/client, sjablonen/files/library beschikbaar via dropdowns. "Ontkoppel" link maakt binding ongedaan. `useRenderTemplate` accepteert nu `string | undefined`. Gebouwd sessie 137 (13 mei).
- ✅ **Email-trigger detectie** — Inkomende mail van debiteur → auto status "Verweer beantwoorden" + AI draft via verweer-bibliotheek. Gebouwd sessie 134.
- ✅ **Tenant-instelling UI** — `pipeline_auto_drafts_enabled` flag aan/uit per tenant via Instellingen → Workflow → Automatiseringsregels. Gebouwd sessie 137.
- ✅ **TransitionsSection vervangen** — UI in pipeline-page hernaamd naar "Automatische regels" paneel. Gebouwd sessie 137.

**QA & Testdekking (sessie 28):**
- ✅ **35 backend integration tests** — `test_incasso_pipeline.py`: deadline kleuren, email templates, auto-complete (BUG-29 regressie), auto-advance, batch preview, batch execute (met/zonder email, partial failure, edge cases), pipeline overview, queue counts. Alle 35 PASSED.
- ✅ **9 Playwright E2E tests** — `frontend/e2e/incasso-pipeline.spec.ts`: page load, deadline colors, action bar, pre-flight dialog, email toggle, queue filters, stappen beheren.
- ✅ **Smoke test checklist** — `docs/qa/p1-smoke-test-checklist.md`: 6 scenario's, 30+ handmatige checks.

---


## Volgorde van werken

> Volledige lijst van alle afgeronde items staat in `docs/completed-work.md`

**Volgende prioriteit:** Security Sprint (SEC-1 t/m SEC-15) + Code Quality Sprint (CQ-1 t/m CQ-9) — sessie 83 audits

### Pre-Launch Sprint (sessie 62 audit → uitrol)

**Doel:** Alle blokkers oplossen zodat Lisanne daadwerkelijk met Luxis kan werken.

| # | Taak | Effort | Blokkerend? | Status |
|---|------|--------|-------------|--------|
| PL-1 | **Backups activeren op VPS** — crontab instellen, backup dir aanmaken, eerste backup testen | 15 min | JA — zonder backup = dataverlies risico | ✅ Sessie 63 (13 mrt) |
| PL-2 | **Factuur-PDF generatie** — endpoint + template + download knop op factuurdetail | 4-6 uur | JA — kan geen facturen versturen | ✅ Sessie 64 (13 mrt) |
| PL-3 | **E2E auth test fixen** — URL+sidebar check i.p.v. time-dependent greeting | 30 min | Nee (test, niet productie) | ✅ Sessie 63 (13 mrt) |
| PL-4 | **Timer persistent maken** — localStorage opslag zodat page reload timer niet kwijtraakt | 1 uur | Nee maar high-impact UX | ✅ Was al geïmplementeerd |
| PL-5 | **Default uurtarief per gebruiker** — settings + auto-fill bij tijdregistratie | 1-2 uur | Nee maar dagelijkse frustratie | ✅ Sessie 63 (13 mrt) |
| PL-6 | **CSV payment import UI** — frontend pagina voor bestaand backend endpoint | 2-3 uur | Nee maar bij 20+ dossiers essentieel | ✅ Was al gebouwd (sessie 56-57) |

**Geschatte doorlooptijd:** 1.5-2 sessies

### Security Sprint (sessie 83 pentest)

**Bron:** Security audit sessie 83 (20 maart 2026). Volledige OWASP Top 10 + extra checks op advocatenkantoor-specifieke risico's.

**Positief:** Tenant isolation via JWT consistent, OAuth tokens encrypted at rest (Fernet), bcrypt correct, JWT access tokens 15 min expiry, Sentry PII disabled, Pydantic validatie op alle schemas, productie Docker ports niet exposed.

**Prioriteit legenda:** 🔴 Kritiek (direct exploiteerbaar) | 🟠 Hoog (serieus risico) | 🟡 Medium | 🟢 Laag/Info

#### Fase 1 — Kritiek (vóór volgende deploy)

| # | Issue | Ernst | Grootte | Status |
|---|-------|-------|---------|--------|
| SEC-1 | **SQL injection in tenant middleware** — f-string in `SET app.current_tenant = '{tenant_id}'`. Fix: UUID validatie vóór interpolatie. | 🔴 Kritiek | S | ✅ Sessie 83 |
| SEC-2 | **OAuth state parameter niet gesigned** — base64-encoded JSON zonder HMAC. Fix: HMAC signing + nonce + 10min expiry. | 🔴 Kritiek | M | ✅ Sessie 83 |
| SEC-3 | **XSS via email HTML** — `dangerouslySetInnerHTML` op 3 plekken zonder sanitatie. Fix: DOMPurify geïnstalleerd + sanitizeHtml helper. | 🔴 Kritiek | S | ✅ Sessie 83 |
| SEC-4 | **SECRET_KEY default waarde** — placeholder string als JWT signing key. Fix: startup check die weigert te starten met default key in productie. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-5 | **Password reset token in logs** — plaintext reset URL gelogd. Fix: URL verwijderd uit logmelding. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-6 | **API secrets roteren** — gecontroleerd: .env is NOOIT gecommit in git history. Secrets zijn veilig. | 🟠 Hoog | S | ✅ Sessie 83 |

#### Fase 2 — Hoog (binnen 1-2 sessies)

| # | Issue | Ernst | Grootte | Status |
|---|-------|-------|---------|--------|
| SEC-7 | **Rate limiting op auth endpoints** — slowapi geïnstalleerd. Login: 10/min, forgot-password: 3/uur, reset: 5/uur. | 🟠 Hoog | M | ✅ Sessie 83 |
| SEC-8 | **postMessage wildcard origin** — OAuth success popup stuurt `postMessage('*')`. Fix: specifieke origin + HTML/JS escaping. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-9 | **PostgreSQL RLS niet actief** — RLS policies bestonden maar werden niet afgedwongen (owner bypast RLS). Fix: `FORCE ROW LEVEL SECURITY` + `luxis_app` non-superuser role + `SET LOCAL ROLE` in middleware. | 🟠 Hoog | M-L | ✅ Sessie 84 + fix sessie 86 |
| SEC-10 | **Jinja2 Server-Side Template Injection** — Fix: `SandboxedEnvironment` voor alle DB-templates. | 🟠 Hoog | S | ✅ Sessie 83 |
| SEC-11 | **Container draait als root** — Fix: `adduser appuser` + `USER appuser` in Dockerfile. | 🟡 Medium | S | ✅ Sessie 83 |

#### Fase 3 — Medium/Laag (hardening)

| # | Issue | Ernst | Grootte | Status |
|---|-------|-------|---------|--------|
| SEC-12 | **Refresh token rotation** — oude refresh tokens blijven geldig tot expiry (7 dagen). Fix: token blocklist of DB-opslag met rotation. | 🟡 Medium | M | ✅ Sessie 84 |
| SEC-13 | **Wachtwoord-complexiteit** — alleen min 8 chars, geen complexiteitsregels. Fix: min 12 + complexiteit voor advocatenkantoor. | 🟡 Medium | S | ✅ Sessie 84 |
| SEC-14 | **HTML-escape user input in emails** — Fix: `html.escape()` vóór newline-conversie in 3 bestanden. | 🟡 Medium | S | ✅ Sessie 83 |
| SEC-15 | **File upload hardening** — .doc/.xls (macro-gevoelig) toegestaan, geen magic byte validatie. Fix: legacy formaten verwijderen + python-magic check. | 🟡 Medium | S-M | ✅ Sessie 84 |

**Toekomstig (backlog):**
- Audit trail voor alle data-wijzigingen (AVG/GDPR compliance)
- GDPR data export + verwijdering endpoints (Art. 15/17)
- Failed login logging + monitoring

**Aanbevolen volgorde:** SEC-1 → SEC-2 → SEC-3 → SEC-4/5/6 → SEC-7 t/m SEC-11 → SEC-12 t/m SEC-15

### Mega-Audit Sprint (sessie 89, 21 maart 2026)

**Bron:** 6 parallelle audit-agents: security, backend code, frontend code, juridisch, UX/design, infra/DevOps. 100+ bevindingen geconsolideerd en gededupliceerd.

#### CRITICAL — Must-fix (juridisch/financieel/security risico)

| # | Issue | Domein | Status |
|---|-------|--------|--------|
| SEC-16 | **Fernet KDF zwak** — enkele SHA-256 zonder salt/iteraties voor OAuth token encryptie. Fix: PBKDF2HMAC met salt + 600k iteraties. | Security | ✅ Sessie 90 (al gefixt, bevestigd sessie 91) |
| SEC-17 | **DB/Redis poorten open in prod** — ports verplaatst van base naar dev override; prod heeft geen exposed ports. | Infra | ✅ Sessie 92 |
| SEC-18 | **Redis zonder wachtwoord** — geen `requirepass` in productie. | Infra | ✅ Sessie 90 (REDIS_PASSWORD ingesteld op VPS) |
| SEC-19 | **localStorage tokens** — JWT in localStorage, XSS-extractable. Interim: centraliseer in tokenStore. Later: httpOnly cookies. | Security | ✅ Sessie 91 (tokenStore module, 17 bestanden gemigreerd) |
| CQ-10 | **Missing db.commit()** — file upload, credit note, approve, send, cancel, add/remove line, expenses, payments nooit gecommit. | Backend | ✅ Sessie 90 |
| CQ-11 | **N+1 query in receivables** — 1 DB query per factuur in loop. Fix: single grouped aggregate. | Backend | ✅ Sessie 90 |
| CQ-12 | **Silent catch{} blocks** — 14+ plaatsen in frontend slikken financiële mutatie-errors. Gebruiker ziet niks. | Frontend | ✅ Sessie 91 (4 catch blocks → toast.error) |
| CQ-13 | **parseFloat voor geldbedragen** — IEEE 754 precisieverlies bij transport naar backend. Fix: string transport. | Frontend | ✅ Sessie 91 (alle parseFloat verwijderd, string transport) |

#### HIGH — Serieus risico

| # | Issue | Domein | Status |
|---|-------|--------|--------|
| SEC-20 | **Geen account lockout** — 10/min rate limit = 14.400 pogingen/dag. Fix: per-account lockout na 5 mislukte pogingen. | Security | ✅ Sessie 90 (lockout na 5 pogingen + migratie) |
| SEC-21 | **OAuth callback unauthenticated** — user_id trusted uit state parameter. Fix: server-side nonce in Redis. | Security | ✅ Sessie 91 (Redis nonce, single-use, 10min TTL) |
| SEC-22 | **Input sanitization** — user input niet gesanitized. Fix: backend + frontend sanitization. | Security | ✅ Sessie 90 (backend sanitize.py + frontend DOMPurify) |
| SEC-23 | **Filename injection Content-Disposition** — ongesanitized filename in headers. Fix: strip speciale chars. | Security | ✅ Sessie 90 (al gefixt, bevestigd sessie 91) |
| SEC-24 | **Token encryption** — OAuth tokens onvoldoende versleuteld. Fix: Fernet encryption. | Security | ✅ Sessie 90 (Fernet versterkt) |
| SEC-25 | **OAuth state parameter** — geen validatie van state parameter. Fix: server-side validatie. | Security | ✅ Sessie 90 (state parameter validatie + frontend USER directive) |
| SEC-26 | **PyJWT migratie** — python-jose niet meer onderhouden. Vervangen door PyJWT. | Backend | ✅ Sessie 90 |
| CQ-14 | **Compound interest rounding** — year_interest niet afgerond voor kapitalisatie. | Backend | ✅ Sessie 90 |
| CQ-15 | **_recalculate_totals stale** — in-memory loop i.p.v. DB aggregate voor factuur totalen. | Backend | ✅ Sessie 90 |
| CQ-16 | **list_cases missing eager loads** — MissingGreenlet crash risico bij serialisatie. | Backend | ✅ Sessie 90 |
| CQ-17 | **Factuur paid zonder payments** — status `paid` bereikbaar zonder betalingsrecords. | Backend | ✅ Sessie 90 |
| CQ-18 | **files_service uploader lazy load** — crash in async context. Fix: selectinload. | Backend | ✅ Sessie 90 |
| CQ-19 | **Float divisie betalingsregeling** — installment bedrag berekend met JS float. Fix: integer cents arithmetic. | Frontend | ✅ Sessie 91 (integer cents i.p.v. float divisie) |
| CQ-20 | **KYC/WWFT data typed als any** — compliance risico. Fix: typed KycData interface. | Frontend | ✅ Sessie 90 (KycSection getypeerd) |

#### MEDIUM — Moet gefixt, geen acuut risico

| # | Issue | Domein | Status |
|---|-------|--------|--------|
| SEC-27 | **Security headers in prod** — ontbrekende security headers in docker-compose.prod.yml. | Infra | ✅ Sessie 90 |
| SEC-28 | **Dev deps in prod image** — Changed to `uv pip install "."` (without dev extras). | Infra | ✅ Sessie 92 |
| SEC-29 | **Mass assignment setattr** — Explicit ALLOWED_FIELDS allowlist in update_profile + update_tenant. | Security | ✅ Sessie 92 |
| SEC-30 | **CSP unsafe-inline/unsafe-eval** — Removed unsafe-eval from script-src in Caddyfile. | Infra | ✅ Sessie 92 |
| CQ-21 | **Backend .dockerignore** — Created backend/.dockerignore excluding .env, tests, cache, docs. | Infra | ✅ Sessie 92 |
| CQ-22 | **Container health checks** — Added healthchecks for all 4 services in docker-compose.prod.yml. | Infra | ✅ Sessie 92 |
| CQ-23 | **Container resource limits** — Added mem_limit + cpus for all services in prod compose. | Infra | ✅ Sessie 92 |
| CQ-24 | **Off-site backups** — rclone → Backblaze B2 bucket `Luxis-backup`. Dagelijkse cron 03:00, DB + uploads, 90d retentie off-site, 7d lokaal. Draait sinds maart 2026. | Infra | ✅ Compleet |
| CQ-25 | **Uptime monitoring** — Self-hosted health check actief (elke 5 min, auto-restart bij downtime). /health endpoint extern beschikbaar. UptimeRobot (extern) nog opzetten vóór soft launch. | Infra | ⏳ UptimeRobot vóór soft launch |
| UX-14 | **Responsive tabellen** — overflow-x-auto + min-width op alle tab-tabellen en incasso pipeline. | Frontend | ✅ Sessie 98 |
| UX-15 | **Form validatie** — inline foutmeldingen op factuur, email compose, betaling, instellingen formulieren. | Frontend | ✅ Sessie 98 |
| UX-16 | **Unsaved changes warning** — beforeunload op nieuwe relatie (andere formulieren hadden het al). | Frontend | ✅ Sessie 98 |
| UX-17 | **Empty state guidance** — lege lijsten missen begeleiding/onboarding. EmptyState component + 7 tabs vervangen. | Frontend | ✅ Sessie 97 |
| UX-18 | **Breadcrumbs** — waren al geïmplementeerd (breadcrumb-context + useBreadcrumbs hook op alle detail pages). | Frontend | ✅ Al compleet |
| UX-19 | **Error boundaries per tab** — waren al geïmplementeerd (ErrorBoundary + TabErrorFallback op alle 10 tabs). | Frontend | ✅ Al compleet |
| UX-20 | **formatCurrency NaN** — null-safe arithmetic (??0) in dossiers pagina. | Frontend | ✅ Sessie 98 |
| UX-21 | **isError niet afgevangen** — financiële queries tonen lege lijst i.p.v. error. | Frontend | ✅ Sessie 91 (QueryError in 5 financial tabs) |
| UX-22 | **Frontend Design Audit** — alle pagina's doorlopen met Frontend Design skill en UI verbeterpunten inventariseren (anti-"AI slop", design systeem, typografie, kleurgebruik, compositie). Rapport: `docs/research/UX-22-FRONTEND-DESIGN-AUDIT.md` (score 5.5/10, 20 pagina's geaudit). | Frontend | ✅ Sessie 96 |
| UX-23 | **Design Sprint deel 1** — 8/10 UX-22 Top 10 items geïmplementeerd: Inter font, login redesign, empty states, KPI cards, sidebar secties, tabel responsiveness, microinteracties. | Frontend | ✅ Sessie 97 |
| UX-24 | **Design Sprint deel 2** — resterende 2 items: incasso pipeline collapse lege secties + correspondentie in/uit visueel + date grouping. | Frontend | ✅ Sessie 98 |

### Bugs & Issues

| # | Omschrijving | Ernst | Status |
|---|-------------|-------|--------|
| BUG-51 | **Correspondentie zoekfunctie** — zoeken op de correspondentie pagina geeft geen resultaten. | Midden | ✅ Niet reproduceerbaar (sessie 99, 22 mrt) — zoekfunctie werkt correct |

### AI UX/UI Verbetering (sessie 98 feedback)

**Bron:** Gebruiker-feedback: AI resultaten zijn niet zichtbaar genoeg BINNEN de workflow. Designkeuze blijft: geen aparte AI-pagina, AI is onzichtbaar maar de resultaten moeten wél duidelijk zijn op de plekken waar ze relevant zijn.

| # | Omschrijving | Status |
|---|-------------|--------|
| AI-UX-01 | **AI badges op email-rijen** — classificatie-badge (categorie + confidence) direct zichtbaar in de correspondentie email-lijst, niet alleen na klikken in detail-panel. | ✅ Done (sessie 99, 22 mrt) |
| AI-UX-02 | **"Wacht op review" indicator** — visuele hint op emails die nog op AI-review wachten (icoontje of kleur). | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-03 | **AI suggesties in Mijn Taken** — AI-secties met paarse AI-badge, tonen altijd (ook als lege state). Geen aparte AI-pagina. | ✅ Done (sessie 99, 22 mrt) |
| AI-UX-04 | **AI suggestion banner op dossier** — bovenaan dossier-detail een inklapbare kaart met de huidige AI-suggestie + Accepteren/Afwijzen. Uitgebreid sessie 128: uitklapbaar emailbericht + klikbare bronnen. | ✅ Done (sessie 100, 23 mrt) · ✅ Uitgebreid (sessie 128, 24 apr) |
| AI-UX-05 | **AI indicators op incasso pipeline** — AI-badge op dossier-kaarten in de pipeline ("Termijn verloopt morgen", "Actie voorgesteld"). | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-06 | **AI in activity feed** — AI-acties in dezelfde tijdlijn als menselijke acties, met AI-badge/avatar. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-07 | **Dashboard AI widget** — samenvatting "3 dossiers vereisen actie, 2 termijnen verlopen vandaag". | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-08 | **Nederlandse tekstlabels i.p.v. percentages** — "Aanbevolen" (blauw), "Mogelijk" (oranje), "Onzeker" (grijs) i.p.v. "95%". | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-09 | **AI concept-berichten klaarzetten** — bij accepteren schrijft de AI een kant-en-klaar inhoudelijk bericht. Niet een standaard afwijzing, maar een onderbouwd antwoord op basis van ALLE dossiercontext (zie AI-UX-13). Lisanne reviewt en verstuurt. Alleen voor incasso. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-10 | **Response templates tailoren** — de 6 standaard antwoord-templates afgestemd op Kesting Legal juridische stijl. | ✅ Sessie 112 — professionele juridische toon, mr. L. Kesting signatuur, consequenties bij niet-betaling |
| AI-UX-11 | **Algemene voorwaarden per cliënt** — upload/opslag van algemene voorwaarden per cliënt (niet van Kesting Legal). AI valt hier op terug bij betwistingen. Per dossier gekoppeld via de cliënt. | ✅ 23 maart 2026 |
| AI-UX-13 | **AI raadpleegt volledige dossiercontext** — de AI leest ALLES voordat hij een concept schrijft: (1) alle emails in+uit, (2) notities/telefoonnotities in het dossier, (3) contract/overeenkomst PDF, (4) factuur PDF, (5) algemene voorwaarden cliënt, (6) vorderingen + betalingen, (7) activity feed, (8) eerder verzonden brieven. Zonder deze context is de AI te simpel. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-14 | **Bronvermelding in concept-berichten** — AI verwijst naar specifieke artikelen uit contract/AV, berekent termijnen, citeert relevante correspondentie. Lisanne kan snel checken of het klopt. | ✅ Done (sessie 100, 23 mrt) |
| AI-UX-12 | **Correspondentie zoekfunctie** — zoeken werkt niet (BUG-51). | ✅ Niet reproduceerbaar (sessie 99, 22 mrt) |

### AI Technische Verbeteringen (sessie 98 research)

| # | Omschrijving | Status |
|---|-------------|--------|
| AI-TECH-01 | **pymupdf4llm** — vervang pdfplumber door pymupdf4llm in `backend/app/ai_agent/pdf_extract.py`. Betere tabel/layout extractie, 5-10x sneller, Markdown output voor LLM. Simpele swap (~30 min). | ✅ 23 mrt 2026 |
| AI-TECH-02 | **Claude native PDF voor contractanalyse** — bij betwistingen/zware analyse: stuur PDF direct naar Claude API i.p.v. tekst extractie. Alleen voor dure taken (1-2x/week), dagelijks werk blijft Kimi. | ✅ 23 mrt 2026 |
| AI-TECH-03 | **Claude Structured Outputs** — gebruik structured outputs bij Claude Haiku calls zodat responses gegarandeerd het juiste JSON format hebben. Elimineert parsing errors. Alleen voor Claude calls, niet Kimi. | ✅ 23 mrt 2026 |

### Tooling Upgrade (sessie 96)

**Bron:** Research sessie 95 — 1.000+ repos gescand, 20 tools geëvalueerd. Installeer tools die directe waarde toevoegen aan development en marketing.

| # | Tool | Categorie | Doel | Status |
|---|------|-----------|------|--------|
| TOOL-01 | **Codebase Memory MCP** | Dev infra | Knowledge graph van codebase, 99% minder tokens | ✅ Sessie 96 |
| TOOL-02 | **Context7 MCP** | Dev infra | Up-to-date library docs (Next.js 15, React 19, SQLAlchemy 2.0) | ✅ Sessie 96 |
| TOOL-03 | **Tavily MCP** | Search/scrape | Vervangt Perplexity + Firecrawl (gratis 1.000 calls/mnd) | ✅ Sessie 96 |
| TOOL-04 | **Systematic Debugging skill** | Dev skill | 4-fase debugging: root cause → patroon → hypothese → fix | ✅ Sessie 96 |
| TOOL-05 | **Receiving Code Review skill** | Dev skill | Regels voor feedback verwerken, anti-slijmerij, YAGNI check | ✅ Sessie 96 |
| TOOL-06 | **Verification Before Completion skill** | Dev skill | Operationeel protocol: verse output, verboden woorden, agent-verificatie | ✅ Sessie 96 |
| TOOL-07 | **Frontend Design skill** | Dev skill | Anti-"AI slop" design richtlijnen, merge met frontend/CLAUDE.md | ✅ Sessie 96 |
| TOOL-08 | **Deep Research skill** | Dev + Marketing | 8-fase research pipeline met citations | ✅ Sessie 96 |
| TOOL-09 | **Claude SEO** | Marketing | SEO audit + schema + E-E-A-T + AI Search optimalisatie voor kestinglegal.nl | ✅ Sessie 96 |
| TOOL-10 | **Marketing Skills** (Corey Haines) | Marketing | 30+ skills: SEO, copywriting, cold email, content strategie | ✅ Sessie 96 |
| TOOL-11 | **Brand Guidelines skill** | Marketing | Kesting Legal branding vastleggen voor consistent materiaal | ✅ Sessie 96 |
| TOOL-12 | **Canvas Design skill** | Marketing | Social graphics, LinkedIn visuals zonder designer | ✅ Sessie 96 |
| TOOL-13 | **Perplexity MCP verwijderen** | Opruimen | Te duur, geen free tier, geen budget | ✅ Sessie 96 |
| TOOL-14 | **Firecrawl MCP verwijderen** | Opruimen | Credits op, niet vernieuwd | ✅ Sessie 96 |

### Demo Feedback Lisanne (sessie 115, 30 maart 2026)

| # | Item | Status |
|---|------|--------|
| DF-01 | **Mail compose full-screen** — dialog 95vw/92vh, flex layout, body neemt alle ruimte | ✅ Sessie 115 |
| DF-02 | **Mail template bewerkbaar** — iframe → contentEditable div, edits gaan mee bij verzending | ✅ Sessie 115 |
| DF-03 | **Correspondentie als volledige mailbox** — tabs Alle/Ongesorteerd, dossier-badge per email | ✅ Sessie 115 |
| DF-04 | **AI concept assertiever** — rente+BIK in context, zakelijke toon, concrete betalingstermijn | ✅ Sessie 115 |
| DF-05 | **Factuur parsing** — geen errors gevonden, backend hergebouwd met dependencies | ✅ Sessie 115 |
| DF-06 | **Document preview** — betere foutmelding bij niet-ondersteunde types, LibreOffice rebuild | ✅ Sessie 115 |
| DF-07 | **Bestandsnaam aanpasbaar** — PATCH endpoint + inline rename UI in DocumentenTab | ✅ Sessie 115 |
| DF-08 | **Rentefrequentie onder rente-instellingen** — alleen zichtbaar bij contractuele rente | ✅ Sessie 115 |
| DF-09 | **Standaard rente per client** — default_interest_type op Contact + pre-fill in wizard | ✅ Sessie 115 |
| DF-10 | **Sync error 2026-00048** — geen bug, dossier mist case_parties (wederpartij toevoegen) | ✅ Sessie 115 |
| DF-11 | **Facturatie-widget weg** — BillingSettingsSection verwijderd uit dossier sidebar | ✅ Sessie 115 |

### Demo Feedback Lisanne (sessie 117, 7 april 2026 — 21 punten in 7 categorieën)

Bron: live demo met Lisanne 7-4-2026. Notities gecategoriseerd in 7 groepen. 2 punten opgepakt deze sessie, rest geparkeerd voor volgende sessies of na overleg.

| # | Item | Status |
|---|------|--------|
| DF117-01 | **Adres-parsing factuur → dossier** — alleen postcode kwam binnen, niet de straat. Root cause: IntakeRequest miste postal_* velden + AI gaf soms onvolledig adres terug + regex-detector pakte straat als blok-name. Fix: 3 nieuwe velden + line-based block scanner + post-process backfill. 9 nieuwe tests. | ✅ Sessie 117 |
| DF117-02 | **Standaard rente per klant met inheritance** — DF-09 (sessie 115) bleek half-af: backend Contact had de velden niet, frontend faalde stilzwijgend. Fix: Contact model + schemas + create_case inheritance + nieuwe-relatie form + bewerk-relatie save + nieuw-dossier "overgenomen van klant" hint. 6 nieuwe tests. | ✅ Sessie 117 |
| DF117-03 | **AI leest dossier-context bij berichtcompositie** — bij het opstellen van een bericht moet de AI alle relevante dossier-context kennen: AV, facturen, vorderingen, overeenkomsten. **Samengevoegd met DF117-06.** | ✅ Sessie 117 — `_gather_case_context` uitgebreid met CaseFiles + invoices, prompt vermeldt 5 bron-types, 6 nieuwe tests |
| DF117-04 | **Incassokosten + provisie zichtbaar op factuur naar cliënt** — Vorderingen-tab heeft nu wel BIK + provisie-velden, maar (a) incassokosten alleen als bedrag, niet als percentage en (b) komt niet als regel op de uitgaande factuur. Wat bij debiteur verhaald wordt moet ook bij klant zichtbaar zijn. Wacht op overleg met Lisanne | 🟡 DEELS — backend voegt BIK/provisie als invoice_lines toe (`invoices/service.py:1168-1190`), maar PDF-template markeert ze niet apart als "BIK-regel" (alles ziet er hetzelfde uit). Verificatie met Lisanne nodig of dit genoeg is. |
| DF117-05 | **Incassokosten achteraf toevoegen in dossier** — UI ontbreekt buiten Vorderingen-tab. Wacht op overleg met Lisanne | 🟡 FUNCTIONEEL GEDAAN — Lisanne kan via `Dossier → Documenten → Nieuwe factuur` naar `/facturen/nieuw?case_id=X`, waar `IncassoKostenPanel` automatisch BIK/Rente/Provisie toont en 1-klik toevoeging biedt. **Te bespreken met Lisanne:** of ze een meer expliciete "Incassokosten factureren" shortcut wil i.p.v. de algemene "Nieuwe factuur"-knop. |
| DF117-06 | ~~AI leest dossier-documenten voor berichtvoorstel~~ — samengevoegd met DF117-03 | ✅ Sessie 117 (via DF117-03) |
| DF117-07 | **Uren toevoegen vanuit dossier-tab** — kan alleen via Uren-pagina, niet vanuit dossier > tab Uren | ✅ Reeds gebouwd — `UrenTab.tsx` heeft "+ Uren toevoegen" knop met `AddTimeEntryDialog` (regel 48-54). Verificatie sessie 121. |
| DF117-08 | **Zoekfunctie documenten-tab** — op dossier-niveau door documenten zoeken | ✅ Reeds gebouwd — `DocumentenTab.tsx` regel 880-881 + 1354-1360, met `documentSearch` state en ilike-filter. Verificatie sessie 121. |
| DF117-09 | **Minimum bedrag incassokosten bij versturen** — instelbaar minimum zodat provisie niet te laag wordt | ✅ Sessie 120 — Backend `is_minimum_applied` flag + line description + per-cliënt inheritance |
| DF117-10 | **Verschot in reguliere factuur** — nu alleen in dossier-factuur, moet overal | 🟡 GEDAAN voor concept — elke concept factuur (ook reguliere, niet alleen voorschotnota) met `case_id` heeft nu "Verschot toevoegen" knop via `AddExpenseDialog`. Voor verzonden facturen niet: dat raakt financial precision (verstuurde factuur wijzigen of nieuwe aanmaken?). **Te bespreken met Lisanne:** wat is de gewenste flow als factuur al verstuurd is? |
| DF117-11 | **Factuur+verschot in 1 flow samenvoegen** — nu 2 stappen in dossier, kan in 1 | 🟡 DEELS — `/facturen/nieuw` combineert factuur + voorschotnota in 1 wizard, maar verschot zit nog in aparte `VerschottenSection` bij dossier-facturen |
| DF117-12 | **Filter op facturen-pagina** — relatie/dossiernummer, zoals andere pagina's | ✅ Reeds gebouwd — `facturen/page.tsx` regel 52-57 + `invoices/service.py` regel 126-148 ilike-search op invoice_number, case.case_number, contact.name. Verificatie sessie 121. |
| DF117-13 | **Goedkeuren → Versturen stuurt geen email** — `send_invoice()` doet nu alleen statuswijziging, moet OutlookProvider integratie | ✅ Sessie 117 — `send_invoice()` rendert PDF + roept OutlookProvider aan via `send_with_attachment`, fail-loud bij ontbrekend email of provider-fout, frontend confirm dialog, `?skip_email=true` opt-out, 6 nieuwe tests |
| DF117-14 | **Klik vanuit facturen-overzicht naar dossier** | ✅ Reeds gebouwd — `facturen/page.tsx` regel 685 linkt facturen naar contact/dossier via querystring. Verificatie sessie 121. |
| DF117-15 | **Verschot op voorschotnota achteraf** — bv. griffierecht later toevoegen | 🟡 GEDAAN voor concept — `AddExpenseDialog` werkt in concept voorschotnota's. Voor sent/paid voorschotnota: raakt financial precision. **Te bespreken met Lisanne samen met DF117-10:** gewenste flow (bestaande wijzigen of nieuwe maken)? |
| DF117-16 | **Creditnota visueel duidelijk in dossier** | ✅ Reeds gebouwd — `DocumentenTab.tsx` regel 511-545 splitst regularInvoices + creditNotes visueel met rode kleur (`#dc2626`) in template. Verificatie sessie 121. |
| DF117-17 | **Creditnota wordt niet correct van totaal afgehaald** — grondig testen, financial precision | ✅ Sessie 121 — grondige test-coverage toegevoegd: 3 nieuwe tests naast bestaande 5 (totaal 8 credit-note tests groen). Dekt 3 BTW-regimes tegelijk (21/9/0%), meerdere deelcredits stapelend, en credit op approved status. Geen bug gevonden, de backend-logica klopt al correct. |
| DF117-18 | **Creditnota eigen uren: bedrag-optie** — keuze tussen aantal×tarief OF los bedrag | ✅ Reeds gebouwd — `facturen/[id]/page.tsx` regel 111-123 heeft "calc" vs "direct" mode voor creditnota-regels. Verificatie sessie 121. |
| DF117-19 | **Klik op debiteur → openstaande facturen direct** — niet de algemene relatie-detail | ✅ Sessie 119 — Link navigeert naar `/facturen?contact_id=X&status=sent,partially_paid,overdue` |
| DF117-20 | **Batch dossier-aanmaak** — meerdere zaken tegelijk via email | ✅ Sessie 117 — POST `/api/intake/approve-batch` met per-item failure handling, frontend checkboxes + select-all + action bar op pending_review tab, 2 nieuwe tests (3 succesvol + partial failure) |
| DF117-21 | **Derdengelden-rekening + verrekening met eigen nota** — Lisanne ontvangt op derdengeldrekening, soms doorstorten, soms verrekenen. Vereist eigen module-onderzoek (Stichting Derdengelden, juridische verrekeningsregels) | ✅ COMPLEET — Sessie 118: verrekening-flow met cliënt-toestemming (Voda art. 6.19 lid 5) + consolidatie van twee parallelle systemen op `trust_funds`. Sessie 119: top-level `/derdengelden` overzichtspagina (cross-cliënt aggregatie), NOvA mutatieoverzicht + saldolijst CSV exports, SEPA pain.001.001.03 export voor uitbetalingen vanaf Stichting Derdengelden Rabobank-rekening, en `backend/app/app/` shadow-copy verwijderd. 26/26 trust_funds tests groen. Nog open voor latere sessie: MT940 bank-import voor de Stichting Derdengelden rekening (auto-deposits). |
| DF117-22 | **Standaard incassokosten per klant** — net als de standaard rente per klant (DF117-02): op Contact instelbaar als vast bedrag of percentage van hoofdsom, en automatisch overgenomen bij nieuw dossier (per dossier wijzigbaar). | ✅ Sessie 117 |

### Demo Feedback Lisanne (sessie 120, 8 april 2026 — round 2)

Na de derdengelden-afronding kwam Lisanne met nieuwe feedback. Geclassificeerd in 3 sessies: 120 (bugs + inheritance + test data), 121 (producten-catalogus), 122 (mail-sjablonen + verweer-bibliotheek).

| # | Item | Status |
|---|------|--------|
| DF120-01 | **Creditnota BTW klopt niet** — bij mixed-BTW factuur (bv. 21% honorarium + 0% onbelaste verschotten) werd de credit geforceerd naar één rate. Root cause: frontend stuurde geen per-regel btw_percentage mee. Backend was OK. Fix + regressietest groen. | ✅ Sessie 120 |
| DF120-02 | **Facturen-overzicht in dossier klopt niet na creditnota** — vermoedelijk symptoom van DF120-01 (verkeerde totalen op credit → verkeerde som op dossier). Bevestigen na Lisanne test. | ⏳ Verificatie na DF120-01 |
| DF120-03 | **Rente-periode (maand/jaar) op klantniveau** — DF117-02 had rentetype + -percentage per klant, maar periode (yearly/monthly) stond niet op Contact. `default_rate_basis` toegevoegd, cascadet bij claim-creatie. | ✅ Sessie 120 |
| DF120-04 | **Minimum provisie op klantniveau** — DF117-22 had BIK-override, maar geen minimum. `default_minimum_fee` toegevoegd, cascadet bij case-creatie. | ✅ Sessie 120 |
| DF120-05 | **Derdengelden testdata voor Arsalan** — seed script dat 3 dossiers × 3 transacties injecteert (approved deposit + approved disbursement + pending disbursement). Cleanup via `--clean`. Gedraaid op productie. | ✅ Sessie 120 |
| DF120-06 | **VPS disk-full crash preventie** — sessie 120 ontdekt: door `--no-cache` bij elke deploy was `/var/lib/docker` 143GB groot, Postgres crash-loopte met PANIC. 4-layer defense: stop `--no-cache` default + auto-prune na deploy + hourly disk-guard cron + weekly build-cache cleanup. | ✅ Sessie 120 |
| DF120-07 | **KVK API-koppeling** — Lisanne wil automatisch bedrijfsgegevens ophalen bij ingave van KvK-nummer. Nu alleen handmatig veld. | 📋 Backlog (laag) |
| DF120-08 | **Producten/artikel-catalogus uit Basenet Excel** — 30 Basenet-artikelen met grootboekrekeningen + BTW-codes. Nieuwe products module (CRUD + seed), product-dropdown op factuurregels, per-line GL account in Exact Online sync, beheer-pagina in Instellingen. 8 tests, 27 invoice tests ongewijzigd. | ✅ Sessie 122 |
| DF120-09 | **Mail-sjablonen vervangen door Lisanne's Basenet export** — niet 4 maar **15 brieven** in SOMMATIE-eml ontdekt. Alle 11 NL + 4 EN templates 1-op-1 overgenomen met exacte Basenet-wording, derdengelden IBAN, en correcte termijnen per scenario. Concept verzoekschrift als DOCX-template die automatisch naar PDF wordt gerenderd bij bijlage-select (harde regel: alle externe bestanden als PDF, nooit DOCX). Compose dropdown heeft nu 7 groepen met 22 templates. Auto-invulling: VSO totaalbedrag wordt automatisch `totaal_openstaand` (voorstel Arsalan, te bespreken met Lisanne). Handmatige placeholders (gele markers) blijven voor onderhandelingsbeslissingen: `[VUL SCHIKKINGSBEDRAG IN]`, `[VUL TERMIJNEN IN]`, `[HIER INHOUDELIJKE REACTIE OP VERWEER INVULLEN]`. 17 nieuwe render-tests + 51 bestaande tests groen. | ✅ Sessie 121 |
| DF121-Q1 | **Placeholder-beslissing bespreken met Lisanne** — welke velden moeten auto-gevuld vs handmatig? Nu auto: VSO totaalbedrag (= totaal_openstaand). Nu handmatig: schikkingsbedrag (onderhandeling), VSO-termijnen (betalingsschema), verweer-weerlegging (juridische inhoud). Vragen: (a) moet schikkingsbedrag auto-voorgesteld worden op bijv. 70% van openstaand als start? (b) moet VSO-totaalbedrag auto blijven of toch handmatig voor meer controle? (c) wil ze een andere default voor verweer-weerlegging (bijv. AI-suggestie uit verweer-bibliotheek DF120-10)? | 📋 Te bespreken met Lisanne |
| DF120-10 | **Verweer-bibliotheek voor AI inspiratie** — 5 verweer-templates (art 20.4, art 9.3, NCNP, stilzwijgende verlenging, English) als Python module. Automatisch geïnjecteerd in AI draft prompt bij juridisch_verweer/betwisting classificatie. | ✅ Sessie 122 |
| DF120-11 | **Exact Online koppeling voor facturen** — facturen direct doorboeken naar Exact. Afhankelijk van DF120-08 (grootboeknummers per item). | 📋 Backlog (na sessies 121+122) |
| DF126-01 | **Incasso pipeline overhaul (20 stappen)** — Pipeline uitgebreid van 4 naar 20 stappen op basis van 4-fasemodel (minnelijk → gerechtelijk → executie → afsluiting + regeling/administratief). Nieuwe velden: step_category, debtor_type (b2b/b2c/both), is_terminal, is_hold_step. Seed met 20 default stappen. | ✅ Sessie 126 |
| DF126-02 | **Staphistorie (CaseStepHistory)** — Audit trail per dossier: elke stapwissel wordt gelogd met entered_at/exited_at, trigger_type (manual/batch/auto_advance/ai_agent), triggered_by, template_sent, email_sent, document_id, notes. Nieuw model + migratie + API endpoint GET /cases/{id}/step-history. | ✅ Sessie 126 |
| DF126-03 | **Verweer-tracking** — has_verweer, verweer_note, verweer_date op Case model. Blokkeert auto-advance. Batch preview rapporteert verweer_blocked apart. POST /cases/{id}/verweer endpoint. Shield-badge in UI. | ✅ Sessie 126 |
| DF126-04 | **Lijstweergave incasso** — Default view is nu platte tabel (alle dossiers), toggle naar "Per stap" groepering. Kolommen: dossiernr, cliënt, wederpartij, stap (category-colored badge), type (B2B/B2C), hoofdsom, openstaand, dagen, verweer-badge. | ✅ Sessie 126 |
| DF126-05 | **move_case_to_step() uniforme functie** — Alle staptransities (batch, auto-advance, handmatig) gaan via 1 functie. Sluit oude CaseStepHistory af, maakt nieuwe aan, update Case positie, logt CaseActivity. | ✅ Sessie 126 |
| DF126-06 | **Stappenbeheer uitgebreid** — StappenTab nu met categorie-dropdown, debiteurtype-dropdown, eindstap/pauzeerstap checkboxes. Category-badges met kleurcoding per fase. | ✅ Sessie 126 |
| DF127-01 | **"Markeer verweer" batch knop** — Amber Shield-knop in floating action bar op /incasso. Promise.allSettled voor parallelle calls, lokale loading state, per-case error reporting. | ✅ Sessie 127 |
| DF127-02 | **Staphistorie tab op zaakdetail** — StaphistorieTab component met verticale timeline (stap naam, categorie badge, actief-indicator, duur, trigger type, template/email indicators, notities). Alleen zichtbaar bij incasso dossiers. | ✅ Sessie 127 |
| DF127-03 | **Seed idempotent** — seed_default_steps() voegt nu alleen ontbrekende stappen toe (check by name). Bestaande stappen blijven intact, nieuwe krijgen sort_order na hoogste bestaande. | ✅ Sessie 127 |
| DF127-04 | **Add form uitgebreid** — Expanded row onder add-stap formulier met is_terminal/is_hold_step checkboxes en email template subject/body velden. | ✅ Sessie 127 |
| DF127-05 | **Briefsjabloon dropdown compleet** — Combineert managed templates (DB) + template_types uit bestaande stappen. 5 ontbrekende keys toegevoegd aan beide label maps (TEMPLATE_TYPE_LABELS + TEMPLATE_KEY_LABELS). | ✅ Sessie 127 |
| DF122-01 | **Meerdere incasso-workflows** — Pipeline-model bovenop stappen, zodat per cliënt/scenario een aparte workflow gekozen kan worden. Basis gelegd in DF126-01 (20 stappen + categorieën). | 📋 Backlog (basis gelegd) |
| DF122-02 | **AI Orchestrator** — Event bus + orchestrator gebouwd (sessie 129). State machine + LLM hybrid. Auto-draft disabled (kwaliteit). Agent SDK geëvalueerd en uitgesteld naar fase 3 (200+ cases). Custom Python approach voor v1. | ✅ Basis gebouwd (sessie 129), auto-draft disabled |
| DF122-03 | **M365 email forwarding** — BaseNet forwardt kopieën naar M365, Luxis synct van M365. Parallelle werking: oude zaken op BaseNet, nieuwe op Luxis. Filter zodat ongelinkte mails niet zichtbaar. | 📋 Backlog (met Lisanne) |
| DF122-04 | **Mailsjablonen-editor** — Email templates van hardcoded Python naar DB verhuizen. WYSIWYG editor in Instellingen zodat Lisanne templates zelf kan aanpassen zonder developer. | 📋 Sessie 124 (uitgesteld uit 123) |
| DF122-05 | **Documenten tab herordenen** — Bestanden (uploads) bovenaan, document genereren onderaan. Split genereren in brieven vs processtukken. | ✅ Sessie 123 |
| DF122-06 | **Rente per vordering aanpasbaar** — Nu alleen rate_basis (maand/jaar). Ook percentage per vordering instelbaar (`Claim.interest_rate`, leeg = wettelijk). | ✅ Sessie 123 |
| DF122-07 | **Factuur-onderbouwing bij eerste sommatie** — Facturen uit dossier als bewijs bij eerste sommatie template tonen. | ✅ Sessie 123 (auto-bijlage bij template_type=sommatie) |
| DF120-12 | **Read-only view contact-detail toonde rate_basis + minimum_fee niet** — tijdens E2E test op prod gevonden: edit-mode werkt, maar de read-only `<dl>` sloeg deze 2 velden over. Fix: "· per maand/jaar" achter rente, "Minimum provisie" regel in `ContactInfoSection.tsx`. | ✅ Sessie 120 (hotfix `22996ca`) |

### Demo Feedback Lisanne (sessie 138, 13 mei 2026 — 23 fixes tijdens live demo)

| # | Item | Status |
|---|------|--------|
| DF138-01 | **Data-loss bij partij-wijzigen in nieuw-dossier wizard** — naam-pills van cliënt/wederpartij/advocaat klikbaar → opent relatie-detail in nieuw tab; "Wijzigen" hernoemd naar "Andere kiezen" | ✅ Sessie 138 |
| DF138-02 | **Advocaat wederpartij mist kantoor-flow** — selector Advocatenkantoor/Persoon + 3-veld grid + contactpersoon-veld (default = kantoor) | ✅ Sessie 138 |
| DF138-03 | **"Minimumkosten" label verwarrend in dossier** — hernoemd naar "Minimum provisie" met uitleg-regel | ✅ Sessie 138 |
| DF138-04 | **Aanhef-veld "De heer/Mevrouw" op contactpersoon** — `Contact.salutation` enum (mr/mrs/unknown), migratie `df139a_salutation`, dropdown in `relaties/nieuw` & detail-edit; `_resolve_contact_person` returnt (achternaam, salutation); AI-prompt + HTML-renderer maken "Geachte heer X" / "Geachte mevrouw X" / generiek | ✅ Sessie 139 |
| DF138-05 | **Verkeerd kenmerk in concept-mail** — `case.reference` (klant-kenmerk) niet meer doorgegeven aan AI/subject-render; alleen dossiernummer | ✅ Sessie 138 |
| DF138-06 | **Concept-mail toonde alleen hoofdsom** — `gather_case_context` gebruikt nu `get_financial_summary` voor rente + BIK + BTW | ✅ Sessie 138 |
| DF138-07 | **Datums in mail US-format** — server-side naar DD-MM-JJJJ + prompt-instructie | ✅ Sessie 138 |
| DF138-08 | **Relaties tonen vandaag als aangemaakt** — `ContactSummary` schema miste `created_at`/`visit_city`; frontend kreeg `undefined` → `Intl.DateTimeFormat` viel terug op vandaag | ✅ Sessie 138 |
| DF138-09 | **Relatie verwijderen "doet niets"** — soft-delete werkt, maar relatie bleef zichtbaar in dossiers. `delete_contact` blokkeert nu met 409 + duidelijke melding bij koppeling aan actief dossier | ✅ Sessie 138 |
| DF138-10 | **Geen sortering op relaties-lijst** — sorteerbare kolom-koppen (Relatie/Contact/Plaats/Aangemaakt) met chevron-indicator; backend whitelist | ✅ Sessie 138 |
| DF138-11 | **Inline contactpersoon bij Bedrijf-aanmaak** — naam + e-mail veld onder bedrijf-blok; maakt direct Person + ContactLink | ✅ Sessie 138 |
| DF138-12 | **Info-box rente onduidelijk zonder klant-default** — grijze box "Geen rente-default — wettelijke rente toegepast, stel in op klantkaart" wanneer alleen BIK% gezet | ✅ Sessie 138 |
| DF138-13 | **Rentefrequentie (per maand/jaar) cascadet niet** — `default_rate_basis` toegevoegd aan cascade in wizard useEffect + info-box toont nu "per maand/per jaar" | ✅ Sessie 138 |
| DF138-14 | **Minimum bij BIK-percentage niet toegepast** — `get_financial_summary` + `get_incasso_invoice_preview` checken nu `case.bik_minimum_fee` als bodem | ✅ Sessie 138 |
| DF138-15 | **Oude voetnoot in mails en sjablonen** — `email/incasso_templates.py` ("en/of" → "en / of"), `templates/_generate_templates.py` (volledige disclaimer), DOCX-bestanden geregenereerd, `scripts/reseed_builtin_templates.py` (nieuw) — 8 managed_templates rijen opnieuw gevuld | ✅ Sessie 138 |
| DF138-16 | **Aparte velden voor provisie-minimum en BIK-minimum** — `default_bik_minimum_fee` op Contact + `bik_minimum_fee` op Case (migratie `df138a_bik_min` met data-migratie); cascade in `create_case`; backend BIK-berekening gebruikt nieuw veld | ✅ Sessie 138 |
| DF138-17 | **Uitleg-suffix bij BIK-bedrag overbodig** — `— minimumtarief van € X toegepast` uit `bik_source` weggehaald | ✅ Sessie 138 |
| DF138-18 | **`default_bik_minimum_fee` niet opgeslagen vanuit klant-detail** — `relaties/[id]/page.tsx` init editForm + save-payload missten het veld; UI toonde wel, DB bleef NULL | ✅ Sessie 138 |
| DF138-19 | **Frontend negeerde BIK-bodem in dossier Vorderingen-tab** — `FinancieelTab.tsx` deed client-side `pct * principal` en overschreef `summary.total_bik`; nu past frontend ook `case.bik_minimum_fee` toe | ✅ Sessie 138 |
| DF138-20 | **Pipeline-step body had oude voetnoot** — SQL UPDATE op `email_body_template` + Python regex-fix voor `email_body_template_html` (Eerste sommatie) | ✅ Sessie 138 |
| DF138-21 | **Rente € 0,00 hardcoded in pipeline-template** — body_template + HTML-cellen leeggemaakt; `html_renderer.render_template_html` roept nu `_fill_amount_cell` aan voor label "Rente" met `amounts.rente` | ✅ Sessie 138 |
| DF138-22 | **Volledige naam in aanhef** — `_resolve_contact_person` extract nu alleen laatste woord wanneer `last_name` leeg is en `name` de volledige naam bevat. Tussenvoegsels gaan dan verloren — vul `last_name` expliciet in op de relatie voor "Geachte heer/mevrouw de Vries" | ✅ Sessie 138 (met caveat) |
| DF138-23 | **Lege factuur-placeholder-rijen in mail-template** — `_fill_invoice_rows` strijkt overgebleven placeholder-rijen weg na vullen met factuurdata | ✅ Sessie 138 |
| DF138-bulk-delete | **Bulk-actie toolbar op dossiers/relaties** — dossiers: verwijder-knop in bestaande toolbar; relaties: nieuwe checkboxes + select-all + bulk-toolbar. Sequential DELETE met mixed-resultaat toast (typisch 409 bij dossier-koppeling). Confirm-dialog destructive variant via `useConfirm` hook | ✅ Sessie 139 |
| DF138-sort-persist | **Sortering onthouden tussen pagina-bezoeken** — URL search params `?sort_by=&sort_dir=` op relaties + dossiers; `useSearchParams` leest, `router.replace` schrijft. Browser-back en directe links bewaren sortering | ✅ Sessie 139 |
| S139-zaken-sort | **Sorteerbare kolommen op dossiers** — backend whitelist (case_number/status/case_type/date_opened/total_principal/total_paid), frontend `CaseSortHeader` met chevron-indicator + URL-persist | ✅ Sessie 139 |
| S139-av-versies | **AV-versies per cliënt met smart-default** — nieuwe `contact_terms` tabel (file, label, valid_from, valid_to), `case.contact_terms_id` FK, cliënt-detail UI met versie-lijst + upload/edit/delete, `gather_case_context` kiest versie op eerste factuur-datum, data-migratie van legacy `terms_file_path`. Dossier-UI voor handmatige keuze nog te bouwen (smart-default werkt autonoom) | ✅ Sessie 139 (deels — dossier-UI volgende sessie) |

### Feature & UX Audit (sessie 113, 29 maart 2026)

**Bron:** Volledige feature & UX audit (`docs/research/FEATURE-UX-AUDIT.md`). Score: **7.5/10**. Alle pagina's, modules en workflows doorgelopen vanuit het perspectief van Lisanne.

#### Bouwen — Dagelijks gebruik

| # | Item | Effort | Status |
|---|------|--------|--------|
| FUA-01 | **Notificatie-backend activeren** — Model, service, router, migratie 043, scheduler (deadlines + verjaring) | M (4-6 uur) | ✅ Sessie 114 (30 mrt) |
| FUA-02 | ~~Opdrachtbevestiging DOCX-template~~ | — | ✅ Lisanne heeft dit al |
| FUA-03 | ~~Uren afronden op 6 minuten~~ | — | ✅ Al gebouwd (BUG-52, sessie 78) — `Math.ceil(seconds / 360) * 6` |

#### Bouwen — Regelmatig gebruik

| # | Item | Effort | Status |
|---|------|--------|--------|
| FUA-04 | ~~Afsluitbrief DOCX-template~~ | — | ✅ Lisanne heeft dit al |
| FUA-05 | ~~Incassomachtiging DOCX-template~~ | — | ✅ Niet nodig (bevestigd door gebruiker) |
| FUA-06 | **"Vergeten uren" waarschuwing op dashboard** — Amber banner als gisteren werkdag met 0 uren | S (1 uur) | ✅ Sessie 114 (30 mrt) |

#### Bevestigd om te bouwen

| # | Item | Effort | Status |
|---|------|--------|--------|
| FUA-07 | **Unified tijdlijn per dossier** — alle activiteit (emails, documenten, betalingen, notities) in één chronologisch overzicht | M (4 uur) | ✅ Sessie 115 (30 mrt) |
| FUA-09 | **Agenda-widget op dashboard** — vandaag + morgen events zichtbaar bij inloggen | S (2 uur) | ✅ Sessie 115 (30 mrt) |
| FUA-11 | **Pauzeknop op timer** — amber Pause-knop in floating timer | S (1 uur) | ✅ Sessie 114 (30 mrt) |
| FUA-12 | **Engelse termen vertaald** — Word-sjablonen, Werkstroom, Bankimport, Faseverdeling | S (30 min) | ✅ Sessie 114 (30 mrt) |
| FUA-13 | **A11y form labels (htmlFor/id)** — formuliervelden koppelen aan labels voor toegankelijkheid | S (2 uur) | ✅ Sessie 115 (30 mrt) |

#### Niet bouwen (besloten)

- ~~FUA-08 Tags op relaties~~ — niet nodig
- ~~FUA-10 Facturen-widget dashboard~~ — debiteuren-tab is voldoende

#### Niet bouwen (besloten)

- ~~Kanban view~~ — niet hoe advocaten werken, Basenet/Kleos heeft het ook niet
- ~~Archiveren dossiers~~ — status "afgesloten" doet hetzelfde
- ~~Document editor in browser~~ — Lisanne werkt in Word
- ~~Subdossiers~~ — te complex voor solo-praktijk
- ~~CSV import relaties~~ — eenmalig, via migratiescript
- ~~Cliëntportaal~~ — pas bij meerdere kantoren

### Code Quality Sprint (sessie 83 audit)

**Bron:** Codebase audit sessie 83 (20 maart 2026). Alle bevindingen uit onafhankelijke code review.

**Prioriteit legenda:** 🔴 Kritiek (functioneel risico) | 🟡 Belangrijk (onderhoud) | 🟢 Nice-to-have

| # | Issue | Prioriteit | Grootte | Kan zonder Lisanne? | Status |
|---|-------|-----------|---------|---------------------|--------|
| CQ-1 | **Float → Decimal in cases/models.py** — 11 financiële velden (`total_principal`, `budget`, `hourly_rate`, etc.) gebruiken `Mapped[float]` i.p.v. `Mapped[Decimal]`. Database is NUMERIC(15,2) maar Python geeft floats terug. | 🔴 Kritiek | M | ✅ Ja | ✅ Sessie 84 |
| CQ-2 | **Float → Decimal in cases/schemas.py** — 15+ Pydantic schema-velden voor geld als `float` i.p.v. `Decimal` | 🔴 Kritiek | S | ✅ Ja | ✅ Sessie 84 |
| CQ-3 | **Float in relations/models.py** — `default_hourly_rate` is `Float` kolomtype (niet NUMERIC). Financieel veld in IEEE 754 floating-point. | 🔴 Kritiek | S | ✅ Ja | ✅ Sessie 84 |
| CQ-4 | **Stille no-op: "Herbereken rente" batch-actie** — `incasso/service.py` regel ~807: loop telt `processed += 1` maar doet niks. Gebruiker krijgt succesbericht terwijl er niks gebeurt. | 🔴 Kritiek | S-M | ✅ Ja | ✅ Sessie 84 |
| CQ-5 | **invoices/service.py opsplitsen** — 1292 regels, bevat CRUD + PDF + credit notes + provisie + budget tracking. Minimaal splitsen in 2-3 files. | 🟡 Belangrijk | M | ✅ Ja | ✅ Sessie 84 |
| CQ-6 | **Frontend god-components splitsen** — IncassoTab.tsx (2292r), zaken/nieuw/page.tsx (1823r), relaties/[id]/page.tsx (1545r). Moeilijk te onderhouden/debuggen. | 🟡 Belangrijk | L | ✅ Ja | ✅ Sessie 85 |
| CQ-7 | **Paginatie-duplicatie opruimen** — `pages` veld toegevoegd aan alle custom paginatie-schemas + manual dict return gefixt. | 🟢 Nice-to-have | S | ✅ Ja | ✅ Sessie 85 |
| CQ-8 | **Dead code verwijderen** — GmailProvider (364 regels verwijderd) | 🟢 Nice-to-have | S | ✅ Ja | ✅ Sessie 84 |
| CQ-9 | **Test hygiene** — 21x hardcoded datum `"2026-02-17"` → `date.today().isoformat()` in test_cases.py | 🟢 Nice-to-have | S | ✅ Ja | ✅ Sessie 84 |

**Aanbevolen volgorde:** CQ-1 + CQ-2 + CQ-3 (float→Decimal, samen doen) → CQ-4 (stille bug) → CQ-5 → CQ-6 → CQ-7/8/9

### Uitrolplan (na pre-launch sprint)

1. ✅ **QA Walkthrough** — volledige Playwright walkthrough (sessie 75, 16 mrt)
2. ✅ **QA Bugfixes** — 4 P1 + 3 P2 bugs gefixt (sessie 76, 18 mrt)
3. **AI Factuur Parsing Validatie** — LF-10 feature uitgebreid testen met echte facturen van Lisanne. Test cases: verschillende factuurtypes (B2B/B2C), incomplete facturen, meerdere vorderingen, edge cases. Doel: betrouwbaarheid valideren voor productiegebruik.
4. ✅ **Test data opschonen** — 13 rommel cases + 15 rommel contacten verwijderd (sessie 76, 18 mrt)
5. **Demo met Lisanne** — samen door hele workflow lopen, feedback verzamelen
6. **Feedback-fixes** — top-5 items fixen (1 sessie)
7. **Soft launch** — 2-3 echte dossiers in Luxis, BaseNet blijft primair (2 weken)
8. **Parallel draaien** — nieuwe dossiers in Luxis, BaseNet als backup (1 maand)
9. **M0b: Lisanne naar M365** — email migratie
10. **BaseNet opzeggen** — als alles bewezen werkt

---

### QA-traject: Systeembrede Testdekking

**Doel:** Elke module dezelfde testdekking als P1 — backend integration tests, Playwright E2E, smoke test checklist.

**Aanpak:** Per module, in prioriteitsvolgorde. Elke fase levert: pytest tests + E2E tests + smoke checklist.

| Fase | Module | Huidige dekking | Wat nodig is | Status |
|------|--------|----------------|--------------|--------|
| QA-0 | Bestaande test fixes | 20 tests stuk (BUG-30 t/m 35) | URL paden, schema's, transitions updaten | ✅ Compleet (3 mrt, sessie 29) — 380/380 tests PASSED |
| QA-1 | Auth & Permissions | 14 tests (passing) | Login, refresh, token validatie, expired JWT, inactive user, tenant isolation | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-2 | Relaties/Contacts | 23 tests (passing) | CRUD, links, conflict check, zoeken, cross-tenant isolation (5 tests) | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-3 | Zaken/Cases | 19 tests (passing) | CRUD, status workflow, partijen, activiteiten, cross-tenant isolation, terminal status lock | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-4 | Email/Sync | 11 tests | Case emails, unlinked, link/bulk-link, dismiss, detail, attachments, tenant isolation | ✅ Compleet (3 mrt, sessie 30) |
| QA-5 | Workflow/Taken | 19 tests | Statuses CRUD, transitions (B2B/B2C), tasks CRUD, rules, calendar, verjaring | ✅ Compleet (3 mrt, sessie 30) |
| QA-6 | Facturatie | 19 tests | Invoice CRUD, status workflow, BTW precision, credit notes, lines, expenses, payments | ✅ Compleet (3 mrt, sessie 30) |
| QA-7 | Tijdregistratie | 15 tests | CRUD, filters (case/billable/date), unbilled, summary, my/today, tenant isolation | ✅ Compleet (3 mrt, sessie 30) |
| QA-8 | Dashboard | 10 tests (passing) | KPI's, recente activiteit, auth checks, cross-tenant isolation | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-9 | Documents/Templates | 28 tests (passing) | Template CRUD, DOCX generatie, cross-tenant template/doc/docx isolation | ✅ Uitgebreid (3 mrt, sessie 31) |
| QA-P1 | Incasso Pipeline | 35 tests + 9 E2E | **Compleet** (sessie 28) | ✅ Gedaan |

### E2E Tests (Playwright) — Sessie-overzicht

**Doel:** Elke core flow gedekt met Playwright E2E tests naast backend pytest tests.

**Aanpak:** Opgesplitst in 3-4 sessies. Auth setup via storageState (login eenmalig, hergebruik in alle specs).

| Sessie | Scope | Tests | Status |
|--------|-------|-------|--------|
| E2E-1 | Auth + Dashboard + Sidebar + Relaties CRUD | 16 tests (1 setup + 4 auth + 3 dashboard + 3 sidebar + 5 relaties) | ✅ Compleet (4 mrt, sessie 32) |
| E2E-2 | Zaken CRUD (7 detail tabs, edit, status, delete) | 8 tests | ✅ Compleet (4 mrt, sessie 33) |
| E2E-3 | Facturen (7) + Tijdschrijven (5) | 12 tests | ✅ Compleet (5 mrt, sessie 35) |
| E2E-4 | Correspondentie (2) + Agenda (3) + Taken (3) | 8 tests | ✅ Compleet (5 mrt, sessie 36) |
| E2E-fix | Incasso pipeline tests gefixt + lint cleanup | 7 tests un-skipped | ✅ Compleet (6 mrt, sessie 37) |

**Totaal nu:** 44 E2E tests (nieuwe) + 7 incasso E2E tests (gefixt) = **51 E2E tests passing** (was 44 passing + 7 skipped)

### DevOps Enhancements (sessie 33, 4 maart) ✅

- Bekende fouten gecodificeerd: 15 → 28 items (retroactieve analyse 32 sessies)
- `/learn`, `/compact-smart`, `/verify` commands aangemaakt
- Stop hook met session-end checks (SESSION-NOTES, ROADMAP, uncommitted/unpushed)
- Security deny list (ssh, scp, dangerous rm/curl)
- `float()` → `Decimal` fix in dashboard + incasso services/schemas

**Bestanden:**
- `frontend/e2e/auth.setup.ts` — storageState setup
- `frontend/e2e/auth.spec.ts` — login, invalid creds, persistence, logout
- `frontend/e2e/dashboard.spec.ts` — greeting, KPI cards, new dossier button
- `frontend/e2e/sidebar.spec.ts` — nav items, click navigation, collapse/expand
- `frontend/e2e/relaties.spec.ts` — list, create company/person, edit, delete
- `frontend/e2e/helpers/auth.ts` + `api.ts` — shared utilities
- `frontend/e2e/facturen.spec.ts` — invoice lifecycle (create, detail, approve, send, payment, delete)
- `frontend/e2e/tijdregistratie.spec.ts` — time entry CRUD (create, verify, edit, delete)

---


> Bron: `PROMPT-BEVINDINGEN-LISANNE.md` — 10 bevindingen uit 10 min testen
> Analyse: `BEVINDINGEN-ANALYSE.md` — volledige gap-analyse met concurrent-research

**Kernprobleem:** Het dossier is niet compleet als werkhub. Bij BaseNet/Clio/Kleos doe je ALLES vanuit het dossier. Luxis mist kritieke velden en acties.

### F-Sprint 1: P0 Quick Wins — ✅ GEDAAN (commit `97e9d22`, 20 feb 2026)

| # | Bevinding | Status |
|---|-----------|--------|
| F1 | **Zoekfunctie** — `/api/search` endpoint gebouwd (global search over zaken, relaties, documenten) | ✅ Gedaan |
| F2 | **Postadres tonen** bij relaties | ✅ Gedaan |
| F3 | **Geboortedatum** bij personen | ✅ Gedaan (migration 022) |
| F4 | **Referentienummer partij** (`external_reference` op case_parties) | ✅ Gedaan (migration 022 + UI in PartijenTab) |
| F5 | **Rechtbank/rolnummer** (`court_case_number` op cases) | ✅ Gedaan (migration 022 + UI in Dossiergegevens) |

### F-Sprint 2: P1 Uitbreidingen — ✅ GEDAAN (commits `c55846b` + `821e281`, 20 feb 2026)

| # | Bevinding | Status |
|---|-----------|--------|
| F6 | **Facturatieprofiel** bij relaties (`default_hourly_rate`, `payment_term_days`, `billing_email`, `iban`) | ✅ Gedaan (migration 023 + Facturatie-sectie op relatiedetail) |
| F7 | **Afwijkende factuurrelatie** per dossier (`billing_contact_id` FK op cases) | ✅ Gedaan (migration 023) |
| F8 | **Inline contact aanmaken** bij dossier-aanmaak ("+ Nieuwe relatie" knop) | ✅ Gedaan (frontend modal op nieuw-dossier pagina) |
| F9 | **Uitgebreide filters** dossier-overzicht (assigned_to, date_from, date_to, bedrag) | ✅ Gedaan (backend + "Meer filters" panel) |
| F10 | **Telefoonnotitie-knop** met auto-timestamp template | ✅ Gedaan (quick-action knop op zaakdetail) |

### F-Sprint 3: P2 — NOG TE DOEN

| # | Bevinding | Complexiteit | Status |
|---|-----------|-------------|--------|
| F11 | **E-mail naar elke partij vanuit dossier** | L (eerst M365) of M (SMTP basis) | ✅ DONE (21 feb) |

> Detail per bevinding + concurrent-analyse + zelfkritiek: zie `BEVINDINGEN-ANALYSE.md`

**Werkwijze per feature:**
1. Onderzoek concurrenten
2. Plan voorleggen
3. Bouwen
4. `npm run build` / `pytest` + handmatig checken
5. Committen
6. Volgende feature

---

## Lisanne Feedback Sprint (LF-01 t/m LF-22)

**Bron:** `docs/research/LISANNE-FEEDBACK-13MRT.md` (13 maart 2026, eerste echte gebruik)
**Projectplan:** `.claude/plans/staged-popping-haven.md`
**Aanpak:** 8 fasen, 2 terminals parallel per fase, ~5-7 sessies doorlooptijd

### Alle items

| # | Beschrijving | Cat. | Grootte | Fase | Status |
|---|-------------|------|---------|------|--------|
| LF-01 | Contact aanmaken: adresvelden ontbreken | UX | S | 2 | ✅ 16 mrt |
| LF-02 | Dossieroverzicht: partijnamen niet zichtbaar bij smal scherm | UX/Responsive | S | 1 | ✅ 16 mrt |
| LF-03 | Afgesproken rente: geen keuze maand/jaarbasis | Feature | S-M | 2 | ✅ 16 mrt — rate_basis op Claim model |
| LF-04 | Vordering invullen bij aanmaken dossier | UX/Feature | M | 4 | ✅ 16 mrt — onderdeel wizard (LF-11) |
| LF-05 | Kenmerk client ontbreekt (veld bestaat al als `reference`) | UX/Vindbaarheid | S | 1 | ✅ 16 mrt |
| LF-06 | Vordering niet zichtbaar na invullen, hoofdsom 0, incassokosten niet zichtbaar | Bug | M | 1 | ✅ 16 mrt — Case.total_principal cache fix |
| LF-07 | Navigatie factuur → terug → facturenoverzicht i.p.v. dossier | Bug | S | 1 | ✅ 16 mrt |
| LF-08 | Vorderingen niet aanpasbaar (edit UI ontbreekt) | Bug | S-M | 1 | ✅ 16 mrt — inline edit + useUpdateClaim |
| LF-09 | Geüploade factuur niet gekoppeld aan vordering | Feature | M | 3 | ✅ 16 mrt — backend: invoice_file_id FK + PATCH endpoint |
| LF-10 | AI factuur parsing: auto-invullen bij aanmaken dossier | Feature (AI) | XL | 8 | ✅ 16 mrt |
| LF-11 | Dossier aanmaken: alles in een keer (wizard) | UX/Feature | L | 4 | ✅ 16 mrt — 3-step wizard: zaakgegevens → partijen → vordering |
| LF-12 | Incassokosten handmatig aanpasbaar + calculator | Feature | M | 2 | ✅ 16 mrt — frontend UI + backend persistence (bik_override) |
| LF-13 | Tabs "Vorderingen" en "Financieel" samenvoegen | UX | M | 3 | ✅ 16 mrt |
| LF-14 | Tabs "Betalingen" en "Derdengelden" samenvoegen | UX | M | 3 | ✅ 16 mrt |
| LF-15 | Betalingsregeling: termijnen, koppeling, meldingen | Feature (nieuw) | L-XL | 6 | ✅ 16 mrt |
| LF-16 | Email template vanuit dossier (functie bestaat, niet vindbaar) | UX/Vindbaarheid | S | 1 | ✅ 16 mrt |
| LF-17 | Dossierbestand als email bijlage + omgekeerd | Feature | M | 5 | ✅ 16 mrt |
| LF-18 | Batch-verstuurde brieven niet traceerbaar per dossier | Bug | M | 1 | ✅ 16 mrt |
| LF-19 | Uurtarief per dossier aanpasbaar | Feature | S-M | 2 | ✅ 16 mrt — hourly_rate op Case model |
| LF-20 | Incassokosten doorbelasten bij facturatie (succesprovisie) | Feature | L | 7 | ✅ 16 mrt — provisie berekening, budget tracking, advance balance |
| LF-21 | Fixed price, max uren, voorschot bij facturatie | Feature | L | 7 | ✅ 16 mrt — billing_method, voorschotnota, budget status |
| LF-22 | Debiteursinstellingen in dossier | Feature | M | 2 | ✅ 16 mrt — payment_term_days, collection_strategy, debtor_notes |

### Fase-overzicht

| Fase | Doel | Items | Terminals |
|------|------|-------|-----------|
| 1 | Bugs & Vindbaarheid | LF-02, LF-05, LF-06, LF-07, LF-08, LF-16, LF-18 | 2 parallel |
| 2 | Kleine features + velden | LF-01, LF-03, LF-12, LF-19, LF-22 | 2 parallel |
| 3 | Tab herstructurering | LF-09, LF-13, LF-14 | 2 parallel |
| 4 | Dossier wizard | LF-04, LF-11 | 2 sequentieel |
| 5 | Email verbeteringen | LF-17 | 2 sequentieel |
| 6 | Betalingsregeling | LF-15 | 2 sequentieel |
| 7 | Geavanceerde facturatie | LF-20, LF-21 | 2 parallel |
| 8 | AI factuur parsing | LF-10 | 2 sequentieel |

### Dependencies

```
LF-04 → onderdeel van LF-11
LF-06 → moet gefixt voor LF-12, LF-13
LF-08 → moet gefixt voor LF-09, LF-12
LF-16 → moet vindbaar voor LF-17
LF-19 → basis voor LF-20, LF-21
LF-10 → afhankelijk van LF-11
```

---

> **Toekomstige modules** (M365, AI Agent, Data Migratie, etc.) staan in `docs/future-modules.md`
>
> **AI Agent Masterplan** (sessie 38, 6 maart 2026): Uitgebreid onderzoeksplan in `docs/research/AI-AGENT-MASTERPLAN.md` (branch `claude/admiring-engelbart`).
>
> **AI Agent — Fase A1: MCP Tool Layer** ✅ Compleet (sessie 49, 11 maart 2026):
> 34 tools wrappen bestaande Luxis services voor Claude tool use. Fundament voor A2-A4.
> Componenten: ToolRegistry, ToolExecutor, serialize utility, 10 handler modules.
> Tools: cases (5), contacts (3), collections (5), documents (3), email (2), invoices (5),
> pipeline (3), workflow (3), time_entries (2), general (3). 26 bestaande tests passing, ruff clean.
> 57 tests voor tool layer toegevoegd in sessie 50 (registry 14, executor 8, serializer 35). Totaal: 83 AI agent tests.
> **AI Agent — Fase A2.1: Dossier Intake Agent** ✅ Compleet (sessie 52, 11 maart 2026):
> Client stuurt email met factuur → AI extraheert debiteur/factuurdata → concept-dossier → 1-klik goedkeuring.
> Kimi 2.5 primair ($0.001/call), Haiku 4.5 fallback ($0.005/call). PDF parsing via pdfplumber.
> Componenten: IntakeRequest model, kimi_client (dual AI provider), pdf_extract, intake_service (detect/process/approve/reject),
> intake_router (7 endpoints), intake_schemas, intake_prompts. Scheduler: elke 7 min. Migratie: 037_intake_requests.
> 20 tests (detection 5, processing 4, approve 3, reject 1, queries 2, multi-tenant 1, API 4). 509 totaal tests passing.
> **AI Agent — Fase A2.1 Frontend: Intake Review UI** ✅ Compleet (sessie 53, 11 maart 2026):
> Overzichtspagina (/intake) met status filter tabs + confidence bars + paginatie.
> Detail/review pagina (/intake/[id]) met inline-bewerkbare velden, approve/reject flow, AI analyse card.
> Sidebar integratie met pending count badge. 7 TanStack Query hooks. Frontend-only deploy.
>
> **AI Agent — Fase A2.2: Follow-up Advisor** ✅ Compleet (sessie 54, 11 maart 2026) — **Productietest PASS** (sessie 60):
> Rules-based workflow advisor — scant actieve incasso-dossiers, maakt aanbevelingen als min_wait_days bereikt.
> Backend: FollowupRecommendation model, scan service (30min scheduler), approve/reject/execute endpoints, 19 tests.
> Execute-flow: document genereren, email versturen, auto-advance pipeline stap. Geen AI/LLM nodig (deterministisch).
> Frontend: /followup pagina met status tabs + urgentie badges + 1-klik uitvoeren. Sidebar badge. Case detail banner.
> Productietest (sessie 60): 3/3 recommendations correct aangemaakt, urgency correct (normal/overdue), approve+execute succesvol (doc+email+auto-advance).
>
> **AI Agent — Fase A3: Betalingsmatching** ✅ Compleet (sessie 56-57, 11 maart 2026):
> CSV-import van Rabobank derdengeldrekening → auto-match aan incasso-dossiers → 1-klik goedkeuring.
> 5 matching methoden: dossiernr (95), factuurnr (90), IBAN (85), bedrag (70), naam (50).
> Execute: Derdengelden deposit + Payment record met art. 6:44 BW distributie. Volgt A2.2 patroon.
> Backend: 7 bestanden (models, csv_parsers, algorithm, schemas, service, router, migration). 15 API endpoints. 40 tests (568 totaal).
> Frontend: /betalingen pagina met CSV drag-and-drop upload, match review (confidence badges), 1-klik approve, bulk approve (≥85%), stats badges, sidebar met pending count badge.
>
> **AI Agent — Intake E2E Testpakket** (COMPLEET ✅):
> Laag 1: ✅ Seed script (`scripts/seed_intake_testdata.py`) — 18 intake_requests met diverse statussen/confidence/scenario's. --dry-run en --cleanup. (sessie 58, 11 maart)
> Laag 2: ✅ Test-factuur PDFs (`scripts/generate_test_invoices.py`) — 5 professionele Nederlandse facturen via WeasyPrint. Output: `scripts/test_invoices/`. (sessie 58, 11 maart)
> Laag 3: ✅ COMPLEET — Geautomatiseerd E2E script (`scripts/e2e_intake_test.py`) — directe service-calls met gemockte AI extractie. 4 scenario's (happy path, lege email body, edit-before-approve, reject flow). Marker-based cleanup, deterministische UUIDs, onafhankelijke DB sessies per scenario. (sessie 59, 11 maart)
> **LET OP: GEEN Gmail gebruiken — alles via OutlookProvider/Graph API met M365 account.**
>
> **AI Agent — Knowledge Base & Learning Loop** ✅ KERN LIVE (S171, 5 juli 2026):
> De "kennisbank" bleek grotendeels al te bestaan — `ContactTerms` (geversioneerde AV per cliënt met
> `valid_from`/`valid_to`/label, S140) + `case.contact_terms_id` + versie-selectie `select_terms_for_date`,
> én `automation_service.py` injecteert de gekozen AV al volledig in de verweer-prompt. S171: 3 AV-sets
> gekoppeld aan de 7 opdrachtgevers via de bestaande API + **end-to-end geverifieerd** (juiste versie +
> 5019 tekens per zaak). **K1 dus NIET nieuw bouwen — hergebruik `ContactTerms`; het K1-plan hieronder
> (nieuw `knowledge_documents`-systeem) is grotendeels achterhaald.** K0-gate poot 2 (voorwaarden) rond;
> poot 1 = Lisanne's review loopt (S171: 12 goedgekeurd / 118 kandidaat). **Openstaand:** `draft_service.py`
> leest nog legacy `Contact.terms_file_path` (verweer-pad correct); verweer-type-woordenschat te smal
> (5 types → 93% "Overig" — zie audit `docs/sessions/PROMPT-AUDIT-code-vs-roadmap.md`). Onderzoek S169
> hieronder blijft als achtergrond/architectuur-onderbouwing.
>
> **AI Agent — Knowledge Base & Learning Loop** 🔶 Onderzoek afgerond (S169, 4 juli 2026 — Fable 5):
> Volledige bevindingen + gefaseerd plan: `docs/research/kennisbank-learning-loop-onderzoek-2026-07-04.md`;
> premortem: `docs/research/premortem-report-2026-07-04.html` (+ transcript).
> **Uitkomst:** niemand (ook Harvey niet) laat het model "vanzelf leren" — industrie-standaard = gecureerde bronnen + mens keurt +
> voorbeelden in de prompt + meten; Luxis doet die vorm al (defense_library, verweer-bibliotheek, edit-rate, S160).
> **Architectuurkeuze:** deterministische selectieve prompt-injectie, GEEN RAG/vector-DB/embeddings (klein begrensd corpus,
> structurele selectiesleutels, AVG); upgrade-pad pgvector indien ooit nodig.
> **Plan (deels ACHTERHAALD per S171/S172):** ~~K1 kennisbank nieuw bouwen~~ → bestaat al (`ContactTerms`, gevuld S171).
> Wat overeind blijft: K0-gate (Lisanne's review — loopt), de met/zonder-vlag voor edit-rate-vergelijking (→ S174),
> K2 geaggregeerde meting (per-voorbeeld attributie GESCHRAPT), K3 GEPARKEERD, Kesting-begrippen richting data.
> **Nieuwe kern na audit S172: eerst VERBINDEN** — de kennisbank voedt maar 1 van de 3 AI-paden; zie prioriteitenblok bovenaan + PROMPT-S173.
>
> Oorspronkelijke omschrijving:
> De agent heeft een kennisbank nodig (algemene voorwaarden, wettelijke regels, interne richtlijnen) en een feedback/learning loop
> zodat hij leert van Lisanne's correcties en steeds beter wordt. Vereist: onderzoekssessie (hoe doen Harvey AI, CoCounsel, Clio AI dit?)
> → architectuurkeuze (RAG vs structured prompting) → knowledge base UI → feedback loop mechanisme.
> Onderdelen:
> - Knowledge base in Luxis (algemene voorwaarden Kesting Legal, wettelijke regels, standaard reacties, interne richtlijnen)
> - Feedback loop: agent voorstel → Lisanne keurt goed/corrigeert → agent onthoudt de juiste aanpak
> - Patroonherkenning: na N dossiers leert de agent welke aanpak werkt bij welk type debiteur
> - UI voor kennisbeheer (toevoegen/bewerken van kennis door Arsalan/Lisanne)
> - Meetbaarheid: success rate, aantal escalaties, verbetering over tijd
>
> **AI Email Classificatie** (sessie 39-43, 6 maart 2026): Eerste concrete AI-feature. Classificeert debiteur-emails in 8 categorieën, selecteert antwoord-template, Lisanne reviewt met 1 klik. Claude Haiku 4.5 via Anthropic SDK. Status: **Fase 1-7 COMPLEET** ✅ — E2E getest op productie.
>
> **AI Classificatie — Fase 7: Echte actie-executie** ✅ Compleet (sessie 45, 7 maart 2026):
> Alle acties in `execute_classification()` geïmplementeerd met echte side-effects:
> | Actie | Wat het doet | Status |
> |-------|-------------|--------|
> | `dismiss` | `SyncedEmail.is_dismissed = True` | ✅ |
> | `send_template` | Jinja2 template renderen + email versturen via EmailProvider/SMTP | ✅ |
> | `request_proof` | Template "verzoek betalingsbewijs" versturen via EmailProvider/SMTP | ✅ |
> | `wait_and_remind` | WorkflowTask aanmaken met due_date = vandaag + N dagen | ✅ |
> | `escalate` | WorkflowTask aanmaken (urgent, due_date=vandaag) | ✅ |
> | `no_action` | Alleen CaseActivity loggen | ✅ (was al werkend) |
> 4 nieuwe tests toegevoegd (26 totaal), ruff clean.

## Deploy

**Belangrijk:**
- `.env` moet bestaan in `/opt/luxis/`. Docker Compose leest dit automatisch. Als het ontbreekt: `cp .env.production .env`.
- `.env` bevat `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml` — hierdoor werkt gewoon `docker compose up -d` zonder `-f` flags.
- `POSTGRES_PASSWORD` in `.env` werkt ALLEEN bij eerste DB-initialisatie (volume aanmaken). Wachtwoord later wijzigen? → `docker compose exec db psql -U luxis -d luxis -c "ALTER USER luxis PASSWORD 'nieuw_wachtwoord';"` + `docker compose restart backend`
- Frontend moet ALTIJD relatieve URLs gebruiken (`""`) — NOOIT `localhost:8000`. Pre-commit hook blokkeert dit.
- Na Alembic migraties: `docker compose run --rm backend python -m alembic upgrade head` (gebruik `run` niet `exec` als backend crashed)

Frontend + backend:
```bash
cd /opt/luxis && git pull && \
docker compose build --no-cache frontend backend && \
docker compose up -d frontend backend
```

Alleen backend:
```bash
cd /opt/luxis && git pull && \
docker compose build --no-cache backend && \
docker compose up -d backend
```

Alleen frontend:
```bash
cd /opt/luxis && git pull && \
docker compose build --no-cache frontend && \
docker compose up -d frontend
```
