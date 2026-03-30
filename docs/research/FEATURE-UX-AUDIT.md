# Luxis — Feature & UX Audit

**Datum:** 29 maart 2026
**Beoordelaar:** Onafhankelijke legal-tech consultant (AI)
**Perspectief:** Lisanne (solo incasso-advocaat, Kesting Legal, Amsterdam)

---

## DEEL 1: FEATURE COMPLETENESS — MODULE VOOR MODULE

---

### 1.1 Dashboard

**Wat Lisanne ziet bij inloggen:**
- Persoonlijke begroeting met naam + datum
- 4 KPI-kaarten: actieve dossiers, relaties, openstaand bedrag (incasso), vandaag gewerkte uren, open facturen
- Pipeline bar (visuele verdeling dossiers per status)
- "Actie nodig" widget (dossiers in status sommatie/14-dagenbrief/nieuw)
- AI Suggesties widget (classificaties die goedkeuring wachten)
- Mijn Taken widget (openstaande taken, follow-ups, intakes)
- Week-uuroverzicht + recente facturen
- Recente activiteit (tijdlijn per dossier)
- Snelknop "Nieuw dossier"

**Wat mist:**
- **Geen deadlines/termijnen overzicht.** Lisanne ziet niet welke termijnen vandaag of deze week verlopen. De "Actie nodig" widget toont alleen dossier-statussen, geen datum-gedreven deadlines. Een rechter stuurt een tussenvonnis met een termijn van 4 weken — waar ziet Lisanne dit terug?
- **Geen openstaande betalingen/debiteurenoverzicht.** Er is een "Openstaand" KPI-kaart, maar geen lijst van welke facturen verlopen zijn en wie moet betalen. Vergelijking: Basenet toont verouderde facturen direct op het dashboard.
- **Geen omzet-widget.** Geen zicht op maandomzet, gefactureerd deze maand, of omzet vs vorig jaar. Rapportages-pagina bestaat wel maar is niet op het dashboard.
- **Vergeten uren waarschuwing ontbreekt.** Er is een "vandaag gewerkt" KPI, maar geen melding als gisteren 0 uren geschreven is. Clio waarschuwt hier proactief voor.

**Cijfer: 7/10** — Sterk voor een incasso-praktijk, maar mist deadline-awareness en financieel inzicht.

---

### 1.2 Relatiebeheer

**Velden per relatie:**
- Naam (bedrijf of voor/achternaam voor persoon)
- E-mail, telefoon, KvK-nummer, BTW-nummer
- Bezoekadres + postadres (adres, postcode, plaats)
- Geboortedatum, notities
- Standaard uurtarief, betalingstermijn, factuur-e-mail
- IBAN (via relatie-detail)
- Contact Links (koppeling persoon ↔ bedrijf met functietitel)

**Wat kan het:**
- Zoeken op naam, e-mail, KvK-nummer
- Filteren op type (bedrijf/persoon)
- Paginatie
- Detailpagina met inline editing
- Gekoppelde dossiers zichtbaar
- KYC/Wwft-module (indien actief): risicoclassificatie, ID-verificatie, UBO, PEP/sancties
- Document upload (KYC-documenten)
- Contact Links (meerdere contactpersonen per bedrijf)

**Wat mist:**
- **Geen tags/labels.** Lisanne kan relaties niet categoriseren (bijv. "incassobureau", "vaste cliënt", "wederpartij"). Alle concurrenten bieden dit.
- **Geen meerdere e-mailadressen/telefoonnummers.** Eén email en één telefoon per relatie. In de praktijk heeft een bedrijf een algemeen mailadres + contactpersoon-mail.
- **Geen correspondentieoverzicht vanuit relatie.** Je ziet gekoppelde dossiers, maar niet alle correspondentie met deze relatie over alle dossiers heen.
- **Geen import/export.** Geen CSV-import voor bestaande contacten, geen vCard-export.
- ~~IBAN-veld: WEL aanwezig op relatie-detailpagina in sectie "Financieel", bewerkbaar in edit-modus.~~
- **Geen vrije velden.** Geen mogelijkheid om custom velden toe te voegen.

**Cijfer: 6.5/10** — Basisfunctionaliteit is er, maar mist flexibiliteit die dagelijks gebruik vereist.

---

### 1.3 Dossierbeheer

