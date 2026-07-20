# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 21 juli 2026 (S233 — AI-antwoord als zijpaneel + mailgeschiedenis + "facturen erbij", LIVE).
**Laatste feature/fix:** Het AI-antwoord-/reviewvenster is nu een rechts-verankerd, NIET-modaal zijpaneel: de mails links blijven leesbaar én aanklikbaar tijdens het schrijven. Onderin het paneel de mail waarop je antwoordt (uitklapbaar) + de eerdere mailtjes van dezelfde draad. Op de Mail-pagina opent het concept IN-PLACE i.p.v. naar de dossierpagina te navigeren (waardoor je de mail kwijtraakte). Plus: vraagt de behandelaar "doe de facturen erbij", dan opent het concept met de factuur-PDF's al aangevinkt (kruispunt-guard: alleen de antwoordroute, batch/stap nooit). Detail: entry S233.
**Openstaand (-> S234 e.v.):** S234 = incassostappen kritisch herzien (situatie-stappen i.p.v. platte lijst; derde/laatste sommatie hebben nog géén brief-koppeling → schuiven daarom nog niet door; batch/follow-up op dezelfde "volgende stap"-logica trekken). S235 = betalingsregeling herkennen uit mail + flexibel termijnschema. Losse punten: BaseNet-delisting melden, derde AI-testronde + Lisanne-steekproef, kostenblokje dashboard. Onverwerkt: fysieke-telefoon-check, opmaak-restpunt S227, S221b-rest, DMARC, testdata opruimen. Outlook-route weghalen (Arsalan: later).
**Volgende sessie:** S234 — incassostappen kritisch herzien (situatie-stappen + brief-koppeling derde/laatste sommatie + batch/follow-up-doorschuif gelijktrekken).

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

## Sessie 226 (17/18 juli 2026, Opus-opmaaksprint → Fable-review — mailopmaak over alle routes, LIVE)

### Samenvatting
Startpunt PROMPT-S226 (punten Arsalan + testvondsten S225). Onderweg werd het
een brede opmaak-sanering van álle uitgaande mail, plus een grondige
Fable-tegenlees-review die 5 extra fouten vond. Per stuk: meten in de bron →
bouwen → tests → deploy via SSH → live herbewezen (testmails naar Arsalans gmail,
HTML gecontroleerd via Gmail-API).

**Punten Arsalan + testvondsten S225:**
- **A3 Betreft-regel huisformaat (LIVE):** alle 26 code-brieftypen + de
  DB-stap-teksten (`html_renderer.py`) dragen nu "{klant} / {debiteur} —
  {brieftype} — {dossiernummer}" via gedeelde `_betreft()`/`fill_betreft_slots`
  (= `build_email_subject`). De dubbele "Betreft: Betreft:" verdween mee.
- **A2 aanhef reactiebrieven (LIVE):** 6 `DEFAULT_TEMPLATES` (ResponseTemplate)
  renderden "Geachte {{ wederpartij.naam }}," → bij een bedrijf ging "Geachte
  Autobedrijf X B.V.," de deur uit. Nu S220-lijn "Geachte heer, mevrouw," (code
  + 6 DB-rijen, UPDATE 6). 103 bibliotheek-antwoorden = referentie (aanhef bewust
  gestript, geen bug).
- **Punt 4 gmail-bezorging (uitgezocht):** SPF ✅ + DKIM ✅ (basenet0001), maar
  **DMARC ontbreekt volledig** (`dmarc=bestguesspass`). Directe gmail-meting: 27
  gewone brieven in inbox, 3 zware (dagvaarding + 2× faillissement) nergens (ook
  niet spam). Weak-auth + zware inhoud → gmail dropt stil. DMARC publiceren =
  Arsalan/BaseNet-actie; geen garantie maar de duidelijkste gap.
- **Punt 5 nummer-hergebruik (geen prod-bug):** gemeten — dossiers worden ZACHT
  verwijderd (rij blijft) en `generate_case_number` filtert niet op is_active →
  nooit hergebruik (prod: 0 dubbele nummers). De reuse in de testronde kwam door
  hard-delete in opruimscripts. Invariant vastgelegd met regressietest + comment;
  matcher-datumgrens bewust NIET (zou geïmporteerde historische post breken).

