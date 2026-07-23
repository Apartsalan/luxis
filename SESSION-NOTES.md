# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 23 juli 2026 (S242-start: S240-entry alsnog geschreven uit logboek + git log; S241 was al afgerond — testronde 3 + Negeren-fix + meldingen-bundeling LIVE).
**Laatste feature/fix:** Meldingen-bundeling in de bel (3+ ongelezen van zelfde type = één rij; klik = overzichtspagina + stapel gelezen) + fix "Negeren wint van elke sync". Detail: entry S241 + `docs/sessions/S241-SCENARIOS.md`.
**Openstaand:** voorstel-lijst (S242-kandidaten: dubbelklik-betaling-slot, belofte×regeling dubbel werk, eigenaarloze-taken-melding; rest S239-lijst onaangeraakt); 2 echte mails (IN100128, IN100586) + verweer IN100592/IN100606 + IN100492 bij Lisanne; opruimronde mét Lisanne; **2 verjaringsmeldingen (IN100015 VERJAARD, IN100127) nu zichtbaar door de bundeling — aandacht Lisanne/Arsalan**. Losse punten: BaseNet-delisting, kostenblokje, opmaak-restpunt S227, S221b-rest, DMARC, testdata, 4 cosmetische restjes S235, sharp-CVE's; derde AI-testronde bewust afgevoerd (S241).
**Volgende sessie:** S242 (Opus) — zie `docs/sessions/PROMPT-S242.md`.

## Sessie 241 (23 juli 2026, Fable-testronde → Opus-bouw → Fable-tegenlezing — testronde 3 + Negeren-fix + meldingen-bundeling, LIVE)

### Samenvatting
Parallel aan de S240-afronding in een andere terminal (afspraak: administratie
dáár, dus deze afsluiting kwam pas na expliciete opdracht van Arsalan; de
S240-entry ontbreekt hier nog). Model-cyclus netjes gevolgd: testronde op Fable,
bundeling gebouwd op Opus (wissel door Arsalan), Fable-tegenlezing erna.

**Testronde 3 — 10 scenario's, drie verse brillen** (logboek:
`docs/sessions/S241-SCENARIOS.md`; verwacht-resultaat vooraf, wegwerpdossier
2026-00021 volledig gewist + nageteld 0, lokale wegwerp-medewerker idem):
- **Bril A (S240-functies op kruispunten):** belofte-taak met verleden-datum,
  auto-sluiten bij betaling, heropening, dossier-sync×melding — allemaal goed.
  **Vondst 1 (gefixt, `da81429`): een met "Negeren" weggedrukte mail werd bij een
  latere sync stil aan een dossier gekoppeld** (via dossier-sync én via later
  aangemaakt dossiernummer). Rode test eerst; Negeren wint nu van elke sync,
  bounces mogen wél blijven koppelen (tegenproef). 6 wachters, 1002 tests groen.
- **Bril B (twee gebruikers/rollen):** werklijst-verschil seidony 61 vs kesting 38
  = puur toewijzing + bewuste eigenaarloze-taken-regel; rollen-matrix klopt (droog
  + live steekproef lokale omgeving: 4× 403 beheer, 200 dagelijks werk).
- **Bril C (de ochtend van morgen):** server draait UTC → jobs 08:00-10:00 NL;
  morgen kleurt 1 taak, 0 nieuwe meldingen (30-dagen-dedup werkt). Werklast-meting:
  65 taken (39 test/26 echt), 21 adviezen (14/7), 16 aanvragen — opruimronde is de
  sleutel, niet nieuwe bouw. Blok D (derde AI-ronde) bewust overgeslagen: S238
  testte de antwoordlaag vers en S240/S241 raakten dat pad niet.