**Wat staat op een dossierpagina:**
- Header: dossiernummer, beschrijving, status-badge met transitieknoppen
- Tabbladen: Overzicht, Partijen, Vorderingen/Financieel, Uren, Betalingen/Derdengelden, Facturen, Documenten, Correspondentie, Activiteiten
- Sidebar: zaakgegevens, partijen-samenvatting, quick-stats
- AI-banner: classificaties + follow-up suggesties
- Auto-timer: start automatisch bij openen dossier

**Wat kan het:**
- Wizard voor nieuw dossier (3 stappen: zaakgegevens → partijen → vorderingen)
- Conflict check bij aanmaken
- Invoice upload zone (AI parseert facturen naar vorderingen)
- Bulk status wijzigingen
- CSV export van dossierlijst
- Zoeken, filteren op type/status/behandelaar/datum
- Activiteitenlog per dossier
- Workflow-engine met configureerbare statussen en transities
- Email compose vanuit dossier (via Outlook/Graph API)

**Wat mist:**
- **Geen archiveren/heropenen.** Er is geen expliciete archief-functie. Gesloten dossiers verdwijnen niet uit de lijst.
- **Geen subdossiers/gekoppelde dossiers.** Incassozaak → executie → faillissement: deze keten is niet te modelleren.
- **Geen kanban-view.** Alleen tabelweergave. Concurrenten (Clio, Basenet) bieden kanban als alternatief.
- **Geen vrije velden per dossiertype.** Je kunt geen custom metadata toevoegen.
- **Referentienummer client ontbreekt in wizard.** Het veld `reference` bestaat, maar is niet prominent in de wizard.
- **3-clicks dossiercreatie:** Wizard is 3 stappen. Met inline relatie-aanmaak en invoice-upload is het goed, maar elke stap vraagt veel scrollen. Scenario A (nieuwe incassozaak) kost ca. 15-20 clicks als alle relaties nieuw zijn.

**Cijfer: 7.5/10** — Sterk fundament, wizard is goed, maar mist archivering en subdossiers.

---

### 1.4 Incassomodule (KRITISCH)

**Wat kan het:**
- Vorderingen registreren per dossier: beschrijving, hoofdsom, verzuimdatum, factuurnummer, factuurdatum
- Rentetype per dossier: wettelijke rente (6:119), handelsrente (6:119a), overheidsrente (6:119b), contractuele rente
- Compound + simple interest berekening
- Historische rentetarieven (seed data)
- Renteoverzicht dialog met per-periode breakdown (tarief, dagen, bedrag)
- WIK-staffel berekening (art. 6:96 BW, correct met min €40, max €6.775)
- BTW-optie op BIK
- B2C compliance checks (14-dagenbrief, minimumbedrag)
- Deelbetalingen registreren
- Art. 6:44 BW toerekening (kosten → rente → hoofdsom)
- Betalingsregelingen (promise_date/amount)
- Pipeline werkstroom: configureerbare stappen (herinnering → aanmaning → 14-dagenbrief → sommatie → dagvaarding)
- Batch-acties: meerdere dossiers tegelijk door de pipeline sturen
- Template-generatie per stap (Word documenten)
- AI-classificatie van emails + follow-up suggesties
- Bank import (CSV) met automatische matching
- Derdengelden-administratie
- Provisie-instellingen

**Wat mist:**
- **Opdrachtbevestiging ontbreekt.** Eerste document dat naar de cliënt gaat bij een nieuwe zaak — essentieel.
- **Afsluitbrief ontbreekt.** Bij sluiting dossier: eindafrekening + bevestiging aan cliënt.
- **Incassomachtiging ontbreekt.** Volmacht van cliënt om namens hen te incasseren.
- **Geen processtukken-overzicht.** Welke brieven/documenten zijn verstuurd in welke volgorde? Dit is nu verspreid over correspondentie + documenten tabs.

**Wat WEL aanwezig is (en goed werkt):**
- Renteoverzicht als DOCX-template (`renteoverzicht.docx`) — genereerbaar vanuit dossier
- Dagvaarding als DOCX-template (`dagvaarding.docx`) — volledig aanwezig
- Griffierechten-berekening (`griffierechten.py`) — 2026-tarieven kanton + rechtbank, naturlijk persoon + rechtspersoon

**Wat is GOED:**
- Financiële precisie (Decimal, geen floats) — beter dan veel concurrenten
- Wettelijke rente per halfjaar-periode is correct geïmplementeerd
- WIK-staffel is correct
- Art. 6:44 BW toerekenoning is correct
- B2C/B2B onderscheid met compliance guards is zeldzaam goed voor een nieuw systeem
- Pipeline werkstroom is uniek — geen enkele concurrent biedt dit

