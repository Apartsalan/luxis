# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 17 juli 2026 (S228, Fable-bouw — Luxis volledig werkbaar op telefoon + tablet, LIVE).
**Laatste feature/fix:** Mobiel-geschikt maken van de hele app (voorrang telefoon): PWA-fundament (app-icoon + schermvullend openen), grotere tikdoelen + 16px-velden (geen iOS-zoom), veilige schermranden; dialoog-vangnet schermvullend op telefoon + Vaul-Drawer-infra; compose-Verstuurknop volledig zichtbaar; dossier-Correspondentie leest als één paneel; alle horizontale overloop weg (16 routes = schermbreedte op 390 én 820); incasso-werkstroom als kaartweergave met volle-breedte actiebalk; onderste navigatiebalk (Home/Dossiers/Mail/Taken/Menu); overloop-wachter-spec. Desktop ongewijzigd. Detail: entry S228.
**Openstaand (→ S229):** **Fysieke-toestel-check op Arsalans telefoon** (iOS-Safari-zoom/safe-area/beginscherm-icoon — enige niet-bewezen aanname); opmaak-restpunt S227 ("niet goed maar prima" — nog niet uitgevraagd, Arsalan wilde iets anders doen); testdata 2026-00007 t/m -00019 opruimen (na GO); DMARC kestinglegal.nl (Arsalan/BaseNet); S221b-rest; auto-concept-gate (steekproef Lisanne). KvK-sleutel ~22 juli → backfill voorrang. MAILSLOT OPEN.
**Volgende sessie:** mobiel doorklikken op fysieke telefoon (Arsalan) → resterende puntjes; dan opmaak-restpunt óf S221b-rest óf KvK-backfill zodra sleutel er is (~22 juli).

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

## Sessie 221 (15 juli 2026 avond/nacht, Opus — demolijst DEEL 2, 6 blokken LIVE)

### Samenvatting
Vervolg op S220. Per blok: bouwen → tests → deploy via SSH → prod-verificatie. 7 commits,
1 migratie (additief). Geen echte debiteuren gemaild.

**Blok 3.4 — overgeslagen/afgeronde taken (LIVE + BEWEZEN).** `my-tasks` gaf alleen open
taken terug → de "Afgerond"-weergave op Taken was altijd leeg (17 skipped + 2 completed
onzichtbaar). Nieuw `?include_done=true` (gecapt 100, nieuwste eerst); dashboard-widget
ongemoeid. Terugzet-knop (→ pending) + undo-toast direct na overslaan. **Prod: zonder de
optie 8 open taken, mét de optie 27 waaronder 17 eerder-onzichtbare overgeslagen taken.**

**Blok 3.2/N3 — dubbele concepten + zombies (LIVE, migratie `s221_ai_draft_intent_step`).**
Concepten misten intent + stap-koppeling. Nu: `generate_unified_draft` geeft een bestaand
open concept terug i.p.v. een tweede (betaalde) generatie (next_step→zaak+stap,
reply→zaak+bron-mail, free_compose→nooit); `move_case_to_step` gooit verouderde 'volgende
stap'-concepten weg (net als de adviezen in S220). Auto-conceptroute kreeg dezelfde koppeling.
Tests: 3 dedupe + 1 discard + de S220-supersede-suite groen (72 in de bredere run).

**Blok 4 — classificatie direct ná mailsync (LIVE).** De losse 6-min-cyclus draaide soms nét
vóór de sync klaar was → verse mail wachtte een ronde (~7,5 min). Nu triggert de sync bij
nieuwe mail meteen `classify_new_emails` (idempotent, sleutel-guard). Latency → ~5 min.

**Blok 4.3 — begrip-eerst antwoordroute + testronde-script (LIVE + BEWEZEN op prod).**
`_REPLY_PROMPT` herschreven naar spelregels (feiten ALLEEN uit dossier, geen toezeggingen,
escaleren bij lastige gevallen) i.p.v. sjabloon-dwang; de reply-context krijgt nu
opdrachtgever/debiteur/openstaand/vorderingen mee (`_build_dossier_facts`). Nieuw
`backend/scripts/ai/antwoord_testronde.py`: vaste proefset + corrector-AI + rapport, verstuurt
niets, raakt geen echte dossiers (analyse/iteratie = Fable S222). **Prod-rookproef (de casus
IN100607 "wie zijn jullie"): AI noemt kantoor + opdrachtgever (LegalWork B.V.) + debiteur,
gebruikt alleen echte dossierbedragen; corrector alle checks groen, 0 zware fouten.**

