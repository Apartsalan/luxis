# Audit S183 — Architectuur + Beveiliging vóór livegang

**Datum:** 8 juli 2026 (S183, Fable, read-only)
**Vraag:** "Vibe-coded software zou onstabiel / onveilig / niet future-proof / verspillend zijn — klopt dat hier?"
**Methode:** meten in de bron — code op commit `63f83a2` (VPS == lokaal, geverifieerd), prod-DB uitsluitend SELECT, live gedragsbewijs waar mogelijk. Elke bevinding heeft een concreet faalscenario; zonder faalscenario geen bevinding.

---

## Executive summary: **JA, MITS**

Het systeem staat er wezenlijk beter voor dan het "vibe-coded"-vooroordeel suggereert. De rekenkernen zijn wet-conform en zwaar getest, de buitenkant is dicht (auth, rate-limits, OAuth, uploads, secrets), de afscherming per kantoor staat op 46 van de 48 tabellen hard aan, en de kernbevinding van S172 (drie AI-diensten met drie geheugens) is aantoonbaar opgeruimd.

**MITS — drie dingen vóór of direct na de heropening fixen (S184):**

1. **[HOOG] Renteberekening rekent fout bij creditfacturen + deelbetalingen** — bewezen met de echte functie; 4 zaken uit de heropeningslijst (372) hebben deze combinatie nu al.
2. **[MIDDEN] Het RLS-vangnet heeft twee structurele gaten** — de nieuwste tabel mist afscherming (bewezen op prod) en de afscherming valt stil uit na een tussentijdse commit in een verzoek (bewezen op prod, 31 plekken). Vandaag geen lek (één kantoor + handmatige filtering overal), maar het vangnet is niet wat de ontwerpdocumentatie belooft.
3. **[MIDDEN] Niets dwingt af dat toekomstige tabellen afscherming krijgen** — de drift van punt 2 gaat zich herhalen.

Geen blockers. Livegang met echte PII kan verantwoord — de twee beveiligingsgaten zijn vangnet-gaten (tweede verdedigingslinie), geen actieve lekken; de geldbevinding is klein in euro's maar hoort niet in brieven van een advocatenkantoor.

---

## As 1 — Beveiliging / buitenkant

### S183-1 · [MIDDEN · NIEUW] Tabel `learned_answers` heeft géén RLS op productie

- **Bewijs (prod-query):** van de 48 tabellen met `tenant_id` hebben er 46 `FORCE ROW LEVEL SECURITY` + policy; `users` is een gedocumenteerde uitzondering (`app/security/rls.py:31`), **`learned_answers` niet** — `rls=f, force=f, 0 policies`.
- **Oorzaak:** de RLS-migratie (`h2_rls_complete`, 2 juni) ontdekte tabellen dynamisch — eenmalig. `learned_answers` is aangemaakt op 18 juni (`1badcb2940ce_s168_learned_answers_shadow_learning.py`) zonder RLS-statements. `apply_rls` draait alleen in die ene migratie en in de testsuite.
- **Faalscenario:** tweede tenant komt erbij → één vergeten `tenant_id`-filter in een toekomstige query op deze tabel lekt Lisanne's (geanonimiseerde én ruwe!) verweerteksten cross-tenant. Vandaag: alle queries in `app/ai_agent/learned_answers.py` filteren netjes op tenant — geen actueel lek.
- **Verzwarend:** de adversariële test (`tests/test_rls_isolation.py:61`) zet RLS **zelf** aan vóór hij test — hij bewijst dat het beleid wérkt, niet dat productie het hééft. Drift is dus onzichtbaar voor de testsuite.

### S183-2 · [MIDDEN · NIEUW] `SET LOCAL ROLE` vervalt bij tussentijdse commit — rest van het verzoek draait als superuser