**Cijfer: 8/10** — De kern is sterk en juridisch correct. Mist templates en processtuk-output.

---

### 1.5 Correspondentie

**Wat kan het:**
- Ongesorteerde emails: lijst met niet-aan-dossier-gekoppelde mails
- Auto-sync elke 5 minuten via Graph API
- Auto-koppeling op dossiernummer, referentie, contactpersoon
- Handmatige koppeling met dossiersuggesties
- Bulk-acties: meerdere emails tegelijk koppelen of verbergen
- Email detail met body + bijlagen
- Per-dossier correspondentietab: alle in- + uitgaande mails
- Compose via Outlook (Graph API)

**Wat mist:**
- **Geen chronologisch overzicht per dossier dat brieven + emails combineert.** Correspondentietab toont alleen synced emails. Gegenereerde documenten staan in een apart tab. In de praktijk wil Lisanne alles in één tijdlijn.
- **Geen brief-tracking.** Als een sommatie verstuurd is per post, kan dit niet als "verstuurd op datum X" geregistreerd worden.
- **Geen email-compose vanuit de correspondentie-pagina.** Je kunt alleen emails componeren vanuit een dossier. Op de ongesorteerde-pagina kun je niet direct antwoorden.

**Cijfer: 7/10** — Sterke email-integratie, maar mist unified tijdlijn.

---

### 1.6 Documenten & Templates

**Templates beschikbaar:**
- Herinnering, Aanmaning, 14-dagenbrief, Sommatie, Tweede sommatie, Dagvaarding, Renteoverzicht
- Managed templates (uploadbare DOCX-bestanden)
- HTML-templates: sommatie, 14_dagenbrief, renteberekening

**Wat kan het:**
- Document genereren vanuit dossier-tab
- Merge fields vullen automatisch (relatie, vordering, rente, etc.)
- Download als DOCX
- Template-beheer in instellingen

**Wat mist:**
- **Geen opdrachtbevestiging, afsluitbrief, incassomachtiging** (zie 1.4)
- **Inline preview IS aanwezig** — DocumentenTab heeft preview-functionaliteit via `/api/documents/{id}/preview`. ~~Eerder gemist in audit.~~
- **Geen versiebeheer.** Als je een document genereert, bewerkt, en opnieuw genereert, is de oude versie weg.
- **Geen online editor.** Geen mogelijkheid om een gegenereerd document in de browser te bewerken. Je moet het downloaden, bewerken in Word, en opnieuw uploaden.

**Cijfer: 7/10** — 7 DOCX-templates aanwezig (incl. dagvaarding + renteoverzicht), inline preview werkt. Mist 3 templates (opdrachtbevestiging, afsluitbrief, incassomachtiging) + document editor.

---

### 1.7 Tijdschrijven

**Wat kan het:**
- Floating timer (altijd zichtbaar, klikt mee per dossier)
- Auto-timer: start automatisch bij openen dossier
- Handmatig invoeren: datum, dossier, activiteitstype, duur, omschrijving, billable toggle
- Week-, maand-, dagweergave
- Per-dossier urenlijst
- Bewerken en verwijderen
- Samenvatting: totaal uren, declarabel, omzet
- Activiteitstype labels (correspondentie, telefoon, dossierwerk, overleg, etc.)
- Case picker in timer

**Wat mist:**
- **Timer heeft beperkte pauze.** Bij browser-sluiting wordt de timer gepauzeerd en kan hervat worden. Maar er is geen expliciete pauzeknop in de UI.
- **Geen dichter/afronden-functie.** Geen mogelijkheid om uren af te ronden op 6 minuten (standaard advocatuur).
- **Geen "vergeten te schrijven"-detectie.** Geen melding als er gisteren 0 uren staan.

**Cijfer: 8/10** — Auto-timer is een killer feature. Mist afrondingslogica.

---

### 1.8 Facturatie

**Wat kan het:**
- Factuurlijst met zoeken en filteren op status
- Aanmaken: handmatig of op basis van dossier + uren
- Debiteuren-tab: openstaande vorderingen per relatie met ageing
- Concept/verzonden/betaald/verlopen statussen
- Credit nota's
- PDF generatie
- Factuurregels met omschrijving, aantal, tarief, BTW

