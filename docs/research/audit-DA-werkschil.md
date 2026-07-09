# Doorlichting D-A — Werkschil: Dashboard, Mijn Taken, Agenda, Documenten

**Sessie:** 9 juli 2026, Fable, 100% read-only (geen mutatie op prod; alleen queries,
code-lezen en doorklikken in de ingelogde app als seidony@).
**Onderdeel van:** `docs/plans/PLAN-doorlichting-menu.md` (kijk-sessie 1 van 3).
**Methode:** per onderdeel 3 lagen — techniek (5 vragen), partner-blik, UX/UI.
Elke bewering hieronder is deze sessie gemeten (query/code/klik), tenzij expliciet
"niet geverifieerd".

---

## 0. Belangrijkste vondsten (samenvatting)

| # | Vondst | Ernst |
|---|--------|-------|
| 1 | **Verjaringsalarmen zijn structureel onzichtbaar**: monitor werkt en vond 2 verjaarde zaken (IN100015, IN100127 — beide in de heropeningslijst, samen €14.286), maar maakt taken zonder eigenaar aan terwijl "Mijn Taken" alleen taken mét eigenaar toont. Niemand ziet ze. | HOOG (geld/juridisch) |
| 2 | **"Nieuwe Dossiers"-blok op Mijn Taken is kapot**: filtert op status `pending`, prod gebruikt `pending_review` → toont altijd 0 (Intake-teller zegt 6). | MIDDEN (bug) |
| 3 | **AI-classificatielijn is een doodlopend eiland**: 394 classificaties, álle op "pending", nooit één verwerkt; 264 ongelezen "classificatie klaar"-meldingen verzuipen de meldingenbel; dashboard-link "394 classificaties →" wijst naar een pagina die ze niet toont. | MIDDEN (reliek/ruis) |
| 4 | **Dashboard is voor ~40% dood gewicht voor dit kantoor**: uren-widget, facturen-widget, uren-zeurbanner en "vandaag gewerkt"-KPI staan allemaal op 0 — er is in 4+ maanden nooit één uur geschreven of factuur gemaakt. | MIDDEN (product) |
| 5 | **Agenda is leeg (0 afspraken ooit)** en Lisanne kán er niet mee syncen (alleen Outlook-sync bestaat; haar mail/agenda is BaseNet-IMAP). Enige inhoud = 4 taak-deadlines uit de werkstroom. | MIDDEN (product) |
| 6 | **Testdossier 2026-00001 (8 juli) staat in de echte werkvoorraad** en vervuilt teller (18 i.p.v. 17), werkstroom-widget en activiteitenfeed. | LAAG (opruimen, met akkoord) |
| 7 | "Recente activiteit" op dashboard is de facto dood: 2 regels ooit — pipeline/mail schrijven geen activiteiten. | LAAG |
| 8 | Verjaring nr. 3 komt eraan: IN100016 verjaart 23-09-2026. | INFO (meenemen in heropening) |

---

## 1. Dashboard

### Techniek
- **Doet het het?** Ja. Geen consolefouten. KPI-definities kloppen (S175b: actief =
  zonder afgesloten archief; openstaand incl. rente/BIK via dezelfde motor als dossierdetail).
- **Gebruikt?** Ja — het is de landingspagina.
- **Verbonden?** Grotendeels. Maar:
  - "Recente activiteit" leest `case_activities`: **2 rijen ooit** (beide van testdossier
    2026-00001, 8 juli). De incasso-pipeline, mail en heropening schrijven daar niets →
    feed is de facto dood.
  - "AI-suggesties"-widget: badge "407" (= 394 classificaties + 13 follow-ups). De link
    "394 classificaties →" gaat naar `/taken`, waar classificaties **niet** getoond worden
    (doodlopende link). De 3 getoonde suggesties waren alle drie "Niet gerelateerd /
    Wegzetten"-ruis.
  - KPI "1169 relaties — **1169 nieuw deze maand**": technisch juist (BaseNet-import was
    2 juli), inhoudelijk misleidend. Telt `created_at >= 1e van de maand`.
  - Kleinigheid (perf): activiteitenfeed doet 1 query per regel (20 extra queries per
    load) — `dashboard/service.py::get_recent_activity` haalt per activiteit de zaak op.
- **Verdict: houden + snoeien/repareren.**

