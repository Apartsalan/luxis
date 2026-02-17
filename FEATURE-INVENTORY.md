# Luxis — Feature Inventory

> Samengesteld op basis van onderzoek naar Basenet, Kleos (Wolters Kluwer), Urios,
> LegalSense, NEXTmatters, CClaw, Clio, CE-iT/MA!N en iFlow.
>
> **Doel**: Compleet overzicht van alle features die een modern PMS voor een
> Nederlands advocatenkantoor (specifiek: incasso & insolventierecht) moet hebben.
> Arsalan & Lisanne reviewen dit document en markeren per feature: bouwen / niet bouwen / later.
>
> **Classificatie**:
> - **MUST** = Standaard in elk PMS, zonder dit kun je niet werken
> - **SHOULD** = Gangbaar, verwacht door de meeste kantoren
> - **COULD** = Nice-to-have, differentiator
> - **INNOVATIVE** = Cutting-edge, weinig PMS-systemen bieden dit

---

## Module 1: Relatiebeheer (CRM / Contact Management)

### 1.1 Contactgegevens — MUST
- [ ] Bedrijven en personen als aparte entiteiten
- [ ] Koppeling persoon ↔ bedrijf (functie, afdeling)
- [ ] Adres, telefoon, e-mail, KvK-nummer, BTW-nummer
- [ ] Meerdere adressen per relatie (bezoek, post, factuur)
- [ ] Vrije velden / tags per relatie
- [ ] Zoeken en filteren op alle velden
- [ ] Import/export (CSV, vCard)

### 1.2 Partijrollen — MUST
- [ ] Relatie kan meerdere rollen hebben: cliënt, wederpartij, deurwaarder, rechtbank, etc.
- [ ] Rollenhistorie per dossier (wie was wanneer wat)
- [ ] Automatische suggestie van bestaande relaties bij aanmaak

### 1.3 Conflict Check — MUST
- [ ] Bij nieuw dossier: automatisch controleren of wederpartij al cliënt is (of was)
- [ ] Zoeken op naam, KvK, e-mail, BSN
- [ ] Conflict-logboek (wie heeft wanneer gecontroleerd, resultaat)
- [ ] Blokkering dossier bij onopgelost conflict

### 1.4 WWFT / KYC — MUST
- [ ] Cliëntidentificatie vastleggen (type ID, nummer, datum verificatie)
- [ ] UBO-registratie
- [ ] Risicoclassificatie (laag/midden/hoog)
- [ ] Wwft-dossier per relatie met checklijst
- [ ] Melding ongebruikelijke transacties (FIU-Nederland)
- [ ] Bewaarplicht 5 jaar na einde dienstverlening
- [ ] Export/rapport voor NOvA-toezicht

### 1.5 Cliëntportaal — SHOULD
- [ ] Cliënt kan eigen dossier(s) inzien
- [ ] Documenten uploaden
- [ ] Berichten sturen naar behandelaar
- [ ] Facturen en betalingen inzien
- [ ] Vragenlijsten invullen (intake)

### 1.6 Communicatielog — SHOULD
- [ ] Alle contactmomenten vastleggen (telefoon, e-mail, brief, vergadering)
- [ ] Automatisch koppelen aan dossier
- [ ] Notities en gespreksverslagen

---

## Module 2: Dossierbeheer (Case/Matter Management)

### 2.1 Dossier CRUD — MUST
- [ ] Aanmaken met type (incasso, insolventie, advies, etc.)
- [ ] Automatische dossiernummering (configureerbaar formaat)
- [ ] Koppeling aan cliënt, wederpartij, overige partijen
- [ ] Verantwoordelijk advocaat + behandelaar(s)
- [ ] Status-workflow (zie Module 5)
- [ ] Referentievelden (eigen ref, cliënt ref, zaak ref)
- [ ] Vrije velden / metadata per dossiertype
- [ ] Archiveren en heropenen

### 2.2 Dossieroverzicht — MUST
- [ ] Lijst/tabel met alle dossiers, filterable en sorteerbaar
- [ ] Snelzoeken op dossiernr, partijnaam, referentie
- [ ] Groepering op status, type, behandelaar
- [ ] Kanban-view (optioneel drag & drop)