**Wat mist:**
- **Factuur-PDF niet beoordeeld** (zou live moeten zien voor kwaliteitsoordeel). Wettelijke vereisten (factuurnummer, KvK, BTW, IBAN, betalingstermijn) zijn afhankelijk van kantoorinstellingen.
- **Geen automatische herinnering bij onbetaalde facturen.** Geen "stuur een herinnering na 14 dagen".
- **Geen Mollie/iDEAL-integratie.** Geen online betaalmogelijkheid.
- **Geen geautomatiseerde facturatie.** Geen maandelijks automatisch factureren van uren.

**Cijfer: 7/10** — Functioneel compleet voor handmatige facturatie, mist automatisering.

---

### 1.9 Agenda & Taken

**Wat kan het (Agenda):**
- Maand-, week-, dagweergave
- Events aanmaken met type (afspraak, telefonisch overleg, zitting, deadline, herinnering)
- Koppeling aan dossier en/of relatie
- Outlook sync (bi-directioneel via Graph API)
- Nederlandse dag/maandnamen
- Kleurcodes per eventtype

**Wat kan het (Taken):**
- Taken per dossier
- Workflow-taken (automatisch gegenereerd bij statustransities)
- Follow-up suggesties (AI-gestuurd)
- Intake-taken (openstaande intakes)
- Terugkerende taken
- Prioriteit/urgentie indicators
- Groepering: te laat / vandaag / deze week / later
- Afronden en overslaan

**Wat mist:**
- **Notificatiesysteem is voorbereid maar niet actief.** Frontend heeft volledige notificatie-UI met 10 types (deadline_approaching, deadline_overdue, verjaring_warning, etc.) + 30-sec polling. Backend is een stub die lege responses geeft. De frontend is klaar, backend moet nog geïmplementeerd.
- **Geen agenda-widget op dashboard.** Je moet apart naar de agenda-pagina navigeren.
- **Geen drag & drop.** Events verplaatsen vereist bewerken.

**Cijfer: 7.5/10** — Dubbele module (agenda + taken) is goed. Mist notificaties.

---

### 1.10 Zoeken

**Wat kan het:**
- Command Palette (Ctrl+K): globale zoekfunctie
- Zoekt over dossiers, relaties, documenten
- Quick actions: snelnavigatie naar modules
- Keyboard navigatie (pijltjes + Enter)
- Debounced API-zoekactie

**Wat mist:**
- **Zoekt niet over correspondentie.** Als Lisanne zoekt op "Van der Berg" vindt ze de relatie en het dossier, maar niet de email van vorige week over die zaak.
- **Geen zoekresultaat-previews.** Je ziet titel + subtitle, maar geen snippet van de inhoud.
- **Geen recente items.** Bij openen van de palette: geen lijst van recent geopende dossiers.

**Cijfer: 7/10** — Command Palette is modern en snel, maar zoekscope is beperkt.

---

## DEEL 2: UX & UI BEOORDELING

---

### 2.1 Eerste indruk

Het systeem ziet er **modern en professioneel** uit. Donkere sidebar met lichte content-area. Consistent gebruik van shadcn/ui componenten, Tailwind CSS. Animaties (fade-in), skeleton loaders, gradient KPI-kaarten. Het voelt als een hedendaags SaaS-product, niet als een intern tooltje.

**Vergelijking:**
- **vs Basenet:** Luxis wint visueel. Basenet ziet er gedateerd uit (2010-era UI).
- **vs Clio:** Vergelijkbaar niveau, Clio is iets gepolijster door jaren iteratie.
- **vs Urios:** Luxis wint. Urios is functioneel maar visueel spartaans.
- **vs Legalsense:** Vergelijkbaar, Legalsense heeft een iets zakelijker uiterlijk.

**Cijfer: 8/10** — Modern, consistent, professioneel. Top-tier voor een nieuw product.

---

### 2.2 Navigatie

- Sidebar met secties: Overzicht, Beheer, Financieel, Systeem
- Collapsible sidebar (desktop), slide-over (mobiel)
- Badge-counts op sidebar items (correspondentie, incasso, taken, betalingen)
- Breadcrumbs met dynamische labels (dossiernummer, relatienaam)
- Command Palette (Ctrl+K) voor snelle navigatie
- Tabs binnen pagina's (dossier-detail, instellingen, enz.)

**Alles bereikbaar in 2 clicks:** Ja. Sidebar → pagina. Maximaal 1 extra click voor detail.

**Wat mist:**
- **Geen "recent geopend" in sidebar.** Geen snelle manier om terug te gaan naar het vorige dossier zonder te zoeken.
- **Tab-state gaat verloren bij navigatie.** Als je op dossier-tab "Correspondentie" zit en naar een ander dossier navigeert, begin je weer op "Overzicht".