**Blok 4 punt 11 — geen scheve bedrag-kolommen (LIVE).** Beide AI-prompts sturen nu weg van
spatie-uitgelijnde kolommen naar gelabelde regels ("Hoofdsom: € 3.500,00"). Échte HTML-tabellen
vergen aanpassing van het render/opschoon-pad (injectie-oppervlak) → bewust apart gelaten.

**Blok 5 — UX (LIVE).** Intake uit de zijbalk + commando-palet (Mail-tab "Aanvragen" is de
ingang); menu+paginakop "Bankimport" → "Betalingen"; rapportage-label "Incasso-ratio" →
"Geïnd op lopende zaken" + uitleg-tooltip; dossiernummer klikbaar in de mail-LIJSTrij.

### Gewijzigde bestanden
Backend: `dashboard/router.py`, `ai_agent/{models,unified_draft_service,incasso_email_prompts}.py`,
`incasso/{service,automation_service}.py`, `workflow/scheduler.py`, migratie
`s221_ai_draft_intent_step`, `backend/scripts/ai/antwoord_testronde.py` (nieuw). Tests:
`test_workflow.py`, `test_unified_draft_service.py` (+4), `test_supersede_recommendations.py` (+1).
Frontend: `hooks/use-workflow.ts`, `taken/page.tsx`, `layout/app-sidebar.tsx`, `command-palette.tsx`,
`betalingen/page.tsx`, `rapportages/page.tsx`, `correspondentie/page.tsx`.

### Bekende issues / bewust niet gedaan (→ S221b/S222)
- **NIET gedaan:** review-scherm (classificatie+concept naast elkaar), voortgangsindicator bij
  genereren, échte HTML-tabellen, Blok 5-rest (tijdlijn-mailregel klikbaar, agenda lege staat,
  soft-delete-banner, follow-up dossierlink/dagen-kolom/sorteerbare koppen, intake-detectie
  dempen), Blok 6-beslismemo b2b/b2c.
- **GATED:** auto-concept per categorie (Verweer + Algemene/overig) — bewust NIET aangezet;
  hangt aan de kwaliteit van de antwoord-route → pas ná de testronde (Fable S222).
