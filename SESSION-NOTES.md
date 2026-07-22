# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 22 juli 2026 (S236 — werklijst = Taken-pagina + 7 eerste sommaties verstuurd + spook-inkomend-fix, LIVE).
**Laatste feature/fix:** Verstuur-adviezen krijgen een gespiegelde taak op de Taken-pagina (keuze Arsalan); de 7 import-dossiers kregen hun eerste sommatie (alle 7 sent, doorgeschoven; IN100606 betwistte binnen 25 min → verweer-keten werkte); mails namens incasso@ komen nooit meer als "inkomende post" terug. Detail: entry S236.
**Openstaand (→ S237 e.v.):** verweer IN100606 (concept klaar voor Lisanne); reacties op de overige 6 sommaties verwerken; IN100613 wacht op Lisanne; IN100607 heeft stale eerste-sommatie-advies terwijl hij op 'Verweer beantwoorden' staat; voorstel escalatie-adviezen óók als taak. Losse punten: BaseNet-delisting, derde AI-testronde + Lisanne-steekproef, kostenblokje, fysieke-telefoon-check, opmaak-restpunt S227, S221b-rest, DMARC, testdata opruimen, 4 cosmetische restjes S235.
**Volgende sessie:** S237 — zie `docs/sessions/PROMPT-S237.md`.

## Sessie 236 (22 juli 2026, Opus-bouw → Fable-review → Opus-fixes — werklijst-taken + 7 sommaties verstuurd + spook-inkomend-fix, LIVE)

### Samenvatting
Startpunt PROMPT-S236. Besluiten Arsalan vooraf: IN100613 laten liggen (Lisanne nog
niet geantwoord); **Taken-pagina = dé werklijst**; de 7 sommaties mochten na eigen
grondige controle de deur uit ("als jij het hebt nagekeken mag je het doen").

**1. Werklijst-taak voor verstuur-adviezen (LIVE + live bewezen).** Elk openstaand
verstuur-advies van de follow-up-adviseur krijgt een gespiegelde taak
"{stap} versturen — {zaaknummer}" op de Taken-pagina (scanner-backfill dekt ook oude
adviezen; ontdubbeld per advies via rec_id in action_config). De taak sluit op exact
de advies-momenten: brief écht verstuurd → completed op de gedeelde doorschuif-motor
`advance_after_step_send` (dus álle verzendroutes); advies afgewezen/superseded →
skipped (`close_followup_send_tasks` in `supersede_open_recommendations` +
`reject_recommendation`). Taken-pagina kreeg knop "Controleren & versturen" → /followup
(niet visueel doorgeklikt; tsc schoon). Live bewezen: na de 30-min-scan stonden exact
de 4 juiste taken op prod.

**2. De 7 eerste sommaties (IN100592/98/99, 602/03/04/06) — VERSTUURD.** Controle
per dossier vóór verzending: 0 mails/documenten/staphistorie ooit (vers gemeten);
hoofdsom = som losse vorderingen (7/7 exact, incl. creditnota's −1.200,01 en −621,53
netjes in de brieftabel); **BIK onafhankelijk nagerekend volgens de wettelijke
staffel: 7/7 op de cent**; rente-steekproef IN100604 met de hand (2%/mnd samengesteld):
257,40 vs 257,38 in de brief (deelmaand-conventie); alle 7 b2b → geen
14-dagenbrief-plicht; afzender incasso@ via Graph. Alle 7 sent (0 bounces), elk
dossier → Tweede sommatie, adviezen executed. **IN100603 draagt een negatieve
renteregel (−107,90; creditnota ouder dan facturen — S181-F-gedrag, voordeel
debiteur).** **IN100606 (Maatwerk Zorgbemiddeling) betwistte binnen 25 min**: AI
classificeerde betwisting (0.95), dossier auto → 'Verweer beantwoorden', AI-concept
klaar — de hele verweer-keten live bewezen op een échte debiteur. **IN100607 bewust
NIET verstuurd**: bleek op 'Verweer beantwoorden' te staan (stale eerste-sommatie-
advies van vóór de stap-wissel).