### Partner-blik
Voor een incassokantoor met 1 advocaat is dit dashboard half raak. Wat een advocaat
's ochtends wil zien: wat moet ik VANDAAG doen (deadlines, verlopen termijnen,
regelingen die gemist zijn, verjaringen!), wat is er binnengekomen (mail/betalingen),
hoe staat de portefeuille ervoor. Dat eerste — het belangrijkste — ontbreekt juist:
er is géén "vandaag"-blok met deadlines/alarmen (de verjaringstaken staan alleen in
een agenda waar niemand kijkt). In plaats daarvan: uren- en factuurwidgets die permanent
op 0 staan omdat dit kantoor (nog) niet op uurtje-factuurtje werkt, plus een dagelijkse
zeurbanner "Geen uren geschreven op [gisteren]". Concurrenten (Clio, Smokeball) tonen
precies zo'n takenlijst/deadlines-eerst-dashboard.
**Kans:** vervang de uren/factuur-widgets door een "Actie vandaag"-blok (taak-deadlines,
verjaring, gemiste regelingtermijnen, verlopen stap-wachttijden). De widgets kunnen terug
zodra uren/facturatie echt gebruikt worden (instellingen-vlag bestaat al: modules).

### UX/UI
- Netjes en consistent (kaarten, kleuren, NL). Geen fouten.
- "Goedenavond, Lisanne" terwijl je als seidony@ ingelogd bent: het admin-account heet
  "Lisanne Kesting" met seidony-mailadres — verwarrend (accountnaam-opruiming stond al
  open sinds S186).
- Meldingenbel toont "9+" bij 299 ongelezen — waarvan 264 "classificatie klaar"-spam
  (244 aan seidony, 20 aan lisanne). De bel is daarmee onbruikbaar als signaal.
- Werkstroom-widget toont nu één balk "Nieuw 18" — prima zodra er meer statussen komen.

## 2. Mijn Taken