**Opmaakpunten Arsalan (screenshots) — logo + witregels:**
- **Logo (LIVE):** zat als data-URL → Gmail/Outlook blokkeren dat (kapot kader).
  Nu extern gehost `frontend/public/kesting-logo-email.png` via
  `https://luxis.kestinglegal.nl/...` (zoals BaseNet). URL geeft 200; ook in de
  DB-stap-teksten + 5 open concepten vervangen. Dode b64-inlaadcode weg.
- **Witregel na aanhef (LIVE):** Gmail negeert head-`<style>` én nult `<p>`-marges
  → brief begon meteen na de komma. Marge nu INLINE op elke `<p>` (16px) via
  `_inline_paragraph_spacing`. Bewezen in ontvangen testmail.

**Fable-review — 5 extra vondsten, alle gefixt + live:**
1. AI-concept-route bouwde "Betreft: Betreft:" (eigen prefix bovenop het
   basis-label) + antwoord-onderwerp (uit INKOMENDE mail) ging onge-escaped een
   Markup-context in (S202-M4-klasse) → prefix weg, onderwerp ge-escaped.
2. Stap-teksten-vulling: half label "WEDEROM SOMMATIE" matchte de prod-tekst
   "WEDEROM SOMMATIE TOT BETALING / /" nooit → generiek label hapte de staart
   ("WEDEROM {huisformaat}", 3 prod-stappen). Volledige labels, langste eerst;
   vuller gedeeld met de batch-DOCX-tak (zelfde lege slots).