**3. Fable-review-vondst: spook-inkomend (gefixt, LIVE).** Elke mail namens
kantooradres incasso@ ('Verzenden als' op seidony's account) kwam via de Verzonden
Items-sync als **inbound** terug: eigen sommaties als ontvangen post, mét notificatie
en AI-beoordelingscall (~$0,03 voor 7), patroon sinds 17-7 (verklaart de S233b-
"doorstuurregel gmail"-randobservatie). Rode test eerst; fix: eigen-afzender-set
(accountadres + Tenant.email) in richting-oordeel, ontdubbel-poort en
contact-matching (`sync_service.py`, 3 wachters).

**4. Tweede reviewvondst op eigen werk (gefixt, LIVE).** Het taak-filter keek alleen
naar "stap heeft sjabloon" → 10 oude escalatie-adviezen (van vóór de S234-
briefkoppeling, testdossiers) kregen een misleidende "versturen"-taak. Nu ook
filteren op advies-type GENERATE_DOCUMENT (+wachter).

**5. Prod-opruiming (één transactie, tellingen exact):** 10 misleidende taken weg;
7 spookmails weg mét bijlage- en classificatierijen, hun echte Graph-ids overgezet
op de uitgaande records (= wat de gefixte poort gedaan zou hebben); 14 onterechte
"nieuwe e-mail"-meldingen weg. Echte reacties + meldingen onaangeraakt (nageteld).

### Gewijzigde bestanden
Backend: `ai_agent/followup_service.py` (taak-aanmaak + reject-koppeling),
`incasso/service.py` (`close_followup_send_tasks` + motor + supersede),
`email/sync_service.py` (eigen-afzender-set). Frontend: `taken/page.tsx` (knop).
Tests: `test_followup_send_tasks.py` (nieuw, 10), `test_email_sync.py` (+3).
Commits `e91037d`, `e18c2d2`, `1782310`; backend+frontend via SSH `--force-recreate`
(geen migratie).

### Verificatie
9+1 nieuwe werklijst-wachters groen; 201 kruispunt-tests (followup/advance/workflow/
arrangement) groen; mail-kruispunt 952 groen (15 errors = botsing met parallelle
eigen run, schoon herdraaid: 98/98); ruff + tsc schoon; CI groen op alle 3 commits
(29910413122 + 29911747328 conclusion=success via API nagetrokken; de Frontend
Dependency Audit-job faalt daarbinnen niet-blokkerend op 4 sharp/libvips-CVE's —
extern, zie Bekende issues); containers healthy, login-API 200 na beide deploys;
alle prod-mutaties met dry-run + natelling (10/7/7/7/7/14 exact).

### Bekende issues / bewust niet gedaan
- **Escalatie-adviezen (o.a. 5 échte 'Voorstel dagvaarding'-dossiers) staan NIET op
  de Taken-pagina** — buiten de gekozen scope (verstuur-adviezen). Voorstel voor
  Arsalan: ook die als taak spiegelen.
- **IN100607**: stale pending eerste-sommatie-advies terwijl de zaak op 'Verweer
  beantwoorden' staat — advies zou superseded moeten worden (data-fix, niet gedaan).
- Werklijst-taak is éénrichting: handmatig afvinken laat het advies op de
  Follow-up-pagina staan (bewuste keuze); taak-aanmaak schrijft geen
  dossier-activiteit (cosmetisch).
- Batch-generatie zónder verzending laat de verstuur-taak bewust open (er ging niets
  de deur uit) maar schuift de zaak wél door (bestaand S234-randgeval).
- IN100613 onaangeraakt (wacht op Lisanne); heeft ook nog een oud pending advies.
- **npm-audit-waarschuwing (niet-blokkerend):** `sharp` erft 4 libvips-CVE's
  (CVE-2026-33327/-33328/-35590/-35591, 3× high) — sharp updaten zodra er een
  gepatchte versie is.

### Volgende sessie
S237: reacties op de 7 sommaties verwerken (IN100606-verweer ligt bij Lisanne;
meer reacties verwacht) + de open beslispunten hierboven. Zie
`docs/sessions/PROMPT-S237.md`.

## Sessie 235 (22 juli 2026, Fable-review ontwerp+S234 → Opus-bouw → Fable-review + volledige live-test — betalingsregeling compleet, LIVE)

### Samenvatting
Startpunt PROMPT-S235. Vooraf twee Fable-reviews: (1) het S235-ontwerp tegen de bron
gehouden → 3 correcties (Gat B-meting te rooskleurig: regeling-mail deed automatisch
NIETS; Gat C zou letterlijk gebouwd altijd geweigerd worden door de hold-stap-blokkade in
`advance_guard_reason`; wanprestatie heeft twee routes + 2 NOT NULL-velden vergen een
keuze); (2) S234 nagereviewd → scanner-skip-motivatie klopte niet (zie gecorrigeerde
entry S234), beslispunt werklijst, budgetfix. Daarna Opus-bouw in 5 blokken, daarna
**alles end-to-end live getest op prod-testdossiers** (wens Arsalan: "volledig testen,
niet een deel") en per test exact teruggedraaid.

**Blok 1 — melding bij auto-afsluiten (besluit Arsalan 22-7, LIVE + live bewezen).**
Nieuw meldingstype `case_closed_invoice`: sluit een dossier automatisch na volledige
betaling, dan krijgen alle actieve gebruikers "Dossier {nr} volledig betaald en
afgesloten — wil je de cliënt factureren?" met doorklik naar de facturen-tab
(`notifications/service.py::create_case_closed_invoice_notification`, aangeroepen in
`workflow/hooks.py::on_payment_received`; frontend-type + tab-route). Live bewezen op
2026-00019: echte betaling €358,69 → zaak betaald + rente bevroren + concept discarded +
advies superseded + melding bij béíde gebruikers; doorklik landde op de facturen-tab.
Terugdraai-bijvangst: betaling verwijderen heropent de zaak automatisch (bestaand
vangnet `_reopen_case_if_no_longer_paid` — bevestigd werkend).

**Blok 2 — Gat A flexibel termijnschema (LIVE + live bewezen).** `ArrangementCreate`
accepteert `installments[{due_date,amount}]`; som moet exact het totaalbedrag zijn
(Decimal; 400 bij mismatch, wachter-getest), termijnen letterlijk overgenomen (gesorteerd
op datum), `installment_amount` = eerste termijn (NOT NULL, ontwerpkeuze), start/eind =
eerste/laatste termijn. UI (`BetalingsregelingSection`): schakelaar "Handmatig schema" →
rijen-editor (datum+bedrag) + lopende telling in centen; Aanmaken disabled tot de som
klopt; kaart toont "Flexibel schema" i.p.v. frequentie bij ongelijke bedragen. Live
bewezen op 2026-00007 (2×200+1000, expres ongesorteerd aangeleverd → exact goed).

**Blok 3 — Gat C pijplijnkoppeling (LIVE + live bewezen).** Nieuwe regeling →
`_move_case_to_regeling_step`: zaak naar hold-stap 'Bijhouden regeling' via
`move_case_to_step` (trigger_type "arrangement"); bewust NIET via `advance_guard_reason`
(blokkeert hold-doelen), wél gesloten/verweer-checks; stap ontbreekt → log + niets.
Wanprestatie → `_ensure_arrangement_defaulted_task` op het gedeelde punt van BEIDE
routes (`default_arrangement` + `update_arrangement`), gededuped; annuleren/afronden
geen taak. Live: 2026-00007 verhuisde Derde sommatie → Bijhouden regeling; wanprestatie
gaf direct de taak "Regeling verbroken — vervolg bepalen".

**Blok 4 — Gat B regeling-mail → taak (LIVE + live bewezen mét echte AI).** Nieuwe
orchestrator-handler `handle_email_classified_arrangement` op het classified-event:
categorie `betalingsregeling_verzoek` → `ensure_arrangement_request_task` ("Betalingsregeling
vastleggen — {zaak}", due vandaag) op het moment van herkennen — niet in de dode
goedkeur-wachtrij. Geen taak bij actieve regeling/gesloten zaak/open taak. Kruispunt: de
escalate-tak van `execute_classification` slaat zijn escalatie-taak over zolang de
gerichte taak open staat. Live: testmail "ik wil een betalingsregeling in drie termijnen"
op 2026-00006 → echte AI classificeerde `betalingsregeling_verzoek` (0.95) → taak stond
er direct; 0 nieuwe AI-concepten (verweer-route bleef terecht stil).

**Blok 5 — budgetfix (Fable-reviewpunt S234).** Sjabloon-skips in de dagelijkse AI-batch
worden nu vóór de budget-slice weggefilterd — een skip kost geen AI-oproep en verdringt
geen echte sjabloonloze gevallen meer (`workflow/scheduler.py`).

### Gewijzigde bestanden
Backend: `notifications/service.py`, `workflow/hooks.py`, `workflow/scheduler.py`,
`collections/{service,schemas}.py`, `ai_agent/{orchestrator,service}.py`. Frontend:
`use-notifications.ts`, `use-collections.ts`, `app-header.tsx`,
`BetalingsregelingSection.tsx`. Tests (16 nieuwe wachters):
`test_case_closed_notification.py` (2), `test_arrangement_pipeline.py` (6),
`test_arrangement_request_task.py` (5), `test_payment_arrangements.py` (+3).
Docs: S235-ONTWERP.md (3 correcties), S234-entry gecorrigeerd. Commits `53d52e5`
(ontwerp-review), `5f3dc67` (S234-correctie), `41497aa` (bouw). Backend+frontend
gedeployd via SSH `--force-recreate` (geen migratie — alles additief op bestaande tabellen).

### Verificatie
221 tests groen (brede -k-run installment/regeling/payment/followup/arrangement);
ruff + tsc schoon; CI groen op alle 3 commits (incl. GitHub-Deploy, geen race dit keer);
containers healthy; login+API 200. Live-testronde op prod-testdossiers (2026-00007/-00019/
-00006): alle vier ketens end-to-end bewezen, daarna per keten in één transactie
teruggedraaid en nageteld (staphistorie hersteld, betaling weg, zaak heropend,
meldingen/taken/testmail gewist). Enig blijvend spoor: 1 rij in `ai_usage` (de echte
classificatie-call, ~¢) — dat is juist het doel van die tabel.

### Bekende issues / bewust niet gedaan
- **4 cosmetische restjes** (Fable-review, geen fix nodig): (a) geannuleerd formulier
  onthoudt de handmatige rijen bij heropenen; (b) etiket "Flexibel schema" verschijnt
  alleen bij ongelijke bedragen; (c) som-mismatch-melding toont bedragen met punt
  (1400.00) i.p.v. NL-notatie; (d) status "nieuw" wordt "in_behandeling" bij regeling
  (gevolg van de stap-zet — correct maar goed om te weten).
- **IN100613** blijft wachten op Lisanne (niet aangeraakt).
- **Beslispunt werklijst** (taken- vs follow-up-pagina) ligt bij Arsalan/Lisanne.
- De 7 'Eerste sommatie'-import-dossiers hebben hun sommatie nog nooit gehad — de 7
  pending follow-up-adviezen zijn terecht en wachten op verwerking (GO per verzending).

### Volgende sessie
S236: verwerk het antwoord van Lisanne over IN100613 (dry-run + GO + natelling) en het
werklijst-beslispunt; daarna losse punten of nieuw hoofdonderwerp naar keuze Arsalan.
Zie `docs/sessions/PROMPT-S236.md`.

## Sessie 234 (21 juli 2026, Fable-onderzoek/ontwerp → Opus-bouw → Fable-review — incassostappen situatie-gestuurd afgemaakt, LIVE)

### Samenvatting
Startpunt PROMPT-S234. In de bron gemeten (fable-diepte): het stappen-model is onder
water al situatie-gestuurd (stilte → follow-up-advies + AI-concept; verweer → auto-switch;
betaling; regeling). Geen nieuw model nodig — de gaten gedicht. **Kernvondst tijdens de
plan-review: mijn eigen vraag-premisse klopte niet** — het systeem zet een dossier ál
automatisch op 'betaald' bij volledige betaling (`workflow/hooks.py::on_payment_received`);
Blok C-betaling daarom NIET gebouwd, als vraag voor Arsalan neergelegd.

**Blok A — één doorschuif-motor (LIVE).** `advance_after_step_send` is nu de enige motor
voor álle stap-brief-routes (compose/send + AI-concept gebruikten 'm al; batch + follow-up
gemigreerd). Nieuwe gedeelde guard `advance_guard_reason`: niet doorschuiven bij gesloten
zaak, openstaand verweer, terminale/hold-doelstap, of **consumentendossier → zakelijke stap**
(nieuw gat: na de derde sommatie zijn alle vervolgstappen b2b → een b2c-zaak zou richting
faillissement geduwd worden; nu gestopt + eenmalige "vervolg bepalen"-taak). Deze waarborgen
zaten eerder alléén in `_try_auto_advance` (verwijderd). `record_send`-vlag behoudt "batch-
generatie zónder verzending schuift door zonder email_sent te zetten".

**Blok B — derde + laatste sommatie een brief (LIVE, prod-mutatie).** Derde sommatie →
`wederom_sommatie_kort`, laatste → `sommatie_laatste_voor_fai` (bestaande BaseNet-renderers).
2 UPDATEs op prod (dry-run + natelling: beide stappen NULL → gezet; 11 geraakte dossiers zijn
testdata; sjablonen nergens anders in gebruik). Nu draagt het hele hoofdpad (6 stappen) een
brief → verzending schuift die stappen door (S232-mechaniek, geen codewijziging), doorschuif-
regels bestaan al. `STEP_TEMPLATE_FAMILIES` kreeg een eigen derde-familie.

**Blok D — stilte zonder AI-kosten (LIVE, wens Arsalan tijdens review).** De dagelijkse
AI-conceptbatch slaat nu elke match over waarvan de doelstap een sjabloon heeft → 0 AI-oproepen
voor stilte (was 21 op 21-7); verweer-concepten (mail-hook) + handmatige AI-knoppen blijven.
De follow-up-adviseur (elke 30 min, géén AI) is het seintje "tijd voor {volgende sommatie}" +
sjabloon-verzending. Scanner-skip op open staphistorie met email_sent toegevoegd (geen
her-advies van een via de app verstuurde brief). **CORRECTIE (Fable-review 22-7): de
motivatie voor die skip klopte niet** — voor de 7 'Eerste sommatie'-dossiers is in Luxis
nooit iets verstuurd (0 mail-logs/documenten/uitgaande mails) en ze hebben als
import-dossiers géén staphistorie, dus de skip raakt ze per definitie niet. "Brief 12
dagen weg" was vermoedelijk de ouderdom van het openstaande advies (aangemaakt 9-7). De
7 pending adviezen zijn TERECHT (bevestigd Arsalan 22-7: BaseNet doet geen incasso meer,
Luxis is de waarheid) en wachten op verwerking. De skip zelf is onschadelijk en blijft
(dekt toekomstige echte verstuurd-maar-niet-doorgeschoven-gevallen).
`evaluate_timeout_rules` filtert
gesloten/verweer/b2c→b2b — **IN100613** (afgesloten, maar op 'Tweede sommatie') kreeg daardoor
elke ochtend een nieuw sommatie-concept; die stroom is nu dicht (de zaak zelf onaangeraakt).

### Gewijzigde bestanden
Backend: `incasso/service.py` (guard + motor + families + seed + `_ensure_followup_decision_task`,
`_try_auto_advance` weg), `incasso/automation_service.py` (evaluator-guard),
`ai_agent/followup_service.py` (motor + scanner-skip), `workflow/scheduler.py` (batch-skip).
Tests: `test_advance_after_send_routes.py` (guard-matrix + b2c-taak + verweer), `test_followup.py`
(scanner-skip), `test_incasso_pipeline.py` (evaluator-skip; `_try_auto_advance`-tests weg).
1 commit (`bd81744`), backend gedeployd via SSH `--force-recreate` (geen migratie). Prod-DB:
2 UPDATEs op `incasso_pipeline_steps` (template_type).

### Verificatie
423 tests groen in de brede -k-run (1 test-isolatie-ERROR die geïsoleerd slaagt, raakt niet
mijn code); gerichte suites groen (incasso 55, follow-up+advance 61). Ruff `app/` schoon.
Backend healthy na deploy. Prod nageteld: hoofdpad = 6 stappen mét sjabloon (AI-batch-skip-set);
doorschuif-regels Derde→Laatste→Faillissement aanwezig. CI-afsluitcheck: zie kop.

### Bekende issues / bewust niet gedaan
- **Blok C betaling NIET gebouwd** — foute premisse: `on_payment_received` sluit al
  automatisch af bij €0 openstaand. Arsalans keuze "taak i.p.v. automatisch" = wijziging van
  bestaand gedrag → eerst bevestigen. **Vraag voor Arsalan.**
- **IN100613 onaangeraakt** — afgesloten (15-7) maar op stap 'Tweede sommatie'. Codefix stopt
  de dagelijkse concept-stroom; de zaak-data zelf raak ik niet aan. **Vraag voor Lisanne
  klaargezet** (wat is er gebeurd, mag 'ie naar 'Afgesloten').
- **Geen live-mailproef** — echt versturen is een naar-buiten-actie (GO per geval); Arsalan
  keek niet mee. Keten is unit+integratie-getest + op prod-data nageteld. Arsalan kan het op
  2026-00006 (zijn gmail) zelf natrekken.
- **Generate-only batch schuift nog steeds door zonder verzending** (bestaand gedrag, bewust
  behouden via `record_send=False`) — latente eigenaardigheid, buiten S234-scope.
- **Uit de Fable-review 22-7 (naast de scanner-correctie hierboven):** (a) doorschuiven
  maakt geen taak meer aan op de nieuwe stap (`_create_tasks_for_step` verdween uit de
  batch/follow-up-route; compose/AI hadden 'm sinds S232 al niet) — takenpagina leunt nu
  volledig op de follow-up-adviseur; **beslispunt voor Arsalan/Lisanne** welke pagina de
  werklijst is. (b) In de dagelijkse AI-batch tellen sjabloon-skips mee voor het
  50/dag-budget (randgeval, éénregel-fix, kan mee in S235). (c) De b2c-"vervolg
  bepalen"-taak wordt niet aangemaakt als de doelstap óók hold/terminaal is
  (guard-volgorde) — speelt met de huidige prod-stappen niet.

### Volgende sessie
S235: betalingsregeling herkennen uit mail (classificatie bestaat al) + flexibel termijnschema.
Eerst de 2 vragen hierboven met Arsalan/Lisanne afhandelen. Zie `docs/sessions/PROMPT-S235.md`.

## Sessie 233b (21 juli 2026, Fable-review → Opus-bouw → Fable-review — S233-review + vier mailfixes, LIVE)

### Samenvatting
Arsalan vroeg een volledige review van S233, inclusief het klikwerk dat die nacht was
overgeslagen ("dat kon je wel"). Klopte: alles bleek gewoon klikbaar.

**Review S233 (Fable, live op prod):** zijpaneel + non-modaal + bronmail onderin opnieuw
bevestigd; AI-generatie mét instructie "doe de facturen erbij" live gedaan (1 AI-call) →
`attach_invoices=true` op het concept, en de batch-draft van diezelfde ochtend bleef
`false` (kruispunt-guard in het echt bewezen). Bedragen kloppen: € 140,49 (16/7) →
€ 140,55 (21/7) = exact 5 dagen wettelijke rente op € 100.

**Vier fixes uit de review, alle gecommit + gedeployd + CI groen:**
1. `e37b815` — uitgaande mails kregen nooit een draad-kenmerk (alle 6 op het testdossier
   leeg) → het antwoord-paneel toonde eigen verstuurde mails nooit. Nu draagt elke
   verzending zijn draad-wortel (antwoord = References-wortel, verse mail = eigen id,
   zelfde regel als de inkomende-sync). Live: 0→2 uitgaande mails in de draad, paneel
   toont ze. Plus: waarschuwing in het compose-paneel als de behandelaar facturen vroeg
   maar het dossier geen factuur-PDF heeft (de AI-tekst beloofde een bijlage die er
   niet was). Wachters: `test_outbound_thread_id`.
2. `4166f30` — Fable-review-restpunten: "Je vroeg" → u-vorm; draad-paneel cap 50→200
   (drukste dossier ~83, oudere draadmails vielen stil weg). Plus correctie op de
   commit-tekst van e37b815: de "bonus" (auto-koppeling inkomend via draad) geldt alleen
   binnen één mail-account — in de echte opzet (IMAP in via 8a1f…, Outlook uit via
   226e…) verandert daar niets; het draad-paneel filtert niet op account en is het
   echte effect.
3. `1abae63` — LIVE-BUG (gevonden bij de verificatie): élk antwoord via de
   Outlook-route faalde met 400 — Graph's `/reply` kreeg het RFC Message-ID van een
   IMAP-gesyncte mail, maar eist het postvak-interne id. Rode test eerst, dan fix:
   RFC-id valt terug op gewone sendMail. Live: exact dezelfde call die 400 gaf → 200.
4. `a291692` — Fable-review op de fix zelf, gemeten in prod: de `<`-check was te smal
   (3099 BaseNet-import-mails dragen `basenet:…`-ids zonder `<` → vielen alsnog in de
   kapotte /reply-tak), én de /reply-tak kent geen bijlagen (zouden stil wegvallen).
   Nu positieve tekenset-keuring (`_looks_like_graph_id`) + met bijlagen altijd
   sendMail. Wachters: `test_outlook_reply_routing` (5).

### Gewijzigde bestanden
Backend: `email/send_service.py` (provider_thread_id op outbound SyncedEmail),
`email/compose_router.py` (draad-wortel doorgeven), `email/providers/outlook.py`
(reply-routing). Tests: `test_outbound_thread_id.py` (nieuw, 2),
`test_outlook_reply_routing.py` (nieuw, 5). Frontend: `email-compose-dialog.tsx`
(invoiceWarning + u-vorm), `mail-thread-panel.tsx` (cap 200).

### Verificatie
151 tests groen (send/advance/step/compose-subset) + 5+2 nieuwe wachters; ruff + tsc
schoon; 4 commits gedeployd via SSH `--force-recreate`, containers healthy; CI groen op
e37b815/4166f30/1abae63 (a291692 liep nog bij afsluiten — natrekken met `gh run list`).
Live-bewijzen op prod: draad 0→2, factuurwaarschuwing zichtbaar, reply-call 400→200.

### Bekende issues / bewust niet gedaan
- **Factuur-vinkje positief pad niet visueel getest** — testdossier 2026-00006 heeft
  geen factuur-PDF (echte dossiers als IN100487 wél, maar die zijn van echte
  debiteuren). Keten is backend-getest; wil je het zien, hang eenmalig een test-PDF
  aan een claim van 2026-00006.
- **Externe threading op onderwerp:** de sendMail-terugval zet geen In-Reply-To-header
  (Graph staat dat niet toe) — in de mailbox van de debiteur threadt het antwoord op
  "Re: onderwerp". Upgradepad: createReply-draft. Niet urgent.
- **Testsporen:** 2 testantwoorden naar Arsalans gmail op 2026-00006; 1 ongebruikt
  AI-concept (met factuur-vlag) op diezelfde mail. Randobservatie: het testantwoord
  dook óók als inkomend op in de M365-box (vermoedelijk doorstuurregel gmail) — 
  onschuldig, niet uitgezocht.

### Volgende sessie
S234: incassostappen kritisch herzien — situatie-stappen i.p.v. platte lijst; brief
koppelen aan derde/laatste sommatie; batch/follow-up op de gedeelde doorschuif-logica.
Zie `docs/sessions/PROMPT-S234.md`.

## Sessie 233 (21 juli 2026, Opus-bouw → Fable-review — AI-antwoord-zijpaneel + mailgeschiedenis + "facturen erbij", LIVE)

### Samenvatting
Autonome nachtsessie (Arsalan sliep, opdracht: "doe je ding, sluit af als vol").
Startpunt PROMPT-S233. Alles hieronder is live, getest en op prod nageteld.

**Taak 1 — AI-antwoord/compose is nu een zijpaneel (LIVE + live bewezen).** Het
compose-/reviewvenster was een gecentreerde bijna-schermvullende dialoog; bij een
AI-antwoord op de Mail-pagina werd je bovendien naar de dóssierpagina genavigeerd
(`router.push(?draft=)`) → de mail waarop je antwoordde was weg. Nu:
- Nieuwe `components/ui/sheet.tsx` — rechts-verankerd, NIET-modaal (geen
  verduisterende overlay, geen buiten-klik-sluiten) → links blijven de mails
  leesbaar én aanklikbaar tijdens het schrijven. `email-compose-dialog` rendert
  hierin (geldt meteen op alle drie de plekken: Mail-pagina, dossier-Correspondentie,
  documenten-tab). **Live bewezen op prod:** compose opent als rechterpaneel; een mail
  links aanklikken terwijl het paneel open staat opent diens detail en het paneel
  blijft staan.
- Nieuwe `components/mail-thread-panel.tsx` — onderin het paneel de mail waarop je
  antwoordt (uitklapbaar, standaard open) + de eerdere mailtjes van dezelfde draad
  (`provider_thread_id`), lazy per mail. Vergde `provider_thread_id` op de
  case-emails-summary (`sync_router`), anders bleef de draad-filter altijd leeg.
- Mail-pagina opent het concept nu IN-PLACE (`openAiDraft` → zijpaneel met de
  bronmail), verzendt via `compose/send` (`already_branded`, `skip_pipeline_advance`)
  + `advance-after-send` (markeert concept verzonden, sluit reviewtaak). Een antwoord
  schuift de pijplijn NOOIT door (P1 — advance-after-send weet dat via reply-intent).
  Dossierpagina + Correspondentie-tab geven de bronmail nu door aan `openDraftDialog`.

**Taak 2 — AI luistert naar "doe de facturen erbij" (LIVE).** Nieuwe kolom
`ai_drafts.attach_invoices` (migratie s233, additief, default false). De reply-prompt
laat de AI dit signaal zetten als de behandelaar-instructie erom vraagt; parsing zet
`draft.attach_invoices`. Nieuw endpoint `GET /email/compose/cases/{id}/invoice-files`
(factuur-CaseFiles route-onafhankelijk). Het concept opent dan met die PDF's al
aangevinkt (echte bijlagen; gebruiker kan weghalen). **Kruispunt-guard:** de vlag zit
op `intent == REPLY_TO_EMAIL`, niet op de AI → de dagelijkse auto-conceptbatch
(next_step, geen instructie) vlagt NOOIT facturen, ook niet als het model het per
ongeluk teruggeeft. Wachter-test dekt precies dit.

### Gewijzigde bestanden
Backend: `ai_agent/models.py` (attach_invoices), `unified_draft_service.py`
(prompt + parsing), `router.py` + `schemas.py` (response), `email/compose_router.py`
(invoice-files endpoint), `email/sync_router.py` (provider_thread_id op summary),
`alembic/versions/s233_ai_draft_attach_invoices.py`. Tests:
`test_unified_draft_service.py` (+4: reply zet/next_step nooit + prompt-wachter),
`test_invoice_files_endpoint.py` (nieuw). Frontend: `components/ui/sheet.tsx` (nieuw),
`components/mail-thread-panel.tsx` (nieuw), `email-compose-dialog.tsx` (Sheet +
geschiedenis + factuur-voorselectie), `correspondentie/page.tsx` (in-place),
`zaken/[id]/page.tsx` + `CorrespondentieTab.tsx` (bronmail doorgeven),
`hooks/use-email-sync.ts` (provider_thread_id-type). 1 commit (`d8da982`),
backend+frontend gedeployd via SSH met `--force-recreate`, migratie op prod gedraaid
(s230b → s233, kolom geverifieerd default false).

### Verificatie
- Backend: 45 tests groen (unified_draft_service 36 incl. 4 nieuwe wachters; drift-guard,
  email-sync, compose-attachments, invoice-files 9). Ruff schoon. Frontend tsc schoon.
- Migratie op prod toegepast; `attach_invoices boolean default false` bevestigd; alembic
  head = s233; alle 5 containers healthy.
- **Live op prod (Chrome-extensie):** compose = rechterpaneel, mails links zichtbaar;
  mail links aanklikken tijdens open paneel opent detail, paneel blijft → non-modaal
  bewezen. Ingelogd als Lisanne met kesting@kestinglegal.nl (S232-wijziging leeft).

### Bekende issues / bewust niet gedaan
- **AI-generatie → in-place paneel + draad + factuur-voorselectie NIET met browser
  doorgeklikt** — het aanklikken van een specifieke inbound-mail haperde door
  renderer-freezes in de automation, en een verse generatie kost een AI-call (bewust
  vermeden i.v.m. kostenpunt). De onderliggende logica is tsc-schoon + backend-getest;
  het riskantste stuk (zijpaneel-layout + non-modaal) is wél live bewezen. Arsalan kan
  dit met één klik op zijn telefoon natrekken op een inbound-mail van 2026-00006.
- **Playwright-MCP-profiel zat vast** (extern lock) → verificatie via de Chrome-extensie
  gedaan i.p.v. Playwright.
- "Open in Outlook" op een AI-concept op de Mail-pagina verzendt direct (onSend=sendAiDraft)
  i.p.v. een .eml te maken — randgeval, primaire knop is Versturen; niet gebruikt in de
  beschreven flow.

### Volgende sessie
S234: incassostappen kritisch herzien — situatie-stappen i.p.v. platte lijst; een brief
koppelen aan derde/laatste sommatie (dan schuiven die ook door); batch- en follow-up-route
op dezelfde "volgende stap"-logica als compose/send + AI-route trekken. Zie
`docs/sessions/PROMPT-S234.md`.

## Sessie 232 (20 juli 2026, Opus-bouw — sjabloon-doorschuiven + 3 demo-fixes, LIVE)

### Samenvatting
Kruispunt-sessie op de verzendroutes. Alles hieronder is live, getest en op prod nageteld.
Vóór de bouw met Fable de kruispunten in kaart gebracht (welke routes/pagina's raakt elke
wijziging), daarna met Opus gebouwd.

**Hoofdtaak — sjabloon-verzending schuift door (LIVE + wachter).** In de demo stuurde
Arsalan een eerste sommatie via het mailvenster met sjabloon; de mail ging weg maar het
dossier bleef op "Eerste sommatie". Alleen de AI-conceptroute (`advance-after-send`) schoof
door. Gemeten: er zijn vier routes die een stap-brief versturen (AI-concept, batch, follow-up,
compose/send) met twéé verschillende "volgende stap"-logica's. Voor nu compose/send op
dezelfde regel als de AI-route gezet, de andere twee met rust (die herzien we in S234).
- Gedeelde helper `advance_after_step_send()` (incasso/service.py) — de kern die
  `advance-after-send` al gebruikte: verzending vastleggen op de huidige stap + default
  timeout-rule + `move_case_to_step`. De router hergebruikt hem nu (dubbele code weg).
- Brief-families `STEP_TEMPLATE_FAMILIES`: alle sommatie-varianten tellen als "de brief van
  hun stap" → eerste én tweede sommatie schuiven door. **Match op de EXPLICIETE template_type**
  (niet de afgeleide): AI-drafts dragen geen sjabloon → schuiven alleen via advance-after-send
  → nooit dubbel. Extra guard `skip_pipeline_advance` dekt het randgeval (AI-concept waar de
  gebruiker alsnog een sjabloon koos). **Grens:** derde/laatste sommatie hebben in prod géén
  brief-koppeling → schuiven nog niet door (S234).
- Wachter `test_advance_after_send_routes.py`: hele poort-matrix (stap-brief→door;
  antwoord/vrij/herverzending/skip→niets) + gedrag van de helper. 13 tests.

**Witregel na "Geachte" teruggedraaid (LIVE).** De S227-extra lege regel ná de aanhef was
te veel — de opmaak was daarvóór al goed. Centraal in `_inline_paragraph_spacing`, dus overal
tegelijk (stapbrieven, AI-concepten, AI-antwoorden). De S226-alinea-marge (de echte Gmail-fix)
en de vaste witregel tussen Betreft en aanhef blijven. Wachters in `test_incasso_templates.py`
omgedraaid: slaan nu alarm als de extra regel terugkomt.

**Bijlagen: geen aantal-limiet meer (LIVE).** Wens Arsalan. De echte beperking is de totale
mailgrootte (de provider stopt alle bijlagen base64 in één request), niet het aantal. Aantal-cap
(10) weg op alle plekken; nieuwe totale-groottegrens `_assert_total_attachment_size` (25 MB),
route-onafhankelijk vóór verzending. Per-bijlage 3 MB blijft. Test omgezet naar totaal-grootte.

**Dossierfilters onthouden (LIVE).** De sortering stond al in de URL, de filters niet → na een
dossier openen + terug via het menu waren ze weg. Nu bewaard in localStorage (`zaken-filters-v1`);
een doorklik vanaf dashboard/rapportage (filters in de URL) wint en negeert het geheugen.

**Twee prod-datamutaties (na expliciete GO, nageteld).**
- Gebruikersnaam Lisanne `lisanne@kestinglegal.nl` → `kesting@kestinglegal.nl` (`UPDATE 1`).
  De mailkanalen hangen aan het account (user_id), niet aan dit veld → verzenden/ontvangen
  intact; wachtwoord-hash onaangeraakt. **Lisanne logt vanaf nu in met kesting@kestinglegal.nl.**
- IN100605 → "Tweede sommatie". Bewezen dat de eerste sommatie 20-7 2× de deur uit ging
  (`email_logs` status sent, sjabloon `sommatie_drukte`) terwijl het dossier bleef staan.
  Doorgezet via de nieuwe gedeelde helper (default advance-rule, staphistorie-spoor).

### Gewijzigde bestanden
Backend: `incasso/service.py` (families + `advance_after_step_send` + poort), `incasso/router.py`
(hergebruikt helper), `email/compose_router.py` (doorschuiven + totaal-groottegrens +
`skip_pipeline_advance`), `email/incasso_templates.py` (witregel terug). Tests:
`test_advance_after_send_routes.py` (nieuw), `test_compose_attachment_limits.py`,
`test_incasso_templates.py`. Frontend: `zaken/[id]/page.tsx` (doorschuif-toast + refresh +
skip-guard), `zaken/page.tsx` (filter-geheugen).

### Bewust niet gedaan / grenzen
- **Outlook-route (.eml) NIET wegdoen** — Arsalan: later. Doorschuiven zit alleen op de
  directe verzendknop (bij .eml weet Luxis niet of de mail echt weg is).
- **Derde/laatste sommatie schuiven nog niet door** — geen brief aan die stappen gekoppeld
  (data/ontwerpkeuze voor S234; de mechaniek dekt het dan zonder codewijziging).
- **Batch- en follow-up-route** houden hun eigen "volgende in de lijst"-logica — recht te
  trekken in de S234-stappensessie.

## Sessie 230/231 (20 juli 2026, Fable-onderzoek + Opus-bouw — werkorders V1-V4 + drie live storingen)

### Samenvatting
Begonnen als afwerksessie van de S229-eindkeuring; halverwege omgeslagen naar
storingsdienst tijdens Arsalans demo met Lisanne. Alles hieronder is live en
nageteld op prod.

**V1 — 27 consumentendossiers gecorrigeerd (€ 9.794,65).** Meting vers herhaald,
onafhankelijk van S229: hoofdsom per dossier opnieuw opgeteld uit de losse
vorderingen, eigen staffelberekening, plus kruiscontrole via de app-API
(`GET /api/cases/{id}/bik`) — 4/4 identiek. Arsalans twijfel ("waarom zag je dit
pas nu?") beantwoord met de import-datum: alle 27 kwamen op 3 juli binnen; de
S229-keuring was de eerste brede financiële controle ná die import. **Nieuw t.o.v.
S229:** de 26 "afgesloten" dossiers bleken géén afgehandelde zaken — in BaseNet
stonden ze 21× Lopend / 3× Wacht / 2× Gereed / 1× Geannuleerd, 0 van de 27 volledig
betaald, 25 zonder één cent betaling, samen € 172.692,60 hoofdsom open, 16 met
mailverkeer in 2026. Daarmee verviel het bezwaar tegen corrigeren. Na GO van
Arsalan (alle 27 bevestigd particulier): `bik_override` → NULL in één transactie,
gejoind op id én exact oud bedrag (`UPDATE 27`), oude waarden dubbel bewaard
(`_s230_bik_backup` + lokale kopie). Natelling: sweep 0, IN100082 nu € 1.102,21,
IN100345 € 385,30; doorwerking bewezen op IN100009 (openstaand zakte exact de
€ 66,96 te veel geheven kosten). **Wachter:** `find_bik_above_staffel()` loopt de
hele DB af (dagelijks 06:45 UTC) — de twee bestaande wachters keken alleen naar het
moment van handelen, de import kwam daar buitenom. 7 tests.

**V2 — handelsrente 1-7-2026 (10,40%).** Op verzoek eerst bewezen dát het ontbrak:
prod-tabel eindigde bij 10,15% (1-7-2025), alle 150 rijen aangemaakt op 18-02-2026
en nooit gewijzigd (de BaseNet-import raakt deze tabel niet — de importcode schrijft
alleen een contractueel percentage op de zaak). Twee onafhankelijke bronnen:
Rijksoverheid ("sinds 1 juli 2026 10,4%") + rekenregel art. 6:119a lid 2 (ECB-refi
2,40% per 17-6-2026 + 8pp). Losse rentetabel-sites liepen achter — vandaar de
kruiscontrole. Migratie `s230_handelsrente_2026_07` (commercial + government),
natelling 51 rijen per soort. **Wachter:** actualiteitscheck met peildatum-constante
(>7 maanden → rood), bewust niet "nieuwste rij" zodat een halfjaar zónder
tariefwijziging geen vals alarm geeft.

**V4 — .env-rechten.** Bleek zes bestanden i.p.v. één: naast `.env` stonden vijf
oudere kopieën met echte waarden ook op 644. Alle zes → 600. Ook de S229-aanname
"alleen root heeft shell" weerlegd: `github-runner` heeft `/bin/bash` én zit in de
`docker`-groep (de facto root).

**V3 — auto-conceptpoort AAN.** S222-herbeoordeling zelf nagerekend op prod: € 40,87
(IN100418) en € 22,64 (IN100122) zijn exact de echte openstaande bedragen; IN100370
staat letterlijk in de onderwerpregel. Corrector herkalibreerd (3 regels), niet-
debiteurenmails weigeren nu netjes i.p.v. JSON-crash. Volledige ronde: 55 gevallen,
0 storingen, 54 beoordeeld, 3 afgekeurd — waarvan **2 opnieuw corrector-missers**
(bedrag + dossiernummer) en 1 échte vondst ("onderneem geen verdere actie tot u van
ons hoort" leest als opschorting → spelregel toegevoegd). Netto ~1 echte fout op 54.
Steekproef door Fable i.p.v. Lisanne (op verzoek): 10 goud-gevallen naast Lisannes
echte antwoorden, 6/6 bedragen live geverifieerd. Poort AAN na bewijs dat de batch
alléén concepten maakt (taak "Bekijk en verstuur", plafond 50/dag).

**Kosten meetbaar (los verzoek).** Nieuwe globale tabel `ai_usage`: elke aanroep in
`kimi_client` schrijft doel, model, 4 tokentellingen en kosten (Decimal, officiële
prijstabel; cache-lezen 0,1×, cache-schrijven 1,25×). Eigen sessie met gedempte
fouten — meten mag een aanroep nooit laten falen. Live bewezen; ving diezelfde
middag 2 echte concepten (~$0,075).

**Storing 1 — bijlagen niet te openen (Arsalan, demo).** Vijf plekken toonden
bijlagen, drie konden ze niet openen: dossier-chip klikte in het luchtledige
(bestand zat niet in `inlineFiles`), "gaat automatisch mee"-etiketten waren
doodlopend, Mail-pagina linkte kaal zonder inlogbewijs (401). Fix als gedeelde
route: `frontend/src/lib/attachments.ts` + bijlagen krijgen serverkant een ADRES
(`template_type` of `case_file_id`); facturen per stuk i.p.v. als telling.
Bulkscherm kreeg een informatieregel (geen knoppen — bij tientallen dossiers ruis).
**Reviewvondst op eigen werk:** de opvolg-voorvertoning wijst óók stap-brieven aan,
maar `render-pdf` weigerde alles buiten mijn eigen whitelist — precies de
kruispuntfout die de fix moest oplossen. Eigen lijst weg; `render_docx` is de ene
registry.

**Storing 2 — mail kaatst terug (demo).** Bounce zelf gelezen: Microsoft weigert
BaseNets uitgaande relay 194.180.216.120 (550 5.7.1, S3150). Lisannes BaseNet-
webmail kwam wél aan → andere uitgang, dus zelf oplosbaar. Vervoer en afzender
gescheiden: `resolve_office_channel()` kiest (1) kantooradres via Graph, (2) ander
Graph-account mét incasso@ als afzender, (3) BaseNet als vanouds. Arsalan zette
`incasso@` als gedeeld postvak + Verzenden-als in M365. **Live bewezen:** proefmail
kwam aan in Arsalans hotmail-inbox (niet in ongewenst); daarna sommatie IN100605
opnieuw verstuurd zonder bounce.

**Storing 3 — badge "Nog te openen" op een heropend dossier.** De herkomst-badge
keek alleen naar de BaseNet-herkomst, niet naar de huidige status → IN100605 (fase 1
LegalWork, in behandeling) toonde nog "Nog te openen". Nu "Heropend" (groen).

### Gewijzigde bestanden
`backend/app/collections/compliance.py` (sweep), `backend/app/workflow/scheduler.py`
(dagelijkse BIK-check), `backend/app/notifications/service.py`,
`backend/alembic/versions/s230_handelsrente_2026_07.py`, `s230b_ai_usage.py`,
`backend/app/ai_agent/kimi_client.py` + `models.py` (AIUsage),
`backend/app/email/oauth_service.py` (`resolve_office_channel`), `send_service.py`,
`compose_router.py`, `providers/{base,outlook,imap_provider}.py`,
`backend/app/documents/router.py`, `backend/app/ai_agent/followup_{service,schemas}.py`,
`frontend/src/lib/attachments.ts` (nieuw), `status-constants.ts`,
`email-compose-dialog.tsx`, `correspondentie/page.tsx`, `followup/page.tsx`,
`incasso/page.tsx`, `zaken/page.tsx`, `DetailsTab.tsx`,
`scripts/ai/antwoord_testronde.py`. Nieuwe tests:
`test_interest_rate_freshness_guard.py`, `test_bik_staffel_sweep.py`,
`test_ai_usage.py`, `test_attachment_openable_guard.py`,
`test_office_channel_guard.py`. Docs: `docs/sessions/S230-werkorders.md`,
deploy-regels-skill (docker cp-valkuil).

### Bekende issues
- **Sjabloon-route schuift niet door.** Een eerste sommatie via de mail-dialoog met
  sjabloon beweegt de pijplijn niet; alleen de AI-conceptroute doet dat
  (`incasso/router.py::advance_after_send`, gate `intent in (None,"next_step")`).
  Arsalan verwacht terecht dat de sjabloon-route hetzelfde doet — kruispuntfout.
  **IN100605 staat daardoor nog op Eerste sommatie terwijl de sommatie eruit is.**
- **BaseNet-relay nog steeds geblokkeerd** bij Microsoft. Wij omzeilen het; melden
  bij BaseNet is nog niet gedaan (conceptmail staat in het sessieverloop).
- **Kostenmeting begint pas 20 juli** — waar de eerdere ~€10 heenging is niet meer
  te achterhalen. Voorstel (niet gebouwd): kostenblokje op het dashboard.
- **Derde AI-testronde niet gedraaid** (meet het effect van de laatste 2 ingrepen);
  bewust niet ongevraagd i.v.m. het kostenpunt. Lisanne-steekproef op de echte
  batch (eerste draait 21-7 08:00 UTC) staat nog open.
- Niet met een browser doorgeklikt: de nieuwe bijlage-knoppen (wel alle
  onderliggende routes live bewezen + tsc/lint schoon).

### Volgende sessie
S232: sjabloon-verzendroute laten doorschuiven naar de volgende stap (zelfde regel
als `advance_after_send`, met wachter over álle verzendroutes), daarna IN100605
handmatig rechtzetten. Zie `docs/sessions/PROMPT-S232.md`.

## Sessie 229 (18 juli 2026, Fable — grote eindkeuring van heel Luxis, read-only)

### Samenvatting
Op verzoek Arsalan één brede, zelfstandige keuring (bewezen Fable-werk). Vier sporen,
alles alleen-lezen op prod, niets verstuurd/gewijzigd. Rapport met bewijs per bewering:
`docs/sessions/S229-eindkeuring.md`. Nieuws deze sessie: **Fable blijft in het abonnement**
(geen laatste dag). KvK-instructie: niet meer naar vragen/checken — Arsalan komt er zelf
op terug (vastgelegd in memory; de vaste voorrang-check hoort uit PROMPT-S230+).

**Spoor 1 — verzendroutes × huisregels: GROEN.** Route-inventaris vers via grep = exact de
allowlists in `test_send_route_drift_guard.py`. Prod-meting sinds 15/7: 34/34 mails via
incasso@ (M1), 0 logs zonder drieluik (M2), onderwerpen huisformaat (M4), 0 oud-adres in
stapteksten/sjablonen, 0 open concepten/adviezen/taken op gesloten zaken (P3), 0 dubbele
nummers, 0 wees-records, 0 B2C zonder 14-dagenbrief-bewijs.

**Spoor 2 — financiële steekproef: GROEN op de cent, 2 randvondsten.** Eigen onafhankelijke
narekening van 6 dossiers × systeem-API: **12/12 exact gelijk** (wettelijk compound over
tariefwissel, 2%/mnd met deelmaanden, creditrente, bevriesdatums). Art. 6:44-toerekening
klopt (IN100377, IN100180). **V1 (echte vondst):** 27 actieve B2C-zaken met vlakke-15%-
`bik_override` boven de dwingende WIK-staffel = **€9.794,65 te veel** (grootste IN100082:
€4.908 waar €1.102 mag); alle opdrachtgevers btw-plichtig, 12 zelfs boven staffel+21%;
app-wachter AUDIT-23 blokkeert nieuwe invoer maar de import kwam eromheen; niemand op
actieve mailstap. **V2:** handelsrente-rij 1-7-2026 (10,4%) ontbreekt — máár alle 7
handelsrente-zaken zijn vóór 1-7 bevroren → **impact vandaag €0** (na navraag Arsalan
genuanceerd; de "rentecorrectie" van 13/7 betrof de contractuele 2%/mnd, niet deze tabel).

**Spoor 3 — beveiliging: GROEN.** RLS live bewezen: onder `luxis_app`-rol geeft een vreemde
tenant 0/626 dossiers, zonder tenant-instelling faalt de query dicht; 44/44 tenant-tabellen
RLS+FORCE+policy. Secrets-scan schoon, `/api/cases` zonder token = 401, firewall 22/80/443.
**V4 (klein):** `/opt/luxis/.env` staat op 644 → 600 passend.

**Spoor 4 — AI-antwoordkwaliteit + auto-concept-poort.** De S222-poortmeting (6 "zware
fouten" → poort DICHT) herbeoordeeld mét feitencheck op prod: **4 van de 6 hard weerlegd**
— "verzonnen" €40,87 (IN100418) en €22,64 (IN100122) zijn exact de échte openstaande
bedragen (corrector telde facturen op zonder betalingen te zien); "verzonnen" IN100370
staat letterlijk in het mail-onderwerp. Herscoord: hooguit 1 middelzware fout op 51
generaties (~2%), 0 verzonnen bedragen. De poort werd tegengehouden door de béoordelaar,
niet de AI. **V3-volgorde:** corrector herkalibreren → niet-debiteur-mails netjes weigeren
i.p.v. JSON-crash → verse ronde → Lisanne-steekproef.

### Gewijzigde bestanden
Alleen docs: `docs/sessions/S229-eindkeuring.md` (nieuw, 2 commits). Geen code, geen
migraties, geen prod-mutaties, niets verstuurd. Memory: KvK-instructie + Fable-blijft.

### Bekende issues / bewust niet gedaan
- **V1-V4 zijn werkorders, niet uitgevoerd** — elk met dry-run + GO vooraf (rapport §
  "Werkorders deel 2"). V1 heeft als enige echt geld erachter.
- Niet geverifieerd: of alle 27 V1-debiteuren écht consument zijn (10 gecheckt, allen
  particulier ogend; KvK-backfill beslecht); wat de 22 wachtende classificaties/146
  ongelezen notificaties precies zijn (observatie, geen oordeel).
- Onverwerkt uit S228/S227: fysieke-telefoon-check, opmaak-restpunt S227, S221b-rest,
  DMARC, testdata 2026-00007 t/m -00019.

### Volgende sessie
S230 (Opus voor de fixes): begin met V1 (B2C-BIK-correctie, lijst met Lisanne). Dan
V2 (handelsrente-rij), V3 (corrector + verse ronde), V4 (.env-rechten).

## Sessie 228 (17 juli 2026, Fable-bouw — Luxis werkbaar op telefoon + tablet, LIVE)

### Samenvatting
Op verzoek Arsalan: één grondig onderzoek + compleet bouwplan (`docs/sessions/
PLAN-S228-MOBIEL.md`) en dat in dezelfde sessie uitgevoerd (Fable, geen Opus-wissel).
Doel: Lisanne werkt straks dagelijks vanaf haar telefoon → alles moet op telefoon
(voorrang) en tablet netjes werken. Startmeting live op prod via Playwright op
390×844 (telefoon) en 820×1180 (tablet): 8 pagina's/vensters kapot of met overloop.
GitHub-onderzoek naar beste bouwstenen → **Vaul/shadcn Drawer** (onderschuif-paneel,
past in de bestaande componentenset) + Next.js ingebouwde PWA (géén extra pakket voor
het app-icoon). Konsta/Ionic/service-workers bewust afgewezen.

**Uitgevoerd in 8 blokken (elk: bouwen → tsc → live meten op 390+820 → deploy):**
- **Blok 0 fundament:** `manifest.webmanifest` + app-iconen (weegschaal-logo, huisblauw)
  + apple-touch-icon (iOS negeert manifest-iconen); `viewportFit: cover` + safe-area-
  helpers; knoppen/inputs/selects grotere tikdoelen (h-11 <md) + 16px op telefoon;
  floating-timer boven de onderbalk; meldingen-popover schermvullend op telefoon;
  zoek-icoon in de balk op telefoon; **bovenbalk-overloop weg** (links krimpt met
  min-w-0 + truncate kruimelpad, rechts shrink-0) — dit fixte overloop op álle pagina's.
- **Blok 1 dialogen:** `dialog.tsx` schermvullend onder sm (vangnet, wint van
  consumer-max-w; consumer kan met max-sm: overrulen); `vaul` geïnstalleerd + `drawer.tsx`
  + `responsive-dialog.tsx` (Dialog ≥md, Drawer <md) als infra; compose-dialoog
  voetknoppen stapelen, **Verstuurknop volledig zichtbaar** (was half buiten beeld).
- **Blok 2 dossier-detail:** Correspondentie-tab lijst↔lezen-wissel onder lg (+ Terug
  naar lijst, wrappende actieknoppen) — **was twee onleesbare kolommetjes**; Overzicht-
  tab overloop (814→390) via DetailsTab `grid-cols-1` + `min-w-0`.
- **Blok 3 mail:** toolbar (zoek/nieuwe mail/sync) stapelt + tabs wrappen (867→390).
- **Blok 4 incasso + lijsten:** incasso-werkstroom **kaartweergave op telefoon**
  (tabel md:block) + floating batch-actiebalk volle breedte, wrapt, boven de onderbalk;
  zaken-filters/betalingen-tabs/uren-nav wrappen (622/404/404→390).
- **Blok 5 restpagina's:** dashboard + relatie-detail grid-overloop (grid-cols-1 +
  min-w-0 op elke flex-tussenlaag); alle overige routes gemeten = 390.
- **Blok 6 onderbalk:** `mobile-nav.tsx` (5 items, <md, safe-area, tellers Mail/Taken,
  Menu opent de bestaande lade); content krijgt onderruimte. Desktop: geen onderbalk.
- **Blok 7 wachter:** `e2e/mobile-overflow.spec.ts` + mobiel Playwright-project — alle
  16 routes × 390/820 assert `scrollWidth ≤ clientWidth` (fout-SOORT-wachter breed-testen).

**Bewijs (live op prod, telefoon 390 + tablet 820):** 16 routes = exact schermbreedte
(geen overloop); compose-Verstuurknop volledig in beeld; dossier-Correspondentie leest
als één paneel; incasso-kaarten + volle-breedte batch-balk; onderbalk + Menu-lade werken;
manifest/iconen geven 200; **desktop 1440 ongewijzigd** (volledige zijbalk, geen onderbalk).

### Gewijzigde bestanden
Nieuw: `frontend/src/hooks/use-is-mobile.ts`, `components/ui/{drawer,responsive-dialog}.tsx`,
`components/layout/mobile-nav.tsx`, `public/{manifest.webmanifest,icon-192,icon-512,
apple-touch-icon}.png`, `e2e/mobile-overflow.spec.ts`. Gewijzigd: `app/layout.tsx`,
`app/globals.css`, `app/(dashboard)/layout.tsx`, `components/ui/{dialog,button,input,select}.tsx`,
`components/{floating-timer,email-compose-dialog}.tsx`, `components/layout/app-header.tsx`,
`app/(dashboard)/{page,zaken/page,zaken/nieuw n.v.t.,correspondentie/page,incasso/page,
betalingen/page,uren/page,relaties/[id]/page}.tsx`, `zaken/[id]/components/{CorrespondentieTab,
DetailsTab}.tsx`, `components/relations/detail/ContactInfoSection.tsx`, `playwright.config.ts`,
`frontend/package.json` (+vaul). ~10 commits, frontend meermaals via SSH gedeployd (geen
migratie, geen prod-DB-mutatie).

### Fable-reviewronde (zelfde sessie, brede jacht — 3 vondsten, alle gefixt + live herbewezen)
1. **Onderruimte viel weg op 640-767px** (telefoon liggend/klein tablet): de onderbalk
   dekte daar de laatste inhoud af (gemeten: 24px i.p.v. 64px op 700px breed) →
   pb-regel ook binnen het sm-blok; herbewezen 64px.
2. **iOS-zoom-gat:** de 16px-fix zat op de UI-componenten, maar 89 kale `<select>`'s
   (+ losse inputs) droegen nog 14px → globale max-md-regel in globals.css
   (input/select/textarea 16px, !important); herbewezen 16px op de zaken-filters.
3. **Kleine vensters uitgerekt:** het schermvullende vangnet verdeelde de lege ruimte
   over de rijen (notitie: titel boven, veld midden, knoppen zwevend) →
   `max-sm:content-start`; herbewezen compact. Compose-Verstuurknop na de fix opnieuw
   gemeten: volledig in beeld (bounding box 374/744 binnen 390/844).
Ook gecontroleerd, geen fout: meldingen-klok (volle breedte, leesbaar), zoekknop
telefoon (opent commando-palet), incasso "Per stap" (scrollt binnen kader, krap maar
werkbaar — kaart-lijst is de hoofdroute), desktop 1440 ongewijzigd. CI na reviewfixes
volledig groen (8/8 jobs, afsluitcheck).

### Bekende issues / bewust niet gedaan
- **Fysiek toestel niet getest** — gemeten in desktop-Chrome met mobiele viewport. iOS-
  Safari-zoom, 100dvh, safe-area, beginscherm-icoon: op regels-kennis meegenomen, pas
  bewezen na doorklikken op Arsalans telefoon (→ S229).
- **Overloop-wachter niet automatisch-gated:** CI draait geen Playwright-e2e (alleen
  lint/typecheck/build). De spec compileert schoon en is een handmatig/lokaal vangnet;
  de assertie is deze sessie live op alle 16 routes bevestigd.
- **Vaul-Drawer alleen als infra** — het schermvullende dialoog-vangnet lost de
  bruikbaarheid al op; de snelle-actie-dialogen (notitie/taak/uren) zijn nog niet één
  voor één naar de Drawer omgezet (kan later, puur gevoel-polish).
- **Deploy-race ontdekt:** GitHub "Deploy to VPS" draait óók bij elke push en botst met
  handmatige SSH-deploy (container-naamconflict → rode Deploy-run, app draait wel). Herstel
  + preventie vastgelegd in memory [[feedback_deploy_via_ssh]].
- Grouped ("Per stap") incasso-weergave + enkele detail-tabellen scrollen horizontaal
  binnen hun kader (bewust; niet elke tabel herbouwd).

## Sessie 227 (17 juli 2026, Opus-bouw → Fable-review — AI-antwoord-knop op dossier + briefopmaak-veeg, LIVE)

### Samenvatting
Startpunt PROMPT-S227 (KvK-check: sleutel niet binnen → door met A1). Halverwege
wisselde Arsalan naar Fable voor de review; les vastgelegd in memory: de cyclus
Fable plant → Opus bouwt → Fable test+reviewt (óók visueel) is VAST — niet meer
bespreken, en de review is een brede jacht, geen zelfcontrole.

**A1 — AI-antwoord-knop op dossier-tabblad Correspondentie (LIVE + doorgeklikt).**
De S223-dialoog is nu een gedeelde component (`components/ai-reply-dialog.tsx`);
zelfde endpoint/dedupe/spelregels. Verschil per plek: Mail-pagina navigeert met
`?draft=`, dossier-tab opent het concept in-page via `openDraftDialog` (BUG-73:
`?draft=` is onbetrouwbaar bij same-page-navigatie). Beide flows visueel bewezen
op prod, incl. dedupe-tak ("bestaand openen / nieuw maken") en force_new
(oude concept aantoonbaar `discarded`, geen zombie).

**Fable-reviewvondst — dubbele slotgroet (gefixt + live).** Het model schreef
soms zelf "Met vriendelijke groet," terwijl de aankleding "Hoogachtend, …"
toevoegt. Deterministische strip op het ene knooppunt (`generate_unified_draft`,
alle intents) + 5 wachters. Route-matrix wees óók de tweede generator aan
(`draft_service`, auto-concept/klant-update — gated/UI-dood maar op de roadmap):
die prompt INSTRUEERDE de eigen groet → omgedraaid + prompttekst-wachter.

**Vondsten Arsalan (foto + Word-referentie `Betreft.docx`):**
1. Dialoog barstte open bij lang BaseNet-onderwerp (grid zonder `min-w-0`) —
   gold ook al op de Mail-pagina sinds S223. Gefixt, op IN100458 gereproduceerd
   én na de fix bewezen.
2. Keuze combinatie (AskUser): antwoord-Betreft ín de brief = huisformaat
   "klant / debiteur — Reactie op uw bericht — nr"; mail-onderwerp blijft
   "Re: …" (draad intact) maar BaseNet-codes "[IN100458_I…]" worden gestript.
3. Witregels: de kale `<p>&nbsp;</p>` tussen Betreft en aanhef kreeg per client
   eigen marges (editor ~3 regels, Gmail niets) → vaste maat `margin:0` = exact
   één lege regel; plus échte extra lege regel ná "Geachte …"/"Dear …" (NL+EN,
   centraal in `_inline_paragraph_spacing`); AI-alinea-marge 12→16px gelijk.

**Opmaak-veeg ("doe alles").** Vier routes bouwden nog één platte "\n→<br>"-blob
waar de witregel-regels nooit op grepen: classificatie-antwoord, follow-up
(verzending + preview), documenten-custom-body, .eml-fallback → alle vier door
gedeelde `plain_paragraphs_html` (lege regel = alinea, escape ingebouwd) +
AST-achtige wachter tegen nieuwe platte blobs. Bijvangst: een GETYPTE "Open in
Outlook"-mail vertrok altijd al kaal (geen logo/handtekening/schuldhulpblok; de
.eml gaat direct Outlook in) → krijgt nu `ensure_branded_body`. Live bewezen:
.eml-route compleet (Betreft/witregels/logo/1× handtekening/schuldhulp),
follow-up-preview 11 alinea's op maat. Bewust met rust: DB-stap-brieven
(BaseNet-opmaak, S225 live goedgekeurd 12/12) en interne SMTP-testmail.

**Verstuurd (GO Arsalan):** 1 opmaaktest-mail naar zijn gmail via 2026-00006 —
afzender incasso@, drieluik vastgelegd. Arsalans oordeel: **"niet goed maar
prima, laat maar — komt later"** → het opmaak-restpunt staat open voor S228,
wat er precies schort is niet gespecificeerd.

### Gewijzigde bestanden
Frontend: `components/ai-reply-dialog.tsx` (nieuw), `correspondentie/page.tsx`,
`zaken/[id]/{page,components/CorrespondentieTab}.tsx`. Backend:
`email/{incasso_templates,subject,compose_router}.py`, `ai_agent/{unified_draft_
service,draft_service,service,followup_service}.py`, `documents/router.py`.
Tests: `test_{unified_draft_service,email_subject,incasso_templates}.py`
(+15 wachters). 8 commits (`12bb361`→`d5dd3f4`), frontend 2× + backend 4×
gedeployd via SSH (geen migratie). Geen prod-DB-mutaties.

### Bekende issues / bewust niet gedaan
- **Opmaak-restpunt Arsalan** (zie boven) — S228 eerst uitvragen (screenshot).
- Classificatie-antwoord-route: alinea-fix test-gedekt, NIET live gevuurd
  (zou echt versturen + zijn reviewwachtrij raken).
- Test-concepten op 2026-00006 (1 open, 2 vervallen) — gaan mee met de
  afgesproken testdata-opruiming; IN100458 alleen-lezen benaderd.
- Klant-update-endpoint is UI-dood (S224-klasse beslispunt, niet opgeruimd).
- Laatste 2 CI-runs liepen nog bij afsluiten (eerdere 6 groen; zelfde tests
  draaiden lokaal groen) — uitslag komt via achtergrondtaak.

### Volgende sessie
S228: opmaak-restpunt uitvragen (screenshot van wat nog niet klopt), dan
S221b-rest óf KvK-backfill (voorrang zodra sleutel binnen, ~22 juli).