**Cijfer: 8/10** — Uitstekende navigatiestructuur.

---

### 2.3 Formulieren

- Relatie-formulier: validatie op blur (KvK 8 cijfers, email-format, postcode-format)
- Verplichte velden gemarkeerd met validatiefoutmeldingen
- `beforeunload` warning bij onopgeslagen wijzigingen
- Inline editing op detail-pagina's

**Wat mist:**
- **htmlFor/id associaties ontbreken op veel formulieren.** Dit is al geïdentificeerd in de backlog. Screen readers kunnen labels niet aan velden koppelen.
- **Geen auto-save.** Bij langere formulieren (nieuwe relatie met 13 velden) is er geen tussentijds opslaan.
- **Sommige labels zijn technisch.** "Rate basis" (renteberekening), "pipeline steps" — dit zijn ontwikkelaarstermen, geen Lisanne-termen.

**Cijfer: 6.5/10** — Validatie is goed, a11y ontbreekt, auto-save mist.

---

### 2.4 Tabellen & lijsten

- Alle lijsten zijn sorteerbaar (impliciet via API)
- Filteren: zoeken, type-filter, status-filter, datum-range, behandelaar
- Paginatie met pagina-nummers
- Hover-effects, doorklikbaar naar detail
- Mobile card view + desktop tabelweergave
- Bulk selectie met checkboxes
- Export naar CSV

**Cijfer: 8.5/10** — Professioneel. Mobile card view is een nice touch.

---

### 2.5 Lege states

- Reusable `EmptyState` component met icon, titel, beschrijving, en actie-knop
- Relaties: "Geen relaties gevonden" + "Nieuwe relatie toevoegen"
- Dossiers: "Geen dossiers gevonden" + "Nieuw dossier aanmaken"
- Context-aware: als er een filter actief is → "Probeer andere zoektermen"

**Cijfer: 8/10** — Goed geïmplementeerd, helpt nieuwe gebruikers.

---

### 2.6 Feedback & states

- Skeleton loaders op elke pagina
- Toast notifications (sonner) voor success/error
- Loading spinners op knoppen (Loader2 icon)
- QueryError component met retry-knop
- Bevestigingsdialoogen voor destructieve acties (verwijderen)

**Cijfer: 8.5/10** — Consistent en professioneel.

---

### 2.7 Responsive / mobiel

- Mobile card view op relaties + dossiers
- Hamburger menu met slide-over sidebar
- Responsive grid (sm/md/lg breakpoints)
- Hidden columns op smaller screens

**Maar:**
- Agenda maandweergave is niet bruikbaar op telefoon (42-cellen grid)
- Dossier-detail met 9 tabs is krap op mobiel
- Formulieren scrollen ver op small screens

**Cijfer: 6.5/10** — Basis-responsive, maar niet optimaal voor dagelijks mobiel gebruik.

---

### 2.8 Nederlandse taal

- **Vrijwel alles in het Nederlands.** Menu, labels, knoppen, foutmeldingen, lege states.
- Tab-labels: "Werkstroom", "Stappen beheren", "Profiel", "Kantoor" — correct.
- Dag/maandnamen: "maandag", "dinsdag", "januari" — correct.

**Engelse woorden die opvallen:**
- "Word Templates" (op documenten-pagina) — moet "Word-sjablonen" zijn
- "HTML Sjablonen" — mix van Engels en Nederlands
- "Rate basis" in incasso-formulier
- "Pipeline" op dashboard
- "Case" in sommige API-gerelateerde labels
- "Billable" toggle op uren

**Cijfer: 7.5/10** — Goed, maar er zijn nog Engelse termen die uit de code lekken.

---

## DEEL 3: DAGELIJKSE WORKFLOW — SCENARIO'S

---

### Scenario A: Nieuwe incassozaak

| Stap | Actie | Clicks |
|------|-------|--------|
| 1 | Dashboard → Nieuw dossier | 1 |
| 2 | Type selecteren (incasso) | 1 |
| 3 | Beschrijving invoeren | 1 (typen) |
| 4 | Volgende stap | 1 |
| 5 | Cliënt zoeken → niet gevonden → inline aanmaken | ~8 (naam, email, KvK, etc.) |
| 6 | Wederpartij zoeken → inline aanmaken | ~6 |
| 7 | Volgende stap | 1 |
| 8 | 3 vorderingen invoeren (3x beschrijving, bedrag, datum) | ~15 |
| 9 | Dossier opslaan | 1 |
| 10 | Naar vorderingen-tab, renteberekening controleren | 2 |
| 11 | Documenten-tab → sommatiebrief genereren | 2 |
| 12 | Document downloaden | 1 |