### 2.3 Dossier-activiteitlog — MUST
- [ ] Chronologisch overzicht van alle acties op het dossier
- [ ] Wie deed wat wanneer (audit trail)
- [ ] Filteren op type actie (brief, betaling, status, etc.)

### 2.4 Subdossiers / Gekoppelde dossiers — SHOULD
- [ ] Meerdere vorderingen onder één hoofddossier
- [ ] Koppeling gerelateerde dossiers (bijv. incasso → faillissement)
- [ ] Cross-referentie zoeken

### 2.5 Templates per dossiertype — SHOULD
- [ ] Standaard velden, documenten, taken per type
- [ ] Automatisch aanmaken van startdocumenten bij nieuw dossier
- [ ] Configureerbaar door admin

---

## Module 3: Incassomodule (Collections) ⭐ KERNMODULE

> Dit is de belangrijkste module voor Kesting Legal.
> Elke feature hieronder moet juridisch correct zijn volgens Nederlands recht.

### 3.1 Vordering Registratie — MUST
- [ ] Factuurnummer, factuurdatum, vervaldatum, bedrag
- [ ] Meerdere vorderingen per dossier
- [ ] Hoofdsom per vordering
- [ ] Status per vordering (open, deels betaald, betaald, afgeboekt)
- [ ] Opmerkingen per vordering
- [ ] Batch-invoer (meerdere vorderingen tegelijk)
- [ ] Import vanuit CSV / boekhoudsysteem

### 3.2 Renteberekening — MUST
> Alle bedragen in `Decimal` / `NUMERIC(15,2)`. Geen floats. Nooit.

#### Rentetype selectie per dossier:
- [ ] **Wettelijke rente** (art. 6:119 BW) — consumenten (B2C, C2C)
- [ ] **Wettelijke handelsrente** (art. 6:119a BW) — zakelijk (B2B)
- [ ] **Overheidshandelsrente** (art. 6:119b BW) — overheid als debiteur
- [ ] **Contractuele rente** — vrij in te stellen percentage per dossier

#### Compound vs. Simple interest:
- [ ] Wettelijke rente: **samengestelde rente** (compound, jaarlijks)
- [ ] Handelsrente: **samengestelde rente** (compound, jaarlijks)
- [ ] Overheidshandelsrente: **samengestelde rente** (compound, jaarlijks)
- [ ] Contractuele rente: **configureerbaar** (enkelvoudig of samengesteld)
  - Default: enkelvoudig (als contract niets zegt)
  - Optioneel: samengesteld (als contract dit bepaalt)

#### Berekeningsregels:
- [ ] Rente per periode berekenen (tarieven wijzigen per halfjaar/KB)
- [ ] Historische rentetarieven tabel (1934 t/m heden, uit seed data)
- [ ] Ingangsdatum rente = verzuimdatum (niet per se factuurdatum)
- [ ] Einddatum rente = datum betaling of berekendatum
- [ ] Bij compound: "telkens na afloop van een jaar" toevoegen aan hoofdsom
- [ ] Jaar loopt vanaf verzuimdatum, NIET vanaf 1 januari
- [ ] Pro-rata berekening bij gebroken periodes
- [ ] Renteberekening-rapport genereren (Word/PDF)
- [ ] Overzicht met per periode: tarief, dagen, berekende rente

### 3.3 Buitengerechtelijke Incassokosten (BIK) — MUST

#### WIK-staffel (art. 6:96 BW, sinds 1 juli 2012):
- [ ] Automatische berekening op basis van hoofdsom
- [ ] Staffel: 15% over eerste €2.500, 10% over €2.500-€5.000, 5% over €5.000-€10.000, 1% over €10.000-€200.000, 0,5% over €200.000+
- [ ] Minimum: €40
- [ ] Maximum: €6.775
- [ ] BTW optie: wel/niet btw-plichtige schuldeiser (21% BTW over BIK)

#### Voorwerk II (pre-2012, legacy):
- [ ] Staffel met vaste bedragen per schijf
- [ ] Alleen voor zaken waar 14-dagenbrief vóór 1 juli 2012 is verzonden