- **Bewijs (live op prod-DB):** `BEGIN; SET LOCAL ROLE luxis_app; COMMIT;` → `current_user` is daarna weer `luxis` (superuser) en `app.current_tenant` is leeg. Gedocumenteerd PostgreSQL-gedrag, hier live aangetoond.
- **Mechanisme:** `set_tenant_context` (`app/middleware/tenant.py:36,56`) draait één keer per verzoek in `get_current_user` (`app/dependencies.py:53`). Elke `await db.commit()` middenin een handler beëindigt de transactie; er is geen her-toepassing (geen event-hook, grep bevestigt).
- **Omvang (gemeten):** 31 plekken waar een handler ná `db.commit()` nog databasewerk doet (o.a. `ai_agent/followup_router.py`, `intake_router.py`, `payment_matching_router.py` — patroon: commit → `get_X(db, tenant_id, id)` voor de response; plus één schrijfactie: `incasso/router.py:413`).
- **Faalscenario:** elke toekomstige query ná zo'n commit die per ongeluk het tenant-filter mist, leest/schrijft cross-tenant — RLS vangt het niet, terwijl het ontwerp ("fails closed", `app/security/rls.py:35`) belooft van wel. Vandaag compenseert de handmatige filtering op alle 31 plekken.
- **Bekende-residual-relatie:** dit maakt het bekende punt "app draait als DB-superuser" concreet: het lekpad bestaat, alleen de app-laag staat ervoor.

### Aantoonbaar op orde (as 1)

- **Auth:** alle 28 routers per-route geguard; enige publieke routes zijn login/refresh/forgot/reset (rate-limited: 10/min, 20/min, 3/uur, 5/uur) en OAuth-callbacks. `/register` is admin-only (`auth/router.py:84`).
- **OAuth-state:** HMAC-getekend + eenmalige nonce in Redis + vervaltijd (`email/oauth_service.py:53-109`). Tokens versleuteld opgeslagen (ook Exact Online).
- **Uploads:** Caddy begrenst álles op 55 MB aan de rand (geverifieerd op VPS-Caddyfile); dossierbestanden/AV/sjablonen hebben eigen extensie-whitelist + 10 MB-cap + magic-byte-check; bankimport leunt op de Caddy-cap (55 MB CSV in geheugen — acceptabel).
- **Secrets:** geen hardcoded geheimen in de code (sweep), `.env`-bestanden staan niet in git, alleen examples.
- **Drift:** VPS draait exact git HEAD, werkboom schoon.
- **Tokenopslag:** access + refresh in `localStorage` (`frontend/src/lib/token-store.ts`) — bekende, bewuste keuze; refresh-token-rotatie (sec12) beperkt de schade bij XSS. Laag.

---

## As 2 — Architectuur / houdbaarheid

### Aantoonbaar op orde (as 2)

- **S172-kernbevinding "3 AI-diensten / 3 geheugens" is opgeruimd:** alle drie de conceptpaden (`incasso/automation_service.py:445`, `ai_agent/draft_service.py:128`, `ai_agent/unified_draft_service.py:246`) gebruiken nu de gedeelde `knowledge_context.resolve_case_terms` + gedeelde geleerde-voorbeelden. Welke knop Lisanne klikt maakt niet meer uit voor wat de AI weet.
- **Scheduler:** één uvicorn-proces (Dockerfile:41, geen `--workers`) → geen dubbele jobs; APScheduler default `max_instances=1`; de 5-min-backfill heeft bovendien een advisory-lock per tenant (`learned_answers.py:500`). Elke job heeft per-tenant/per-account foutisolatie met logging — geen stille uitval van de hele run.
- **Stil falen:** slechts 7 `except: pass`-plekken, allemaal smal (parse-fallbacks in CSV/IMAP/JSON-decodering), geen enkele op een geld- of verzendpad.
- **N+1:** zakenlijst en pipeline-bord zijn eager-loaded/gegroepeerd (2 queries + geheugen); geen N+1 op de hete paden.
- **Tenant-scope:** steekproef over alle service-functies — handlers geven consequent `user.tenant_id` door. Enige gedeelde functie zonder eigen tenant-check is `calculate_case_interest` (aanroepers zijn gescoped; verdedigbaar).