**Totaal: ~40 clicks, ~10-15 minuten**

**Knelpunten:**
- Invoice-upload (AI-parsing) kan stappen 8 reduceren naar ~3 clicks — sterke feature
- Maar als de relaties al bestaan is het ~20 clicks — acceptabel
- Sommatiebrief wordt gedownload maar niet automatisch gearchiveerd in correspondentie

---

### Scenario B: Ochtendstart

| Vraag | Antwoord vanuit dashboard? |
|-------|---------------------------|
| Deadlines vandaag/week? | **NEE** — geen deadline-widget |
| Betalingen binnengekomen? | **DEELS** — Bank Import badge, maar geen inline overzicht |
| Dossiers die actie nodig hebben? | **JA** — "Actie nodig" widget |
| Gisteren vergeten uren? | **NEE** — geen waarschuwing |

**Lisanne moet 3 extra clicks maken** (naar agenda, naar betalingen, naar uren) om haar ochtendoverzicht compleet te krijgen. Basenet en Clio tonen dit in één scherm.

---

### Scenario C: Deelbetaling verwerken

| Stap | Actie | Clicks |
|------|-------|--------|
| 1 | Zoek dossier (Ctrl+K) | 2 |
| 2 | Tab "Betalingen" | 1 |
| 3 | Betaling registreren | ~4 (bedrag, datum, omschrijving) |
| 4 | Rente herberekening → automatisch | 0 |
| 5 | Specificatie genereren | 2 |
| 6 | Downloaden | 1 |

**Totaal: ~10 clicks, 2-3 minuten** — Goed. Art. 6:44 BW toerekening is automatisch en correct.

---

### Scenario D: Factuur maken

| Stap | Actie | Clicks |
|------|-------|--------|
| 1 | Naar dossier | 2 |
| 2 | Tab "Uren" bekijken | 1 |
| 3 | Tab "Facturen" → Nieuwe factuur | 2 |
| 4 | Regels invullen of uren importeren | ~5 |
| 5 | Opslaan | 1 |
| 6 | PDF bekijken/downloaden | 1 |

**Totaal: ~12 clicks, 3-5 minuten** — Acceptabel.

---

### Scenario E: Dossier zoeken

- **Ctrl+K → "Van der Berg"**: vindt relatie + eventueel dossier. **1-2 seconden.**
- **Zoek op "Janssen"**: vindt relatie, en via relatie het dossier. **2-3 clicks.**
- **Zoek op dossiernummer**: direct resultaat. **Instant.**

**Cijfer: 8/10** — Command Palette maakt zoeken snel.

---

## DEEL 4: CONCURRENTIEPOSITIE

---

### 4.1 Waar wint Luxis?

1. **Pipeline werkstroom voor incasso.** Geen enkele concurrent heeft batch-verwerking van incassodossiers door een configureerbare pipeline. Dit is een unieke feature die Lisanne uren per week bespaart.

2. **AI-classificatie van emails.** Inkomende emails worden automatisch geclassificeerd met follow-up suggesties. Clio noch Basenet bieden dit.

3. **Auto-timer.** Timer start automatisch bij openen dossier. Smokeball biedt dit, maar geen enkel Nederlands PMS doet dit.

4. **Bank import met auto-matching.** CSV-upload van bankafschriften die automatisch gematcht worden aan dossiers. Basenet heeft dit niet.

5. **Invoice-upload met AI-parsing.** Factuur uploaden → vorderingen worden automatisch aangemaakt. Uniek.

---

### 4.2 Waar verliest Luxis?

1. **Notificatie-backend nog niet actief.** Basenet, Kleos en Clio sturen proactieve waarschuwingen. Luxis frontend is volledig klaar (10 notificatietypes, polling, UI), maar backend geeft lege responses.

2. **Geen unified tijdlijn per dossier.** Clio en Basenet tonen alle activiteit (emails, brieven, documenten, betalingen, notities) in één chronologisch overzicht. Luxis verspreidt dit over meerdere tabs.

3. **Geen cliëntportaal.** Basenet en Clio bieden cliënten een inlogmogelijkheid om hun zaak te volgen.

4. **Geen kanban-view voor dossiers.** Clio en NEXTmatters bieden dit als alternatieve weergave.

5. **Exact Online-integratie nog niet live.** Basenet en Kleos hebben boekhoudkoppelingen. De Luxis-integratie is gebouwd maar wacht op credentials.