#### 14-dagenbrief:
- [ ] Template generatie met juiste wettelijke formulering
- [ ] Automatisch invullen hoofdsom + berekende BIK
- [ ] Datum verzending registreren (voor termijnbewaking)
- [ ] Termijn: 14 dagen na ontvangst (niet na verzending!)

### 3.4 Betalingsverkeer — MUST

#### Betalingen registreren:
- [ ] Ontvangen betaling boeken op dossier
- [ ] Datum, bedrag, betalingskenmerk, bron
- [ ] Automatisch verdelen via **art. 6:44 BW**: kosten → rente → hoofdsom
- [ ] Handmatig overschrijven van verdeling (met audit log)
- [ ] Deelbetalingen bijhouden
- [ ] Restschuld automatisch herberekenen na betaling

#### Betalingsregelingen:
- [ ] Betalingsregeling aanmaken (bedrag per termijn, frequentie, startdatum)
- [ ] Automatisch controleren of termijnen worden nagekomen
- [ ] Signalering bij gemiste termijn
- [ ] Regeling beëindigen bij wanbetaling (hele restschuld weer opeisbaar)
- [ ] Overzicht actieve regelingen

### 3.5 Derdengelden (Stichting Derdengelden) — MUST
- [ ] Aparte derdengelden-administratie per dossier
- [ ] Ontvangst boeken op derdengeldenrekening
- [ ] Afdracht aan cliënt registreren
- [ ] Inhouding (eigen declaratie, kosten)
- [ ] Saldo per dossier inzien
- [ ] Totaalsaldo derdengelden over alle dossiers
- [ ] Afstorting: derden → kantoorrekening voor eigen declaratie
- [ ] Rapportage voor Stichting Derdengelden (jaaroverzicht)

### 3.6 Provisies & Commissie — SHOULD
- [ ] Commissiepercentage per dossier instellen
- [ ] Berekening over geïncasseerd bedrag
- [ ] Minimumvergoeding instellen
- [ ] Rapportage commissie-inkomsten per periode

### 3.7 Incasso Workflow — MUST

#### Standaard fasen:
- [ ] **Aanmaning** — eerste herinnering door cliënt
- [ ] **14-dagenbrief** — wettelijk vereiste brief (art. 6:96 BW)
- [ ] **Sommatie** — brief van advocaat
- [ ] **Dagvaarding** — gerechtelijke procedure starten
- [ ] **Vonnis** — vonnis ontvangen
- [ ] **Executie** — deurwaarder, beslag, etc.
- [ ] **Betaald / Afgesloten** — dossier afronden

#### Workflow features:
- [ ] Configureerbare workflow per dossiertype
- [ ] Automatische taak-generatie bij statuswijziging
- [ ] Termijnen per fase (bijv. 14 dagen na sommatie → escaleren)
- [ ] Handmatige override mogelijk (met reden)
- [ ] Visuele workflow-indicator op dossier

### 3.8 Kosten & Berekeningen — MUST

#### Proceskosten:
- [ ] Griffierecht berekenen op basis van vorderingshoogte + sector
- [ ] Salaris gemachtigde / advocaat (liquidatietarief)
- [ ] Explootkosten deurwaarder
- [ ] Nakosten
- [ ] Totaaloverzicht proceskosten

#### BTW-berekening:
- [ ] 21% BTW over BIK (als schuldeiser btw-plichtig)
- [ ] BTW over eigen honorarium
- [ ] BTW-vrij markeren voor bepaalde kosten

#### Kostenspecificatie:
- [ ] Gedetailleerde specificatie genereren voor rechtbank
- [ ] Export naar Word/PDF

### 3.9 Bulk Operaties — SHOULD
- [ ] Meerdere dossiers tegelijk aanmaken (batch import)
- [ ] Statuswijziging voor meerdere dossiers
- [ ] Bulk brief/e-mail genereren en verzenden
- [ ] Bulk renteberekening uitvoeren
- [ ] Bulk betalingsimport (CSV/MT940)
- [ ] Selectie op basis van filters (status, bedrag, leeftijd, etc.)

### 3.10 Afboeking & Oninbaarheid — SHOULD
- [ ] Vordering (deels) afboeken met reden
- [ ] Rapportage oninbare vorderingen
- [ ] Notificatie na x maanden zonder betaling
- [ ] Heractivering mogelijk na afboeking