### Kleine punten (laag, deels bekend)

- `daily_pipeline_auto_drafts` zet `SET app.current_tenant` (sessie-breed, zonder rolwissel — `workflow/scheduler.py:683`): heeft als superuser geen RLS-effect; cosmetisch verwarrend.
- Twee workflow-systemen (`case.status` naast pipeline-stap) en vier sjabloon-opslagplaatsen: bekende residuals uit S172, ongewijzigd, bewuste keuzes/latere opruimklus.
- Groei naar 2e advocaat/meer volume: geen schaal-blokkades gevonden; volumes (607 zaken, 6.393 mails) zijn triviaal voor Postgres; de dagelijkse jobs itereren per tenant en schalen lineair.

---

## As 3 — Geld-correctheid

### S183-3 · [HOOG · NIEUW] Pro-rata-verdeling van betalingen over vorderingen rekent fout bij creditfacturen

- **Plek:** `app/collections/interest.py:524-565` (`_build_claim_reductions`).
- **Bewijs (functie zelf uitgevoerd):** vorderingen +€1.000 / −€200 (credit) / +€200, betaling €500 naar hoofdsom → het algoritme boekt **€600** af op de positieve vorderingen (€100 te veel) en niets op de creditvordering. Mechanisme: het negatieve pro-rata-aandeel wordt wél bij `distributed` opgeteld maar niet toegepast (`if share > 0`), waarna de laatste vordering `allocated - distributed` = te veel krijgt.
- **Gevolg:** te lage rente op de positieve vorderingen (nadeel cliënt) én de creditvordering blijft onverminderd negatief doorrenten. Elk bedragen-overzicht in een sommatiebrief op zo'n zaak wijkt af.
- **Omvang (prod-gemeten):** 68 negatieve vorderingen (−€22.870,47) op 45 zaken; **11 zaken** combineren negatieve vordering + deelbetaling; **4 daarvan zitten in de heropeningslijst van 372** (IN100334 — 4 creditfacturen + 7 betalingen —, IN100469, IN100505, IN100553). Elke toekomstige creditfactuur+deelbetaling-zaak raakt dit ook.
- **Fix-richting (S184):** negatieve vorderingen buiten de pro-rata-basis houden (verdelen over positieve vorderingen; creditbedrag als verrekening op zaak-niveau), met rode test op het bewezen scenario.

### S183-4 · [LAAG · NIEUW] Betaling op/vóór de verzuimdatum wordt genegeerd in de renteberekening

- **Plek:** `app/collections/interest.py:276` — filter `default_date < d < calc_date` gooit betalingen op of vóór de verzuimdatum van een vordering weg → rente loopt over het onverminderde bedrag.
- **Omvang (prod-gemeten):** 18 betalingen (€9.485,81 hoofdsom-allocatie) raken dit filter — **alle 18 op afgesloten zaken**, geen enkele in de heropeningslijst. Meestal gaat het om een zaak met meerdere vorderingen waar de betaling vóór het verzuim van één deelvordering valt (het pro-rata-deel voor die ene vordering verdampt).
- **Faalscenario (toekomst):** betalingsregeling loopt terwijl een deelfactuur nog niet in verzuim is → rente op die deelfactuur licht te hoog (nadeel debiteur — juridisch vervelender dan te laag).

### Aantoonbaar op orde (as 3)