6. **3 templates ontbreken.** Opdrachtbevestiging, afsluitbrief, incassomachtiging — standaarddocumenten die concurrenten wel bieden.

---

### 4.3 Ontwerpkansen uit market research

| # | Kans | Score | Toelichting |
|---|------|-------|-------------|
| 1 | Best-of-both-worlds-architectuur | **Goed** | Moderne stack (Next.js + FastAPI), cloud-native, API-first. Technisch sterker dan Basenet/Kleos. |
| 2 | Radicaal moderne UX | **Goed** | Visueel op Clio-niveau. Gradient KPI's, skeleton loaders, Command Palette. |
| 3 | Diep geïntegreerde AI | **Goed** | Email classificatie, follow-up suggesties, invoice parsing, smart replies. Voorop de markt. |
| 4 | Sterke nichemodules (incasso) | **Goed** | Juridisch correcte renteberekening, WIK, art. 6:44, pipeline. Sterkste punt. |
| 5 | Document automation als kernfunctie | **Goed/Matig** | 7 DOCX-templates + inline preview. Mist 3 templates + online editor. |
| 6 | E-mailintegratie "die gewoon werkt" | **Goed** | Graph API, auto-sync, auto-koppeling, compose via provider. Sterker dan Basenet. |
| 7 | Tijd/facturatie met moderne pricingmodellen | **Matig** | Auto-timer is sterk. Facturatie is functioneel maar geen subscription/flat-fee ondersteuning. |
| 8 | Termijnbewaking met uitleg en audittrail | **Matig** | Agenda werkt, notificatie-frontend compleet (10 types), maar backend is stub. Activeren = biggest quick win. |
| 9 | Migratie-product als USP | **Niet gestart** | Data-migratie scripts zijn gepland maar nog niet gebouwd. |
| 10 | Transparante communicatie over roadmap | **n.v.t.** | Intern product, geen externe roadmap. |

---

## UITVOER

---

### Scorecard

| Module / Onderdeel | Cijfer (1-10) | Toelichting |
|---|---|---|
| Dashboard | 7 | Sterk voor incasso, mist deadlines en financieel inzicht |
| Relatiebeheer | 7 | IBAN aanwezig, contact links werken, mist tags en multi-email |
| Dossierbeheer | 7.5 | Goede wizard, mist archivering en subdossiers |
| Incassomodule | 8.5 | Juridisch correct, unieke pipeline, dagvaarding+griffierechten aanwezig, mist 3 templates |
| Correspondentie | 7 | Sterke email-sync, mist unified tijdlijn |
| Documenten & templates | 7 | 7 DOCX-templates aanwezig, inline preview werkt, mist 3 templates + editor |
| Tijdschrijven | 8 | Auto-timer is killer feature, mist afrondingslogica |
| Facturatie | 7 | Functioneel compleet, mist automatisering |
| Agenda & taken | 7.5 | Dubbele module, mist notificaties |
| Zoeken | 7 | Command Palette is modern, zoekscope beperkt |
| UI-ontwerp & consistentie | 8 | Modern, consistent, professioneel |
| Navigatie & flow | 8 | Uitstekend, mist recente items |
| Nederlandse taal | 7.5 | Goed, enkele Engelse termen lekken door |
| Mobiel / responsive | 6.5 | Basis-responsive, niet optimaal voor mobiel |
| Concurrentiepositie | 7 | Wint op AI + incasso, verliest op completeness |
| **TOTAALCIJFER** | **7.5** | **Sterker dan initieel beoordeeld. Klaar voor MVP, bijna verkoopklaar.** |

---

### Top 10 — Dit mist Lisanne morgen

1. **Notificatie-backend activeren** — Frontend is klaar (10 types incl. deadline_approaching, verjaring_warning), backend is een stub. Zodra dit live is, heeft ze termijnbewaking. Hoogste urgentie.
2. **Opdrachtbevestiging template** — Eerste document bij elke nieuwe zaak, nu handmatig. Template ontbreekt.
3. **Unified tijdlijn per dossier** — Ze moet meerdere tabs doorlopen om het totaalplaatje te zien.
4. **Openstaande facturen op dashboard** — Ze ziet niet welke klanten te laat betalen zonder door te klikken.
5. **Uren afronden op 6 minuten** — Standaard declaratiepraktijk die nu handmatig moet.
6. **"Vergeten uren" waarschuwing** — Ze vergeet tijd te schrijven en mist omzet.
7. **Incassomachtiging + afsluitbrief templates** — Standaarddocumenten die bij elke zaak nodig zijn. Templates ontbreken.
8. **Tags op relaties** — Ze kan niet snel filteren op "alle incassobureaus" of "vaste cliënten".
9. **Agenda-widget op dashboard** — Ze moet apart naar agenda navigeren om events van vandaag te zien.
10. **Expliciete pauzeknop op timer** — Browser-pauze werkt, maar handmatige pauze (bijv. lunchpauze) niet.