---

## Module 4: Insolventiemodule — SHOULD

> Kesting Legal doet ook insolventie. Aparte module, maar gerelateerd aan incasso.

### 4.1 Faillissementsdossier — SHOULD
- [ ] Dossiertype "faillissement" met specifieke velden
- [ ] Curator, rechter-commissaris, rechtbank vastleggen
- [ ] Schuldenlijst bijhouden (preferent, concurrent, boedel)
- [ ] Uitdelingslijst beheren
- [ ] Verslagen voor rechtbank genereren

### 4.2 WSNP — SHOULD
- [ ] Dossiertype "schuldsanering" (WSNP)
- [ ] Bewindvoerder-gegevens
- [ ] Saneringsplan bijhouden
- [ ] Termijn saneringsperiode bewaken

### 4.3 Recofa-rapportage — SHOULD
- [ ] Verslagen conform Recofa-richtlijnen
- [ ] Template voor curator-/bewindvoerderverslagen

---

## Module 5: Workflow & Statusbeheer

### 5.1 Statusmodel — MUST
- [ ] Configureerbare statussen per dossiertype
- [ ] Statusovergangen definiëren (bijv. sommatie → dagvaarding, niet andersom)
- [ ] Verplichte velden per status (bijv. vonnis vereist datum vonnis)
- [ ] Automatische triggers bij statuswijziging (taken, notificaties)

### 5.2 Taken — MUST
- [ ] Taak aanmaken, toewijzen, deadline instellen
- [ ] Taak koppelen aan dossier
- [ ] Takenlijst per medewerker
- [ ] Terugkerende taken (bijv. maandelijkse controle)
- [ ] Prioriteiten en labels
- [ ] Melding bij deadline nadering

### 5.3 Termijnbewaking — MUST
- [ ] Automatische termijnen bij acties (14 dagen na brief, etc.)
- [ ] Waarschuwing vóór verstrijken termijn (configureerbaar: 1, 3, 7 dagen)
- [ ] Overzicht openstaande termijnen per medewerker
- [ ] Wettelijke termijnen (beroepstermijn, verjaringstermijn)
- [ ] Kalender-integratie (zie Module 8)

### 5.4 Automatisering — COULD
- [ ] Automatisch brief/e-mail sturen na x dagen
- [ ] Automatisch status wijzigen na ontvangst betaling
- [ ] Automatisch taak aanmaken bij nieuwe event
- [ ] Workflow-engine met if/then regels

---

## Module 6: Tijdschrijven (Time Registration)

### 6.1 Urenregistratie — MUST
- [ ] Handmatige invoer (uren/minuten, of decimaal)
- [ ] Stopwatch/timer functie
- [ ] Koppeling aan dossier (verplicht)
- [ ] Activiteitcodes (vergadering, correspondentie, telefoneren, studie, etc.)
- [ ] Declarabel / niet-declarabel markeren
- [ ] Uurtarief per medewerker, per dossier, of per activiteit
- [ ] Correctie en verwijdering met audit trail
- [ ] Bulk invoer voor meerdere uren

### 6.2 Urenoverzichten — MUST
- [ ] Per medewerker: dag/week/maand overzicht
- [ ] Per dossier: totaal bestede uren + kosten
- [ ] Rapportage: billability ratio, realisatie
- [ ] Export naar facturatie (uren → declaratie)

### 6.3 Mobiel tijdschrijven — SHOULD
- [ ] App of mobiele webversie
- [ ] Timer op telefoon
- [ ] Offline registratie, sync bij verbinding

---

## Module 7: Facturatie & Financieel

### 7.1 Declaraties — MUST
- [ ] Declaratie genereren op basis van uren + verschotten
- [ ] Conceptdeclaratie voor review
- [ ] Goedkeuringsworkflow (behandelaar → partner)
- [ ] Vaste bedragen (fixed fee) per dossier
- [ ] Abonnementsfacturatie (terugkerend, bijv. kvartaal)
- [ ] Deelfacturatie / tussentijdse declaratie
- [ ] Creditnota