### Techniek
- **Doet het het?** Deels. Drie tegenstrijdigheden op één scherm:
  1. Zijbalk-badge zegt **19**, paginakop zegt "Geen openstaande taken", onderaan
     "Alles gedaan! Goed werk!". De badge = follow-up (13) + intake (6) + eigen verlopen
     taken (0 voor dit account) — dubbeltellingen van tellers die er al naast staan.
  2. Er bestáán 4 taken (2× "VERJARING — VERJAARD! Direct actie vereist", 2× "Review
     concept-email") maar alle 4 hebben **geen eigenaar** (`assigned_to_id = NULL`).
     `/api/dashboard/my-tasks` filtert op eigenaar = ingelogde gebruiker → **taken zonder
     eigenaar zijn voor iedereen onzichtbaar**. De verjaring-monitor (workflow/scheduler)
     maakt ze bewust zonder eigenaar aan. Zelfde stille-alarm-patroon dat S182 bij
     regelingen dichtte (daar gekozen: melding aan álle actieve gebruikers).
  3. Blok "Nieuwe Dossiers": `useIntakes("pending", …)` maar prod-statussen zijn
     `pending_review` (6) en `rejected` (1) → **altijd leeg**. Kapot sinds de
     status-naamgeving; badge-endpoint telt wél goed.
- **Gebruikt?** Het eigen-taken-deel kan niet gebruikt worden (zie boven); het
  AI-aanbevelingen-blok is een 1-op-1 kopie van de Follow-up-pagina.
- **Verdict: repareren + ontdubbelen.** Dit hoort DE werklijst van Lisanne te zijn.

### Partner-blik
"Mijn Taken" is potentieel het belangrijkste scherm van het product — de plek waar een
advocaat 's ochtends begint. Nu is het een verzamelbak van kopieën (follow-up), een kapot
blok (intake) en een onzichtbare kern (echte taken). Kies één van twee richtingen:
(a) maak dit hét startpunt: alle soorten werk (taken mét en zonder eigenaar, follow-up,
intake, gemiste regelingen) in één geprioriteerde lijst, en laat de aparte pagina's de
detail-flows doen; of (b) schrap de kopieën en maak dit een pure takenlijst (incl.
eigenaarloze taken). Optie (a) is wat Clio/Smokeball doen ("dagstart-lijst").

### UX/UI
- Interne codetaal in beeld: "Document 'sommatie_drukte' kan gegenereerd en verstuurd
  worden", "staat 0 dagen in stap 'Eerste sommatie'. Minimale wachttijd (0 dagen)
  bereikt." — moet mensentaal zijn ("Sommatie klaar om te versturen voor IN100599").
- De "Akkoord"-knop genereert én verstuurt (approve-and-execute) — zwaar gevolg achter
  één klik zonder bevestiging of preview-link. Minimaal een bevestigingsdialoog met
  wat er precies uitgaat. (Niet aangeklikt deze sessie.)
- 13 aanbevelingen worden als lange kaartenlijst getoond; met 100+ heropende zaken wordt
  dit onwerkbaar — bulk/groepering nodig (zelfde les als S24 Recruit: selectie-gedreven).

## 3. Agenda

### Techniek
- **Doet het het?** De pagina werkt (maand/week, event-dialoog met dossier/relatie-koppeling,
  Outlook-sync-knop). Geen consolefouten.
- **Gebruikt?** **Nee. 0 afspraken ooit** (`calendar_events` leeg). Enige zichtbare inhoud:
  4 werkstroom-taken als kalender-items (2 verjaring op 4 juli, 2 review op 9 juli) via
  `/api/workflow/calendar` (taken + KYC).
- **Verbonden?** Half. Outlook-sync (handmatig + elke 15 min automatisch) bestaat, maar
  alleen het seidony-account heeft Outlook; **Lisanne (IMAP/BaseNet) kan niet syncen** —
  haar sync-knop geeft een foutmelding. De sync heeft 0 events opgeleverd.
- **Verdict: aansluiten of afslanken** (beslispunt voor fase 2).

### Partner-blik
Een lege agenda-module maakt het product doods. Twee opties:
(a) **Aansluiten op echt gebruik**: als Lisanne haar agenda in BaseNet/elders bijhoudt,
is de vraag of ze een tweede agenda wil. Realistischer: maak dit de **termijnen-agenda**
van de praktijk — stap-deadlines, regeling-vervaldagen, verjaringen, zittingen — die
automatisch gevuld wordt (workflow-feed bestaat al!) en waar handmatige afspraken bijkomen.
(b) **Afslanken**: alleen de deadline-weergave houden, "Nieuw event"/sync verstoppen tot
er een echte agenda-koppeling is (M365-migratie Lisanne staat al als toekomstmodule).
Advies: (a)-light — de feed is er al, alleen betalingsregeling-termijnen en
incasso-stap-deadlines ontbreken er nog in.

### UX/UI
- Verjaring-items tonen als afgeknepen rode reepjes "VERJARING: IN100015 — VERJAARD!…"
  — het belangrijkste signaal van het systeem verdient een opvallender plek dan een
  kalendercel in het verleden (4 juli) waar je overheen scrollt.
- Dubbele weergave van identieke taken ("Review concept-email" 2× onder elkaar op 9 juli)
  zonder dossiernummer — je moet klikken om te weten waarover het gaat.

## 4. Documenten

### Techniek
- **Doet het het?** Ja (sjablonenlijst laadt, geen fouten). "Genereer" niet aangeklikt
  (schrijfactie) — flow eind-tot-eind **niet geverifieerd**.
- **Gebruikt?** De sjablonen zelf zijn de motor onder de incasso-brieven (9 in beheer,
  alle actief). Maar `generated_documents` staat vandaag op **0 rijen** — er is (sinds de
  schone lei) nooit een Word-document vanuit een dossier gegenereerd; alle uitgaande
  communicatie loopt via e-mail-sjablonen (aparte lijn, werkt).
- **Verbonden?** Menu zegt "Documenten", pagina heet "Sjablonen" — en de **2619 echte
  dossierstukken** (BaseNet-import, `case_files`) zijn hier nérgens te zien; die leven
  alleen per dossier. Tab "HTML Sjablonen" leest een lege, als DEPRECATED gemarkeerde
  tabel (`document_templates`, 0 rijen) en zegt tegen de gebruiker "Ze kunnen via de API
  worden aangemaakt" — ontwikkelaarstaal, reliek.
- **Verdict: hernoemen + reliek weg + kans beoordelen.**

### Partner-blik
Advocaten verwachten onder "Documenten" hun documénten (doorzoekbaar over dossiers heen:
"waar staat die creditnota van maart?"). Dat kan hier niet — terwijl de 2619 bestanden er
al zíjn. Concurrenten (Clio, BaseNet zelf) hebben zo'n centrale documentenbibliotheek.
**Kans:** maak "Documenten" een echte bibliotheek (zoeken op naam/dossier/datum over
`case_files` + bijlagen), en verhuis sjabloonbeheer naar Instellingen (daar bestaat al
een sjablonen-tab!). Nu staat sjabloonbeheer dubbel: hier én in Instellingen.

### UX/UI
- Kaart "verzoekschrift_faillissement" toont de interne sleutel als titel en heeft geen
  omschrijving (de nette naam "Verzoekschrift faillissement (concept)" stáát in de data).
- Iedere kaart zegt "Beschikbaar" — betekenisloos label als álles beschikbaar is.
- De info-banner ("documenten genereer je vanuit een dossier") is goed — maar bevestigt
  eigenlijk dat deze pagina geen documentenpagina is.

---

## 5. Losse bevindingen (bijvangst)

1. **Testdossier 2026-00001** (aangemaakt 8 juli, status nieuw) telt mee in werkvoorraad
   (18→17), werkstroom-widget en is de enige bron van de activiteitenfeed. Opruimen =
   destructief → apart akkoord vragen.
2. **Dubbele incasso-stap "Eerste sommatie"** (één actief, één inactief, zelfde
   sjabloontype). Inactief exemplaar is onschadelijk (S182-poortwachter) maar is datavervuiling.
3. **Meldingen-typen zonder waarde**: `classification_done` (264 ongelezen) zou geen
   melding moeten maken zolang niemand classificaties verwerkt; `email_received` (30)
   dubbelt met de Mail-teller in het menu.
4. IN100016: verjaring 23-09-2026 — meenemen in de eerstvolgende heropeningsbatch-beslissing.

## 6. Niet geverifieerd (bewust, read-only sessie)

- "Genereer"-flow van sjablonen (schrijfactie) — 0 gegenereerde documenten gemeten, maar
  of de flow werkt is niet getest.
- "Nieuw event"/event-bewerking in agenda (schrijfactie).
- "Akkoord/Afwijzen" op follow-up-aanbevelingen (verstuurt/genereert).
- Het meldingenpaneel zelf (klik op de bel) — alleen de data erachter gemeten.
- Of de verjaring van IN100015/IN100127 juridisch écht is ingetreden: de monitor rekent
  kaal 5 jaar vanaf oudste opeisbaarheid (2020-10-15 resp. 2021-03-23) en kent
  **stuitingen niet** (aanmaningen uit het BaseNet-tijdperk kunnen gestuit hebben,
  art. 3:317 BW). Oordeel is aan Lisanne — maar juist daarom moet het alarm zichtbaar zijn.

## 7. Werkorder-kandidaten uit D-A (voor fase 2-beslislijst)

| # | Actie | Type | Inschatting |
|---|-------|------|-------------|
| A1 | Taken zonder eigenaar zichtbaar maken (my-tasks: ook eigenaarloze taken van de tenant tonen, of verjaring-taken aan alle actieve gebruikers toewijzen zoals S182-alarmen) | fix, HOOG | klein |
| A2 | "Nieuwe Dossiers"-blok: statusfilter `pending` → `pending_review` (of hergebruik intake-hook van de Mail-tab) | fix | heel klein |
| A3 | Mijn Taken herontwerpen tot dagstart-lijst (of ontdubbelen tot pure takenlijst) — beslispunt | product | middel |
| A4 | Dashboard: uren/factuur-widgets + zeurbanner achter module-vlag; "Actie vandaag"-blok ervoor in de plaats | product | middel |
| A5 | Classificatie-eiland: meldingen uit, en beslissen — verwerk-flow bouwen óf classificatielijn uitzetten | beslispunt | klein/middel |
| A6 | "1169 nieuw deze maand" → import-datum uitsluiten of label aanpassen | fix, cosmetisch | heel klein |
| A7 | Documenten-pagina: HTML-tab weg, slug-titel fixen, hernoemen naar "Sjablonen" óf ombouwen tot documentenbibliotheek over case_files — beslispunt | product | klein / groot |
| A8 | Agenda: termijnen-agenda maken (regeling-vervaldagen + stap-deadlines in de bestaande feed) of afslanken — beslispunt | product | middel |
| A9 | Activiteitenfeed: pipeline/mail/heropening laten schrijven in case_activities, of feed vervangen door iets dat al data heeft | product | middel |
| A10 | Testdossier 2026-00001 opruimen (mét akkoord) | opschonen | heel klein |
| A11 | Meldingenbel: classification_done/email_received niet meer als melding | fix | klein |
| A12 | Accountnaam seidony ("Lisanne Kesting") rechtzetten | opschonen | heel klein |

**Volgende kijk-sessies:** D-B (Relaties, Dossiers, Incasso, Follow-up, Intake) en
D-C (Bankimport, Derdengelden, Uren, Facturen, Rapportages, Instellingen).