**Meldingen-bundeling gebouwd + LIVE (GO Arsalan, `275d9f4`).** Meting: 112
ongelezen bij seidony, 93 bij kesting (63× taak-te-laat, 25× nieuwe-mail) — de
bel was onbruikbaar. Nu: typen met 3+ ongelezen worden één bundel-rij met teller
("63 taken of deadlines te laat"); klik → overzichtspagina van dat type + hele
stapel in één keer gelezen (nieuwe route `PUT /read-by-type`, alleen eigen
gebruiker+type). Bundels altijd bovenaan (nooit weggedrukt door de 15-rijen-kap);
losse + gelezen meldingen onveranderd; platte lijst (dossier-actiefeed) expliciet
ongewijzigd — wachter bewaakt beide. Direct effect: 2 verjaringswaarschuwingen
("VERJAARD! Direct actie vereist", IN100015 + IN100127) werden zichtbaar die
eerst in de stapel verdronken → **inhoudelijk oppakken is aan Lisanne/Arsalan
(rolverdeling S240)**. Fable-tegenlezing: geen fouten; 3 bewuste nuances
gedocumenteerd (snooze telt mee in bundel-klik, zelfde rijen als dossier-feed,
badge blijft ruw aantal).

### Gewijzigde bestanden
`backend/app/email/sync_service.py` (Negeren-poort),
`backend/app/notifications/{service,schemas,router}.py` (bundeling),
`frontend/src/hooks/use-notifications.ts`,
`frontend/src/components/layout/app-header.tsx`. Nieuwe tests:
`test_s241_sync_kruispunten.py` (6), `test_notification_bundling.py` (7).
Logboek: `docs/sessions/S241-SCENARIOS.md`.

### Verificatie
Email/sync-suite 1002 groen + 33 meldingen-tests groen; ruff + tsc schoon; 2×
gedeployd via SSH `--force-recreate` (backend; daarna backend+frontend),
containers healthy, login 200, prod-logs 0 fouten. Bundeling live nageteld
(gebundelde én platte lijst naast elkaar); klik-flow live bewezen met 3
wegwerp-meldingen (precies 3 gelezen, 0 andere geraakt, daarna gewist,
natelling 0). CI: fix-commit groen (alleen bekende sharp-audit rood, mag falen);
bundeling-commit liep nog bij afsluiten — **natrekken bij S242-start**.

### Bekende issues
- S240-entry in dit bestand ontbreekt nog (parallelle terminal) — staat die er
  bij S242-start nog niet, schrijf hem dan compact uit `S240-SCENARIOS.md` + git log.
- Voorstellen (niet gebouwd, scope-hek): belofte-taak naast actieve regeling =
  dubbel bewakingswerk; eigenaarloze te-laat-taken melden bij "eerste" gebruiker
  (willekeurige volgorde).

### Volgende sessie
S242 (Opus): kleine veegsessie voorstel-lijst — zie `docs/sessions/PROMPT-S242.md`.

## Sessie 240 (23 juli 2026, Opus-bouw → Fable-review → Fable-testronde 2 — bak-melding + belofte-bewaking + klik-ronde, LIVE)

### Samenvatting
Entry geschreven bij S242-start (compact uit `docs/sessions/S240-SCENARIOS.md` +
git log) — de parallelle terminal sloot af zonder deze entry.

**Bouw (GO Arsalan na S239, `4c8f787`, Opus):** de twee sterkste S239-voorstellen:
- **Melding ongesorteerde bak** — nieuwe binnenkomende mail die niet automatisch
  te koppelen is → melding bij alle actieve gebruikers (dicht het S237-gat
  "debiteur-reactie vanaf onbekend adres valt stil"); geldt alleen NIEUWE
  binnenkomers, de 81 oude ongesorteerde mails spammen niet.
- **Betaalbelofte-bewaking** — belofte-mail (datum+bedrag al herkend door de
  classificatie) → bewakingstaak op de beloofde datum
  (`ensure_payment_promise_task`); sluit automatisch bij volledige betaling.

**Fable-review → 2 fixes (`d141f35`):** belofte-taak sluit ook bij handmátig
zaak-afsluiten (route-kruispunt); melding-doorklik werkt ook als de Mail-pagina
al open staat. Rolverdeling vastgelegd (`b42a140`, Working Agreement CLAUDE.md):
sessies bouwen, Lisanne doet het inhoudelijke werk.

