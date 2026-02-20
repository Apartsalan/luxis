# Analyse Bevindingen Lisanne — Praktijktest Luxis

> Gegenereerd op basis van: PROMPT-BEVINDINGEN-LISANNE.md
> Met concurrent-research: BaseNet, Clio, PracticePanther, Smokeball, Kleos, Hammock, Legal365

---

## Samenvatting

Lisanne heeft in 10 minuten testen 10 fundamentele gaps gevonden. De kern: **het dossier is niet compleet als werkhub**. Bij elk professioneel PMS (BaseNet, Clio, Kleos) is het dossier de centrale plek waar je alles doet — Luxis mist nog kritieke velden en acties.

### Resultaat per bevinding

| # | Bevinding | Backend? | Frontend? | Concurrent heeft het? | Complexiteit | Prioriteit |
|---|-----------|----------|-----------|----------------------|-------------|-----------|
| 1 | Postadres | ✅ Ja | ❌ Niet getoond | ✅ Allemaal | **XS** (alleen frontend) | P0 — Quick win |
| 2 | Geboortedatum | ❌ Nee | ❌ Nee | ✅ Allemaal | **S** (migration + frontend) | P0 — Quick win |
| 3 | Facturatiegegevens | ❌ Deels (KvK/BTW ja, rest nee) | ❌ Deels | ✅ Allemaal | **M** (migration + frontend) | P1 |
| 4 | Afwijkende factuurrelatie | ❌ Nee | ❌ Nee | ✅ Clio, PP, Kleos | **M** (migration + logica) | P1 |
| 5 | Rechtbank + advocaat wederpartij | ✅ CaseParty model | ❌ Geen UI | ✅ Allemaal | **S** (frontend toevoegen) | P0 — Quick win |
| 6 | E-mail naar elke partij | ❌ Deels (template-email) | ❌ Basaal | ✅ Allemaal | **L** (M365 integratie) | P2 (afhankelijk M365) |
| 7 | Referentienummer andere partij | ❌ Nee | ❌ Nee | ✅ BaseNet, Clio, Kleos | **S** (migration + frontend) | P0 — Quick win |
| 8 | Inline contactpersoon aanmaken | ❌ Backend: via apart endpoint | ❌ Geen inline | ✅ Allemaal | **S** (frontend modal) | P1 |
| 9 | Filters op dossier-overzicht | ✅ Backend filters bestaan | ❌ Beperkt (type+status) | ✅ Allemaal | **M** (frontend uitbreiden) | P1 |
| 10 | Zoekfunctie | ❌ Endpoint bestaat NIET | ❌ Cmd+K roept 404 aan | ✅ Allemaal | **M** (backend + frontend) | P0 — Kritiek |

---

## Per bevinding: diepte-analyse

### 1. Postadres ontbreekt bij relaties

**Waarom niet eerder gevonden:**
Het **backend model heeft postal_address/postal_postcode/postal_city al sinds de eerste sprint**. De frontend schemas (use-relations.ts) kennen deze velden ook. Echter: het edit-formulier op de relatiepagina toont alleen "Bezoekadres" — het postadres-blok is nooit in de UI gebouwd. Dit is een pijnlijke oversight: het veld bestaat in de database maar de gebruiker kan het niet zien of bewerken.

**Backend status:**
- ✅ `Contact` model: `postal_address`, `postal_postcode`, `postal_city` bestaan
- ✅ `ContactCreate`/`ContactUpdate` schemas accepteren deze velden
- ✅ `ContactResponse` geeft ze terug
- ❌ Frontend edit-formulier toont ze NIET

**Wat concurrenten doen:**
- **BaseNet:** Twee gescheiden adresblokken: "Bezoekadres" en "Postadres (postbus)"
- **Clio:** "Primary Address" + "Secondary Address" + optioneel "Billing Address"
- **Kleos:** Bezoekadres + Postadres + Factuuradres als aparte secties
- **PracticePanther:** Multiple address types (Physical, Mailing, Billing)
- **Smokeball:** Contact kan meerdere adressen hebben met type-labels

**Complexiteit: XS (2-4 uur)**
- Alleen frontend: postadres-blok toevoegen aan edit-formulier
- View-mode: postadres tonen als het verschilt van bezoekadres
- Documentgeneratie: keuze welk adres (later, P1)