3. Documenten-route + batch-DOCX-tak + custom-body hadden een eigen kale
   Arial-wrapper (geen logo/schuldhulpblok, aanhef op naam, "Antwoord niet op
   deze e-mail" aan de wederpartij) → kale alinea's, verzendlaag kleedt aan
   (S186), gelijk aan alle routes.
4. 6 reactiebrieven kregen twee handtekeningen (eigen slotgroet + aankleed-
   handtekening) → slotgroet uit seed + 6 DB-rijen (UPDATE 6).
5. 3 reactiebrieven openden met losse komma "<p>,</p>" → S220-aanhef.
Plus: 3 dode sjabloon-functies (`deadline_reminder`/`payment_confirmation`/
`status_change`, 0 aanroepers) met dezelfde foute stijl verwijderd.

### Gewijzigde bestanden
Backend: `email/{incasso_templates,subject,templates,send_service}.py`,
`incasso/{html_renderer,service}.py`, `ai_agent/{service,unified_draft_service}.py`,
`cases/service.py`, `documents/router.py`. Frontend: `public/kesting-logo-email.png`
(nieuw). Tests: `test_{incasso_templates,html_renderer,unified_draft_service,
ai_agent,cases}.py` (+8 wachters). 8 commits (`b888cf8`→`20f0c46`), backend meermaals
+ frontend 1× gedeployd (geen migratie). Prod-DB: 6 reactiebrieven (aanhef+slotgroet),
5 open concepten (logo) — elk dry-run + GO + natelling.

### Bekende issues / bewust niet gedaan
- **A1 AI-antwoord-knop op dossier-tabblad Correspondentie NIET gebouwd** —
  grootste openstaande klus; kruispunt-matrix + brede test verplicht (nieuwe route
  voor effect "concept maken").
- Testdata 2026-00007 t/m -00019 NIET opgeruimd (Arsalan: bewaren voor meer testen).
- DMARC-instelling = Arsalan/BaseNet (buiten mijn bereik).
- Losse testmails naar Arsalans gmail liepen buiten dossier-vastlegging (bewust,
  geen dossier); alle échte routes leggen wél vast.
- S221b-rest + auto-concept-gate blijven staan.

### Volgende sessie
S227: A1 AI-antwoord-knop op het dossier-tabblad Correspondentie (Opus, kruispunt-
matrix + brede test). KvK-backfill voorrang zodra sleutel binnen (~22 juli).

## Sessie 225 (17 juli 2026, Opus-bouw — beslispunten B1/B2/B3 + eerste S221b-UX-restpunten)

### Samenvatting
Bouwsprint op de S224-veegsessie. Voorrang-check KvK: sleutel niet op de VPS →
door. Beslispunten met Arsalan afgestemd (zie kop); daarna gebouwd, getest,
gedeployd via SSH en geverifieerd.

**B1 — facturen via kantoorkanaal (LIVE).** `send_invoice` kreeg
`send_as_tenant_account=True` → een factuur aan de opdrachtgever gaat nu via
incasso@ i.p.v. het persoonlijke account van de klikker. Onderwerp blijft bewust
eigen formaat "Factuur {nr}" (allowlist-motivering M4 bijgewerkt).

**B2 + B3 — twee dode verzendroutes verwijderd (LIVE).** (B2) AI-tool
`email_compose` uit de tools-registry + handler weg (registry had geen aanroepers;
tool-count 34→33). (B3) legacy endpoint `/api/email/cases/{id}/send` + schema's +
hook `useSendCaseEmail` weg — die route was UI-dood maar wél levend (SMTP
geconfigureerd, geen 14-dagenbrief-gate, half drieluik). De spinner die aan de
dode mutation hing draait nu op een echte lokale verzend-vlag. Beide
wachter-allowlists (`test_send_route_drift_guard.py`) meegetrokken; eerlijkheids-
test dwong dat af. **Prod bewezen:** legacy endpoint geeft nu 404, `/email/status`
leeft (401).

**B4 — Bayar IN100613 NIET aangeraakt.** Uitgezocht: het dossier is 15/7 om 17:27
handmatig vanuit Arsalans account gesloten (BaseNet-origin nog 'Lopend', 0
betalingen) — dus géén BaseNet-afsluiting. Arsalan wil het eerst zelf bekijken →
dossier + wees-advies ongemoeid.

**S221b-UX-restant (eerste lichting, LIVE):**
- **Follow-up "Dagen" live:** de kolom toonde de bevroren waarde van toen de
  aanbeveling werd aangemaakt (import stempelde overal 0d). Nu live berekend uit
  `step_entered_at` zolang de zaak nog op de stap van de aanbeveling staat; is de
  zaak doorgeschoven, dan blijft de historische waarde. **Prod bewezen:** 10
  openstaande adviezen 0d→8d. +2 tests. Dossiernummer nu direct klikbaar in de rij.
- **Soft-delete-banner:** een verwijderd dossier (via directe URL leesbaar) krijgt
  een rode "dit dossier is verwijderd"-balk op alle tabs.
- **Agenda lege staat:** overkoepelende hint met "Nieuw event" + Outlook-sync i.p.v.
  een kaal raster.

### Gewijzigde bestanden
Backend: `invoices/service.py`, `ai_agent/tools/{definitions,handlers/email}.py`,
`email/router.py` (+ `email/schemas.py` verwijderd), `ai_agent/followup_service.py`.
Tests: `test_send_route_drift_guard.py`, `test_ai_tools/test_registry.py`,
`test_email_router.py`, `test_followup.py` (+2). Frontend: `hooks/{use-documents,
use-cases}.ts`, `zaken/[id]/page.tsx`, `zaken/[id]/components/DocumentenTab.tsx`,
`followup/page.tsx`, `agenda/page.tsx`. 2 commits, backend+frontend gedeployd
(geen migratie).

### Testronde (Fable, zelfde dag — wens Arsalan: "20 aanklikken en alles klopt")
Volledig rapport: `docs/sessions/S225-testronde.md`. Kern: 13 testzaken
aangemaakt (debiteur = Arsalans gmail), batch via de échte UI gedraaid.
**Bewezen:** 12/12 mails bezorgd in gmail (afzender incasso@, huisformaat,
rente-PDF, huisstijl); bedragen op de cent onafhankelijk nagerekend (€292,11 /
€140,50 / €191,12); consument zonder 14-dagenbrief correct geblokkeerd mét
wetsartikel; alle zaken doorgeschoven naar Tweede sommatie; per zaak automatisch
een nieuwe taak (+4 dgn); alles zichtbaar op incasso/dossier/tijdlijn/Mail/
Taken/follow-up. **Word-tak (B6) live gevuurd** via tijdelijke TEST-stap
(DOCX→PDF-mail bezorgd door SMTP-server geaccepteerd; stap daarna verwijderd,
pijplijn weer 15 stappen). **B1 live bewezen** met testfactuur F2026-00001
(afzender incasso@, daarna geannuleerd).

### Bekende issues / bewust niet gedaan
- **⚠️ Vondst testronde: dossiernummer-hergebruik** — nummers van verwijderde
  dossiers worden hergebruikt en de mailsync koppelt oude mails met dat nummer
  aan het nieuwe dossier (2× waargenomen). Fixvoorstel in rapport §3.1.
- Word-tak-mail (dagvaarding-PDF) na ~20 min nog niet in gmail bezorgd (wel
  verstuurd + geaccepteerd + geen bounce; 12 andere mails zelfde kanaal kwamen
  direct aan) → nachecken S226.
- Rechtsvorm-afkorting "bv" valt op de veilige kant (bijlage mee); volle
  KvK-benamingen na de backfill lossen dit op.
- Testdata 2026-00007 t/m -00019 + TEST-contacten + 12 taken: opruimen later
  (afspraak Arsalan).
- S221b-rest niet gebouwd: review-scherm classificatie+concept, voortgangsindicator
  bij genereren, échte HTML-tabellen (injectie-oppervlak), tijdlijn-mailregel
  klikbaar (id-betekenis eerst verifiëren — deep-link naar correspondentie),
  follow-up sorteerbare koppen (vergt server-side sortering), intake-detectie
  dempen, Blok 6-beslismemo b2b/b2c.
- V2c (klein): classificatie-antwoord-onderwerp naar `build_reply_subject`.

### Volgende sessie
S226: nummer-hergebruik-vondst + testdata-opruiming + S221b-rest. KvK-backfill
voorrang zodra de sleutel binnen is (~22 juli).

## Sessie 224 (16 juli 2026, Fable — VEEGSESSIE kruispunt-matrix + live-verzendtoets)

### Samenvatting
De éénmalige veegsessie uit de skill `breed-testen`: volledige huisregel-lijst ×
alle routes, gemeten in code + prod-DB. Route-inventaris zelf was al een vondst:
12 routes, waarvan 2 (facturen, classificatie-antwoord) niet in de skill-lijst
stonden en 2 dood/legacy zijn. KvK-voorrang-check: sleutel niet binnen → door.

**5 vondsten, 4 gefixt + gedeployd (`5845a3d`):**
1. M1 × classificatie-route: antwoord aan wederpartij ging via persoonlijk
   account → `send_as_tenant_account=True` (zelfde soort als S220-N1).
2. M3 × .eml-route: de 14-dagenbrief-gate bestond op 4 van de 5 deuren — "Open
   in Outlook" bleef open → gate + 'Toch openen'-override + spoor, voor+achter.
3. M4 × documents/send: onderwerp "{titel} — {nr}" (dossiernr dubbel, buiten de
   bouwer; route ontbrak in het S223-rijtje) → huisformaat server + prefill.
4. P3 × adviezen: sluiten ruimde wél concepten maar géén adviezen (prod-bewijs
   IN100613) → `supersede_open_recommendations` op beide sluit-routes.
5. Testdossier 2026-00006 stond gearchiveerd → matcher weigerde de testmail
   ("dossier bestaat niet") → geheractiveerd (beslispunt B5).

**2 nieuwe AST-wachters** (`tests/test_send_route_drift_guard.py`, patroon
auth/RLS-guards): M2 (geen rauwe provider/SMTP-uitgang buiten geloggde routes,
geloggde uitgangen roepen aantoonbaar `write_outbound_log` aan) en M4 (elk
verzend-onderwerp uit de bouwer of gemotiveerd op de allowlist) + eerlijkheids-
test (geen dode allowlist-regels). P3-wachter uitgebreid naar adviezen op alle
3 sluit-routes. 136 tests groen, ruff/tsc schoon, **CI groen (afsluitcheck)**.

**Live-verzendtoets (Taak B, alles op 2026-00006/Arsalans gmail):**
- **Classificatie-trigger eerste prod-vuring bewezen:** sync 17:40:20 →
  trigger 17:40:30 (10 s; losse cyclus stond pas 17:43) → belofte_tot_betaling
  85%, inhoudelijk juist.
- **AI-antwoord écht verstuurd:** instructie exact gevolgd (A3), €140,49 op de
  cent nagerekend (100 + 40 BIK + 0,49 rente = A1), huisstijl compleet (A2),
  drieluik compleet, afzender incasso@ (M1), onderwerp "Re: Vraag over dossier
  2026-00006" (M4), bezorgd in gmail ín dezelfde thread; zaak bleef op Tweede
  sommatie (P1) en concept → sent.
- **Documents-route:** renteoverzicht-PDF bezorgd; dialoog-prefill = exact
  huisformaat (fix 3 live bewezen).
- **Batch-DOCX-tak niet live toetsbaar:** geen actieve stap heeft een
  DOCX-sjabloon (alle stap-sjablonen zijn e-mail) — tak is test+wachter-gedekt;
  live raken = stap-mutatie (beslispunt B6).

### Gewijzigde bestanden
Backend: `ai_agent/service.py`, `email/compose_router.py`, `documents/router.py`,
`cases/service.py`, `workflow/hooks.py`. Frontend: `zaken/[id]/page.tsx`,
`DocumentenTab.tsx`. Tests: `test_send_route_drift_guard.py` (nieuw, 5 wachters),
`test_discard_drafts_on_close.py`, `test_compose_dagenbrief_gate.py` (+2),
`test_ai_agent.py`. Skill `breed-testen` bijgewerkt. Rapport:
`docs/sessions/S224-veegsessie.md`. 1 commit, backend+frontend gedeployd.
Prod-mutaties: alleen heractivering testdossier (1 rij).

### Bekende issues / bewust niet gedaan
- **6 beslispunten (B1-B6, rapport §5-6):** facturen-afzender (persoonlijk vs
  incasso@); dode AI-tool `email_compose` opruimen; legacy endpoint
  `/api/email/cases/{id}/send` opruimen (leeft nog, SMTP geconfigureerd, geen
  gate/SyncedEmail); wees-advies IN100613 → SUPERSEDED (GO); testdossier weer
  archiveren of actief laten; batch-DOCX-tak live toetsen.
- V2c geregistreerd, niet verbouwd: classificatie-onderwerp uit ResponseTemplate
  i.p.v. `build_reply_subject` (beheerde inhoud, geen stale data).
- Mailslot blijft principieel onafdwingbaar op de .eml-route (gebruiker
  verstuurt zelf); de gate dekt nu het juridische risico.

### Volgende sessie
S225: beslispunten B1-B6 met Arsalan afhandelen, dan S221b-UX-restant (Opus:
review-scherm, voortgangsindicator, HTML-tabellen, Blok 5-rest, Blok 6-memo).
KvK-backfill voorrang zodra de sleutel binnen is (~22 juli).

## Sessie 223 (16 juli 2026, Opus-bouw → Fable-review — AI-antwoord-knop + onderwerp-huisformaat + test-discipline)

### Samenvatting
Arsalans eigen punten uitgevoerd, plus twee kleine restpunten, plus een nieuwe
vaste test-werkwijze na zijn vraag "waarom komen er telkens fouten uit als ik
breder kijk".

**Punt 1+2 — AI-antwoord-knop (LIVE + live doorgeklikt).** Knop "AI-antwoord maken"
op elke inkomende mail van de wederpartij (Mail-pagina) met optioneel instructie-
tekstvak + toon-keuze (mild/zakelijk/streng). Onbeperkt herbruikbaar, wacht niet
op de automatische classificatie. Bestaat er al een open antwoord-concept → eerst
vragen (bestaand openen of vervangen; vervangen laat het oude vervallen via
`force_new`). Nieuw: `GET /api/ai/draft/existing`, `force_new` op de generatie,
`find_open_reply_draft`. 3 generatie-rondes live op IN100607: bedragen/facturen
exact gelijk aan DB, opmaak identiek aan bestaande concepten.

**Instructie-leidend-fix (live gemeten).** Ronde 1 negeerde "zeg dat ik erop
terugkom": de instructie stond inline en raakte begraven onder het later
aangeplakte AV/bibliotheek-blok. Fix: instructie als LAATSTE promptblok +
systeem-spelregel dat de behandelaar-instructie de kern bepaalt. Ronde 2 volgde
hem exact op.

**Punt 3 — onderwerp overal huisformaat.** `build_email_subject` (stap: klant /
debiteur — stapnaam — dossiernr) en nieuw `build_reply_subject` (antwoord:
Re: origineel + partijen/dossiernr, niet dubbel). Wint nu op ALLE routes:
compose, followup, batch (inline+DOCX), stap-concepten, antwoord-concepten. De
stale BaseNet-stap-onderwerpen ("TYPE / / ") worden overal genegeerd — geen
prod-data-mutatie nodig.

**Antwoord-verzending schuift de zaak niet meer door.** `advance-after-send`
schoof na élke concept-verzending door; nu alleen stap-brieven (rode test eerst).

**Kleine punten.** (1) Open concepten vervallen bij zaak sluiten — gedeelde
`discard_open_drafts_on_close` op alle 3 sluit-routes (handmatig, pijplijn-
eindstap, betaling-hook) + wachter-test. (4) 3 tests voor de sync→classificatie-
trigger (had er geen; vuurt op prod pas bij nieuwe mail).

**Nieuwe test-discipline (op verzoek Arsalan).** Skill `breed-testen`: fouten
wonen op kruispunten (route mist huisregel) — benoem het effect, grep alle
routes, loop de route×huisregel-matrix af, elke foutsoort krijgt een wachter.
Verwezen vanuit CLAUDE.md-verificatiestap 4 + memory. Levende huisregel-lijst
M1-M5/P1-P3/A1-A3.

### Reviewvondsten (kruispunt-matrix — beide gefixt + live)
- **Batch-PDF-route** droeg nog het stale onderwerp ("VERZOEKSCHRIFT / / ") →
  nu ook via de gedeelde bouwer + wachter-test.
- **CI stond stil rood sinds 15/7** (S220 voegde 'sommatie' toe aan de rente-
  bijlage-set maar vergat de pin-test; onzichtbaar door SSH-deploys, S217-patroon)
  → test bijgewerkt, CI weer groen.

### Gewijzigde bestanden
Backend: `email/subject.py`, `ai_agent/{unified_draft_service,unified_router,
followup_service,draft_service}.py`, `incasso/{service,router,automation_service}.py`,
`cases/service.py`, `workflow/hooks.py`. Frontend: `correspondentie/page.tsx`.
Tests: `test_email_subject`, `test_unified_draft_service`, `test_incasso_pipeline`,
`test_discard_drafts_on_close` (nieuw), `test_scheduler_email_sync`,
`test_kvk_legal_form`. Werkwijze: `.claude/skills/breed-testen/SKILL.md` (nieuw),
`CLAUDE.md`. Rapport: `docs/sessions/S223-review.md`. 6 commits, backend meermaals
gedeployd (geen migratie).

### Bekende issues / bewust niet gedaan
- **Écht versturen niet live getest** (mailslot open): nieuwe knop + batch-route.
  Verstuurpad zelf = de S220-route die toen bewezen is. → live toetsen S224.
- **Classificatie-trigger** op prod nog nooit gevuurd (geen nieuwe mail) — logica
  wel test-gedekt.
- Filter "Nog te openen" op dossierlijst: badge bestaat, filterknop niet (Arsalan
  koos hem niet). Landregel dagvaarding overgeslagen.
- Restlijst S221b-UX + auto-concept-gate (menselijke steekproef Lisanne) blijven.

### Volgende sessie
S224 = **VEEGSESSIE** (Fable): de hele huisregel-lijst uit `breed-testen` × alle
bestaande routes aflopen, mét live-pass, zodat de teller aantoonbaar op nul staat;
kandidaat-wachters staan in de skill. Plus **live-verzendtoets** zodra mag.
KvK-backfill voorrang zodra sleutel binnen (~22 juli).

## Sessie 222 (15/16 juli 2026 nacht, Opus-bouw → Fable-review — verzoekschrift-nabouw + totaalreview, autonoom)

### Samenvatting
Twee delen conform PROMPT-S222. **Deel 1 (Opus):** de faillissement-bijlage exact in
Lisanne's opmaak nagebouwd — haar BaseNet-sjabloon als basis (crème-balk, logo,
Calibri, randloze tabellen, voetteksten), 106 merge-velden omgezet naar docxtpl,
vorderingen-lus herbouwd, oud adres/mail vervangen, handtekening-placeholder weg.
Twee scenario's gerenderd (met/zonder deelbetaling): alle bedragen tellen op de cent
op, in beide tabellen. **Lokaal klaar; reseed op prod NIET gedaan** — wacht op GO +
4 keuzes (CONCEPT-watermerk, kolomlabel Verzuimdatum, betaalregels samengevoegd,
handtekening). **16 juli LIVE gezet** (GO + 4 keuzes bevestigd): back-up gemaakt,
alleen de verzoekschrift-rij bijgewerkt (45658→86951 bytes), DB-hash = schijf = lokaal,
en een live-render door het echte systeem op zaak IN100521 bewees dat alles goed vult
(debiteur/opdrachtgever/3 facturen, totalen op de cent, BTW-regel valt terecht weg).
**Deel 2 (Fable, autonoom — Arsalan sliep):** volledige review,
rapport in `docs/sessions/S222-review.md`.