**Testronde 2 (Fable na modelwissel, logboek `S240-SCENARIOS.md`):** bril
"slordige gebruiker" (8 scenario's, prod-API op wegwerpdossier 2026-00021) +
bril "klik-ronde als Lisanne" (6 scenario's, Playwright tegen prod, desktop +
mobiel 390×844). 13/14 goed — validaties overal netjes (422/400 met NL-meldingen,
bedragen op de cent), cijfers dashboard/dossier consistent én handmatig nagerekend.
- **Vondst 1 (🅰, gefixt `6192ac3`):** melding-doorklik naar exact dezelfde URL
  deed niets na eerdere doorklik + handmatige tabwissel — tabwissel maakt de URL
  nu weer kaal; live herbeklikt en bewezen.
- **Vondst 2 (🅲, → S242):** dubbelklik/2 tabs boekt een deelbetaling dubbel
  (beide 201; alleen UI-demping, geen slot in de service-laag).

Bijvangst (echt, niet aangeraakt): IN100592 (Zwartbol) mailde opnieuw mét
dossiernummer → automatisch gekoppeld + als verweer beoordeeld (0.75).

### Gewijzigde bestanden
Backend: `ai_agent/orchestrator.py`, `collections/service.py`,
`email/sync_service.py`, `notifications/service.py`, `workflow/hooks.py`,
`cases/service.py`. Frontend: `correspondentie/page.tsx`, `app-header.tsx`,
`use-notifications.ts`. Tests: `test_email_unsorted_notification.py`,
`test_payment_promise_task.py`. Commits `4c8f787`, `d141f35`, `6192ac3`,
`b42a140`, `d9e35f0`.

### Verificatie
Wegwerpdossier 2026-00021 volledig gewist (natelling 0); klikproef-melding
gewist (natelling 0); geen mail verstuurd; 0 consolefouten in de klik-ronde;
screenshots mobiel bewaard. CI van alle S240-commits groen (nagetrokken in
S241/S242).

### Volgende sessie
S241 draaide parallel (zie entry hierboven); S242 = veegsessie voorstel-lijst.

## Sessie 239 (22/23 juli 2026, nacht — Fable autonoom: scenario-nachtronde + fixloop, LIVE)

### Samenvatting
Arsalans opdracht (avond 22-7): bedenk 20-30+ scenario's waar Lisanne in haar
dagelijkse advocatenwerk tegenaan kan lopen, test ze, en los alles op — fouten +
kleine ergernissen direct fixen, ontbrekende functies als voorstel; echte
AI-aanroepen mochten; niets naar echte debiteuren; Arsalan sliep. Methode vooraf
onderbouwd (persona-/scenario-testen + "soap opera testing") en aangescherpt met:
verwacht-resultaat vóóraf per scenario, driedeling van vondsten, veilig testterrein
met terugdraai-plicht, wachter per foutsoort, einde-criterium.
**Let op: hele nacht op Fable gewerkt (ook de fixes) — Arsalan was er niet om naar
Opus te wisselen; expliciet gemeld.**

**32 scenario's in 5 groepen** (werkdag, rare debiteur, cliënt-kant, tijd/termijnen,
rand/systeem), volledig logboek in `docs/sessions/S239-SCENARIOS.md`. Geld-scenario's
live op een wegwerpdossier (2026-00020, exact teruggedraaid incl. vorderingen);
mail/AI-scenario's met 2 geïnjecteerde testmails + echte AI-calls op 2026-00006
(teruggedraaid); de rest gemeten op prod (read-only) of droog via code + bestaande
wachters.

**13 vondsten → 5 gefixt (commit `6f15a13`, 10 nieuwe wachters, LIVE):**
1. Betaling op volbetaalde zaak werd stil geboekt → totaal openstaand −100 (live
   gereproduceerd); poort gold alleen bij openstaand > 0. Derdengelden houdt
   surplus-gedrag.
2. Samengesteld kenmerk (`D102733_I71828409`) nooit herkend (underscore-woordgrens);
   na de fix koppelde de sync direct 2 échte mails die 9 dagen resp. 5 weken
   ongesorteerd lagen.
3. Concept weggooien liet de nakijk-taak eeuwig open (8 spooktaken op prod);
   gedeelde sluit-helper op alle 3 vervall-routes (P3-uitbreiding), live bewezen.
4. Regeling nagekomen maar zaak niet vol betaald → bleef stil op pauzestap; nu taak
   "Regeling afgerond — vervolg bepalen" (S235-recept, met tegenproef).
5. Dossier onvindbaar op factuurnummer van de vordering; nu in beide zoekpaden.