---

### 2. Geboortedatum ontbreekt bij personen

**Waarom niet eerder gevonden:**
Er is een `ubo_date_of_birth` in het KYC-model maar niet op het hoofdcontact. De UX review heeft zich gericht op het KYC/WWFT-proces en niet op basale contactvelden. Bij Clio en BaseNet is geboortedatum een standaardveld op elk persoonscontact — niet alleen voor compliance maar voor correspondentie en processtukken.

**Backend status:**
- ❌ `Contact` model: GEEN `date_of_birth` veld
- ✅ `KycVerification` model: heeft `ubo_date_of_birth` (maar dat is voor UBO, niet voor het contact zelf)
- Nodig: Alembic migration + schema update

**Wat concurrenten doen:**
- **BaseNet:** Standaardveld bij personen: geboortedatum + geboorteplaats
- **Clio:** "Date of Birth" standaardveld op person contacts
- **Kleos:** Geboortedatum + BSN (voor identificatie)
- **PracticePanther:** DOB als standaardveld + SSN/ID fields
- **Smokeball:** DOB + government ID fields

**Complexiteit: S (4-6 uur)**
- Backend: migration `date_of_birth` (Date, nullable) op contacts tabel
- Backend: schema update (ContactCreate/Update/Response)
- Frontend: veld toevoegen in edit-formulier (conditional: alleen bij person)
- Frontend: tonen in view-mode

---

### 3. Facturatiegegevens bij relaties

**Waarom niet eerder gevonden:**
KvK en BTW-nummer bestaan al. Wat ontbreekt is het "factuurprofiel": een apart factuur-emailadres, betalingstermijn, en factuuradres. De UX review heeft facturatie als losse module bekeken, niet als onderdeel van het contactprofiel. Bij Clio en Kleos is billing info een standaard-tab op elk contact.

**Backend status:**
- ✅ `kvk_number` en `btw_number` bestaan op Contact
- ❌ `billing_email` — ontbreekt
- ❌ `payment_terms` (standaard betalingstermijn in dagen) — ontbreekt
- ❌ `billing_address`/`billing_postcode`/`billing_city` — ontbreekt (postadres kan dubbelen, maar apart factuuadres is beter)

**Wat concurrenten doen:**
- **BaseNet:** Relatie heeft tabblad "Financieel" met: factuur-email, BTW, KvK, betalingstermijn, IBAN, factuuradres
- **Clio:** Contact > Billing tab: billing email, currency, payment terms, tax number, billing address
- **Kleos:** Relatie > Facturatie: factuur-email, BTW, betalingsvoorwaarden, factuuradres
- **PracticePanther:** Contact > Billing: billing email, payment terms, billing address, tax ID
- **Smokeball:** Contact billing profile met preferred payment method, billing address, payment terms

**Complexiteit: M (8-12 uur)**
- Backend: migration voor `billing_email`, `payment_terms_days`, `billing_address`, `billing_postcode`, `billing_city`
- Backend: schema updates
- Frontend: "Facturatie" sectie toevoegen aan relatie edit-formulier
- Frontend: conditionally tonen (billing_email en payment_terms relevant voor alle types, factuuradres optioneel)

---

### 4. Afwijkende factuurrelatie per dossier

**Waarom niet eerder gevonden:**
Luxis factureert nu via de client_id van het dossier. In de praktijk factureert een advocaat soms aan een derde partij (incassobureau, verzekeraar, legal aid board). Dit is een standaardfunctie in elk serieus PMS maar vereist extra logica in het facturatieproces.

**Backend status:**
- ❌ `Case` model: GEEN `billing_contact_id` veld
- Het huidige facturatieproces koppelt facturen aan `contact_id` (op invoice), maar dit wordt handmatig ingesteld
- Nodig: `billing_contact_id` op Case (nullable, default = client_id)

**Wat concurrenten doen:**
- **BaseNet:** Per dossier: "Factuuradressaat" apart van cliënt
- **Clio:** Matter > Billing Settings: "Bill to" contact (kan afwijken van client)
- **Kleos:** Dossier > Facturatie: "Factuurrelatie" selecteerbaar
- **PracticePanther:** Matter > Billing Contact (separate from client)
- **Smokeball:** Matter billing configuration with alternative billing contact