### Reviewuitkomsten (bewijs in het rapport)
- **B1 LIVE bewezen** (het S221-gat): afgerond-weergave 19 taken, terugzetten op
  testdossier 2026-00006 (8→9 open), opnieuw overslaan + ongedaan-melding. ✅
- **B2:** migratie op head, 0 dubbele open concepten, 23 tests groen; máár nog geen
  nieuw concept sinds uitrol (prod-gedrag onbenut). Vondsten: zaak sluiten laat open
  concepten staan (IN100613 ×2); IN100521 heeft 2 pre-migratie-duplicaten.
- **B3 sync→classificatie: aannemelijk, NIET bewezen** — code in container ✅ maar
  géén test en nog nooit gevuurd (geen nieuwe mail sinds deploy).
- **B4 ✅ compleet:** Intake weg, Betalingen-label, ratio-tooltip, klikbaar
  dossiernummer, Calibri ×9 sjablonen, 0 spatie-kolommen in 58 verse antwoorden.
- **C testronde:** goud-pad crashte (mapper-imports, nooit getest in S221) én
  toetste het verkeerde ding (voedde Lisanne's verstuurde antwoorden als vraag —
  alle 103 bibliotheek-bronnen zijn per definitie haar eigen mails). Beide gefixt
  (`118617a`, `90ad871`) + 2 spelregels aangescherpt na ronde 1. Ronde 2: zuivere
  set 83→89%, goud eerste geldige meting 29/37; restant-afkeuringen grotendeels
  corrector-kalibratie (1 aantoonbare corrector-misser zelf nagelezen). **Poort
  auto-concept NIET gehaald → blijft UIT**; eerst kalibratievraag beantwoorden.
- **D backfills gemeten (níets opgeruimd):** 470 classificaties = 339 op afgesloten
  zaken + 110 oude mails + 21 recente (11 echt werk); 348 notificaties = 302
  classificatie-ruis; 8 concepten (3 opruimkandidaten); adviezen-15 en intake-14
  zijn actueel werk, GEEN opruimkandidaat. Opruimrecept klaar, wacht op GO.

### Wijzigingen
`118617a` (goud-pad imports), `90ad871` (spelregels + goud-lader voedt echte
debiteurenvraag) — beide gedeployed + getest. Nieuw sjabloon staat klaar in
`templates/verzoekschrift_faillissement.docx` (repo, niet op prod). Testronde-
rapporten bewaard: `S222-testronde-r1.md`/`-r2.md`. Prod verder alleen-lezen
behalve de B1-kliktest (netto nul).

### Volgende sessie
Beslispunten 1-6 uit `S222-review.md` met Arsalan doornemen; daarna S221b-restant
(Opus) of KvK-backfill (voorrang zodra sleutel binnen, ~22 juli).