**Goed bevonden (o.a.):** alle geld-rekenwerk op de cent (rente, BIK-staffel,
6:44-verdeling, herrekening na extra vordering — onafhankelijk nagerekend);
rentetabel actueel (handelsrente 10,40% per 1-7-2026, extern geverifieerd);
autosluiting + factureer-melding + heropening-vangnet; mail-koppeling kiest nooit
stil een verkeerd dossier; ontdubbeling 0 dubbelen; verjaring-monitor bestaat.

**Voorstel-lijst (7, niet gebouwd — scope-hek):** melding ongesorteerde bak
(S237-gat, sterkste kandidaat), betaalbelofte-bewaking (datum+bedrag worden al
herkend, live bewezen 0.95), meldingen-bundeling (145 ongelezen), categorie
'onduidelijk', overbetaling-knop, cascade bij dossier-verwijderen, weekend-logica.

### Verificatie
351 tests groen (alle geraakte kruispunten), ruff schoon, backend deployd via SSH
`--force-recreate`, containers healthy, login 200, prod-logs 0 fouten sinds deploy,
live natellingen per fix (zie logboek). CI: liep nog bij schrijven — natrekken.
Testsporen: wegwerpdossier volledig gewist; blijvend: ai_usage-rijen (bedoeld),
1 spooktaak dicht (2026-00012), 2 echte mails gekoppeld (gewenst effect).

### Vervolg (besloten ochtend 23-7)
Arsalan: GO voor voorstel 1+2 (bak-melding + belofte-bewaking) en testronde 2 met
brillen "slordige gebruiker" + "klik-ronde als Lisanne" — in een VERSE sessie op Opus
(S240, prompt klaargezet). CI beide S239-commits groen (success via gh nagetrokken).
De 2 gevonden mails wachten nog op antwoord — eerste vraag van S240.

## Sessie 238 (22 juli 2026, Opus-bouw → Fable-eindreview — expliciete schema-koppeling + native structured outputs, LIVE)

### Samenvatting
Startpunt PROMPT-S238. Model-cyclus expliciet gevolgd (wissel zelf gesignaleerd
vóór start — les S237): bouw op Opus, eindreview op Fable.

**Hoofdtaak — de kwetsbaarste laag van het AI-fundament vervangen.**
`kimi_client` raadde welk JSON-schema bij een aanroep hoorde via een Nederlands
trefwoord in de prompttekst (`_detect_schema`); een gewijzigde promptzin liet zo'n
aanroep stil terugvallen op tekst-parsen. Nu geeft **elke aanroeper zijn schema en
purpose expliciet mee** (verplichte keyword-args, geen defaults): classificatie,
intake, factuur (tekst + PDF), stap-concepten (`call_draft_ai`), dossier-concepten
(`draft_service`), compose/antwoord (`unified_draft_service`) en het testronde-
script. `_detect_schema`, `_PROMPT_SCHEMA_MAP`, `_parse_json`, `_call_haiku` en
`_call_sonnet` zijn weg. Model-routing ongewijzigd (Haiku extractie, Sonnet
concepten); `ai_usage`-registratie blijft per aanroep werken.

**Native structured outputs + drie live gevonden API-grenzen.** Tekst-routes
draaien op `output_config.format` (GA voor Sonnet 4.6/Haiku 4.5; API garandeert
schema-geldige JSON); de PDF-route houdt forced tool_use (docs garanderen de
combinatie met document-input niet), waar mogelijk met `strict`. De prod-natelling
ving drie niet-gedocumenteerde grammar-grenzen: (1) max 24 optionele velden
(factuurschema: 54 → alle velden verplicht gemaakt, nullable), (2) max 16
nullable/union-velden (factuurschema: 27 → statische poort `_grammar_fits` kiest
dan forced tool_use), (3) **"Grammar compilation timed out" op het intake-schema
dat binnen de limieten past** (Fable-reviewvondst) → runtime-vangnet: elke 400 op
het structured-pad krijgt één herkansing via niet-strict forced tool_use — het
oude bewezen gedrag, maar mét expliciet schema. Nooit meer een harde AI-uitval
door een schemagrens.

**Schema's kloppend gemaakt met hun prompts.** De classificatie vroeg `sentiment`
en `defense_type` die het oude schema niet kende; het factuurschema miste 13 van
de 28 promptvelden (o.a. contactpersonen, crediteur-postadres) — met
`additionalProperties=false` zouden die stil zijn weggefilterd. Nieuwe schema's
naast hun prompt: `CASE_DRAFT_SCHEMA`, `UNIFIED_DRAFT_SCHEMA`, `_CORRECTOR_SCHEMA`.