**Complexiteit: M (8-12 uur)**
- Backend: migration `billing_contact_id` (UUID FK → contacts, nullable) op cases tabel
- Backend: schema + service updates
- Frontend: "Factuurrelatie" dropdown in dossier-settings (default: cliënt, wijzigbaar)
- Frontend: factuurcreatie moet billing_contact_id gebruiken als die gezet is

---

### 5. Rechtbank en advocaat wederpartij in dossier

**Waarom niet eerder gevonden:**
Het **backend ondersteunt dit AL via CaseParty** met rollen `rechtbank` en `advocaat_wederpartij`. De Partijen-tab in de frontend kan deze toevoegen. Wat ontbreekt: 1) er zijn geen specifieke velden voor rechtbanknummer/rolnummer, 2) de UI maakt het niet prominent genoeg — je moet weten dat je een "partij" moet toevoegen met die rol.

**Backend status:**
- ✅ `CaseParty` model: `role` kan `rechtbank` of `advocaat_wederpartij` zijn
- ❌ GEEN veld voor `court_case_number` (rolnummer/zaaknummer bij de rechtbank)
- ❌ GEEN prominente UI — het zit weggestopt in "Partijen toevoegen"

**Wat concurrenten doen:**
- **BaseNet:** Dossier heeft vaste velden: "Bevoegde rechtbank" (dropdown NL rechtbanken), "Rolnummer", "Kenmerk rechtbank"
- **Clio:** Matter fields: Court, Court Number, Judge, Opposing Counsel (as related contact with role)
- **Kleos:** Dossier: "Rechtbank" (dropdown), "Zaaknummer rechtbank", "Advocaat wederpartij" (als dossierpartij)
- **PracticePanther:** Court info fields + opposing counsel as related contact
- **Smokeball:** Court details section with court name, case number, judge, dates

**Complexiteit: S (6-8 uur)**
- Backend: migration `court_case_number` (String, nullable) op cases tabel
- Backend: schema update
- Frontend: "Procesgegevens" sectie in dossier-overzicht met:
  - Bevoegde rechtbank (dropdown/combobox met NL rechtbanken)
  - Rolnummer/Zaaknummer rechtbank
  - Advocaat wederpartij (getoond als die CaseParty bestaat)
- Frontend: snelle link om rechtbank/advocaat wederpartij toe te voegen

---

### 6. E-mail versturen vanuit dossier naar elke partij

**Waarom niet eerder gevonden:**
De e-mailfunctie is in de huidige staat minimaal — test-email endpoint + document-bijlage-email. Volledige e-mail vanuit het dossier vereist de Microsoft 365 integratie (M1-M6 in de roadmap). Dit is bewust geparkeerd als groot project.

**Backend status:**
- ✅ SMTP service werkt (test + document bijlage)
- ✅ E-mailtemplates bestaan (document_sent, deadline_reminder, payment_confirmation, status_change)
- ❌ GEEN vrije e-mail vanuit dossier naar willekeurige ontvanger
- ❌ GEEN "recipient picker" die alle dossierpartijen toont

**Wat concurrenten doen:**
- **BaseNet:** E-mail volledig in PMS: inbox, composeren vanuit dossier met auto-koppeling
- **Clio:** Communicate tab in matter: email composition met contact picker uit matter parties
- **Kleos:** Outlook plugin + dossier-communicatie tab: email met auto-filing
- **PracticePanther:** Email tab per matter, compose with pre-filled recipients from matter
- **Smokeball:** Outlook integration met auto-filing + compose vanuit matter
- **Hammock:** Outlook native met BCC auto-koppeling + dossier-inbox

**Complexiteit: L (hangt af van M365 integratie)**
- **Korte termijn (M - 12-16 uur):** SMTP-based "Snel e-mail sturen" vanuit dossier
  - Recipient picker (alle partijen in dossier)
  - Simpel compose formulier (onderwerp, body, bijlage)
  - Via bestaande SMTP service versturen
  - E-mail opslaan als activiteit
- **Lange termijn:** Volledige M365 integratie (zie LUXIS-ROADMAP.md M1-M6)

