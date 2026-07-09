# Doorlichting D-C — Financieel + systeem: Bankimport, Derdengelden, Uren, Facturen, Rapportages, Instellingen

**Sessie:** 9 juli 2026, Fable, 100% read-only (geen mutatie op prod; alleen queries,
code-lezen en doorklikken in de ingelogde app als seidony@).
**Onderdeel van:** `docs/plans/PLAN-doorlichting-menu.md` (kijk-sessie 3 van 3 — laatste).
**Methode:** per onderdeel 3 lagen — techniek (5 vragen), partner-blik, UX/UI.
Elke bewering hieronder is deze sessie gemeten (query/code/klik), tenzij expliciet
"niet geverifieerd". Nul consolefouten in de hele klikrondgang (alle 6 pagina's + 5
instellingen-tabs).

---

## 0. Belangrijkste vondsten (samenvatting)

| # | Vondst | Ernst |
|---|--------|-------|
| 1 | **De hele financiële laag is nooit gebruikt, maar níét kapot**: bankimport, derdengelden, uren, facturen en Exact Online staan allemaal op exact 0 rijen ooit (elke tabel geteld). Anders dan verwacht ("meeste eilanden/relieken") zijn het géén eilanden in de code: uren voeden factuurregels, derdengelden verrekent met facturen, bankimport boekt via derdengelden een art. 6:44-betaling op het dossier. Alles is test-gedekt (aparte testbestanden per module aanwezig). Het zijn goed gebouwde machines die stilstaan. | KERN (verdict-bepalend) |
| 2 | **Bankimport is het antwoord op de regelingen-bewakingsvraag en is al af**: upload Rabobank-CSV → automatisch matchen aan dossiers → beoordelen → uitvoeren (derdengelden-storting + betaling art. 6:44), met terugdraaiknop, handmatig koppelen en "Ongekoppeld"-bak. Kesting bankiert bij Rabobank (IBAN NL20RABO…, gemeten), dus het enige ondersteunde formaat is precies het juiste. De backlog-gedachte "(a) periodieke bankexport inlezen" vergt géén bouwwerk — alleen een werkritueel (wekelijks CSV uploaden) en vondst #3 fixen. | HOOG (kans, geen bug) |
| 3 | **Derdengelden-IBAN = kantoor-IBAN**: in Instellingen → Kantoor staat op béíde velden `NL20RABO0388506520`, terwijl de UI er zelf bij zegt dat de Stichting Derdengelden een apárte rekening is (vier-ogen/Voda-context). Zolang dit zo staat, zou elke derdengelden-boeking en SEPA-uitbetaling van/naar de kantoorrekening lijken te lopen. Data-invoer, geen code — maar blokkerend vóór bankimport/derdengelden live gaan. Ook het BTW-nummer is leeg. | HOOG (vóór ingebruikname) |
| 4 | **Rapportages leeft en rekent op echte data, maar vertelt twee dingen scheef**: (a) "Geïnd € 0,00 / incasso-ratio 0,0%" — de teller kijkt alleen naar nú lopende zaken (total_paid = 0 op alle 18), terwijl er €311.547,70 aan echte betalingen in het systeem staat (255 stuks, 2022–mei 2026); (b) de faseverdeling toont 15 van de 18 actieve zaken — de 3 stap-loze proefzaken (IN100040, IN100215, IN100521 — exact gemeten) vallen weg door een inner join, terwijl het KPI-blok ernaast ze wél als "Geen stap" telt. Gem. doorlooptijd "95 dagen" komt uit de 172 zaken met een sluitdatum (BaseNet-import). | MIDDEN |
| 5 | **Uren-pagina: relatiefilter laadt alle 1169 relaties** (debiteuren, banken, advocatenkantoren incluis) in één dropdown — onbruikbaar en traag; voor tijdschrijven zijn alleen de ±8 opdrachtgevers relevant. Verder werkt de pagina (stopwatch, week/dag/maand, declarabel-splitsing). | LAAG (nu), MIDDEN zodra uren echt gebruikt worden |
| 6 | **Instellingen is netjes op 3 punten na**: de Workflow-tab toont de lege status-engine (D-B #2) zonder enige uitleg — koppen met niets eronder; sjabloonbeheer staat dubbel (ook op Documenten, al D-A A7); en de meldingen-teller in de kop zegt "264 ongelezen" waar de database er 299 telt (alle 299 ongelezen — niemand heeft ooit een melding gelezen). | LAAG/MIDDEN |
| 7 | **Beide gebruikersaccounts heten "Lisanne Kesting"** (ook het admin-account van Arsalan/seidony@, gemeten in users) — audit-sporen ("wie deed wat") zijn daardoor niet te onderscheiden. Was al D-A A12; hier bevestigd én relevanter geworden nu er echt met twee accounts gewerkt wordt (vier-ogen-regel voor derdengelden kijkt naar het aantal actieve gebruikers). | LAAG |
| 8 | **Producten-catalogus (30 artikelen) is een klaarliggende Exact-brug**: elk artikel heeft grootboekrekening + BTW-type conform de BaseNet/Exact-inrichting (8000-serie omzet, 2010/2020 depot/derdengelden, 1950 voorschotten). Gezaaid 14 april, nooit gebruikt (0 facturen), Exact nooit gekoppeld (0 connecties, 0 synclogs). Waardevol precies op het moment dat facturatie in Luxis gaat draaien — niet eerder. | INFO |

---

## 1. Bankimport (menu "Financieel", pagina /betalingen)

### Techniek
- **Doet het het?** UI: ja — drie tabs (Matches met statusfilters, Ongekoppeld,
  Importgeschiedenis), CSV-dropzone ("Rabobank CSV-formaat"), nette lege staten, geen
  consolefouten. De volledige keten (upload → parse → match → uitvoeren) is deze sessie
  bewust níét gedraaid (zou prod muteren) — wel de code gelezen: `payment_matching_service`
  dekt import (dedup op eigen IBAN + volgnummer), automatisch matchen, goedkeuren/afwijzen/
  handmatig/alles-in-één-klik boven een zekerheidsdrempel, uitvoeren (derdengelden-storting
  + betaling die via de gedeelde art. 6:44-helper op het dossier landt) en terugdraaien
  (H16). Eigen testbestand aanwezig (`test_payment_matching.py`).
- **Gebruikt?** Nooit: `bank_statement_imports` 0, `bank_transactions` 0,
  `payment_matches` 0 (exact geteld). De 255 betalingen op prod (som €311.547,70, alle
  `payment_method='bank'`) kwamen via het S179/S180-SQL-recept — buiten deze pagina om.
- **Verbonden of eiland?** Verbonden: uitvoeren boekt derdengelden + dossier-betaling;
  de sidebar-badge telt openstaande matches. Het is de nette voorkant van precies wat
  S180 handmatig deed.
- **Verdict: houden + in gebruik nemen.** Dit ís de "(a) periodieke MT940/CSV-export"
  uit de roadmap-backlog — er hoeft niets gebouwd, alleen gevoed. Let op: alléén
  Rabobank-CSV wordt geparsed (`parse_rabobank_csv`, ander formaat → nette foutmelding);
  dat matcht met de gemeten Rabo-rekening van het kantoor.
- **Missen we iets dat er al is?** Ja — dit onderdeel zelf. De 13 actieve
  betalingsregelingen (121 termijnen, D-B #4) zijn alleen te bewaken als betalingen
  zichtbaar worden; wekelijks een CSV van de derdengeldenrekening uploaden geeft dat
  zicht zonder PSD2-koppeling.

### Partner-blik
Elke incassopraktijk heeft dit dagelijks nodig; BaseNet heeft bankkoppeling, Clio heeft
reconciliatie. Het "upload een CSV"-ritueel is voor een eenmanskantoor prima startniveau;
een PSD2-koppeling (Enable Banking/Ponto, backlog-gedachte b) is de opvolger zodra het
ritueel gaat knellen — niet eerder. **Kans:** de eerste échte upload samen met
Arsalan/Lisanne doen als proef (read-only kan niet, dus als bewuste, kleine prod-actie
met terugdraaiknop bij de hand).

### UX/UI
Strak en consistent (badge-kleuren, score-kolom, 1-klik goedkeuren+uitvoeren). Kleinigheid:
de pagina heet in het menu "Bankimport" maar de breadcrumb zegt "Betalingen".

## 2. Derdengelden

### Techniek
- **Doet het het?** Pagina: ja — samenvattingskaarten (saldo/cliënten/dossiers/wachtend op
  goedkeuring), cliëntzoek, "Mutatieoverzicht"- en "Saldolijst"-CSV-knoppen,
  SEPA-uitbetalingen-tab. Lege staat legt zelfs uit waar stortingen vandaan komen
  ("vanuit een dossier"). Achterkant (code gelezen, 3 testbestanden): stortingen,
  uitbetalingen met vier-ogen-goedkeuring, verrekening met eigen facturen (expliciete
  cliënt-toestemming per transactie), storneringen, SEPA-exportbestand, NOvA-rapportages
  (mutaties/saldolijst) — plus de FIN-2 afwikkelflow uit S170.
- **Gebruikt?** Nooit: `trust_transactions` 0 (geteld). Logisch: er is nog nooit via
  Luxis geld ontvangen of uitbetaald.
- **Verbonden of eiland?** Verbonden: bankimport stort erin, facturen verrekenen eruit,
  dossier-detail heeft de registratie-ingang.
- **Verdict: houden**; gaat vanzelf leven zodra bankimport gevoed wordt.
- **Missen we iets?** Vondst #3: het stichting-IBAN is identiek aan het kantoor-IBAN
  (beide `NL20RABO0388506520`, gemeten in tenants én zichtbaar in de Kantoor-tab).
  De tenaamstelling "Stichting Beheer Derdengelden Kesting Legal" staat er wel. Vóór de
  eerste echte boeking moet hier het échte stichting-IBAN staan — anders kloppen
  SEPA-bestanden en NOvA-lijsten niet.

### Partner-blik
Derdengelden-administratie is hét compliance-pijnpunt voor elk advocatenkantoor
(Voda art. 6.22); dat Luxis vier-ogen + zelf-goedkeuren-uitzondering voor
eenmanskantoren heeft, met de juiste juridische toelichting in de UI, is een echt
verkoopargument. De zelf-goedkeuren-vink staat aan; volgens de UI-tekst geldt met twee
actieve gebruikers (die er nu zijn: lisanne@ + seidony@) automatisch strikt vier-ogen —
of de backend dat ook afdwingt is **niet geverifieerd**.

### UX/UI
Professioneel, rustig, Nederlands. Niets aan te merken bij lege data.

## 3. Uren

### Techniek
- **Doet het het?** Ja: stopwatch (met dossierkiezer), handmatige registratie,
  dag/week/maand-weergave, weektotalen, declarabel-filter. Zwevende timerknop is
  app-breed aanwezig. Achterkant: CRUD + unbilled-lijst + samenvatting, factuurregels
  kunnen aan een uur-regel refereren (traceerbaarheid). Testbestand aanwezig.
- **Gebruikt?** Nooit: `time_entries` 0 (geteld; D-A mat al "0 in 4+ maanden", dit is
  definitief: 0 óóit).
- **Verbonden of eiland?** Verbonden met facturen (unbilled → factuurregel). Dood
  gewicht zolang facturatie niet in Luxis draait.
- **Verdict: houden maar slapend zetten** (module-vlag "tijdschrijven" uit) tót
  Lisanne in Luxis gaat declareren — zie werkorder C3. Incassozaken draaien op
  provisie/kosten, niet op uurtje-factuurtje; het dagelijkse werk mist dit niet.
- **Missen we iets?** Nee — andersom: het staat aan zonder gebruikt te worden en voedt
  de dode dashboard-widgets (D-A A4).

### Partner-blik
Voor een incasso-only praktijk is tijdschrijven optioneel (provisie-model); voor de
bredere advocatuur-doelgroep van Luxis is het wél kern. De module-vlag bestaat precies
hiervoor — gebruiken dus.

### UX/UI
Vondst #5: het relatiefilter is een kale dropdown met álle 1169 relaties, alfabetisch,
inclusief honderden debiteuren, ABN AMRO en de Belastingdienst. Moet cliënt-only (of
weg tot de module leeft).

## 4. Facturen

### Techniek
- **Doet het het?** Ja: lijst met statusfilters (concept→goedgekeurd→verzonden→(deels)
  betaald/achterstallig/geannuleerd), "Debiteuren"-tab (openstaand per relatie),
  nieuw-factuur-wizard, en in de code een complete levenscyclus: goedkeuren, versturen
  (mail), betaling registreren, annuleren, PDF, achterstallig-job, incasso-afwikkelfactuur
  (preview getest in `test_incasso_invoice_preview.py`), 6+ testbestanden.
- **Gebruikt?** Nooit: `invoices`/`invoice_lines`/`invoice_payments`/`expenses` alle 0
  (geteld). Facturatie loopt vandaag via BaseNet/Exact bij Lisanne.
- **Verbonden of eiland?** Verbonden: uren→regels, producten→regels (grootboek),
  derdengelden→verrekening, incasso→afwikkelfactuur. De meest "aangesloten" slapende
  module van de drie.
- **Verdict: houden, slapend zetten of bewust wakker maken.** Dit is een beslispunt
  voor het fase-2-gesprek: gaat Kesting factureren vanuit Luxis (dan module aan laten +
  Exact-koppeling plannen, C7) of blijft dat in BaseNet/Exact tot de overstap (dan
  vlag uit, C3)? De afwikkelfactuur ná een geïnde zaak is het eerste echte gebruiksmoment.
- **Missen we iets?** `expenses` (verschotten) bestaat als tabel maar heeft geen eigen
  UI-ingang buiten factuurregels — prima, geen actie.

### Partner-blik
"Debiteuren" als tabnaam betekent hier "cliënten die mijn facturen nog moeten betalen" —
in een incassokantoor betekent dat woord al iets anders (de wederpartij). Hernoemen naar
"Openstaand per cliënt" voorkomt spraakverwarring.

### UX/UI
Lege staat op de Debiteuren-tab zegt "Alle facturen zijn betaald" terwijl er nooit één
factuur bestaan heeft — technisch waar, feitelijk misleidend ("Nog geen facturen" is
eerlijker).

## 5. Rapportages

### Techniek
- **Doet het het?** Ja, met echte cijfers (gemeten en nagerekend): Openstaand
  €313.721,73 (klikbaar), Actieve zaken 18, Totaal 608, Achterstallige taken 2,
  Deadlines(7d) 2, faseverdeling Eerste sommatie 10 / Verweer 2 / Dagvaarding 3 met
  bedragen, maandgrafiek met klikbare maanden, periodekiezer. Bronnen kloppen met de
  eigen SQL-nameting (18 lopend / hoofdsom €248.775,70 / gem. 95 dagen over 172
  gesloten zaken).
- **Gebruikt?** Door het systeem actief onderhouden (S175b-filters zitten erin);
  menselijk gebruik is niet meetbaar (geen paginastatistieken).
- **Verbonden of eiland?** Verbonden — leest cases/payments/pipeline/workflow-taken.
  Geen relict.
- **Verdict: houden + 2 defecten fixen** (vondst #4):
  1. "Geïnd/incasso-ratio" is gedefinieerd als `total_paid` op *nu lopende* zaken →
     structureel €0/0,0% zodra afgeronde zaken dichtgaan. Zinvolle definitie voor een
     incassokantoor: geïnd per gekozen periode (som betalingen — die data is er:
     €311.547,70 over 255 betalingen).
  2. Faseverdeling gebruikt een inner join op pipeline-stap → stap-loze actieve zaken
     verdwijnen (nu de 3 proefzaken IN100040/IN100215/IN100521; het KPI-blok ernaast
     telt ze wél, als "Geen stap" → de twee blokken spreken elkaar tegen op dezelfde
     pagina: 18 vs 15).
- **Missen we iets?** Voor de 7 vaste opdrachtgevers zou een "per opdrachtgever"-snede
  (zaken/openstaand/geïnd) de eerste vraag van elke klant beantwoorden — kandidaat voor
  later, geen bouwbesluit.

### Partner-blik
Precies wat een klein kantoor nodig heeft: één pagina, geen rapportbouwer. De
"Gem. doorlooptijd 95 dagen" is nu een import-artefact (BaseNet-sluitdatums) — pas
betekenisvol na maanden echt gebruik; geen fix nodig, wel iets om bij het
fase-2-gesprek te weten.

### UX/UI
Consistent met dashboard-stijl, klikbare KPI's zijn een sterk punt. Geen consolefouten.

## 6. Instellingen

### Techniek (deze sessie geklikt: Kantoor, Modules, Workflow, Producten, Exact Online;
de overige tabs steunen op DB-metingen van vandaag en eerdere sessies — per regel benoemd)
- **Kantoor:** werkt (geklikt). Bevat vondst #3 (IBAN's identiek) en leeg
  BTW-nummer. Vier-ogen-uitleg (Voda art. 6.22 lid 8) is juridisch netjes.
- **Modules:** 5 vlaggen — incasso/tijdschrijven/facturatie AAN, WWFT/budget UIT
  (klopt met DB: `{incasso,facturatie,tijdschrijven}`). De hendel voor C3 bestaat dus al.
- **Team:** read-only sinds S179; 2 actieve gebruikers, beiden met naam "Lisanne
  Kesting" (vondst #7).
- **Workflow:** vondst #6 — "Incasso fases & statussen" en "Toegestane transities"
  renderen als koppen boven níéts (0 statussen/transities/regels, D-B #2), zonder
  lege-staat-tekst of "nog niet ingericht"-uitleg. De auto-concepten-toggle staat uit
  (klopt met DB). Automatiseringsregels: nette lege staat ("Geen regels geconfigureerd").
- **Slim leren:** draait (S172-S175-werk; 103 goedgekeurd/28 afgewezen gemeten in D-B) —
  niet opnieuw doorgelicht.
- **E-mail:** 4 accounts in DB (outlook-seidony, imap-incasso@, imap-seidony,
  basenet-import) — mail is S185-188-terrein, niet herhaald.
- **Meldingen:** tab zelf niet geklikt deze sessie; wél gemeten: teller-discrepantie
  kop (264) vs DB (299 ongelezen van 299 totaal) niet verklaard — het échte probleem blijft D-A A5/A11
  (classificatie-spam verzuipt alles).
- **Sjablonen:** dubbel met Documenten-pagina (D-A A7, bevestigd — zelfde beheer).
- **Producten:** vondst #8 — volledige catalogus zichtbaar, met "Basenet import"-knop
  en Exact-grootboektoelichting per rij.
- **Exact Online:** alleen een "Koppel Exact Online"-knop; 0 connecties, 0 synclogs
  (geteld). Bewust niet geklikt (start externe OAuth).
- **Profiel / Weergave:** niet geklikt deze sessie (laag risico, puur persoonlijke
  voorkeuren); geen metingen die erop wijzen dat er iets mis is.

### Verdict
Houden. Drie kleine ingrepen: workflow-tab een echte lege staat geven (of verbergen tot
het B3-besluit over de status-engine valt), sjablonen op één plek, meldingen-teller
kloppend maken bij de A5/A11-aanpak.

### Partner-blik
12 tabs is veel maar elk heeft bestaansrecht; volgorde is logisch. Voor een
buitenstaander is "Workflow" nu de enige tab die kapot oogt.

### UX/UI
Consistent. De tab-parameter in de URL (?tab=modules) blijft staan bij tab-wissel via
de zijnav (cosmetisch — deep-link klopt daardoor niet altijd met wat open staat).

---

## 7. Niet geverifieerd (bewust — read-only sessie)

1. De bankimport-keten eind-tot-eind (CSV uploaden → match → uitvoeren) — zou prod
   muteren. Code + tests gelezen; eerste echte upload is meteen de proef (voorstel C1).
2. SEPA-export, mutatieoverzicht- en saldolijst-download (derdengelden) — knoppen niet
   geklikt (genereren bestanden; mutatie-arm maar niet nul).
3. Factuur aanmaken/PDF/versturen — mutatie.
4. Stopwatch starten/stoppen — mutatie (schrijft time_entry).
5. Of de backend het vier-ogenprincipe echt afdwingt bij 2 actieve gebruikers terwijl
   `trust_allow_self_approval=true` staat — alleen de UI-tekst zegt dat.
6. Exact Online-koppelknop (externe OAuth-flow).
7. Waarom de meldingen-kop 264 zegt en de DB 299 ongelezen telt.
8. Menselijk gebruik van Rapportages (geen kijk-statistieken beschikbaar).

## 8. Werkorder-kandidaten D-C

| # | Werkorder | Type | Omvang |
|---|-----------|------|--------|
| C1 | Bankimport in gebruik nemen als regelingen-betaalzicht: eerste echte Rabobank-CSV van de derdengeldenrekening uploaden (kleine, bewuste prod-actie met terugdraaiknop), daarna wekelijks ritueel; koppelt aan B4 (termijn-vooruitblik). Vervangt "bankkoppeling bouwen" — die is pas nodig als dit ritueel knelt | product, HOOG | klein (ritueel, geen bouw) |
| C2 | Vóór C1: echt Stichting-Derdengelden-IBAN invullen (nu = kantoor-IBAN) + BTW-nummer aanvullen — gegevens bij Lisanne opvragen | data | heel klein |
| C3 | Beslispunt module-vlaggen: tijdschrijven + facturatie UIT (menu en dashboard-widgets verdwijnen automatisch, D-A A4 grotendeels gratis opgelost) tót er een facturatie-besluit ligt; of bewust AAN met startplan | beslispunt | heel klein |
| C4 | Rapportages: "Geïnd"/ratio herdefiniëren naar periode-betalingen (data is er: 255 betalingen, €311.547,70) + faseverdeling outer join met "Geen stap"-rij zodat 18=18 | fix | klein |
| C5 | Uren-relatiefilter: alleen cliënten tonen (nu alle 1169 relaties) — pas relevant bij activeren urenmodule, meenemen in C3-besluit | fix | heel klein |
| C6 | Workflow-tab: echte lege staat + verwijzing naar inrichting (of tab verbergen zolang status-engine leeg is) — volgt het B3-besluit | fix, cosmetisch | heel klein |
| C7 | Exact Online-koppeling activeren + producten-catalogus benutten — pas ná een positief facturatie-besluit (C3); tot die tijd bewust laten liggen | product, later | middel (extern: Exact-app-registratie) |
| C8 | Facturen-teksten: "Debiteuren"-tab → "Openstaand per cliënt"; lege staat "Alle facturen zijn betaald" → "Nog geen facturen" | fix, cosmetisch | heel klein |
| C9 | Meldingen-teller (264 vs 299) verklaren en fixen — meenemen in de A5/A11-meldingenopruiming | fix | heel klein |

---

## 9. Totaaloverzicht D-A + D-B + D-C — concept-beslislijst fase 2

Alle 34 werkorder-kandidaten (A1-A12, B1-B13, C1-C9) gebundeld tot één gesprekslijst
met Arsalan. Volgorde = voorstel, geen besluit. Verwijderen gebeurt nooit autonoom.

**Blok 1 — Repareren, hoogste prioriteit (kapot of gevaarlijk):**
- **B1** Verstuurpad sommaties (kapot voor 10/13 aanbevelingen + fout gemaskeerd) — vóór de eerste echte verzendronde, dus vóór het mailslot eraf gaat (~13 juli).
- **B2 + A1** Verjaring zichtbaar: badge op verzuimdatum, monitor-blinde vlek `date_closed`, taken met eigenaar (IN100016 verjaart 23-09-2026, €16.020).
- **B13** Verzend-vangrails follow-up (preview + vast kanaal) — hoort logisch bij B1.
- **A2** "Nieuwe Dossiers"-blok dashboard (verkeerde statusfilter, altijd 0) — heel klein.

**Blok 2 — In gebruik nemen (bestaat al, staat stil):**
- **C2 → C1** Stichting-IBAN rechtzetten → eerste bankimport-CSV → wekelijks betaalzicht op de 13 regelingen (met **B4** termijn-vooruitblik en **A8** termijnen in agenda als vervolg).
- **B11** 3 proefzaken een stap geven (verdwijnen dan ook uit de rapportage-mismatch).

**Blok 3 — Beslispunten (aan/uit/richting, samen met Arsalan):**
- **B3** Status-engine: seeden en aansluiten óf reduceren tot open/dicht (raakt kapotte knoppen, statusfilter, `date_closed`, C6).
- **A5 + B6 + A11 + C9** Classificatie-eiland: verwerk-flow bouwen óf lijn uitzetten; meldingen ontspammen.
- **C3** Module-vlaggen tijdschrijven/facturatie (lost A4-dashboardleegte grotendeels op; C5/C7/C8 volgen het besluit).
- **A3** Mijn Taken als dagstart-lijst vs pure takenlijst (samen met B13-ontdubbeling).
- **A7** Documenten: sjablonenbeheer op één plek + al dan niet documentenbibliotheek over de 2619 echte stukken.

**Blok 4 — Klein onderhoud/opschonen (met akkoord, in een veegsessie):**
- A6, A10, A12/#7 (accountnaam), B5 (pipeline-vervuiling), B7 (adres-weergave), B8 ("Openstaand"-definitie), B9 (relatielijst-rol), B10 (intake-ruis), B12 (staphistorie), C4 (rapportage-fixes), C6, C8.

**Blok 5 — Later/strategisch (bewust laten liggen tot een trigger):**
- **C7** Exact-koppeling (trigger: facturatie-besluit). PSD2-bankkoppeling (trigger: C1-ritueel knelt). **A9** activiteitenfeed. Rapportage per opdrachtgever. WWFT/budget-modules (staan al bewust uit).

**Rode draad van de drie kijk-sessies:** de rekenkern en de mail zijn gezond (S183-188);
de werkschil heeft zichtbaarheidsgaten (verjaring, taken, meldingen); de kern-motor heeft
één echt kapotte flow (verzendpad) en een lege status-engine; de financiële laag is af
maar onaangesloten. Er hoeft opvallend wéínig gebóúwd te worden — het meeste is
repareren, aansluiten of uitzetten.