### Gewijzigde bestanden
Backend: `ai_agent/kimi_client.py` (herschreven), `ai_agent/{service,intake_service,
invoice_parser,draft_service,unified_draft_service}.py`, `incasso/automation_service.py`,
`scripts/ai/antwoord_testronde.py`. Tests: `test_kimi_client_structured.py` (nieuw, 20
wachters: verplichte keyword-args, schema-geldigheid, prompt↔schema-sync per route,
grammar-poort, runtime-terugval), `test_unified_draft_service.py` (mock-signaturen).
Commits `e278a51`, `6cf04a8`, `0687306`, `80786f1`; backend 4× via SSH
`--force-recreate` (geen migratie, geen frontend).

### Verificatie
20 nieuwe wachters groen; brede AI-run 239 groen (kimi/unified_draft/ai_agent/
intake/invoice) + followup/draft-suites 193 en incasso_pipeline 55 groen; ruff
schoon; CI groen op alle 4 commits (conclusion=success via API nagetrokken).
**Live natelling op prod: alle 7 routes** (classificatie, intake, factuur-tekst,
compose/antwoord, dossier-concept, stap-concept, PDF) — elk 1 echte AI-call, resultaat
schema-conform, 7 rijen in `ai_usage` met kosten. Prod-logs sinds deploy: 0 AI-fouten;
containers healthy, login-API 200. **Extra op verzoek Arsalan: antwoord-testronde met
46 verse AI-antwoorden** (18 scenario's + 28 goud-gevallen, corrector aan, niets
verstuurd) — 0 storingen, 0 echte fouten; de 2 corrector-markeringen beide handmatig
weerlegd als controleur-missers (rapport: `docs/sessions/S238-antwoord-testronde.md`).

### Bekende issues / bewust niet gedaan
- **Intake-route loopt structureel via het tool_use-vangnet** ("Grammar compilation
  timed out" reproduceerde 2×) — functioneel identiek resultaat; als Anthropic de
  grammar-compilatie verbetert gaat de route vanzelf native. Geen actie nodig.
- De verweer-PDF-route (`call_draft_ai` mét AV-PDF) is niet apart live afgevuurd —
  zelfde codepad als de wel-geteste PDF-route (enige verschil: het schema, en
  INCASSO_DRAFT_SCHEMA is live bewezen op de tekst-route).
- Lopende zaken onaangeraakt (bij Lisanne): verweer-concepten IN100592/IN100606,
  IN100492-vraag, opruimronde.

### Volgende sessie
S239: **Arsalan legt de hoofdtaak bij start zelf uit** (aangekondigd bij dit
sessie-einde). Achtergrond-punten die er nog liggen (Lisanne-antwoorden,
opruimronde, onbekend-afzender-gat) staan als context in
`docs/sessions/PROMPT-S239.md`.

## Sessie 237 (22 juli 2026, Fable-meting → Opus-bouw → Fable-review + Fable-onderzoek — sommatie-reacties + escalatie-taken LIVE + toekomst-repos)

### Samenvatting
Startpunt PROMPT-S237. Model-cyclus expliciet gevolgd na correctie Arsalan
("dit is denkwerk → Fable"): meting/review/onderzoek op Fable, bouw op Opus.

**1. Reacties op de 7 sommaties van 22-7 (vers gemeten op prod).** 0 bounces.
Drie afzenders reageerden:
- **IN100606 (Maatwerk)** — bekende betwisting; concept klaar, wacht op Lisanne
  (keuze Arsalan: laten liggen).
- **IN100592 (Onbevreesd) — nieuwe betwisting die het systeem NIET zag:** debiteur
  Zwartbol mailde 2× vanaf privé-hotmail (ander adres dan waar de sommatie heen
  ging, geen dossiernummer) → ongesorteerde bak, geen melding/beoordeling. Na
  handmatig koppelen (keuze Arsalan, via de gewone app-route) deed Luxis de rest
  binnen 6 min zélf: 2× betwisting geclassificeerd (85%/92%), zaak → 'Verweer
  beantwoorden', concept klaar. Bijvangst: 2 concepten + 2 nakijk-taken (elke mail
  triggerde er één) — opruimronde. **Structureel gat genoteerd: debiteur-reactie
  vanaf onbekend adres valt stil** (alleen zichtbaar in ongesorteerde bak).
