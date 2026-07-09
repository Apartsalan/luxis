# Doorlichting D-B — Kern-motor: Relaties, Dossiers, Incasso, Follow-up, Intake

**Sessie:** 9 juli 2026, Fable, 100% read-only (geen mutatie op prod; alleen queries,
code-lezen en doorklikken in de ingelogde app als seidony@).
**Onderdeel van:** `docs/plans/PLAN-doorlichting-menu.md` (kijk-sessie 2 van 3).
**Methode:** per onderdeel 3 lagen — techniek (5 vragen), partner-blik, UX/UI.
Elke bewering hieronder is deze sessie gemeten (query/code/klik), tenzij expliciet
"niet geverifieerd". Nul consolefouten in de hele klikrondgang.

---

## 0. Belangrijkste vondsten (samenvatting)

| # | Vondst | Ernst |
|---|--------|-------|
| 1 | **"Uitvoeren" op Follow-up is kapot voor 10 van de 13 openstaande aanbevelingen én maskeert de fout**: stap-sjabloonsleutels `sommatie_drukte`/`faillissement_dreigbrief` zijn e-mailsjablonen, maar het uitvoerpad probeert er een Word-brief mee te renderen — die sleutels bestaan in géén van beide DOCX-registers (9 beheerde + 8 disk-sjablonen nagekeken). De fout wordt gevangen en de aanbeveling wordt tóch "Uitgevoerd" gemarkeerd; er gaat niets de deur uit. Zelfde kapotte keten in de Incasso-batch "Document genereren" (die meldt de fout wel netjes per zaak). Alleen 'aanmaning' (Tweede sommatie) zou werken. | HOOG (kernflow) |
| 2 | **Dossierstatus is op prod onwijzigbaar en de "Volgende stap"-knoppen op élk dossier zijn kapot**: de status-workflow-engine is leeg (0 statussen, 0 transities, 0 regels — exact geteld), elke statuswijziging faalt backend-side met "Status bestaat niet". De UI toont wel hardcoded knoppen ("14-dagenbrief", "Afgesloten") → klik = foutmelding. Statusfilter op de Dossiers-lijst is een lege dropdown (608 zaken niet te filteren op de 18 open). `date_closed` wordt nooit gezet. | HOOG |
| 3 | **Verjaring is óók in het dossier zelf onzichtbaar/misleidend**: de badge in de dossier-kop rekent vanaf de *openingsdatum van het dossier* i.p.v. de verzuimdatum van de oudste vordering (IN100015: badge zou pas jan 2030 alarmeren, echt verjaard okt 2025) én verbergt zich op afgesloten zaken. Daarnaast heeft de (wél juist rekenende) monitor een blinde vlek: hij skipt zaken mét `date_closed` → **IN100016 (verjaart 23-09-2026, €16.020) is voor het hele systeem onzichtbaar**; IN100064 (jun 2027, €37.002) idem. Samen met D-A #1 (eigenaarloze taken onzichtbaar) is er nu géén enkele werkende verjaring-signaalroute. | HOOG (geld/juridisch) |
| 4 | **13 actieve betalingsregelingen (0/121 termijnen betaald), 12 op afgesloten zaken buiten elke werkstroom**: eerstvolgende termijnen 9 juli (IN100019, VANDAAG), 12 juli (IN100215), 13/15/18 juli… Alleen zichtbaar op dossier-detail (Betalingen-tab) en via het S182-alarm *achteraf* bij een gemiste termijn — er is geen vooruitblik, en de meldingenbel verzuipt al in classificatie-spam (D-A). | MIDDEN→HOOG |
| 5 | **Pipeline-datavervuiling**: 32 stappen in de DB waarvan 17 inactief (16 relieken sort 100-115 + de bekende dubbele "Eerste sommatie"); 29 transities waarvan het merendeel inactief is of naar inactieve stappen wijst — inclusief 2 nog wél actieve regelingsovergangen die naar ináctieve stappen wijzen; de echte regelingstappen (Treffen/Bijhouden regeling) hebben géén transities. `case_step_history` bevat 1 rij (testdossier) → Staphistorie-tab is leeg op alle echte zaken. | MIDDEN |
| 6 | **"AI-suggestie"-badge op alle 18 werkstroomrijen + ruis in het dossier-actieblok** — beide gevoed door het classificatie-eiland (alle 394 classificaties eeuwig "pending", D-A #3): badge = "zaak heeft een pending classificatie" → permanent aan, betekenisloos. Dossier-feed toont "Antwoord geclassificeerd — Categorie: niet_gerelateerd" met een "Antwoord opstellen"-knop. | MIDDEN |
| 7 | **Intake werkt technisch maar heeft nog nooit een echt dossier opgeleverd**: 7 aanvragen ooit, alle test/ruis (5× eigen testmail, 1 doorstuur van bestaande zaak, 1 afgewezen), 0× dossier aangemaakt. Detectie draait elke 7 min en is sinds de S188c-fix gezond. Verdict: aangesloten, wacht op echt gebruik. | INFO |
| 8 | **Relaties is het gezondste onderdeel** — volledig CRUD, AV-versiebeheer, delete-guard. Randjes: adressen plakken aan elkaar ("Johan de Wittlaan 32517 JR"), 23/1169 heeft een telefoonnummer, geen onderscheid opdrachtgever/debiteur in de lijst, en de kolom "Aangemaakt" is na de import overal 03-07-2026. | LAAG |

---

## 1. Relaties

### Techniek
- **Doet het het?** Ja. Lijst (zoeken/sorteren/filteren/bulk), detail, bewerken, AV-versies
  (upload/download/bewerk/verwijder, met versie-selectie op factuurdatum), verwijder-guard
  (blokkeert als relatie aan actief dossier hangt — `relations/service.py::delete_contact`).
  Geen consolefouten.
- **Gebruikt?** Ja — 1169 contacten (815 bedrijven, 354 personen, alle van de BaseNet-import
  3 juli). 596 in gebruik als debiteur, 16 als cliënt, **557 (48%) hangen aan geen enkel
  dossier** (heel BaseNet-CRM is meegekomen, incl. banken/advocatenkantoren). 8 AV-versies
  bij de 8 opdrachtgever-relaties — de motor onder de rente-resolver (S173) draait hierop.
- **Verbonden of eiland?** Verbonden: cases (client/wederpartij), AV→rente, mail-koppeling
  (afzender→relatie→dossier). **Ongebruikte sublagen**: `contact_links` 0 rijen (contactpersoon-
  koppeling bestaat in UI maar nooit gebruikt), KYC/WWFT 0 rijen (achter module-vlag, bewust
  slapend), conflict-check-endpoint (alleen aangeroepen vanuit de dossier-wizard).
- **Verdict: houden.** Datakwaliteit-opruiming is een BaseNet-erfenis, geen bouwfout.
- **Missen we iets?** Telefoonnummers (23/1169) — BaseNet had ze mogelijk wel (fase 1b-contactlinks
  bewust overgeslagen); relevant zodra Lisanne wil bellen vanuit Luxis.

### Partner-blik
Voor een incassokantoor zijn er twee soorten relaties: ±8 opdrachtgevers (de klanten) en
~600 debiteuren. De lijst behandelt ze identiek — je kunt nergens "mijn opdrachtgevers" zien,
en op een debiteur-detail staan klant-labels ("Facturen van deze klant", AV-upload). Clio/
BaseNet kennen relatietypes/labels. **Kans:** rol-kolom of filter (opdrachtgever/debiteur/
overig, afleidbaar uit de dossierrollen) + dossierteller in de lijst; de "Aangemaakt"-kolom
mag daarvoor wijken.

### UX/UI
- Adres-weergave plakt straat+postcode+plaats aan elkaar zonder scheiding:
  "Johan de Wittlaan 32517 JR 'S-GRAVENHAGE" (elke relatie-detail, cosmetisch maar overal).
- Notities tonen rauwe importcodes "[BaseNet-import] rcode=100686 systemid=27106816" —
  acceptabel als herkomst-spoor, geen mensentaal.
- Bulk-verwijderen doet 1 API-call per relatie (traag bij grote selecties); nette waarschuwing
  + guard aanwezig.

## 2. Dossiers

### Techniek
- **Doet het het?** Grotendeels. Lijst (608, zoek/sort/CSV-export), detail met 11 tabs,
  vorderingen/rente op de cent (IN100598: €600,23 + €181,20 + €0 — gelijk aan het
  S188b-ijkpunt), partijen-links, correspondentie, notities. Geen consolefouten. Maar:
  - **Statuswijziging kan niet**: `workflow_statuses`/`workflow_transitions`/`workflow_rules`
    zijn alle drie leeg (exact geteld). `execute_transition` → `get_status_by_slug` →
    "Status bestaat niet" voor élke doelstatus. De "Volgende stap: 14-dagenbrief /
    Afgesloten"-knoppen op elk open dossier komen uit een hardcoded fallback
    (`DossierHeader.tsx::NEXT_STATUSES`) en zouden bij klik een foutmelding geven
    (niet geklikt — schrijfactie; bewijs is code + lege tabellen). Statusfilter op de
    lijst: lege dropdown. `date_closed` wordt nooit gezet (172 zaken hebben er één —
    allemaal import-artefact).
  - **VerjaringBadge rekent fout**: basis = `date_opened` + 5 jaar i.p.v. oudste
    verzuimdatum (`claims.default_date`, zoals de backend-monitor sinds audit #83 wél
    doet). Gemeten verschil: IN100015 badge-datum 02-01-2030 vs echte verjaring
    15-10-2025 — ruim 4 jaar. Bovendien return null bij status betaald/afgesloten →
    voor de huidige portefeuille toont de badge nooit iets (0 open zaken binnen 90d
    op badge-basis).
  - "Openstaand" heeft twee definities: lijst = hoofdsom−betaald (IN100598 €44.609,73),
    detail/sidebar = incl. rente+kosten (€52.082,62).
- **Gebruikt?** Ja — het kernscherm. 608 zaken (590 afgesloten-parkeerstand, 18 open),
  1563 vorderingen op 603 zaken, 255 betalingen op 135 zaken, 2619 dossierstukken op
  596 zaken.
- **Verbonden of eiland?** Sterk verbonden (relaties, claims, betalingen, mail, pipeline,
  derdengelden). **Dode sublagen**: `case_parties` 0 (extra-partijen-feature ongebruikt),
  procesgegevens-blok (rechtbank/rechter/kamer) 0× gevuld, `case_activities` 2 rijen
  (D-A), uren/facturen-tabs op elk dossier terwijl er 0 uren/facturen bestaan.
- **Verdict: houden + repareren** (status-systeem is het beslispunt, zie B3).

### Partner-blik
Het dossierscherm zelf is van professioneel niveau (fase-balk, stap-kiezer, financieel
blok, AI-concept-knop, sneltoetsen). De pijn zit in de dubbele werkelijkheid die de
verbindingskaart al benoemt: `case.status` (dood, onwijzigbaar) naast `incasso_step`
(levend). Een advocaat vraagt "welke zaken zijn open?" — dat kan nu alleen via de
Incasso-werkstroom, niet via de Dossiers-lijst. Kies: status-engine seeden en koppelen
aan de pipeline, óf status reduceren tot een simpel open/gesloten-veld dat de pipeline
volgt. Concurrenten (BaseNet, Kleos) hebben één statusbegrip per dossier.

### UX/UI
- Kapotte knoppen prominent in beeld ("Volgende stap") = vertrouwensschade wanneer
  Lisanne ze ontdekt.
- Interne slugs zichtbaar: sidebar "Debiteur: b2b", statusbadge "nieuw"/"afgesloten"
  in kleine letters op de lijst.
- Debiteurnotities tonen rauwe importregel; "Wat moet u doen?"-blok toont
  classificatie-ruis (zie §3/6).
- Auto-timer-optie ("Timer gestart voor…" bij elk dossier openen) staat gelukkig
  standaard uit; uren/factuur-knoppen ("Uren loggen", "Factuur") staan wel vast in de
  actiebalk — zelfde dood-gewicht-thema als D-A #4.

## 3. Incasso

### Techniek
- **Doet het het?** De werkstroom-lijst wel: 18 zaken, wachtrij-tabs ("Alle 18", "Klaar
  voor volgende stap 5", "14d verlopen 0", "Actie vereist 8"), lijst/per-stap-weergave,
  deadline-stippen, batch-selectie met pre-flight-dialoog. Stappen-beheer (15 actieve
  stappen) werkt. Maar het **brief-verstuurpad is kapot**:
  - Stap "Eerste sommatie" heeft `template_type='sommatie_drukte'`, "Verzoekschrift
    faillissement" heeft `faillissement_dreigbrief`. Dat zijn sleutels uit de
    **e-mail**-sjabloonbibliotheek (`email/incasso_templates.py`). Zowel de batch-actie
    "Document genereren" (`incasso/service.py:1230`) als Follow-up-"Uitvoeren"
    (`followup_service.py:406`) roepen er eerst `render_docx()` mee aan — en die kent
    alleen de 9 beheerde DOCX-sjablonen + 8 disk-sjablonen (beide registers exact
    nagekeken: geen van beide sleutels komt voor) → `NotFoundError` vóór de e-mailstap
    ooit bereikt wordt. Alleen 'aanmaning' (Tweede sommatie) bestaat in beide werelden.
    Consistent hiermee: `email_logs` = 0 en `generated_documents` = 0 — dit pad is
    sinds de schone lei nooit succesvol gelopen. (Niet live geklikt; zou echt versturen.)
  - Het gezonde alternatief bestaat en is bewezen: per-dossier "Concept genereren"
    (AI-concept met huisstijl) + versturen + `advance-after-send` — de route van de
    verweer-flow (2 concepten klaar voor IN100458/483).
- **Gebruikt?** Sinds S188b: ja — 15 zaken in de pipeline, 3 proefzaken bewust zonder stap
  (tonen als stap "Geen" met misleidende dagtellers 540d/381d/168d — geteld vanaf
  openingsdatum).
- **Verbonden of eiland?** De pipeline zelf is verbonden (taken, AI-concepten, verweer-flow,
  timeout-regels S182). Vervuiling eromheen: 17 inactieve stappen en dode transities in de
  DB (onzichtbaar in de UI, dus ook niet op te ruimen via de UI); 2 actieve
  regelingsovergangen wijzen naar ináctieve stappen terwijl de echte regelingstappen géén
  overgangen hebben; `case_step_history` 1 rij → Staphistorie-tab leeg op alle echte zaken.
- **Verdict: repareren (verstuurpad) + opschonen (relieken).**
- **Missen we iets?** De 13 betalingsregelingen (121 termijnen, 0 betaald) leven volledig
  búiten dit scherm: 12 op afgesloten zaken, IN100215 open maar zonder stap. Eerstvolgende
  termijnen: **9 juli (IN100019 — vandaag)**, 12 juli, 13 juli, 15 juli, 2× 18 juli… Het
  S182-alarm meldt pas ná een gemiste termijn; nergens een vooruitblik.

### Partner-blik
Dit is het hart van het kantoor en het scheelt weinig: werkvoorraad-beeld is goed, de
AI-conceptroute is modern en bewezen. Maar de belofte van het scherm — "selecteer 10
sommatiezaken, verstuur in één batch" — faalt op de sjabloonkloof, precies nu er 10 zaken
in Eerste sommatie klaarstaan. Vóór de eerste echte verzendronde móet B1 opgelost, anders
ontstaat het ergste scenario: Lisanne denkt dat er brieven uit zijn terwijl er niets is
verstuurd. De vier sjabloon-opslagplaatsen (verbindingskaart "bekende schuld") zijn hier
niet langer theoretische schuld maar een productieblokkade.

### UX/UI
- "AI-suggestie"-badge op álle 18 rijen (gevoed door eeuwig-pending classificaties) —
  een signaal dat altijd aan staat is geen signaal.
- Wachtrij-benaming is goed NL; deadline-stippen zonder legenda.
- Stappen-beheer toont de sjabloonnamen netjes ("Sommatie (drukte)") maar verhult dat
  het e-mail- en geen briefsjablonen zijn — de kolom heet "Briefsjabloon".

## 4. Follow-up

### Techniek
- **Doet het het?** De lijst wel (13 aanbevelingen, status-tabs, urgentie). Het hart —
  de "Uitvoeren"-knop (approve-and-execute in één klik, geen bevestiging/preview) — is
  voor 10 van de 13 kapot (zie §3). Erger: `execute_recommendation` vangt de sjabloonfout
  en zet de aanbeveling alsnog op **"Uitgevoerd"** met de fout weggestopt in
  `execution_result` → de rij verdwijnt uit "Openstaand" en niemand ziet dat er niets is
  verstuurd. De 3 "Handmatige beoordeling"-aanbevelingen (escalate) maken een taak aan
  mét eigenaar (`case.assigned_to_id`) — die werken.
- **Gebruikt?** Nog nooit een aanbeveling beoordeeld (alle 13 pending; scan draait elke
  30 min sinds 8 juli; hold/terminal-stappen worden terecht overgeslagen — verweer-zaken
  staan er dus correct níet in). Het testdossier 2026-00001 staat er wél in (€0,00).
- **Verbonden of eiland?** Verbonden met pipeline-stappen en (indirect) Mijn Taken —
  waar D-A al vaststelde dat dezelfde 13 kaarten 1-op-1 gekopieerd staan, dáár onder een
  knop die "Akkoord" heet.
- **Verdict: repareren + ontdubbelen** (met D-A A3: één werklijst).

### Partner-blik
Het concept (advisor stelt voor, advocaat keurt) is precies goed voor deze praktijk en
Lisanne's rol. Maar één klik "Uitvoeren" = genereren + PDF + mailen zonder preview is
te zwaar voor een advocatenkantoor — zeker omdat het huidige mailpad bovendien via het
mailaccount loopt van degene die klikt (seidony=Outlook, Lisanne=incasso@) en niet vast
via de incasso-mailbox. Eén bevestigingsdialoog met "dit gaat er precies uit, via dit
adres" lost beide op. De Follow-up-pagina en Mijn Taken vertellen hetzelfde verhaal op
twee plekken met andere knopteksten ("Uitvoeren" vs "Akkoord") — kies één plek.

### UX/UI
- Tabel is helder en data-dense; urgentie-labels goed NL ("Klaar voor actie").
- "Document genereren & versturen" belooft een dubbele actie achter één klein knopje.
- Testdossier met €0,00 in de lijst ondermijnt de geloofwaardigheid van de advisor.

## 5. Intake

### Techniek
- **Doet het het?** Ja (S187/S188-werk): lijst met status-tabs, vertrouwen-labels
  (Aanbevolen/Mogelijk/Onzeker), batch-goedkeuren op de te-beoordelen-tab, detailpagina
  met AI-uittreksel + bron-mail + Goedkeuren/Afwijzen (S188 live bewezen incl. afwijzen).
  Detectie elke 7 min, alleen mail van bekende opdrachtgevers (S188c-fix).
- **Gebruikt?** Technisch ja, inhoudelijk nee: 7 aanvragen ooit — 5 eigen testmails,
  1 doorstuurmail van een bestáánde zaak (Incassocenter/Van Brummelen — terecht laag
  vertrouwen), 1 afgewezen. **0 dossiers ooit via intake aangemaakt** (`created_case_id`
  overal leeg). De 6 "pending_review" zijn dus allemaal ruis die weggewerkt kan worden.
- **Verbonden of eiland?** Goed verbonden: mail → detectie → aanvraag → (goedkeuren) →
  dossier+relatie; teller in zijbalk; ook bereikbaar via Mail→"Nieuwe aanvragen" én
  "Maak dossier van deze mail". D-A-raakvlak bevestigd: de bug zit niet hier maar op
  Mijn Taken (filtert `pending`, prod heeft `pending_review` → blok altijd leeg; A2).
- **Verdict: houden, ruis opruimen, wachten op echt gebruik.**

### Partner-blik
Dit is een onderscheidende feature (geen enkele NL-concurrent maakt automatisch een
compleet incassodossier van een opdrachtgever-mail). Maar de waarde is onbewezen tot de
eerste echte aanvraag erdoorheen is. Dubbele vindbaarheid (menu "Intake" én Mail-tab
"Nieuwe aanvragen") is nu verwarrend meer dan handig — één ingang met een duidelijke
naam ("Nieuwe aanvragen") zou volstaan. De naam "AI Intake" op de pagina is jargon.

### UX/UI
- Zes testregels met "Re: SOMMATIE TOT BETALING"-onderwerpen als eerste indruk —
  opruimen (afwijzen) maakt het scherm direct geloofwaardig.
- Vertrouwen-labels zijn goed vertaald; status-tabs compleet; lege-staat netjes.

---

## 6. Losse bevindingen (bijvangst)

1. **Slim-leren-nieuws**: `learned_answers` is beoordeeld — 103 goedgekeurd / 28 afgewezen
   (131). Het vangnet uit S167/S168 heeft dus goedgekeurde voeding; de afgewezen 28 zijn
   allemaal type "overig".
2. `email_classifications.defense_type` is pas op 14 van de 394 gevuld (alleen classificaties
   van ná S174) — de 380 oude blijven typeloos zolang het eiland-besluit (A5) uitstaat.
3. De 3 proefzaken (IN100040/215/521) staan sinds S175b zonder pipeline-stap in de
   werkstroom met dagtellers 540d/381d/168d — meenemen in de volgende heropeningsbatch
   of een stap geven.
4. Follow-up-mails en batch-mails versturen via het mailaccount van de klikkende gebruiker
   (`send_with_attachment` → `get_email_account(user_id)`); huisstijl wordt wél overal
   toegepast (`ensure_branded_body`).
5. Sjabloontokens in stap-mailteksten worden bij follow-up maar op 3 vaste placeholders
   vervangen (`zaak.zaaknummer` e.d.) — andere Jinja-tokens zouden rauw in de mail komen
   (theoretisch; de HTML-sjablonen zelf renderen via de echte template-engine).

## 7. Niet geverifieerd (bewust, read-only sessie)

- "Uitvoeren"/"Afwijzen" op Follow-up en "Akkoord" op Mijn Taken — niet geklikt
  (verstuurt/muteert). De kapot-claim (#1) steunt op code + exacte registervergelijking
  op prod-data, niet op een live klik.
- "Volgende stap"-statusknoppen op het dossier — niet geklikt; faal-claim steunt op
  code (hardcoded fallback) + lege statustabellen + backend-validatiepad.
- Batch-acties (stap verzetten / document genereren / rente herberekenen) — niet
  uitgevoerd; pre-flight-dialoog niet geopend met echte selectie.
- Nieuw dossier-wizard, nieuwe relatie, bewerken-formulieren — niet ingevuld/opgeslagen.
- Of `move-step`/de actieve regelingsovergangen een zaak naar een ináctieve stap kunnen
  verplaatsen (die dan uit de werkstroom-weergave valt) — niet getest.
- "Concept genereren" op een sommatie-stap (AI-route) — deze sessie niet gegenereerd;
  eerdere sessies bewezen de verweer-variant wel live.

## 8. Werkorder-kandidaten uit D-B (voor fase 2-beslislijst)

| # | Actie | Type | Inschatting |
|---|-------|------|-------------|
| B1 | Verstuurpad sommaties repareren: `template_type` (e-mailsleutels) verzoenen met het DOCX-register — óf follow-up/batch op de e-mail/AI-conceptroute zetten, óf DOCX-sjablonen voor die sleutels maken; en een gefaalde uitvoering nooit meer als "Uitgevoerd" maskeren | fix, HOOG | middel |
| B2 | Verjaring in het dossier: badge op verzuimdatum-basis (zelfde bron als monitor) of weg; monitor-blinde vlek `date_closed` dichten (IN100016 verjaart 23-09-2026!); hangt samen met D-A A1 (alarm zichtbaar maken) | fix, HOOG | klein |
| B3 | Status-systeem beslissen: statussen+transities seeden en koppelen aan de pipeline, óf status reduceren tot open/gesloten dat de pipeline volgt; kapotte "Volgende stap"-knoppen en lege statusfilter meteen mee | beslispunt | middel/groot |
| B4 | Regelingen-vooruitblik: termijnen in de Incasso-werkstroom en/of het "Actie vandaag"-blok (D-A A4); check IN100019-termijn van 9 juli | product | klein/middel |
| B5 | Pipeline opschonen: 17 inactieve stappen + dode/verkeerd-wijzende transities weg of corrigeren; regelingstappen echte overgangen geven | opschonen | klein |
| B6 | "AI-suggestie"-badge en dossier-actieblok ontkoppelen van pending-classificaties (volgt uit A5-besluit over het classificatie-eiland) | fix | klein |
| B7 | Adres-weergave: straat/postcode/plaats met scheiding tonen (relatie-detail) | fix, cosmetisch | heel klein |
| B8 | Eén definitie van "Openstaand" (lijst vs dossier-detail) — incl. rente/kosten overal, of kolom hernoemen | fix | klein |
| B9 | Relatielijst: rol (opdrachtgever/debiteur) + dossierteller i.p.v. "Aangemaakt"-kolom | product | klein |
| B10 | Intake-ruis wegwerken (6 testaanvragen afwijzen, met akkoord) + één ingang kiezen (menu vs Mail-tab) + naam "AI Intake" → "Nieuwe aanvragen" | opschonen/product | heel klein |
| B11 | 3 proefzaken: stap toekennen of dagteller op stap-basis zetten | opschonen | heel klein |
| B12 | Staphistorie voeden (batch/SQL-heropeningen schrijven nu geen regel) of de tab verbergen tot er data is | fix/beslispunt | klein |
| B13 | Follow-up: bevestigingsdialoog met preview + vast verzendkanaal (incasso@) vóór de één-klik-verzending; ontdubbelen met Mijn Taken (D-A A3) | product, HOOG | middel |

**Volgende kijk-sessie:** D-C (Bankimport, Derdengelden, Uren, Facturen, Rapportages,
Instellingen) — prompt: `docs/sessions/PROMPT-DC-doorlichting.md`.