### 7.2 Factuurlayout — MUST
- [ ] Huisstijl template (logo, kleuren, etc.)
- [ ] Urenspecificatie op factuur (optioneel)
- [ ] Meertalig (NL, EN, DE, FR)
- [ ] PDF generatie
- [ ] E-facturatie (UBL/eConnect voor overheidsopdrachtgevers)

### 7.3 Betalingsbeheer — MUST
- [ ] Openstaande facturen overzicht
- [ ] Betalingstermijn per factuur
- [ ] Automatische herinneringen (1e, 2e, 3e aanmaning)
- [ ] Ouderdomsanalyse (aging) van debiteuren
- [ ] Deelbetaling registreren
- [ ] Afboeken oninbare facturen

### 7.4 Verschotten (Expenses) — MUST
- [ ] Voorgeschoten kosten registreren (griffierecht, uittreksels, etc.)
- [ ] BTW per verschot (0%, 9%, 21%)
- [ ] Doorbelasten aan cliënt op factuur
- [ ] Bonnen/bewijsstukken uploaden

### 7.5 Toevoegingen (Legal Aid) — SHOULD
- [ ] Dossier markeren als toevoeging
- [ ] Eigen bijdrage berekenen
- [ ] Export naar Mijn RvR (XML)
- [ ] Tracking vergoeding van Raad voor Rechtsbijstand

### 7.6 Boekhoudkoppeling — SHOULD
- [ ] Koppeling met Exact Online, Twinfield, AFAS, Xero
- [ ] Automatische journaalposten
- [ ] BTW-aangifte ondersteuning
- [ ] Grootboekrekeningen mapping

### 7.7 Betalingsopties — SHOULD
- [ ] iDEAL betaallink op factuur
- [ ] Mollie / Stripe integratie
- [ ] QR-code op factuur
- [ ] Online betalingspagina

---

## Module 8: Agenda & Kalender

### 8.1 Kalender — MUST
- [ ] Dag/week/maand weergave
- [ ] Afspraak aanmaken, koppelen aan dossier
- [ ] Meerdere agenda's (per medewerker)
- [ ] Outlook/Microsoft 365 synchronisatie

### 8.2 Zittingsplanning — SHOULD
- [ ] Zittingsdatum registreren met rechtbank, zaalnr, tijdstip
- [ ] Herinnering vóór zitting (configureerbaar)
- [ ] Reistijd inplannen

### 8.3 Deadlines & Termijnen — MUST
- [ ] Termijnen zichtbaar in kalender
- [ ] Kleurcodering op urgentie
- [ ] Dagelijkse/wekelijkse samenvatting e-mail

---

## Module 9: Documentbeheer (DMS)

### 9.1 Documentopslag — MUST
- [ ] Documenten uploaden en koppelen aan dossier
- [ ] Mapstructuur per dossier (automatisch aangemaakt)
- [ ] Versiebeheer (v1, v2, etc.)
- [ ] Preview in browser (PDF, Word, afbeeldingen)
- [ ] Zoeken in documentinhoud (full-text search)

### 9.2 Documentgeneratie — MUST
- [ ] Word-templates met placeholders (docxtpl)
- [ ] Automatisch vullen: partijgegevens, bedragen, data, renteberekening
- [ ] Templates per dossiertype (incasso: 14-dagenbrief, sommatie, dagvaarding, etc.)
- [ ] PDF conversie
- [ ] Batch generatie (meerdere brieven voor meerdere dossiers)

### 9.3 Templates — MUST

#### Incasso-specifieke templates:
- [ ] 14-dagenbrief (art. 6:96 BW, exacte wettelijke formulering)
- [ ] Sommatie
- [ ] Dagvaarding (kanton / handelsrecht)
- [ ] Renteberekening-rapport
- [ ] Kostenspecificatie
- [ ] Betalingsregeling bevestiging
- [ ] Sluitingsbrief (dossier afgerond)

#### Algemene templates:
- [ ] Opdrachtbevestiging / overeenkomst van opdracht
- [ ] Algemene voorwaarden
- [ ] Brieven (standaard kantoorstijl)

### 9.4 E-signing — COULD
- [ ] Digitale handtekening (Zynyo, DocuSign, Adobe Sign)
- [ ] Status tracking (verstuurd, bekeken, ondertekend)