- **Sjabloon-herzaaiingen — GEDAAN (GO + visueel getest, prod-reseed):**
  (1) Font: de terugval was **Cambria** (niet Courier — die stijl is dood), waardoor sectie-
  kopjes een ander lettertype hadden dan de tekst. Thema-body op **Calibri** gezet in alle 8
  DOCX (`scripts/fix_template_default_font.py`); reseed via `scripts/reseed_builtin_templates.py`.
  ⚠️ Server-render (LibreOffice) maskeerde het verschil al; de winst is vooral zichtbaar als het
  Word-bestand zélf geopend wordt. (2) Verzoekschrift-bijlage: NIET vervangen door de blanco PDF
  (die is leeg → geen bedragen). Keuze Arsalan = **ingevuld mét logo**. Root cause: het invulbare
  sjabloon had nooit een logo; LibreOffice behoudt briefhoofd-logo's wél. KESTING LEGAL-logo
  (image2.png uit Lisanne's origineel) als briefhoofd toegevoegd; alle 62 velden + huidig adres
  blijven. docxtpl-render + PDF **visueel geverifieerd**: logo + ingevulde bedragen + één lettertype.
  Prod DB byte-identiek aan schijf (45658). Back-up: `/root/backup_managed_templates_pre_s221_font.sql`.
- **Open vraag lettertype:** in mijn tests is elke boodschap al één lettertype; als Arsalan het
  mengsel ergens specifieks zag (mail/scherm), schermafbeelding nodig om precies dát te fixen.
- **Verzoekschrift EXACTE opmaak (→ verse sessie, keuze Arsalan):** hij wil Lisanne's PDF-lay-out
  (crème-balk + logo) precies, per zaak ingevuld. Haar bron is een BaseNet-merge-sjabloon (38
  Velocity-velden, loops, keuze-logica) → omzetten naar Luxis docxtpl. Volledig onderzoek +
  mapping + valkuilen in `docs/sessions/PLAN-verzoekschrift-exacte-nabouw.md`. Huidige logo-versie
  blijft intussen live als tussenoplossing.
- **Backfills 3.3** blijven Fable (S222): uitzoeken wát de 470 classificaties/14 intake/8
  concepten/3 adviezen precies zijn vóór er iets gesloten wordt.
- Terugzet-knop/undo-toast (3.4) + maillijst-chip zijn typecheck- + deploy-geverifieerd, niet
  live doorgeklikt (Playwright-browserlock) — meenemen in de visuele Fable-review.
- MAILSLOT OPEN — testdossier 2026-00006 = Arsalans gmail.

### Volgende sessie
Fable-review S220+S221 (VERPLICHT) + antwoord-testronde met de goud-set draaien
(`python -m scripts.ai.antwoord_testronde --goud N --tenant-id <uuid> --out ...` op prod).
Daarna S221b (Opus) voor het restant hierboven. KvK-backfill zodra de sleutel er is (~22 juli).

## Sessie 220 (15 juli 2026 avond, Opus — bouwsprint demolijst, Blok 1/2/3.1/5-fasebalk LIVE)

### Samenvatting
Uitvoersprint op het S219-onderzoek. Per blok: bouwen → tests → deploy via SSH →
prod-verificatie. 9 commits, backend+frontend meermaals gedeployd, 1 prod-DB-mutatie
(stap-teksten) met dry-run + GO Arsalan + natelling. Elk stuk apart getest.

**Blok 1 — verzendpad-fundament (hoofdvondst N1), LIVE + BEWEZEN op prod.** De
primaire verstuurknop (`/compose/send`) ging via het persoonlijke account van de
klikker en legde niets vast. Nu: kantoor-afzender-vangrail (incasso@, patroon B13) +
vastlegging via gedeelde `write_outbound_log` (EmailLog + SyncedEmail + CaseActivity);
`send_with_attachment` gebruikt dezelfde functie; documents-send kreeg de ontbrekende
`send_as_tenant_account=True`. **Testmail op prod (naar Arsalans gmail, GO): from =
incasso@, EmailLog+SyncedEmail+activiteit aangemaakt — bewezen.** Plus: BCC door de
hele keten (schema/providers/.eml/dialog) + CC-verlies-fix; brieftype-afleiding uit de
stap op de AI-concept-route (punt 1/25 — renteoverzicht gaat nu mee, geen factuur);
bijlage-preview-endpoint + "Gaat automatisch mee"-weergave (punt 2); 'sommatie' aan de
rente-set (punt 3); gedeelde onderwerp-bouwer op alle server-routes (punt 5).

**Blok 2 — stap-teksten & sjablonen, LIVE.** De 6 DB stap-mailteksten opgeschoond
(script `scripts/sanitize_step_templates.py`, idempotent, dry-run+GO): oud adres
IJsbaanpad 9 / 1076 CV → Willem Fenengastraat 16E / 1096 BN, kesting@ → incasso@ (beide
kolommen; HTML gebruikte `&nbsp;` → tweede ronde nodig, natelling daarna schoon), aanhef
ingevuld bij de 3 met een losse komma. **Vanaf nu dragen alle AI-concepten het juiste
adres.** Code-sjablonen: aanhef overal "Geachte heer, mevrouw," (keuze Arsalan), BV-naam
uit de aanhef, klant-kenmerk niet meer naar de debiteur (DF138-05), html_renderer-aanhef.

**Blok 3.1 — zombie-opruiming, LIVE.** `move_case_to_step` sluit nu openstaande PENDING
follow-up-adviezen automatisch (nieuwe status SUPERSEDED) → geen dubbel-verstuur-risico
en de scanner is weer vrij (punt 13). Het uitvoerende advies is op dat moment APPROVED,
dus onaangeroerd.

**Blok 5 — fasebalk (punt 14), LIVE.** De 5-vinkjes-balk (vinkte alle categorieën links
af) vervangen door: stapnaam + categoriekleur + "X dagen in deze stap" (step_entered_at
nu in de case-respons) + volgende stap.

**Blok 4.5 — timeout Eerste→Tweede 7→4 (punt 15), GEDAAN op prod.** step_transitions
id 44c31bf7… condition `{"days": 4}` (GO Arsalan; stap-wachttijd + workflow = 4).
Data-only, geen deploy. **Beslissingen S221 (Arsalan):** backfills NIET zelf uitvoeren
→ Fable zoekt eerst uit wat de items zijn; auto-concept AAN voor Verweer + Algemene/overig
maar PAS ná de begrip-eerst-antwoord-route (nut hangt af van antwoordkwaliteit).

### Gewijzigde bestanden
Backend: `email/{compose_router,send_service,subject,providers/*}.py`, `documents/{router,
schemas,docx_service}.py`, `incasso/{service,html_renderer}.py`, `ai_agent/{followup_service,
followup_models}.py`, `collections/compliance.py`, `cases/schemas.py`,
`scripts/sanitize_step_templates.py` (nieuw). Frontend: `email-compose-dialog.tsx`,
`zaken/[id]/{page,components/DossierHeader,components/DocumentenTab}.tsx`,
`correspondentie/page.tsx`, `hooks/{use-documents,use-cases}.ts`. Tests: 5 bestanden
(rente_bijlage_verzendpaden uitgebreid, email_subject, supersede_recommendations nieuw).

### Bekende issues / bewust niet gedaan (→ S221)
- Blok 3.2 (dedupe: bestaand concept tonen i.p.v. tweede maken — `ai_drafts` mist stap-
  koppeling), 3.3 (backfills: 3 verouderde adviezen + 470 pending classificaties + 14
  intake-ruis + 8 verouderde concepten — GO nodig), 3.4 (skipped-taken weergave + herstel).
- Blok 4 (AI-keten): classificatie direct na sync; auto-concept-categorieën (BESLISSING
  Arsalan); antwoord-route begrip-eerst + testronde-script; timeout Eerste→Tweede 7→4 (GO);
  review-scherm. AI-concept-HTML-tabellen (punt 11) hoort hier.
- Blok 5-UX-rest: zaaknummer klikbaar in maillijst, tijdlijn-mailregel klikbaar,
  S218-restanten (menu Intake weg, Bankimport→Betalingen, ratio-label, agenda lege staat,
  soft-delete-banner, follow-up dossierlink/dagen/sort).
- Blok 6: beslismemo b2b/b2c (105 dossiers uit BaseNet-XML) — geen code.
- Deferred prod-mutaties: Courier→Calibri (DOCX-reseed), verzoekschrift-bijlage vervangen
  door de juiste PDF uit de projectmap. Beide sjabloon-herzaaiingen (S210-flow).
- MAILSLOT OPEN — geen echte debiteuren mailen; testdossier 2026-00006 = Arsalans gmail.

## Sessie 219 (15 juli 2026 avond, Fable — demolijst-onderzoek, read-only, ALLE punten onderzocht)

### Samenvatting
Elk demolijst-punt tot op de bodem uitgezocht (prod-DB read-only, code, logs, live
API-render) + een eigen "demoronde": elk demopunt veralgemeend naar een faalpatroon en
daarop breed gejaagd. Volledige metingen: `docs/sessions/S219-onderzoek.md`; status per
punt bijgewerkt in `DEMOLIJST-S218.md`; bouwdraaiboek: `PROMPT-S220.md` (6 blokken).
KvK-voorrang-check gedaan: sleutel duurt nog ~een week (Arsalan).

**Hoofdvondst (N1) — de compose-verstuurknop (dé route van de echte Bayar-sommatie):**
(a) verstuurt via het persoonlijke account van de klikker (voorkeur outlook → seidony@
i.p.v. incasso@; vangrail B13 bestaat alleen op batch/follow-up; zelfde gat op het
document-verzendpad) en (b) legt NIETS vast (geen EmailLog/SyncedEmail/CaseActivity) →
de verstuurde sommatie is onvindbaar in Luxis. Bewijs: mail nergens in synced_emails,
niet in incasso@-INBOX.Sent (sync leest die map), IN100613 heeft alleen pipeline-activiteiten.

**Punt 6/7 (oud adres/handtekening) — bron gevonden:** kantoor-instellingen zijn al
goed; Word- en code-mailsjablonen renderen vers correct (live geverifieerd). Het rot zit
in de 6 stap-mailteksten in `incasso_pipeline_steps` (letterlijke BaseNet-kopieën met
"IJsbaanpad 9" + kesting@) — de AI-prompt kopieert de footer trouw → álle 10 AI-concepten
oud adres (ook verse van 15-07); de verstuurde Bayar-mail had oud adres + kesting@.
Plus: verzoekschrift-bijlage-Word (Lisanne-origineel) hardcoded IJsbaanpad; verzoekschrift-
DOCX hardcoded oud Rabo-derdengelden-IBAN + kosten (beslispunt Lisanne).

**AI-keten gemeten:** echte casus mail→verweer-concept = 7,5 min automatisch (sync 5' +
classificatie 6' + race); handmatige generatie 39 s ($0,07, sonnet, prompt 41k tekens,
geen UI-voortgang → dubbelklik-concepten); auto-concept staat bewust UIT voor alles
behalve verweer (orchestrator.py:78); 470 pending classificaties (import-backfill) +
348 ongelezen notificaties maken wachtrijen onbruikbaar. Punt 21 ("wie zijn jullie"):
geclassificeerd als ongemotiveerde betwisting → standaard-weerlegging zonder klantnaam.

**Fasebalk (punt 14) bewezen:** `isPast = index < currentPhaseIndex` vinkt alle fasen
links van de huidige af, doorlopen of niet; "administratief" is geen fase. Clio/Smokeball
tonen status als label/milestone + tijd-in-fase. Voorstel: stapnaam + dagen-in-stap.

**Nieuwe vondsten demoronde:** (N3) zombie-concepten — IN100613 heeft 2 open "Eerste
sommatie"-concepten terwijl de zaak op Tweede staat (dubbel-verstuur-risico met oud
adres), IN100521 2 identieke; (N4) zes stille ruis-wachtrijen (470/348/79/14/3/18);
route×waarborg-matrix: 14-dagenbrief-gate + mailslot overal gedekt, afzender-vangrail
en logging niet. Kleinere punten: BCC bestaat nérgens in de keten; CC-veld verliest
niet-gecommitte invoer stil; taak IN100607 bestaat nog (status skipped, geen weergave/
herstelknop, 18 taken zo onzichtbaar); timeout 7-vs-4 bevestigd in step_transitions.