---

### 7. Referentienummer van de andere partij

**Waarom niet eerder gevonden:**
Luxis heeft een `reference` veld op het Case model — maar dat is voor het referentienummer van de cliënt. Wat ontbreekt is een referentienummer per dossierpartij. Bijvoorbeeld: het incassobureau heeft referentie "INC-2024-0456", de deurwaarder heeft "DW-789". Dit moet op de case_party koppeling zitten, niet op het contact.

**Backend status:**
- ✅ `Case.reference` — cliënt-referentienummer
- ❌ `CaseParty` heeft GEEN `reference` veld — referentienummer per partij ontbreekt
- Nodig: `external_reference` op CaseParty

**Wat concurrenten doen:**
- **BaseNet:** Per dossierpartij: "Kenmerk andere partij" veld
- **Clio:** Matter > Relationships: per linked contact een "Reference" veld
- **Kleos:** Per dossierpartij: "Referentie" veld
- **PracticePanther:** Per matter relationship: "Their Reference" field
- **Smokeball:** Per matter party: external reference number

**Complexiteit: S (4-6 uur)**
- Backend: migration `external_reference` (String(100), nullable) op case_parties tabel
- Backend: schema update (CasePartyCreate, CasePartyResponse)
- Frontend: referentieveld toevoegen bij partij-koppeling + tonen in Partijen-tab
- Frontend: referentie beschikbaar maken voor documentgeneratie

---

### 8. Nieuwe contactpersoon aanmaken vanuit relatie-koppeling

**Waarom niet eerder gevonden:**
De UX review heeft de ContactLink (persoon→bedrijf koppeling) gezien als een bestaand-contact-selectie flow. In de praktijk heb je vaak een nieuwe contactpersoon nodig (bijv. de nieuwe contactpersoon bij een bedrijf dat je net als cliënt aanneemt). Het moeten navigeren naar /relaties/nieuw, daar aanmaken, dan terug gaan en koppelen — dat is 4+ klikken te veel.

**Backend status:**
- ✅ Contact create endpoint: POST /api/relations
- ✅ ContactLink create endpoint: POST /api/relations/links
- ❌ Geen gecombineerd "create + link" endpoint
- De frontend kan dit oplossen met een inline modal zonder backend wijziging

**Wat concurrenten doen:**
- **BaseNet:** "+" knop bij contactpersonen → inline formulier binnen de relatiepagina
- **Clio:** "Create New Contact" button in contact picker → slide-over panel
- **Kleos:** "Nieuwe relatie" knop in koppeldialoog → inline formulier
- **PracticePanther:** Quick-add contact from anywhere with inline form
- **Smokeball:** "New Contact" in any contact selector → modal

**Complexiteit: S (4-6 uur)**
- Geen backend wijziging nodig
- Frontend: modal/slide-over met mini-contactformulier
- Na aanmaken: automatisch koppelen als contactpersoon
- Herbruikbaar component (ook nuttig bij zaak-aanmaken voor opposing party)

---

### 9. Filters op dossier-overzicht

**Waarom niet eerder gevonden:**
Er zijn al filters! De backend ondersteunt: `case_type`, `status`, `client_id`, `search`, `is_active`. De frontend toont search + case_type + status dropdowns. Wat ontbreekt:
1. **Meer filtermogelijkheden:** rechtbank, datum range, toegewezen advocaat
2. **Filter-persistentie:** filters onthouden na navigatie
3. **Gecombineerde filters:** meerdere statussen tegelijk

**Backend status:**
- ✅ Filter op `case_type` — werkt
- ✅ Filter op `status` — werkt (maar slechts 1 status tegelijk)
- ✅ Filter op `client_id` — werkt
- ✅ Zoeken in case_number, description, reference, client name, opposing party name
- ❌ GEEN filter op `assigned_to_id` (backend ontbreekt)
- ❌ GEEN filter op datum-range (date_opened)
- ❌ GEEN filter op rechtbank (zou via case_parties moeten, complex)
- ❌ GEEN multi-status filter