- **IN100492 (Petri, buiten de 7)** — debiteur vraagt update op een AFGESLOTEN
  dossier met €0 betaald (~€1.950 open). Vraag voor Lisanne.

**2. Escalatie-taken op de werklijst (keuze Arsalan, LIVE + nageteld).** Elk open
escalatie-advies krijgt een taak "Vervolg bepalen — {zaaknummer}" (source
`followup_escalate`), knop "Beoordelen" → /followup. Sluit mee via supersede/
afwijzen (skipped); de doorschuif-motor sluit bewust alléén verstuur-taken
(brief ≠ escalatie-besluit); 'Uitvoeren' dedupet tegen de spiegel-taak.
Prod: 14 taken = exact de 14 geldige pending escalate-adviezen (waarvan 4 échte
'Voorstel dagvaarding'); IN100521 terecht overgeslagen (advies stale — zaak al op
'Verzoekschrift faillissement'). Fable-review: GO; idempotentie live bewezen
(2e scan → nog steeds 14/14), 0 onterechte sluitingen. Eén cosmetisch restje:
logboekregel zegt "taak aangemaakt" ook als de spiegel al bestond.

**3. Open-source-onderzoek (verzoek Arsalan, 10 videotools + GitHub-breed).**
Uitkomst: architectuur gevalideerd — géén lijst "werk voor niks". Enige echte
nu-klus: **Anthropic native structured outputs** vervangt de kwetsbare trefwoord-
schema-detectie (`kimi_client._detect_schema`) → **hoofdtaak S238**. Besluiten
Arsalan: (a) **agent-laag komt er t.z.t.** (als Luxis zo goed als klaar is), dan op
pydantic-ai — tot die tijd alles agent-compatibel bouwen (service-laag-eerst, nu
Working Agreement in CLAUDE.md); (b) toekomst-adopties met triggers in
`docs/TOEKOMST-REPOS.md` (CAMT bij 2e bank, Langfuse self-host bij AI×10, Ollama
bij klant-eis, pgvector bij RAG-heroverweging, Docling, mail-parser-reply) mét
attendering-plicht; (c) afgewezen zonder nieuwe feiten: LiteLLM/Outlines/Chonkie/
Crawl4AI/Qdrant/DSPy/Marker.

### Gewijzigde bestanden
Backend: `incasso/service.py` (close_followup_send_tasks → sources-parameter),
`ai_agent/followup_service.py` (escalatie-spiegel + execute-dedupe). Frontend:
`taken/page.tsx` (knop "Beoordelen"). Tests: `test_followup_send_tasks.py`
(+5, 15 totaal). Docs: `docs/TOEKOMST-REPOS.md` (nieuw), `CLAUDE.md`
(agent-compatibel-regel). Commits `ff21d81`, `2a05a6d`; backend+frontend via SSH
`--force-recreate` (geen migratie). Prod-mutatie: 2 mails gekoppeld aan IN100592
via de app-API (natelling 2/2).

### Verificatie
15 wachters groen; kruispunt-run followup/advance/workflow/arrangement 152 groen;
ruff + tsc schoon; CI groen op ff21d81 (conclusion=success via API); containers
healthy, login 200. Werklijst-natelling prod 14/14 met tweede scan (idempotent),
0 onterechte taak-sluitingen. Onderzoek: web-bronnen in sessieverloop.

### Bekende issues / bewust niet gedaan
- **Gat: debiteur-reactie vanaf onbekend mailadres valt stil** (geen melding) —
  kandidaat-verbetering, niet gebouwd (scope).
- Opruimronde wacht op Arsalan+Lisanne: IN100607/IN100613/IN100521 stale adviezen,
  6 oude nakijk-taken van 21-7, dubbel concept+taak IN100592, logboekregeltje
  execute-escalate.
- "Beoordelen"-knop niet visueel doorgeklikt (zelfde patroon als S236-knop; tsc schoon).
- Verweer-concepten IN100592/IN100606 en IN100492-vraag liggen bij Lisanne.

### Volgende sessie
S238: native structured outputs-refactor (alle AI-aanroepen, eigen sessie, Opus +
volle kruispunt-discipline). Zie `docs/sessions/PROMPT-S238.md`.

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