---

## Module 10: E-mail Integratie

### 10.1 Outlook/365 Integratie — MUST
- [ ] E-mail opslaan bij dossier (drag & drop of knop)
- [ ] E-mail verzenden vanuit dossier
- [ ] Outlook add-in voor koppelen aan dossier
- [ ] Automatisch koppelen op basis van e-mailadres of referentie

### 10.2 E-mail Templates — SHOULD
- [ ] Sjablonen met placeholders (zoals bij documenten)
- [ ] Bulk e-mail verzenden (bijv. betalingsherinnering aan 50 debiteuren)
- [ ] Tracking (verzonden, geopend — optioneel)

### 10.3 E-mail Archivering — SHOULD
- [ ] Alle dossier-gerelateerde e-mail chronologisch bewaren
- [ ] Zoeken in e-mailinhoud
- [ ] Bijlagen automatisch opslaan in DMS

---

## Module 11: Rapportage & Dashboard

### 11.1 Dashboard — MUST
- [ ] Overzicht openstaande dossiers per status
- [ ] Financieel overzicht: omzet, openstaand, geïncasseerd
- [ ] Mijn taken / mijn deadlines
- [ ] Recente activiteit feed
- [ ] KPI's: gemiddelde incassoduur, slagingspercentage, omzet per maand

### 11.2 Management Rapportages — SHOULD
- [ ] Omzet per medewerker / per rechtsgebied
- [ ] Billability ratio per medewerker
- [ ] Debiteurenoverzicht (aging analyse)
- [ ] Incasso-resultaten: geïncasseerd vs. hoofdsom
- [ ] Dossier-doorlooptijd per type
- [ ] Commissie-/provisie-overzicht
- [ ] Export naar Excel/PDF

### 11.3 Financiële Rapportages — SHOULD
- [ ] Omzetrapportage per periode
- [ ] BTW-overzicht
- [ ] Derdengelden-saldo rapport
- [ ] Openstaande facturen rapport
- [ ] Cashflow overzicht

---

## Module 12: Compliance & Beveiliging

### 12.1 Gebruikersbeheer — MUST
- [ ] Rollen: admin, advocaat, secretaresse, financieel
- [ ] Rechten per module (lezen, schrijven, verwijderen)
- [ ] Multi-tenant isolatie (data van tenant A onzichtbaar voor B)
- [ ] Twee-factor authenticatie (2FA)
- [ ] Wachtwoordbeleid (complexiteit, verloop)

### 12.2 Audit Trail — MUST
- [ ] Elke wijziging loggen (wie, wat, wanneer, oude/nieuwe waarde)
- [ ] Onwijzigbaar log (append-only)
- [ ] Raadpleegbaar per dossier en per gebruiker
- [ ] Bewaarplicht: 7 jaar (fiscaal) / 5 jaar (Wwft)

### 12.3 AVG / GDPR — MUST
- [ ] Data export per betrokkene (recht op inzage)
- [ ] Data verwijdering (recht op vergetelheid, met uitzonderingen)
- [ ] Verwerkersovereenkomsten beheren
- [ ] Data minimalisatie (alleen noodzakelijke gegevens)
- [ ] Beveiligingsmaatregelen documenteren

### 12.4 Backup & Recovery — MUST
- [ ] Dagelijkse automatische backups
- [ ] Retentie: 30 dagen
- [ ] Restore procedure gedocumenteerd en getest
- [ ] Encryptie at rest en in transit

---

## Module 13: Integraties

### 13.1 Must-have Integraties — MUST
- [ ] Microsoft Outlook / 365 (e-mail, agenda)
- [ ] Word (documentgeneratie)
- [ ] PDF (WeasyPrint voor generatie)

### 13.2 Should-have Integraties — SHOULD
- [ ] Exact Online / Twinfield (boekhouding)
- [ ] Mollie / Stripe (betalingen)
- [ ] KvK API (bedrijfsgegevens opvragen)
- [ ] Kadaster (onroerend goed informatie)
- [ ] eConnect (e-facturatie overheid)
- [ ] Mijn RvR (toevoegingen export)