### Gewijzigde bestanden
Alleen docs: `docs/sessions/S219-onderzoek.md` (nieuw), `docs/sessions/PROMPT-S220.md`
(nieuw), `docs/sessions/DEMOLIJST-S218.md` (status per punt), SESSION-NOTES, roadmap.
PROMPT-S217/S218 → `docs/archief/prompts/`. Geen code, geen prod-mutaties, niets verstuurd.

### Bekende issues
- De 8 open AI-concepten dragen allemaal het oude adres — NIET versturen vóór S220 blok 2/3.
- Beslispunten: ✅ derdengelden-IBAN (Rabo = stichting, klopt) + ✅ kosten verzoekschrift
  (kloppen) — beantwoord door Arsalan 15-07. Nog open: aanhef-stijl; welke categorieën
  auto-concept aan.
- Punt 21-richting aangepast (Arsalan 15-07): géén vaste antwoord-typen bijbouwen —
  antwoord-route wordt begrip-eerst (AI leest mail + dossier en schrijft zelf het antwoord,
  met spelregels; typen/bibliotheek = referentie). Verwerkt in PROMPT-S220 blok 4.3.
- From-adres Bayar-mail = afleiding (code + afwezigheid in incasso@-Sent); sluitstuk =
  blik in Arsalans M365 Verzonden-map. CC-verlies = code-hypothese, in S220 testen.

### Volgende sessie
S220 (`docs/sessions/PROMPT-S220.md`, Opus): 6 blokken — verzendpad-fundament (vangrail+
logging+brieftype-afleiding+CC/BCC+onderwerp-bouwer), stap-teksten saneren, zombie-
opruiming, AI-keten sneller, fasebalk+UX-rest, beslismemo b2b/b2c. KvK-backfill voorrang
zodra sleutel binnen (~22 juli).