---

### Top 5 — Dit is goed

1. **Incasso pipeline met batch-acties.** Dit is uniek in de markt en bespaart uren per week. De juridische precisie (Decimal, historische tarieven, compound interest) is indrukwekkend.

2. **AI-integratie.** Email classificatie, follow-up suggesties, invoice parsing, smart replies — dit is voorloper-technologie. Geen enkel Nederlands PMS biedt dit.

3. **Auto-timer.** De floating timer die automatisch start bij dossier-opening is een feature waar advocaten van dromen. Gecombineerd met de week/maand/dag-weergave is dit een van de sterkste tijdschrijf-implementaties.

4. **Command Palette (Ctrl+K).** Snelle zoekfunctie die het systeem voelt als een moderne tool. De quick actions maken het extra krachtig.

5. **Visueel ontwerp.** Het systeem ziet er uit als een product dat je zou kopen, niet als een intern tooltje. De gradient KPI-kaarten, skeleton loaders, en consistente UI zijn op het niveau van Clio.

---

### Top 10 — Quick wins

1. **Engelse termen vertalen** — "Word Templates" → "Word-sjablonen", "Pipeline" → "Werkstroom", "Billable" → "Declarabel". ~30 minuten werk.
2. **"Vergeten uren" badge op dashboard** — Check of gisteren 0 registraties → toon waarschuwing. ~1 uur.
3. **Recent geopend in Command Palette** — Toon laatst bezochte dossiers bij openen Ctrl+K. ~2 uur.
4. **Agenda-widget op dashboard** — Toon vandaag + morgen events. ~2 uur.
5. **htmlFor/id toevoegen aan formulieren** — A11y fix, al op de backlog. ~2 uur.
6. **Tab-state behouden bij navigatie** — URL query param `?tab=correspondentie`. ~1 uur (al deels geïmplementeerd).
7. **Openstaande facturen widget op dashboard** — Lijst van verlopen facturen met bedragen. ~2 uur.
8. **Afrondingsoptie bij uren** — Dropdown: exacte minuten / 6 min / 15 min. ~2 uur.
9. **Expliciete pauzeknop op timer** — UI-toggle toevoegen, pauze-logica bestaat al. ~1 uur.
10. **Notificatie-backend activeren** — Frontend polling + UI is volledig klaar, backend stub moet echte notificaties genereren. ~4-6 uur.

---

### Eindoordeel

**Kan Lisanne hiermee haar dagelijkse werk doen zonder Basenet te missen?**

Grotendeels ja. De incasso-kern is sterker dan Basenet — alle 7 DOCX-templates (incl. dagvaarding) zijn aanwezig, griffierechten worden berekend, inline document preview werkt. Email-integratie is beter. Tijdschrijven is beter. Ze zal Basenet missen voor: actieve notificaties (frontend klaar, backend stub), het "unified dossier-overzicht" (nu verspreid over tabs), en 3 ontbrekende templates (opdrachtbevestiging, afsluitbrief, incassomachtiging).

**Zou je dit als product aan een ander kantoor durven verkopen?**

Bijna. Het is een sterke MVP voor een solo-incasso-advocaat. Document preview werkt al, notificatie-frontend is klaar. Voor verkoop aan andere kantoren ontbreekt nog:
- Notificatie-backend (frontend is 100% klaar)
- Cliëntportaal
- Kanban-view
- Onboarding/migratie-tooling
- 3 extra templates

Na 1-2 maanden doorontwikkeling op de quick wins + notificatie-backend is het verkoopklaar.

**Wat zou ik als eerste veranderen?**

**Termijnbewaking.** Eén gemiste rechtstermijn kost meer dan alle andere ontbrekende features samen. Bouw een deadline-widget op het dashboard die:
1. Alle events met type "deadline" of "zitting" toont voor de komende 7 dagen
2. Oranje kleurt bij <3 dagen, rood bij <1 dag
3. Later: email-notificatie de dag ervoor

Dit is de feature die het verschil maakt tussen "handig tooltje" en "onmisbaar systeem".