**Wat concurrenten doen:**
- **BaseNet:** Uitgebreide filterbalk: status (multi-select), zaaktype, datum range, advocaat, afdeling, zaaksoort + "bewaar deze filter" functie
- **Clio:** Sidebar filters: matter type, status, responsible attorney, practice area, originating attorney, open/closed date range, custom field filters
- **Kleos:** Filter panel: status, type, verantwoordelijke, datum, cliënt, wederpartij + opgeslagen filtersets
- **PracticePanther:** Multi-filter with saved views: status, type, attorney, date range, practice area, tags
- **Smokeball:** Smart lists met gecombineerde filters + custom saved views

**Complexiteit: M (10-14 uur)**
- Backend: `assigned_to_id` filter toevoegen (S - 1 uur)
- Backend: `date_from`/`date_to` filter toevoegen (S - 1 uur)
- Frontend: uitgebreide filterbalk met chips/pills
- Frontend: filter state opslaan in localStorage (persistentie)
- Frontend: "Wis filters" button verbeteren + filter count badge

---

### 10. Zoekfunctie werkt niet goed

**Waarom niet eerder gevonden:**
De command palette (Ctrl+K) roept `/api/search?q=...` aan — maar **dit endpoint bestaat niet in de backend**. Er is nooit een global search router gebouwd. De frontend component is gebouwd op basis van een verwachte API die nooit is geïmplementeerd. Dit is een kritieke bug: de zoekfunctie geeft altijd geen resultaten.

**Backend status:**
- ❌ `/api/search` endpoint BESTAAT NIET
- ✅ Individuele zoekfuncties per module (cases, relations, invoices) werken wél via hun eigen endpoints
- Nodig: een globaal search endpoint dat alle modules doorzoekt

**Frontend status:**
- ✅ Command palette component bestaat (Ctrl+K)
- ✅ UI is goed: search input, resultaten per type, keyboard navigatie
- ❌ Roept niet-bestaand endpoint aan → altijd lege resultaten

**Wat concurrenten doen:**
- **BaseNet:** Globale zoekbalk: zoekt over dossiers, relaties, documenten, e-mails, notities. Resultaten gegroepeerd per type.
- **Clio:** Command bar + global search: zoekt over matters, contacts, documents, time entries, invoices. AI-assisted fuzzy matching.
- **Kleos:** Globale zoek: dossiers, relaties, correspondentie, documenten. Met type-filter op resultaten.
- **PracticePanther:** Universal search over all entities
- **Smokeball:** Smart search with recent items + global results

**Complexiteit: M (8-10 uur)**
- Backend: nieuw `/api/search` endpoint
  - Zoek in cases (case_number, description, reference, client name)
  - Zoek in contacts (name, email, kvk_number, phone)
  - Zoek in documents (original_filename, description)
  - Resultaten samenvoegen met type-label
  - Limiet per type (bijv. max 5 per categorie)
- Frontend: command palette werkt al — hoeft alleen de juiste data te krijgen

---

## Gap-analyse: Luxis vs Concurrenten

### Dossier als werkhub — vergelijking

| Functie | BaseNet | Clio | Kleos | PP | Smokeball | **Luxis** |
|---------|---------|------|-------|-----|-----------|-----------|
| **Basis dossierinfo** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Meerdere adressen** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ Backend ja, UI nee |
| **Geboortedatum** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Facturatie-profiel** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Afwijkende factuurrelatie** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Rechtbank/rolnummer** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ CaseParty ja, veld nee |
| **E-mail vanuit dossier** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Ref.nr andere partij** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Inline contact aanmaken** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Geavanceerde filters** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ Basis |
| **Globale zoekfunctie** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ (broken) |
| **Documentgeneratie** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Urenadministratie** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Workflow/taken** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Incasso-specifiek** | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅✅ Uniek sterk |
| **KYC/WWFT** | ⚠️ | ❌ | ⚠️ | ❌ | ❌ | ✅ |
| **Derdengelden** | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Wettelijke rente** | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅✅ Uniek sterk |
| **Agenda/kalender** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Wat Luxis beter doet dan concurrenten
1. **Incasso-workflow:** Gespecialiseerd (14-dagenbrief, sommatie, dagvaarding) — geen enkele concurrent heeft dit als first-class feature
2. **Wettelijke rente:** Automatische berekening per half-jaar conform BW — uniek
3. **KYC/WWFT:** Ingebouwd compliance-systeem
4. **Derdengelden:** Volledig trust account systeem met goedkeuringsflow