- **Alles Decimal:** geen float in enige berekening (sweep); float alleen in een dashboard-percentage en de Exact Online API-serialisatie (0 actieve connecties).
- **Rentemotor:** samengesteld jaar loopt vanaf verzuimdatum (niet 1 januari), kapitalisatie alleen na vol jaar, tariefwissels worden per segment gesplitst, 29-feb-randgeval afgevangen, 365-conventie consequent. `ROUND_HALF_UP` op 2 decimalen overal.
- **WIK-staffel:** tiers/min €40/max €6.775/21% BTW exact conform Besluit (code naast `docs/dutch-legal-rules.md` gelegd).
- **Art. 6:44:** kosten → rente → hoofdsom, negatieve betaling geweigerd, overbetaling apart.
- **Testdekking:** 65+ tests op de drie rekenkernen alleen al (31 rente + 22 WIK + 12 verdeling), plus edge-case-, erving-, arrangements- en trust-suites.
- **Integriteit prod:** `total_paid` == som betalingen op **0** van de actieve zaken afwijkend (herbevestigd; S181-F vond hetzelfde).

---

## As 4 — Verspilling

- **[LAAG · BEKENDE RESIDUAL] `--no-cache` staat nog in de CI-deploy** (`.github/workflows/deploy.yml:29`) — elke automatische deploy bouwt alles opnieuw (trager + build-cache-groei; `disk_guard.sh` beperkt het disk-risico, het S120-incident-mechanisme bestaat dus nog steeds maar gedempt). Eén regel weghalen in S184.
- **AI-kosten zijn bescheiden en niet dubbel:** één centrale modeldefinitie (`kimi_client.py:35` — Sonnet voor concepten, Haiku beschikbaar), 362 classificaties in de laatste 7 dagen, 0 concepten (auto-drafts uit). Kosten per concept (schatting, niet gemeten): AV + voorbeelden ≈ 10-20k tokens input → orde €0,10-0,20; de getrouwheids-poort kan dat ×3 doen bij regeneratie — bewuste kwaliteitskeuze.
- **Klein spul:** `get_learning_stats` doet tot 50 sequentiële queries per dashboard-weergave (alleen dat scherm, verwaarloosbaar); `kimi_client.py` heet nog zo maar is 100% Claude (bekend, cosmetisch); `Contact.terms_file_path` is geen dode code maar een gedocumenteerde fallback in de gedeelde resolver; GmailProvider is al opgeruimd (alleen nog een verwijzing in `base.py`).
- **Geen** onnodige periodieke AI-calls: classificatie/intake-jobs draaien alleen bij nieuwe onverwerkte mail en zijn anders no-ops.

---

## Niet-doen-lijst (aantoonbaar op orde — hier géén sessies aan besteden)

1. RLS-beleid zelf (policy-inhoud, FORCE, WITH CHECK) — klopt op alle 46 gedekte tabellen.
2. Auth-flow, rate-limits, lockout, OAuth-state, token-encryptie — dicht en netjes.
3. Upload-afhandeling — dubbel begrensd (rand + endpoint).
4. De drie rekenkernen (rente/WIK/6:44) — wet-conform, zwaar getest; alleen de twee gemelde randgevallen.
5. Scheduler-opzet — enkel proces, foutisolatie, locks waar nodig.
6. AI-laag-samenhang — S173-consolidatie is echt en volledig.
7. Schaalbaarheid richting 2e advocaat — geen blokkades.

## Werkorder S184 (volgorde van belang)

1. **S183-3** pro-rata bij creditfacturen (rode test eerst; herbereken daarna de 4 heropeningszaken).
2. **S183-1 + drift-guard:** RLS op `learned_answers` + een pytest die op het échte schema controleert dat élke tabel met `tenant_id` (behalve `users`) FORCE RLS + policy heeft — dan kan drift nooit meer stil zijn.
3. **S183-2:** her-toepassing van rol + tenant ná elke commit (bv. SQLAlchemy `after_begin`-event op de sessie) — één structurele fix i.p.v. 31 plekken.
4. **S183-4** betaling-vóór-verzuim (klein; kan mee met 1).
5. `--no-cache` uit deploy.yml (één regel).