### 13.3 Nice-to-have Integraties — COULD
- [ ] Rechtspraak.nl (rolgegevens, ECLI opzoeken)
- [ ] Digitale handtekening (Zynyo, DocuSign)
- [ ] VoIP telefonie (automatisch loggen gesprekken)
- [ ] SharePoint / OneDrive (documentopslag)
- [ ] Company.info (bedrijfsinformatie)
- [ ] Creditinformatiediensten (Creditsafe, Graydon)
- [ ] Deurwaarder-koppeling (digitale opdracht → status updates)

---

## Module 14: AI & Innovatie

### 14.1 Documentanalyse — INNOVATIVE
- [ ] Automatisch samenvatten van juridische documenten
- [ ] Extractie van relevante gegevens (namen, bedragen, data)
- [ ] Vergelijking van documenten

### 14.2 Slimme Suggesties — INNOVATIVE
- [ ] Volgende stap suggereren op basis van dossierhistorie
- [ ] Risico-inschatting bij incassodossier (kans op betaling)
- [ ] Voorspelling doorlooptijd

### 14.3 Communicatie AI — INNOVATIVE
- [ ] Concept-brieven genereren
- [ ] E-mail samenvattingen
- [ ] Vertaling (NL ↔ EN ↔ Farsi)

---

## Module 15: Mobiele Toegang

### 15.1 Responsive Web — SHOULD
- [ ] Volledige applicatie bruikbaar op tablet/telefoon
- [ ] Touch-optimized interface

### 15.2 Offline Functionaliteit — COULD
- [ ] Tijdschrijven offline, sync bij verbinding
- [ ] Dossiergegevens cachen voor offline raadplegen

---

## Prioritering voor Luxis v1.0

### Fase 1: MVP (Maand 1-3) — Zonder dit kan Lisanne niet werken
1. Auth & Multi-tenant (✅ al gebouwd in Fase 0)
2. Relatiebeheer (basis)
3. Dossierbeheer (basis)
4. Incassomodule: vorderingen, renteberekening, BIK, betalingen, art. 6:44
5. Documentgeneratie (14-dagenbrief, sommatie, renteberekening)
6. Dashboard (basis)

### Fase 2: Productief (Maand 3-5) — Vervangt Basenet
7. Tijdschrijven
8. Facturatie (declaraties, verschotten)
9. Derdengelden
10. Betalingsregelingen
11. Workflow & termijnbewaking
12. E-mail integratie (Outlook)

### Fase 3: Compleet (Maand 5-8) — Beter dan Basenet
13. Insolventiemodule
14. Rapportage & management dashboards
15. Boekhoudkoppeling (Exact Online)
16. Cliëntportaal
17. Bulk operaties
18. WWFT/compliance module

### Fase 4: Innovatie (Maand 8+) — Differentiators
19. AI documentanalyse
20. Deurwaarder-koppeling
21. Creditinformatie-integratie
22. Mobiele app
23. E-signing

---

## Open Vragen voor Lisanne

> Deze punten moeten met Lisanne besproken worden voordat we ze bouwen.

1. **Welke boekhoudpakket gebruik je?** (Exact Online, Twinfield, ander?)
2. **Hoe werkt jullie derdengelden nu?** (Eigen Stichting? Welke bank?)
3. **Welke documenttemplates gebruik je dagelijks?** (Kunnen we kopieën krijgen?)
4. **Werken jullie met toevoegingen (RvR)?** (Zo ja, hoe vaak?)
5. **Welke deurwaarders werken jullie mee?** (Digitale koppeling gewenst?)
6. **Hoe registreer je nu uren?** (In Basenet? Stopwatch? Handmatig?)
7. **Welke Basenet-functies gebruik je het MEEST?** (Top 5)
8. **Welke Basenet-functies irriteren je het MEEST?** (Top 5)
9. **Heb je behoefte aan meertalige correspondentie?** (NL/EN/Farsi?)
10. **Hoeveel actieve dossiers heb je gemiddeld tegelijk?**

---

*Laatst bijgewerkt: februari 2026*
*Bronnen: Basenet, Kleos, Urios, LegalSense, NEXTmatters, CClaw, Clio, CE-iT, iFlow*