### Wat Luxis mist (prioriteit)
1. **P0-KRITIEK:** Zoekfunctie werkt niet (endpoint bestaat niet)
2. **P0-QUICK WINS:** Postadres tonen, geboortedatum, referentienummer partij, rechtbank-UI
3. **P1-MIDDEL:** Facturatieprofiel, afwijkende factuurrelatie, inline contact, betere filters
4. **P2-GROOT:** E-mail vanuit dossier (afhankelijk M365)

---

## Additionele gaps (gevonden via competitor research)

Naast Lisanne's 10 punten vallen deze zaken op bij concurrenten die Luxis ook mist:

| # | Gap | Bij wie | Complexiteit | Prioriteit |
|---|-----|---------|-------------|-----------|
| 11 | **Tags/labels op dossiers** | Clio, PP, Smokeball | S | P2 |
| 12 | **Telefoonnotitie vanuit dossier** | BaseNet, Clio, Kleos | XS (activity type) | P1 |
| 13 | **Secure client portal** | Clio, PP | XL | P3 |
| 14 | **Conflictencheck bij nieuw dossier** | ✅ Luxis heeft dit al | - | - |
| 15 | **Bulk acties (facturen, status)** | ✅ Luxis heeft bulk status + export | - | - |
| 16 | **Praktijkgebied/rechtsgebied** | Clio, Kleos | S | P2 |
| 17 | **Verjaring/prescriptie waarschuwing** | ✅ Luxis heeft dit (incasso) | - | - |

---

## Zelfkritiek: waarom dit niet eerder is gevonden

### Patroon 1: "Backend-first blindheid"
De backend is technisch sterk gebouwd (postal address bestaat, CaseParty model is flexibel), maar de **frontend brengt die mogelijkheden niet naar de gebruiker**. Het bouwen was te veel vanuit "welke API's hebben we" in plaats van "wat heeft de advocaat nodig op haar scherm".

### Patroon 2: "Feature-module denken vs. workflow denken"
Features zijn gebouwd als modules (relaties, zaken, facturatie) in plaats van als workflow ("ik open een dossier en doe daar ALLES"). Lisanne denkt in workflows, niet in modules.

### Patroon 3: "Concurrentie-analyse zonder veldniveau check"
De concurrentie-analyse keek naar feature-categorieën (heeft Clio uren? ja ✓) maar niet naar individuele velden (heeft Clio geboortedatum op een contact? ja). De granulariteit was te laag.

### Hoe te voorkomen in de toekomst:
1. **Schaduw-sessie:** 30 min meekijken met Lisanne's dagelijks werk in BaseNet
2. **Veld-voor-veld vergelijking:** Niet "heeft concurrent X facturatie" maar "welke velden heeft concurrent X op het contactformulier"
3. **Workflow-mapping:** Per dagelijkse taak (nieuw dossier openen, brief sturen, factuur maken) het pad door de UI doorlopen

---

## Implementatie-volgorde

### Sprint 1: P0 Quick Wins (geschat: 3-4 dagen)
1. **🔴 Zoekfunctie fixen** — `/api/search` endpoint bouwen (M)
2. **Postadres tonen** in relatie edit/view (XS)
3. **Geboortedatum** toevoegen aan Contact model + UI (S)
4. **Referentienummer partij** toevoegen aan CaseParty + UI (S)
5. **Rechtbank/rolnummer UI** — procesgegevens sectie in dossier (S)

### Sprint 2: P1 Uitbreidingen (geschat: 5-7 dagen)
6. **Facturatieprofiel** bij relaties (M)
7. **Afwijkende factuurrelatie** per dossier (M)
8. **Inline contact aanmaken** — herbruikbare modal (S)
9. **Uitgebreide filters** op dossier-overzicht (M)
10. **Telefoonnotitie** als activiteit type (XS)

### Sprint 3: P2 E-mail & Polish (afhankelijk M365)
11. **E-mail vanuit dossier** (basis SMTP versie)
12. **Tags/labels** op dossiers
13. **Praktijkgebied** als dossier-classificatie
