# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 12 juli 2026 (S204, Fable — review S203-fixes, 100% read-only). 9 van 11 fixes bevestigd; 2 vervolg-punten gevonden. Rapport: `docs/sessions/S204-review.md`.
**Laatste feature/fix:** geen code gewijzigd (reviewsessie). Bewezen defect: mailsync-foutpad vergiftigt volgende accounts (MissingGreenlet na rollback); 14-dagenbrief-gate heeft 2 zijdeuren (follow-up "Uitvoeren" + AI-concept-verzendpad) en een zwakke verstuurd-proxy.
**Openstaand:** S205 = fix-sessie beslislijst S204 (2× juridisch 🔴). Daarna: 35-route-sloop, #7 audittrail, #15 regeling-badge, log-persistentie, S201-import. Mailslot blijft DICHT.
**Volgende sessie:** S205 = gate-zijdeuren + mailsync-fix (`docs/sessions/PROMPT-S205-gate-zijdeuren.md`); checklist morgen: dagelijkse-job-rijen in `scheduler_heartbeat`.

## Sessie 204 (12 juli 2026, Fable — review S203-voorkant-fixes, 100% read-only)

### Samenvatting
Alle S203-fixes (15 commits + na-tag `27842a2`) in de bron nagelezen, tegengesproken en op prod
gecontroleerd (GET-API + read-only SQL). **9 van 11 bevestigd zonder voorbehoud**: tijdlijn (#13),
hernoem-PATCH incl. cross-tenant-404 (#4), €0-markering incl. pop-vóór-prompt + end-to-end test (#3),
1169→1 (#6, prod: 1168/1169 met marker, de ene = "Arsalan"), batch-toast (#9), ratio zelfde populatie
+ cap (#10, prod 5,3), openstaand-labels (#14), intake-startstap = kopie van creatiepad (#8),
logout/Gmail (#16/#17). Heartbeat (#2) werkt bewezen op prod (5 verse rijen). Volledig rapport mét
bewijs per fix: **`docs/sessions/S204-review.md`**.

### Twee gevonden punten (vervolg-bouwsessie nodig)
1. **Mailsync-foutpad (#1) — bewezen latent defect:** `rollback()` in de except expireert álle
   account-objecten (negeert `expire_on_commit=False`); het volgende account crasht op zijn eerste
   attribuutlezing met MissingGreenlet en de log-f-string in de except gooit een tweede → hele run
   stopt. Eén structureel falend account (verlopen token) blokkeert zo elke 5 min de sync van de
   accounts erná, zonder eigen foutmelding en zonder dashboard-alarm. Bewezen met probe op de echte
   sessie-factory. Het gevreesde "geslaagde sync teruggerold" is wél afgedekt (commit per account).
2. **14-dagenbrief-gate (#5) — batch-gate zelf correct, maar 2 zijdeuren + zwakke proxy:**
   follow-up "Uitvoeren" (`execute_recommendation`, 14 pending aanbevelingen op prod) en het
   AI-concept-verzendpad (compose/send + advance-after-send) versturen sommaties zónder gate;
   en `entered_at` = stap-binnenkomst, niet verzending (doorschuiven zonder versturen telt als
   "verstuurd"). Operationeel gat: de 14-dagenbrief-stap heeft op prod geen sjabloon → Luxis kan de
   brief zelf nu niet versturen; beide actieve B2C-zaken (IN100345/350) staan stap-loos → vandaag
   geen acuut risico (batch skipt ze al eerder).

### Verificatie
155 tests groen (8 S203-suites, docker), ruff schoon, prod `alembic_version=s203b`. Prod-API:
`contacts_this_month=1`, `collection_rate=5.3`, `scheduler_alerts=[]`; SQL: 3 sync-accounts vers +
foutveld leeg, heartbeats 18:47, `case_step_history=0` (verwacht: nog geen intake/stap-actie sinds
deploy). Niet geverifieerd: frontend visueel (alleen code + S203-livecheck), dagelijkse
heartbeat-rijen (bestaan pas na de nacht), live logout (zou prod-tokens intrekken — bewust overgeslagen).

### Volgende sessie
S205: beslislijst uit `S204-review.md` §Beslislijst — (1) gate in follow-up, (2) gate in
concept-verzendpad, (3) verzend-proxy verstevigen, (4) mailsync-foutpad, (5) dagenbrief-sjabloon
op de stap (besluit), (6) heartbeat-last_error bij interne jobfouten, (7) check dagelijkse-job-rijen.

## Sessie 203 deel 2 (12 juli 2026, Opus — voorkant-fixes UITGEVOERD + LIVE)

### Samenvatting
Eerst Codex' read-only audits nagecontroleerd (fable-diepte): 8 security-bevindingen zelf in de
bron teruggevonden (alle 8 kloppen), facturatie-onderzoek onafhankelijk hergeteld tegen de
BaseNet-export (567/773/€235.899,91 + de 7 Mollie-conflicten op de seconde) — **Codex-review
betrouwbaar, eerste keer goed gegaan**. Daarna: 11 van 12 S203-taken gebouwd, per fix
rood→groen→commit→push→deploy, 4 deploys, migraties `s203`/`s203b` op prod, alle containers healthy.

**Ronde 1 (klein, live):** (13) tijdlijn-crash `duration_seconds`/`entry_date` → `duration_minutes`/
`date` (+ sibling-bug). (4) hernoem-knop: PATCH `/api/cases/{id}/files/{id}` gebouwd + onError.
(3) AI-concept bij €0-terugval markeert draft + reviewtaak (gegate op €-sjabloon; regressie in
draft-gate zelf gevangen+gefixt). (6) "1169 toegevoegd deze maand" → import-marker uitgesloten,
**live 1169→1**. (9) batch-fouten als waarschuwing mét redenen i.p.v. groene toast. (11/12) nep-tabs
Meldingen+Weergave verwijderd. (10/14) incasso-ratio zelfde populatie + gecapt **49,1%→5,3% live**;
negatief "Openstaand" → "teveel betaald"; lijstkolom "Openstaand (hoofdsom)".

**Ronde 2 (middel, live):** (1) mailsync-gezondheid: `last_sync_error`-veld + banner (rood mislukt /
amber >60min / laatst-gesynct), scheduler zet fout per account atomisch. (2) scheduler-heartbeat:
nieuwe `scheduler_heartbeat`-tabel + APScheduler-listener legt elke job-run vast; dashboard toont
rood alarm als een kritieke dagelijkse job (o.a. verjaringscontrole) >25u niet draaide. (8) intake
wijst nu de eerste pijplijn-stap + historie-rij toe (Staphistorie vult zich weer; going-forward).
(5) 14-dagenbrief-waarborg leest het echte spoor (`CaseStepHistory`) i.p.v. de lege tabel; de batch
blokkeert een B2C-sommatie **hard** als de 14-dagenbrief niet verstuurd is óf binnen 15 dagen daarna
(besluit Arsalan: nooit eerder dan 15 dagen; `DAGENBRIEF_MIN_DAYS=15`). (16/17) logout trekt tokens
server-side in, Gmail-knop verborgen, dode hook `usePendingCount` weg.

### Verificatie
Elke fix: gerichte tests groen (nieuwe tests bij elke fix), `uvx ruff` schoon, `tsc --noEmit` groen.
Betrokken suites samen groen (incasso-pipeline 51, dashboard 23, intake 27, email-sync 28, RLS-drift 8,
compliance-14dagenbrief 3, e.a.). Migraties `s203`+`s203b` op prod = head, containers healthy. Live
via API bevestigd: `contacts_this_month` 1→ (was 1169), `collection_rate` 5.3 (was 49,1), `scheduler_alerts`
veld werkt. Valkuil-les: mijn eerste fix-3 markeerde óók bedragenloze sjablonen + lekte een context-sleutel
in `build_user_prompt` — beide door de draft-gate-tests gevangen vóór deploy (fable-tegenspreker).

### Bekende issues / bewust niet gedaan (scope)
- **35-route backend-sloop niet uitgevoerd** — ⚠️-trace + 3 "niet slopen zonder besluit"-uitzonderingen;
  vraagt een eigen per-route-verificatieronde, niet aan het eind van deze lange sessie geforceerd.
- **#7 document-audittrail** en **#15 regeling-badge** stonden niet in de S203-takenlijst → open.
- **#5 juridisch besloten (Arsalan):** harde blokkade, nooit een sommatie eerder dan 15 dagen ná de
  14-dagenbrief. Open detail voor Lisanne: een buiten Luxis verstuurde 14-dagenbrief moet handmatig
  in het systeem geregistreerd worden, anders blokkeert de gate terecht.
- De 10 bestaande stap-loze intake-zaken zijn een aparte data-actie (going-forward-fix raakt ze niet).
- Mailslot bleef DICHT; niets verstuurd. Statusregel per bevinding: `docs/sessions/S200-BEVINDINGEN.md` (tabel bijgewerkt).

### Incident bij afsluiting — per ongeluk gecommitte bestanden, historie herschreven (mét akkoord)
Bij het sessie-einde veegde één `git add -A` **110 bewust-untracked bestanden** mee in een docs-commit,
waaronder het **derdengelden-bankafschrift** (CSV, 1 jaar), AV-PDF's, `.agents/` en tmp-audit-SQL.
Afhandeling (expliciet akkoord Arsalan): laatste 3 commits vervangen door één schone (`3f5e183`),
force-push, lokaal én op de VPS alle oude objecten vernietigd (reflog+gc; CSV-blob aantoonbaar weg
op beide), VPS-HEAD gelijkgetrokken (ff-pull werkt weer normaal). Tag `sessie-203-fixes` stond vóór
de foute commit → ongemoeid. **Restrisico:** GitHub kan de weggegooide commits server-side nog even
vasthouden tot hun eigen opruiming (privérepo; niet meer bereikbaar via branch/tag). **Borging:**
`.gitignore` dekt de paden nu; harde regel "nooit `git add -A`, stage expliciete paden" toegevoegd
aan CLAUDE.md + AGENTS.md + Claude-memory.

### Volgende sessie
**S204 = Fable-review van deze S203-fixes** (`docs/sessions/PROMPT-S204-fable-review.md`): read-only,
bron + prod nalezen, tests draaien, elke fix tegenspreken. Pas daarna nieuw bouwen (S201-import óf route-sloop).

---

## Sessie 203 deel 1 (12 juli 2026, Sol Ultra — Codex-master Fase A+B, read-only)

### Samenvatting
- **Fase A mailpadaudit afgerond.** Blok 2 in `docs/security/S202-delta-audit.md` is gevuld en onafhankelijk tegengesproken. Nieuwe kern: ongeëscapete dossierdata in systeemmail-HTML, ontvangers niet centraal gevalideerd/begrensd, late bijlagecaps, mailslotcache vóór commit en logvervalsing/PII in logs. Alle drie applicatietransporten controleren het mailslot; prod stond effectief dicht.
- **Fase B BaseNet-onderzoek afgerond.** De parser las 133 entiteiten, 65.761 records en 2 defecte LetterTemplate-fragmenten. De twee gevraagde bouwdocumenten bestaan: facturatierecept plus een volledige 133-rijenmatrix die exact terugtelt.
- **Factuurbesluit:** van 567 koppen/773 regels zijn 439 koppen/630 regels conflict-vrij en automatisch importeerbaar (€302.750,39 bruto; €72.762,09 open). Zeven koppen (€10.854,66) hebben een harde Mollie-`paid` versus volledig-open-koptegenstrijdigheid en blijven buiten automatische import. Negentig derdengeld-/verrekenposten (−€90.718,21) horen niet in omzet.
- **Grootste migratiegat:** 187 niet-geïmporteerde D-dossiers dragen 8.637 correspondentiestukken en 1.236 urenregels. De 1.320 uren worden pas na die dossiers apart geïmporteerd. Donker/Dinc: 12 credits (€21.738,96) zijn geen kantoorfactuurbetalingen; bestaand besluit blijft staan.
- Geen productie-mutatie, geen import, geen mail en geen deploy uitgevoerd.

### Gewijzigde bestanden
- `docs/security/S202-delta-audit.md` — mailpadblok, samenvatting en fixvolgorde bijgewerkt.
- `docs/research/S201-facturatie-recept.md` — gemeten veldmapping, disjuncte importgroepen, betalingen, urenadvies, Donker/Dinc en bouw-/testrecept.
- `docs/research/S201-volledigheidsmatrix.md` — alle 133 entiteiten, relevante gaten en concrete acties.
- `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` — overdracht naar Sol High; S192-entry naar archief.

### Verificatie
- Mailregressie: 26 passed, 1 warning; transports geblokkeerd, geen mail verstuurd. Read-only prod: mailslot dicht, 3 echte accounts versleuteld, 0 `email_logs`.
- Bronasserties: kopgroepen `439+7+12+19+90=567`; regelgroepen `630+13+9+0+90+31=773`; geldsom exact €235.899,91. Regelformule 773/773 en kop-regelsom 542/542 exact. Voor 305 historische betalingen blijft de betaaldatum eerlijk onbekend; memoriaaldatum wordt alleen boekingsmetadata.
- Matrixassertie tegen verse parserrun: 133/133 entiteiten, 65.761/65.761 records, geen ontbrekende/extra/mismatched rij.
- Productie read-only: 58/58 debiteurcodes en 146/146 IN-codes matchen elk exact één Luxis-record; factuur-/uren-doeltabellen staan op 0.

### Bekende issues
- De zeven Mollie/kop-conflicten vereisen per factuur bevestiging door Lisanne/boekhouding vóór import.
- Niet geverifieerd: of de reeks “Facturen met Stephanie” en zeven toekomstige D-afspraken al in Outlook staan; Outlook was niet via een connector beschikbaar.
- S200's 19 voorkantbevindingen en S202-fixes H1/H2/H3/M1/M2 plus mailhardening zijn nog niet gebouwd. M3 (DB-superuser/RLS Fase 2) blijft bewust buiten deze fixronde.

### Volgende sessie
- Zet Codex op Sol High en vervolg `docs/sessions/PROMPT-CODEX-master.md` vanaf Fase C. Werk per fix rood→groen→commit→push→deploy; daarna Fase D en Fable-nacontrole.

## Sessie 202 (12 juli 2026, Fable — security- & consistentie-audit van de delta sinds S183, read-only)

### Samenvatting
- Security-audit van álle wijzigingen `sessie-183..HEAD` (49 commits, 122 bestanden). 6 van 7 blokken deze sessie afgerond; **Blok 2 (mailpad S185-S187) afgebroken door tokengebrek en overgedragen aan Codex**. Rapport op ernst: `docs/security/S202-delta-audit.md`.
- **Hoog (3):** (H1) `save_attachment_to_case` (`email/sync_router.py:527-581`) controleert `case_id` niet tegen tenant vóór het aanmaken van een `CaseFile` → cross-tenant integriteitslek; de guard staat elders in datzelfde bestand al. (H2) fail-open op de "betaald"-guard (`cases/service.py:744-747` + `incasso/service.py:479-490`): rekenfout → €0 aangenomen → dossier mét saldo kan stil op "betaald". (H3) "Geïnd"-rapportage (`reports_service.py:62,220`) sommeert `Payment.amount` zonder `is_active`-filter → verwijderde betalingen tellen eeuwig mee.
- **Middel (3):** bulk-status zonder lengtecap (DoS); auto-advance mist terminale-stap-check; app verbindt als DB-superuser (RLS hangt volledig aan `SET ROLE luxis_app` — bekende "Fase 2").
- **Geruststellingen (op prod gemeten):** RLS compleet zonder drift — 44/44 tenant-tabellen FORCE+policy, alleen `users` bewust uitgezonderd. Geen secrets in repo of delta-diff; `.codex/config.toml` staat nu wél in `.gitignore` (anders dan notities zeiden). Geen `NEXT_PUBLIC_*`-sleutels. PowerSearch injectie-veilig + tenant-gescoped. Bulk-status en pipeline-batch tenant-gescoped in de query zelf.

### Gewijzigde bestanden
- `docs/security/S202-delta-audit.md` (nieuw — het auditrapport, incl. kant-en-klare Codex-vervolgprompt voor Blok 2)
- `docs/sessions/PROMPT-CODEX-master.md` (nieuw — complete Codex-onboarding + 4-fasen-werkvolgorde voor S200/S201/S202-vervolg)
- `docs/sessions/S201-HANDOFF-naar-Sol.md` (van parallel S201-spoor — mee-gecommit voor Codex)
- `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` (afsluiting); S191-entry → archief
- Geen code, geen prod-mutatie (100% read-only nageleefd; DB-toegang alleen SELECT)

### Bekende issues
- Alles in `S202-delta-audit.md`. Blok 2 (mailpad) nog te auditen — prompt staat onderin dat rapport.
- Fix-volgorde voor de bouwsessie: H1 (klein, duidelijkst tenant-lek) → H2 → H3 → M1/M2. M3 (app-als-superuser/Fase 2) is een aparte grote klus.

### Volgende sessie
- Codex neemt over via `docs/sessions/PROMPT-CODEX-master.md` (Ultra: mailpad-audit + facturatie-onderzoek; High: voorkant-fixes + security-fixes). Over ~3 uur checkt Fable Codex' werk na.

## Sessie 200 (12 juli 2026, Fable — "de voorkant liegt"-audit, 100% read-only op prod)

### Samenvatting
- Alle 8 vegen uit `PROMPT-S200.md` uitgevoerd + Lisanne-dag doorgeklikt op prod (ingelogd via gemint token, alleen GET/kijken). Resultaat: **19 genummerde bevindingen** met bewijs, ernst en fix-grootte in `docs/sessions/S200-BEVINDINGEN.md`, gerangschikt op impact voor Lisanne.
- **Hoog (6):** mailsync kan stil doodgaan (geen sync-gezondheid in UI); alle 12 scheduler-jobs incl. verjaringscheck falen alleen naar server-log; AI-concept valt bij rekenfout stil terug op €0 rente/BIK; "Hernoemen" dossierbestand = kapotte knop (PATCH-route bestaat niet + geen onError); 14-dagenbrief-compliancecheck dubbel dood (leest lege tabel én nul UI-callers — juridisch relevant); dashboard "1169 toegevoegd deze maand" (allemaal import-stempels).
- **Middel:** "Gegenereerde documenten"-sectie blijvend leeg (live briefpad persisteert niets); Staphistorie-tab altijd leeg (AI-intake seedt geen stap/historie; 10 stap-loze zaken); batch-fouten verdwijnen in groene toast; incasso-ratio deelt appels door peren; nep-tabs Instellingen→Meldingen/Weergave; latente 500 op dossier-tijdlijn (`duration_seconds` vs `duration_minutes`, 1-regel-fix); negatieve "Openstaand"-bedragen + twee definities van "Openstaand".
- **Relieken:** 35 dode routes (lijst in rapport), dode hook `usePendingCount`, Gmail-knop nog live tegen beleid in, `POST /api/auth/logout` juist nooit aangesloten (security-flag), `document_templates`/`email_logs` reliek.
- **Goed nieuws:** alle 30+ gecontroleerde cijfers op dashboard/rapportages/badges kloppen exact met SQL; 0 console-errors/4xx/5xx bij doorklikken; S191-meldingen-mysterie (264 vs 299) verklaard: bel verbergt `classification_done` per gebruiker — badge 20 is correct.
- Audit 7-beperking: prod-logs bestaan maar ~9 uur (containerlogs weg bij elke deploy) → aanbeveling log-persistentie. Caddy: 29× 502 geclusterd rond S199-deploys (1 mislukte login).

### Gewijzigde bestanden
- `docs/sessions/S200-BEVINDINGEN.md` (nieuw — het rapport)
- `docs/sessions/PROMPT-S203-voorkant-fixes.md` (nieuw — fix-bouwsessie)
- `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` (deze afsluiting); S190-entry → archief
- Geen code, geen prod-data (100% read-only nageleefd; alle DB-toegang was SELECT, API-toegang alleen GET)

### Bekende issues
- Alles in `S200-BEVINDINGEN.md` (fixes = S203). Snelste winst: tijdlijn-crash (1 regel), hernoemen-knop, €0-fallback-markering.
- Untracked in werkkopie (niet van S200): `S201-HANDOFF-naar-Sol.md`, `docs/security/S202-delta-audit.md`, AV-PDF's, bank-CSV, `.agents/`, `AGENTS.md` — laten staan voor het parallelle spoor; Arsalan beslist over committen.

### Volgende sessie
- Sol rondt S201 af (facturatie-onderzoek, handoff-doc) → daarna S202 (security-delta) → daarna S203 (voorkant-fixes, prompt klaar).

## Sessie 199 (12 juli 2026, nacht — /codex-build: Sol bouwt xhigh, Fable verifieert — veegsessie LIVE)

### Samenvatting
Tweede codex-build-rit met Sols write-toegang. Sol (`gpt-5.6-sol`, effort xhigh, sessie
`019f534a…`) bouwde de bevroren veegspec `PROMPT-S199.md` (taak 1–4 + code-delen taak 5)
in één run, geen fix-rondes. Claude (Fable) las de volledige diff na, draaide álle bewijzen
zélf opnieuw en zette per taak live onder Arsalans nacht-akkoord. Bouwlog: `docs/sessions/
S199-BUILD-LOG.md`.

**Taak 1 — 'betaald' = eindstatus overal (`TERMINAL_STATUSES`).** Dashboard-werkvoorraad,
portefeuille-openstaand, AI-classificatie-sweep, betaalhook en `check_verjaring` sloten alleen
'afgesloten' uit; betaalde zaken telden onterecht mee (incl. AI-kosten). Per plek beoordeeld
(rapportage "Geïnd" telt betaald juist wél als geïnd — geen blinde vervanging).

**Taak 2 — bulk-status-endpoint `PUT /api/cases/bulk/status`.** Frontend riep een niet-bestaand
endpoint aan (altijd 404 → "Statuswijziging mislukt"). Nieuw endpoint loopt per zaak via
`update_case_status` (guards intact: €0 voor 'betaald', derdengelden voor 'afsluiten'), slaat
geweigerde zaken over met reden: `{updated, skipped, errors}`, auth verplicht. Tests: happy/
guard-skip/tenant-isolatie. Live: 401 zonder token, {0,0,[]} met token.

**Taak 3 — dode workflow-status-engine gesloopt.** −2.492 regels: CRUD-routes, engine-service,
`on_status_change`/auto-mail-hook, modellen, schemas, frontend-beheer + `NEXT_STATUSES`/
`PIPELINE_STEPS`. Blijft levend: taken, agenda, verjaring. Fasebalk in dossierkop las uit de
lege `workflow_statuses` (blanco) → nu fase uit `step_category` van de actuele pijplijnstap;
geen stap → geen balk. Guarded migratie `s199_cleanup_workflow_engine` dropt 3 tabellen
(weigert bij data). **Prod:** 0/0/0 vóór drop → 3 tabellen weg, `workflow_tasks` (4) intact.

**Taak 4 — rapportages eerlijk.** "Geïnd" = som betalingen met `payment_date` in de gekozen
periode (maandenparam door router→hook→pagina); definitie in comment. Faseverdeling: outer join
+ "Geen stap"-rij → telling sluit. Live: **Geïnd €135.354,77** (was €0); faseverdeling
10+2+5+1+10 = 28 = KPI-som = dashboard.

**Taak 5 (code-deel) — kleine vegen.** Urenfilter toont alleen cliënten (uit dossiers, was alle
1.169 relaties); uren/facturen-widgets nette lege staat; label "nieuw"→"toegevoegd deze maand".

### Verificatie
Eigen proof (niet Sols woord): **1218 passed** (18m49s), `uvx ruff check` schoon, `tsc --noEmit`
+ `npm run build` groen. Migratie zelf gedraaid (lokaal + prod). Deploy geslaagd: alle containers
healthy, migratie = head. Live-checks via API als seidony@ (auth-guard, bulk, KPI's, faseverdeling,
dashboard) allemaal kloppend. Valkuil genoteerd: afgekapte `docker exec pytest` laat het proces
dóórlopen → twee reeksen botsten (vals-rood); voortaan detached ín de container draaien.

### Opruimronde + doorklik — UITGEVOERD (12 juli, mét Arsalans go; prod, elk read-only gemeten vóór mutatie)
- **A12 accountnaam** seidony@ "Lisanne Kesting" → "Arsalan Seidony" (live in UI bevestigd).
- **6 test-aanvragen** alle `pending_review` → `rejected` (0 over). **"AI Intake" → "Nieuwe aanvragen"**
  (kop+broodkruimel+terug-knop, commit `bce1bc7`, gedeployed).
- **2 verweesde verjaringstaken** (IN100015/IN100127, afgesloten+eigenaarloos) verwijderd.
- **Spookstappen:** 17 inactieve stappen + 14 dode transities weg (FK-check: 0 zaken/geschiedenis/
  followup verwezen); 15 actieve stappen + 15 transities intact.
- **Testdossier 2026-00001** hard verwijderd — **20 échte mails eerst ONTKOPPELD** (niet vernietigd);
  test-rommel mee weg. Werkvoorraad 28 → 27.
- **Bulk-status-knop live getest** (omkeerbaar): IN100345+IN100197 via UI naar 'in behandeling'
  ("2 dossiers bijgewerkt"), daarna exact terug naar 'nieuw' + testlogregels verwijderd — nul spoor.
  Dropdown toont enkel de 4 vaste statussen. Fasebalk data-geverifieerd (17 gevuld / 10 verborgen).
- Geen S199-restpunten meer open.

### Volgende sessie
S200 = "de voorkant liegt"-audit (`docs/sessions/PROMPT-S200.md`): 8 systematische vegen op de
zes fout-families + prod-logs + Lisanne-dag als sluitstuk. Read-only meten (Fable), fixes = S201.
Eerst de per-stuk-opruimacties hierboven met Arsalan afmaken.

> 📦 **Archief:** alles ouder dan de laatste 10 sessies staat in `docs/archief/SESSION-ARCHIVE.md` (verplaatst, nooit verwijderd).

## Sessie 198 (11 juli 2026, AUTONOOM Opus + Fable-review + Codex-review — bouwblok 3 klus 1-4 LIVE + reviewronde)

### Samenvatting
Autonome sessie (Arsalan weg): bouwblok 3 gebouwd, per klus gedeployd, daarna verplichte
Fable- + Codex-reviewronde met eigen bron-verificatie en fixes. Alles live op prod.

**Klus 1 — B3: status → 4 vaste waarden + pijplijn stuurt status + stap-filter (LIVE).**
Kernbevinding vooraf bevestigd: de oude `update_case_status` liep via `execute_transition` →
`get_status_by_slug` op de LEGE `workflow_statuses`-tabel → *élke* statuswijziging faalde al.
Nieuw model: status = `nieuw`/`in_behandeling`/`betaald`/`afgesloten`. `move_case_to_step`
stuurt de status (werk-stap → in_behandeling; terminale eindstap → betaald/afgesloten +
date_closed); dode `STEP_NAME_TO_STATUS`-koppeling vervangen. `on_payment_received`: bij €0
direct betaald+date_closed (geen dode validate_transition). `update_case_status`: 4-status-logica
(Afsluiten mét FIN-2-derdengelden-guard, Heropenen wist date_closed). Nieuw **stap-filter** op de
Dossiers-lijst (`incasso_step_id`). Statusfilter + bulk-dropdown → 4 vaste waarden (waren leeg via
de lege workflow-API). DossierHeader: Afsluiten/Heropenen i.p.v. kapotte "Volgende stap"-knoppen.
Migratie `s198_status_simplify` (idempotent, guarded). **Prod-migratie:** 580 afgesloten
onaangeraakt, 18 in_behandeling (op stap), 10 nieuw (zonder stap), 0 legacy-status. Stap-filter
live bewezen (Eerste sommatie 10, Voorstel dagvaarding 5, Bijhouden regeling 1 …).

**Klus 2 — A5: classificatielijn op pauze (LIVE).** `ai_agent`: geen `classification_done`-
meldingen meer (lijn op pauze; de 473 wachtende classificaties NIET aangeraakt). Meldingenbel
verbergt `classification_done` (niet-destructief). Dashboard "AI-suggesties"-widget ontkoppeld
van pending-classificaties → toont alleen follow-ups. **Bel viel van ~342 → 23 ongelezen.**

**Klus 3 — A3: Mijn Taken ontdubbeld (LIVE).** Ontwerpkeuze (autonoom): pure werklijst (optie b).
A1/A2 (eigenaarloze taken zichtbaar + intake pending_review) bleken al gefixt in eerdere sessies.
Zijbalk-badge `taken-combined` telde overdue+follow-up+intake bij elkaar op (dubbeltelling met
eigen badges) → nu exact de openstaande eigen taken (einde "badge 19 vs. Alles gedaan"). Follow-up-
en Intake-kaartblokken (1-op-1 kopie van hun eigen pagina's) vervangen door een compacte verwijs-strip.

**Klus 4 — A7: sjabloonbeheer alleen in Instellingen (LIVE).** HTML-Sjablonen-tab (lege DEPRECATED
tabel + ontwikkelaarstaal) weg; slug-titel `verzoekschrift_faillissement` → "Concept verzoekschrift
faillissement". Documentenbibliotheek bewust NIET gebouwd.

### Reviewronde (Fable-subagent + Codex ultra, beide op de volledige diff)
Elk punt zelf in bron + prod-data geverifieerd. **8 bevestigde fixes** (commit `3cba97d`):
1. **Verweer-mail heropende een BETAALDE zaak stil** (Fable#2/Codex#5, HOOG): guard in
   `trigger_defense_response_for_email`.
2. **€0-guard voor handmatig 'betaald' was weg** (Codex#2, HOOG): terug in `update_case_status`
   én `move_case_to_step` (manual/batch → 'Betaald'-stap).
3. **Auto-betaald rekende openstaand zonder BIK-override** (Codex#3, HOOG): gedeelde helper
   `get_case_outstanding` (mét alle zaakinstellingen).
4. **Teruggedraaide betaling liet zaak op 'betaald'** (Codex#4, HOOG): `update_payment`/
   `delete_payment` heropenen symmetrisch.
5. **email_received niet meer verbergen** (Codex#6, HOOG): dezelfde lijst voedt de dossier-
   actiefeed; alleen classification_done blijft verborgen.
6. `status_for_step` op `is_terminal` i.p.v. stapnaam (Fable#4/Codex#7).
7. Heropenen wist een terminale stap (Fable#3/Codex#8) — geen bord-limbo.
8. Sjabloon-fallback filtert op B2B/B2C (Codex#9) — geen 14-dagenbrief bij B2B.
Stale comments bijgewerkt. Nieuwe tests voor elk. **Prod-check:** 0 zaken op een terminale stap
→ migratie-bevinding (Fable#1/Codex#1) had 0 data-impact; going-forward-code dekt het af.

### Voorstellen (bewust NIET gebouwd — scope)
- **'betaald' telt in dashboard/rapportages nog als actief** (filter `!= afgesloten`; nu betaald een
  frequente auto-eindstatus is → gebruik de nieuwe `TERMINAL_STATUSES`-constante). Fable#5/Codex.
- **Dode code opruimen:** `on_status_change` (0 callers), `execute_transition`/`validate_transition`
  (alleen tests), frontend `NEXT_STATUSES`/`PIPELINE_STEPS`, ongebruikte `TERMINAL_STATUSES`.
- **`/api/cases/bulk/status` bestaat niet** (frontend `zaken/page.tsx` → 404, pre-existing).
- Fase-stepper in DossierHeader leunt nog op de lege `workflow_statuses` (toont blanco).

### Gewijzigde/aangemaakte bestanden
- Backend: `cases/{schemas,models,service,router}.py`, `incasso/service.py` +
  `incasso/automation_service.py`, `workflow/hooks.py`, `collections/service.py`,
  `notifications/service.py`, `ai_agent/service.py`, migratie `s198_status_simplify.py`.
- Frontend: `lib/status-constants.ts`, `hooks/use-cases.ts`, `hooks/use-documents.ts`,
  `zaken/page.tsx` + `zaken/[id]/components/DossierHeader.tsx`, `taken/page.tsx`,
  `components/layout/app-sidebar.tsx`, `(dashboard)/page.tsx`, `documenten/page.tsx`.
- Tests: test_cases, test_integration_api, test_s166_pipeline_status_sync, test_incasso_pipeline,
  test_workflow, test_notifications_service (nieuw + aangepast).
- 5 commits (`b6b2a4a` klus1 / `cc4ccab` klus2 / `738ac0d` klus3 / `207e906` klus4 / `3cba97d`
  reviewfixes) + docs. Prod-migratie s198 gedraaid. Tag `sessie-198`.

### Bekende issues / aandachtspunten
- Mail blijft UIT (niet geraakt). De 473 wachtende classificaties + testdossier 2026-00001
  bewust blijven staan (veegsessie mét akkoord).
- CI-rood `test_role_survives_commit_if_role_exists` (omgevingsgevoelig, S184) → uitrol via SSH.

### Verlengstuk (12 juli, na terugkomst Arsalan) — PowerSearch + Documenten-opruiming LIVE (eerste /codex-build)
**Onderzoek eerst (Fable):** concurrenten hebben géén centrale documenten-bladerpagina behalve Clio;
BaseNet (Lisanne's referentie) lost het op met centraal ZOEKEN op inhoud (PowerSearch). Luxis had al
een globale zoek, maar alleen op namen/onderwerpen. Besluit Arsalan: Documenten-pagina helemaal weg
(sjabloonbeheer zit al in Instellingen) + PowerSearch bouwen.
**Werkvorm (nieuw, eerste rit):** Fable schreef de bevroren spec (`docs/plans/PLAN-powersearch.md`),
**Sol (Codex gpt-5.6-sol, xhigh)** bouwde 'm end-to-end (commit `bc194ae`), Fable reviewde de
volledige diff + draaide alle bewijzen zelf. **Geleverd:** migratie s199 (NL-tsvector-kolommen +
GIN op mails/dossierstukken), extractie (PDF via pymupdf/HTML/tekst) + upload-hook + idempotente
backfill, hybride zoek (substring op nummers/namen blijft; inhoud met NL-stemming, ts_rank-relevantie,
ts_headline-snippets; alles gebonden parameters + tenant-gefilterd), Documenten-pagina/nav/e2e weg.
**Reviewbevindingen:** 1 spec-afwijking terecht (regconfig-cast); 1 prod-bug door Fable gevonden bij
de backfill: PDF-tekstlagen met NUL-bytes (0x00) klapten op PostgreSQL → fix `054d0b9` + regressietest.
**Regelbreuk vastgelegd:** Sol committe+pushte zelf (volgde repo-regel "commit+push na elke taak");
auto-deploy door Fable gecanceld vóór review; volgende contracten krijgen expliciet commit-verbod.
**Live bewezen (prod):** backfill 1.951/2.055 stukken met tekst (104 = scans, OCR bewust later);
zoek op "betalingsregeling" vindt factuur-PDF op inhoud mét snippet; "verjaring" vindt mail-body's.
**Besluit Arsalan (definitief):** 12 onverklaarde bankontvangsten (±€21,7k Donker/Dinc) VERVALLEN —
niet bij de 7 vaste opdrachtgevers → geen incasso, nooit boeken.
**S199-plan klaar:** `docs/sessions/PROMPT-S199.md` (veegsessie + S198-review-voorstellen).

### Volgende sessie
S199 = veegsessie (stapel 4) + de review-voorstellen hierboven (m.n. 'betaald'-als-actief in
dashboard/rapportages + dode code). Prompt: `docs/sessions/PROMPT-S199.md`.

## Sessie 197 (11 juli 2026, Opus+Fable — Codex-hang opgelost + S196-review + mailslot-knop; bouwblok 3 NIET gedaan)

### Samenvatting
Sessie liep anders dan PROMPT-S197 (bouwblok 3): Arsalan wilde eerst de Codex-hang oplossen +
een review van S196 vóór verder bouwen, en een mailslot-knop erbij. Bouwblok 3 verschuift daardoor
volledig naar S198 (autonoom).

**1 — Codex-hang opgelost (kernbevinding).** Twee sessies (S194/S196) timede Codex "na 10 min" uit.
Oorzaak was NIET Codex/ultra maar een botte 10-min-grens: (a) de skill-guard van 600s + (b) de max
foreground-timeout van de Bash-tool. Bewijs gemeten: een triviale `codex exec` antwoordt in 9,5s
(→ opstart/MCP is níét de blokkade), en een échte S196-review op ultra duurde **21 min** en rondde
gewoon af toen hij op de ACHTERGROND liep. Codex heeft zelf al een 5-min stream-retry
(openai/codex#23807). Oplossing: `scripts/codex-review.sh` — draait de review op de achtergrond
zónder tijdslimiet en bewaakt de HARTSLAG (output-mtime): 6 min écht stil = als vastgelopen stoppen
+ melden, anders onbeperkt nadenken. **Ultra blijft** (Arsalans keuze; ultra vond 4 punten waar
"hoog" er 3 vond).

**2 — S196-review + 4 fixes LIVE.** Codex-review (ultra) van commit `42c3e4c` (termijn-vooruitblik).
Geld/beveiliging/tenant-scoping in orde; 4 robuustheidspunten zelf geverifieerd + gefixt (commit
`f2b526b`): (1) laadfout verborg het hele dashboard-blok stil → nu foutmelding; (2) regeling-acties
(aanmaken/betaling/wanprestatie/annuleren/kwijtschelden) verversten `["dashboard"]` niet → nu wel
(anders tot 30s verouderd); (3) footer "+N meer in de komende 30 dagen" kon liegen → "+N meer";
(4) query laadde volledige Case/Contact-entiteiten (selectin-fan-out) → scalar-kolomprojectie.
23 termijn-tests groen.

**3 — Mailslot-knop LIVE + env-noodslot eraf (op expliciet verzoek Arsalan).** Het bouwfase-mailslot
zat als env-var (`OUTBOUND_MAIL_LOCK`, alleen via SSH+herstart). Nu als DB-vlag in nieuwe globale
`app_config`-tabel (geen tenant_id → geen RLS, zoals interest_rates), schakelbaar via Instellingen →
E-mail. Eén chokepoint blijft: `check_outbound_lock()` leest env OF DB-vlag; de 3 verzendwegen
ongewijzigd. **Fail-safe:** `load_mail_lock` gaat bij ontbrekende rij/DB-fout op slot; geseede rij op
DICHT; stand in geheugen geladen vóór requests (single-proces backend). Env-noodslot op prod op
`false` gezet (`.env.bak-s197` als backup) → **de knop is nu de enige controle en staat op UIT**;
Arsalan zet mail zelf aan wanneer nodig. Openen vraagt bevestiging. Live geverifieerd (screenshot:
"op slot", "Openen" actief, geen server-noodslot-melding). Commits `fc151ed` + `25ec657`.

### Klus 1 (bouwblok 3) — onderzoek gedaan + aanpak MET Arsalan afgestemd (nog niet gebouwd)
Gemeten op prod: status kent feitelijk 2 waarden (afgesloten 580, nieuw 28); `workflow_statuses/
transitions/rules` alle 0 → élke statuswijziging faalt ("Status bestaat niet"), "Volgende stap"-
knoppen kapot, statusfilter leeg, auto-"betaald" vuurt nooit, `date_closed` nooit gezet, de
pijplijn→status-koppeling (S166) checkt het lege systeem en vuurt dus nooit. Pijplijn = de echte
motor (15 actieve stappen, 18 zaken erop, 10 heropende zonder stap). **Afgestemde aanpak:** status
reduceren tot 4 (Nieuw / In behandeling / Betaald / Afgesloten), pijplijn stuurt de status (bestaande
dode koppeling repareren, niet iets nieuws), auto-"betaald" + `date_closed` (met bestaande €0-guard),
Afsluiten/Heropenen-acties i.p.v. kapotte knoppen, statusfilter = 4 waarden, **+ nieuw "Stap"-filter
op de Dossiers-lijst** (Arsalans punt: kunnen filteren op sommatie/dagvaarding/vonnis — dat is de
pijplijn-stap, niet status). Lege status-engine NIET slopen (veegsessie-voorstel).

### Gewijzigde/aangemaakte bestanden
- Backend: `app/settings/models.py` (nieuw, AppConfig), `alembic/versions/s197_mail_lock.py` (nieuw),
  `app/email/service.py` (DB-vlag + fail-safe), `app/main.py` (load bij opstart),
  `app/settings/router.py` + `schemas.py` (GET/PUT mail-lock), `app/collections/service.py`
  (scalar-projectie), `tests/test_mail_lock.py` + `conftest.py`.
- Frontend: `instellingen/email-tab.tsx` (mailslot-kaart), `hooks/use-settings.ts` (mail-lock hooks),
  `(dashboard)/page.tsx` (foutstaat + footer), `hooks/use-collections.ts` (dashboard-invalidatie).
- Tooling: `scripts/codex-review.sh` (hartslag-bewaker).
- Prod: migratie s197 gedraaid (app_config geseed dicht), `.env` OUTBOUND_MAIL_LOCK=false
  (`.env.bak-s197` backup). 4 commits (`fc151ed`/`9a61399`/`f2b526b`/`25ec657`) + docs, tag sessie-197.

### Bekende issues / aandachtspunten
- Mail staat UIT via de knop; env-noodslot is eraf. Enige controle = de DB-vlag (fail-safe dicht).
- Bouwblok 3 volledig open → S198 autonoom.

### Volgende sessie
S198 = AUTONOOM (Arsalan is weg): op Opus klus 1-4 van bouwblok 3 bouwen + deployen, dan Fable-review
(subagent) + Codex code-review via `scripts/codex-review.sh`, findings verwerken. Prompt:
`docs/sessions/PROMPT-S198.md`.

## Sessie 196 (11 juli 2026, Opus — bouwblok 2 afgerond: termijn-vooruitblik + 3 proefzaken)

### Samenvatting
Sessie begon met een correctie: `PROMPT-S196.md` was geschreven vóór de C1-uitvoering op de
S195-avond en droeg de bankimport nog als open taak — Arsalan kreeg daardoor voor de derde
keer dezelfde beslisvragen. Stand gecheckt (SESSION-NOTES + Fable-hercontrole): **C1 was al
af**. Prompt kreeg een achterhaald-banner; alleen taak 2 + 3 uitgevoerd.

**Taak 2 — B4/A8 termijn-vooruitblik (LIVE, commit `42c3e4c`).** Dashboardblok "Aankomende
termijnen" in de incasso-kolom: open termijnen van actieve regelingen over álle zaken
(pending binnen 30 dagen; overdue/partial altijd, rood/geel gemarkeerd), gesorteerd op
vervaldatum, max 8 + "+N meer"-voet, klik → Betalingen-tab van het dossier. Backend:
`list_upcoming_installments` (collections-service, tenant-gefilterd, zelfde
geen-zaakstatus-filter-keuze als het regeling-alarm) + `GET /api/dashboard/upcoming-installments`
(auth). Bewust geen aparte pagina (besluit S191: alleen overzicht; 13 regelingen).

**Taak 3 — B11 proefzaken op hun stap (per zaak akkoord Arsalan).** Conform draaiboek
PLAN-heropening-werkvoorraad regel 118-120, alleen `incasso_step_id`+`step_entered_at`
gezet (guarded SQL, transactie): IN100215 → Bijhouden regeling (actieve regeling, termijn
12 juli deels betaald), IN100040 → Voorstel dagvaarding (BaseNet "Procederen?"), IN100521 →
Voorstel dagvaarding (4e sommatie). email_logs 0 vóór==ná; status bleef 'nieuw'.
Kanttekening genoteerd: draaiboek noemt IN100521 B2C, systeem zegt b2b — maakt voor de stap
niet uit, wél later voor rente/14-dagenbrief.

### Verificatie
- 23 tests groen (`test_payment_arrangements.py`, incl. 2 nieuwe: overview + tenant-isolatie);
  ruff schoon; `tsc --noEmit` + `npm run build` groen.
- Deploy backend+frontend via SSH, containers healthy.
- Live: endpoint geeft 14 termijnen die exact matchen met eerdere sessies (IN100019 gemist
  9 juli bovenaan; IN100215 partial €250 — de S195-Fable-fix zichtbaar); Playwright-doorklik
  dashboard → IN100019 Betalingen-tab: zelfde termijn "Achterstallig". Proefzaken via app-API
  bevestigd op de juiste stap.
- **Codex-tegenlezer overgeslagen:** timede na 10 min uit (S194: zelfde). Werkvorm herzien
  vóór volgende bouwsessie; diff was klein + testgedekt.

### Gewijzigde bestanden
- `backend/app/collections/service.py` (+`list_upcoming_installments`),
  `backend/app/dashboard/router.py` + `schemas.py`, `backend/tests/test_payment_arrangements.py`
- `frontend/src/app/(dashboard)/page.tsx` (widget), `docs/sessions/PROMPT-S196.md` (banner)
- prod-DB: 3 rijen `cases` (stap gezet). Commit `42c3e4c` + docs-commit, tag `sessie-196`.

### Bekende issues
- Codex-tegenlezer 2× op rij onbruikbaar (timeout) — beslissen: andere aanroepvorm of
  voorlopig uit het sessieprotocol.
- IN100521 debtor_type b2b vs draaiboek "B2C" — checken vóór er brieven/rente uitgaan.

### Volgende sessie
Bouwblok 3: B3-versimpeling (status volgt pijplijn) + A5-pauze + A3 dagstart + A7 sjablonen.
Prompt: `docs/sessions/PROMPT-S197.md`.

## Sessie 195 (11 juli 2026, Opus — grondige 1-op-1 betalingsaudit + heropenings-notities live)

### Samenvatting
Geen bouwsessie — controle op verzoek Arsalan: "is alles één-op-één overgezet, bij het juiste
dossier, kloppend met bron en bankrekening?" Alle betalingen + regelingen onafhankelijk
herberekend met de echte parser (`scripts/basenet/parse.py` + `mapping.py`) tegen de
BaseNet-export (`Xml_02-07-2026_2400.zip`) én het bankafschrift, alleen-lezen. Eén materiële
bevinding → op verzoek waarschuwingsnotities op de betrokken dossiers gezet.

### Wat gecontroleerd + resultaat
- **56 losse betaal-records (IncassoBetalingAnders):** alle 56 in Luxis, juiste dossier, juiste
  datum, 0 dubbel, 0 ontbrekend. **199 bankregel-betalingen (CashBankLine, S180):** idem, koppeling
  via `cblpcode` klopt. Totaal 255 betalingen ✅.
- **Bedragen:** 191 op de cent; **64 bewust gecapt** — Luxis rekent rente vanaf verzuimdatum → iets
  lager openstaand dan BaseNet → import capte op openstaand (S179: 17×, S180: 47×; deze audit
  reproduceert exact diezelfde aantallen onafhankelijk). Samen €6.198,46 lager geboekt dan werkelijk
  betaald. **Heropeningsrisico:** heropenen + herrekenen zonder correctie doet debiteur te weinig
  lijken te hebben betaald.
- **13 regelingen / 121 termijnen:** exact — juiste zaak, vervaldatum, bedrag; niets mist/dubbel.
  Bron heeft 323 termijnen/37 zaken; bewust alleen 121 toekomstige (vanaf 9 juli 2026) over 13 zaken
  (S179-afspraak: verleden-termijnen niet, want bron zegt niet of ze betaald zijn). Geen zaak met
  toekomstige termijnen ontbreekt.
- **Bankafschrift-kruiscontrole:** 138 credits exact geboekt; alle 57 venster-boekingen zonder exacte
  credit verklaard (gecapt óf "rechtstreeks aan cliënt" — nooit via derdengeldenrekening).
- **Correctie op de eerdere S195-indeling:** groepen B/C (36 rijen ~€48k) waren GEEN gaten — 34/36 zijn
  gewoon geboekt op het gecapte bedrag; datum+bedrag-match zag ze onterecht als "nooit geboekt". Echt
  onboekt uit B+C: alleen Saltik IN100345 (2×€50, plus 2×€50 in groep A).

### Actie op prod (op expliciet verzoek Arsalan)
- **64 dossier-notities** (`case_activities` type `note`) geschreven, één per gecapte zaak, met de exacte
  bron- vs geboekt-bedragen en de instructie "corrigeer betaalbedrag vóór herrekenen bij heropening".
  Idempotent (`[S195-audit]`-marker → NOT EXISTS-guard). Geverifieerd: 64 notities op 64 zaken, en via
  de app-API zichtbaar bovenaan de recente activiteiten van het dossier.

### Verjaringstaken IN100015/IN100127 — NIET afgevinkt
Voorwaarde Arsalan: alleen als ook in BaseNet gesloten. Bron-status was **Lopend** → taken blijven staan
(kandidaten voor heropeningsbatch).

### Gewijzigde/aangemaakte bestanden
- `docs/sessions/S195-1op1-audit.md` (nieuw — volledige bevindingen + 64-rijen gecapte-lijst)
- `docs/sessions/S195-bankimport-indeling.md` (nieuw — complete indeling 212 credits + correctie-banner)
- prod-DB: 64 rijen `case_activities` (notities). Géén code-wijziging, géén deploy.

### Bekende issues / open
- Gecapte betalingen: notitie is een handmatig vangnet. **Voorstel (niet gebouwd):** automatisch slot/
  waarschuwing bij heropening van een zaak met `[S195-audit]`-notitie.
- Kantoorrekening `NL79KNAB0606569456`: Arsalan bevestigde "ja"; stond al goed in systeem.

### C1 bankimport UITGEVOERD (zelfde sessie, ná de audit — op akkoord Arsalan)
Lisanne's werkwijze verklaarde de gaten: zij verwerkt betalingen maandelijks in BaseNet en
stort maandelijks door aan cliënten; de export (2 juli) loopt dus 1 maand achter — juli-
betalingen van debiteuren stonden nog niet in BaseNet, vandaar niet in Luxis.
- **Reconciliatie (gecorrigeerd, na eigen telfout gevonden):** van 212 afschrift-credits →
  138 exact geboekt, 39 gecapt-geboekt, **35 echt niet geboekt**. Die 35: 17 op zaken die in
  BaseNet nog Lopend waren (maar in Luxis dicht), 16 op partijen zónder Luxis-dossier, 1 al
  voldaan, 1 BaseNet-"Gereed".
- **Geboekt:** `scripts/s195_reopen_book.py --execute` → **17 betalingen (€14.922,60)** op de
  Lopend-zaken, als gewone betaling (art. 6:44, workflow-hook UIT, cap op openstaand, marker
  `[S195-heropen …]`), consistent met de 255 bestaande. **10 zaken heropend** (status afgesloten
  →nieuw) waar restant openstond; 3 die de betaling volledig afbetaalt bleven dicht; IN100547
  (al voldaan) + IN100097 (BaseNet "Gereed") overgeslagen. Saltik IN100345: 4×€50, rente-knip
  chronologisch correct.
- **Geverifieerd:** DB (17 betalingen, 18→28 open zaken) + app-API (betaling zichtbaar op
  IN100002/IN100215/IN100345). `--cleanup` beschikbaar als terugrol.
- **Bewust NIET geboekt (besluit Arsalan):** onbekende betalingen — na Fable-hercontrole
  gecorrigeerd naar **12 rijen, €21.738,96** (Donker €17.500 = "Grave/Donker", Dinc 6×€300+€100,
  Königel €1.708, Makkinga €116, Van der Hem €500); 8 eerder-als-onbekend-getelde bleken de
  bankkant van gecapte boekingen.

### Fable-hercontrole van de Opus-uitvoering (zelfde avond, op verzoek Arsalan)
Verse reconciliatie na het boeken: 138 exact + 14 S195-vol + 48 gecapt (incl. 3 van vanavond)
+ 12 onverklaard = 212 ✓. Geen dubbele boekingen (maandreeksen sluiten aan). **2 fixes:**
(1) IN100215's €250 gekoppeld aan regeling-termijn 12-07 als deelbetaling (anders vals
regeling-alarm); (2) de 3 nieuwe gecapte zaken (IN100480/532/585) kregen dezelfde
heropen-notitie als de 64 → totaal 67. Cap-verschil droogloop-vs-boeking verklaard
(openstaand per betaaldag, juridisch juist). Details: `S195-1op1-audit.md` §Fable-hercontrole.

### Volgende sessie
Bouwblok 2 restant: B4/A8 termijn-vooruitblik, B11 3 proefzaken. Prompt: `PROMPT-S196.md`.
