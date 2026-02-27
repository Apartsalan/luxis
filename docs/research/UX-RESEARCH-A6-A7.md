# UX Research: Derdengelden (A6) & Financieel Overzicht per Zaak (A7)

**Datum:** 20 februari 2026
**Doel:** Concurrentieanalyse en UX-aanbevelingen voor twee Luxis-features

---

## Feature A6: Derdengelden UI

### 1. Wat concurrenten doen

#### Clio
- **Saldo-weergave:** Trust balance zichtbaar op zowel het matter-dashboard als het contactdashboard. Aparte sectie "Matter trust funds" toont saldo + minimale drempel.
- **Stortingen:** Via trust requests (e-mail, client portal, QR-code, click-to-pay). Ondersteunt creditcard, bank, cheque. Velden: datum, bron, client, zaak, bedrag, omschrijving.
- **Uitbetalingen:** Expliciete transfer van trust naar operating account. Systeem berekent beschikbaar saldo en blokkeert overdraft. "Protected funds" voor geoormerkte bedragen.
- **Reconciliatie:** Drie-weg reconciliatie ingebouwd (banksaldo vs. trust-grootboek vs. som client-ledgers). Drie kaarten bovenaan het reconciliatiescherm.
- **Bron:** [Clio Trust Accounting](https://www.clio.com/resources/legal-accounting/law-firm-trust-accounting/) | [Clio Reconciliation](https://help.clio.com/hc/en-us/articles/21058568234267)

#### LegalSense (NL/EU)
- **Specifiek voor derdengelden:** Ontworpen rond de Stichting Derdengelden-structuur. Aparte ledgers voor trust en operating.
- **Integratie:** Synchroniseert elke 12 minuten met Twinfield, Exact Online, Fortnox.
- **Velden:** Zaak (project), client, bedrag, datum, omschrijving, doel.
- **Autorisatie:** Ondersteunt twee-directeurengoedkeuring (Dutch bar vereiste). Logt welke directeuren goedkeurden + tijdstempel.
- **Rapportages:** Per-zaak trust-overzicht, audit-ready exports.
- **Bron:** [legalsense.com](https://legalsense.com)

#### PracticePanther
- **Saldo-weergave:** Trust Account Balance prominent op het matter-financieel overzicht.
- **Stortingen:** Via e-mail, SMS, client portal. Velden: datum, client, zaak, bedrag, stortingsmethode, omschrijving.
- **Protected funds:** Geoormerkte bedragen die niet per ongeluk verrekend kunnen worden met facturen.
- **Compliance:** Three-way reconciliation via TrustBooks-integratie. Custom rapporten voor state bar compliance.
- **UX-detail:** Kleurcodering en iconen om trust- vs. operating-transacties te onderscheiden. Dropdown-menu voorkomt commingling.
- **Bron:** [PracticePanther Trust Accounting](https://www.practicepanther.com/legal-billing/trust-accounting-2/)

#### Smokeball
- **Saldo-weergave:** Op de Transactions-tab van elke zaak: huidig saldo, protected funds, beschikbaar saldo, transactiehistorie.
- **Stortingen:** Via "Deposit funds"-knop. Velden: datum, account, zaak, contact, bedrag, type storting. Integratie met LawPay.
- **Trust Payment Requests:** Medewerker initieert betaalverzoek -> goedkeuring door boekhouder/eigenaar -> pas dan uitbetaling. Spiegelt het Dutch twee-directeurenmodel.
- **Protected funds:** Apart zichtbaar als eigen regel + "Available Funds" regel.
- **Reconciliatie:** Bank reconciliation ingebouwd, vergelijkt bank + intern + client-ledgers.
- **Bron:** [Smokeball Trust Overview](https://support.smokeball.com/hc/en-us/articles/13801106657815) | [Trust Payment Requests](https://support.smokeball.com/hc/en-us/articles/32152852866199)

#### BaseNet
- Minder gedetailleerde publieke documentatie. Biedt trust accounting als feature, matter-level tracking, integratie met boekhoudsoftware. Focus op eenvoud zonder dure implementatie.
- **Bron:** [Capterra BaseNet](https://www.capterra.com/p/196696/BaseNet/)

### 2. Nederlandse regelgeving (Stichting Derdengelden)

| Vereiste | Beschrijving |
|---|---|
| **Stichting Derdengelden** | Elke advocaat moet via een onafhankelijke stichting client-fondsen beheren |
| **Twee-directeurengoedkeuring** | Elke transactie vereist goedkeuring van twee directeuren (digitaal of schriftelijk) |
| **Schriftelijke toestemming client** | Geen betaling van advocaatkosten zonder voorafgaande schriftelijke toestemming client |
| **Nooit negatief saldo** | Derdengeldenrekening mag NOOIT negatief staan (tenzij schriftelijke toestemming toezichthouder) |
| **Audittrail** | Volledige logging van alle transacties, goedkeuringen, autorisaties |
| **Jaarlijkse verklaring** | Directeuren verklaren jaarlijks naleving procedures + rapporteren saldo |
| **Toezichthouder-bevoegdheid** | Deken/toezichthouder kan alle informatie opvragen, directeuren ontslaan, volmacht krijgen |
| **Alleen vaste opdrachten aan clients** | Alleen terugkerende betalingen aan clients of derden toegestaan |

### 3. Aanbevolen aanpak voor Luxis

#### Kernprincipes
1. **Derdengelden als first-class entity** — niet een subtab, maar een volwaardig onderdeel van zowel zaak- als clientweergave
2. **Compliance by design** — twee-directeurengoedkeuring en negatief-saldo-blokkade ingebouwd, niet optioneel
3. **Snelle boeking** — een advocaat moet in <30 seconden een storting of uitbetaling kunnen registreren
4. **Visuele scheiding** — duidelijk onderscheid tussen kantoorrekening en derdengeldenrekening via kleur/icoon

#### Minimale MVP-flow
```
Storting:  Zaakpagina -> "Derdengelden" tab -> "+ Storting" knop -> Quick-form (5 velden) -> Opslaan
Uitbetaling: Zaakpagina -> "Derdengelden" tab -> "+ Uitbetaling" knop -> Quick-form + goedkeuring -> Opslaan
```

### 4. Benodigde velden en componenten

#### Storting (Ontvangst)
| Veld | Type | Verplicht | Validatie |
|---|---|---|---|
| Datum | Date picker | Ja | Default vandaag, max vandaag |
| Bedrag | Currency input | Ja | > 0, twee decimalen |
| Zaak | Select (prefilled) | Ja | Moet actieve zaak zijn |
| Client | Select (prefilled) | Ja | Afgeleid van zaak |
| Omschrijving / Doel | Text | Ja | Min 3 tekens |
| Betalingsmethode | Select | Nee | Bank / iDEAL / Contant |
| Referentie | Text | Nee | Bankreferentie / kenmerk |

#### Uitbetaling (Disbursement)
| Veld | Type | Verplicht | Validatie |
|---|---|---|---|
| Datum | Date picker | Ja | Default vandaag |
| Bedrag | Currency input | Ja | > 0, <= beschikbaar saldo |
| Zaak | Select (prefilled) | Ja | Moet actieve zaak zijn |
| Begunstigde | Text / Select | Ja | Naam ontvanger |
| IBAN begunstigde | Text | Nee | IBAN-validatie |
| Omschrijving / Doel | Text | Ja | Min 3 tekens |
| Client-akkoord | Checkbox + upload | Ja* | *Bij betaling advocaatkosten |
| Goedkeuring directeur 1 | Systeem | Ja | Automatisch bij indiening |
| Goedkeuring directeur 2 | Systeem | Ja | Blokkeer tot 2e goedkeuring |

#### Overzichtscomponenten
- **Saldo-kaart:** Groot getal met kleur (blauw/groen). Toont: Totaal saldo, Geoormerkt (protected), Beschikbaar
- **Transactielijst:** Tabel met datum, type (storting/uitbetaling), bedrag, omschrijving, status, goedkeurders
- **Quick-actions:** "+ Storting" en "+ Uitbetaling" knoppen altijd zichtbaar
- **Reconciliatie-indicator:** Badge/chip die toont of de laatste reconciliatie actueel is

### 5. Wireframe-beschrijving (tekstueel)

```
+------------------------------------------------------------------+
| ZAAK: Van Dijk / Overdracht Keizersgracht 123       [Status: ●]  |
+------------------------------------------------------------------+
| [Overzicht] [Dossier] [Uren] [▼ Derdengelden] [Facturen] [...]  |
+------------------------------------------------------------------+
|                                                                   |
|  +-------------------+  +-------------------+  +----------------+ |
|  | TOTAAL SALDO      |  | GEOORMERKT        |  | BESCHIKBAAR    | |
|  | € 45.230,00   ⓘ  |  | € 10.000,00   🔒 |  | € 35.230,00   | |
|  | ▲ +€5.000 vandaag |  | Notariskosten     |  |                | |
|  +-------------------+  +-------------------+  +----------------+ |
|                                                                   |
|  [ + Storting ]  [ + Uitbetaling ]  [ ↕ Oormerken ]  [ ⟳ Recon ] |
|                                                                   |
|  TRANSACTIES                                    [Filter ▼] [Zoek] |
|  +------+--------+-----------+--------+--------+--------+------+ |
|  | Datum| Type   | Omschr.   | Bedrag | Saldo  | Status | Door | |
|  +------+--------+-----------+--------+--------+--------+------+ |
|  | 20/2 | ↓ Ont. | Waarborgsom| +5.000 | 45.230 | ✓ Goed.| AK  | |
|  | 18/2 | ↑ Uit. | Griffier.  | -1.200 | 40.230 | ✓ Goed.| MB  | |
|  | 15/2 | ↓ Ont. | Voorschot  | +25.000| 41.430 | ✓ Goed.| AK  | |
|  | 10/2 | ↑ Uit. | Kadaster   |   -570 | 16.430 | ✓ Goed.| MB  | |
|  | 05/2 | ↓ Ont. | Aanbetaling| +17.000| 17.000 | ✓ Goed.| AK  | |
|  +------+--------+-----------+--------+--------+--------+------+ |
|                                                                   |
|  Laatste reconciliatie: 15 feb 2026 ✓ Kloppend                    |
+------------------------------------------------------------------+
```

**Quick-form storting (modal/slide-over):**
```
+------------------------------------------+
| STORTING REGISTREREN                  [X] |
+------------------------------------------+
| Zaak:    Van Dijk / Keizersgracht  (vast)|
| Client:  De heer Van Dijk          (vast)|
|                                          |
| Datum:   [20-02-2026        📅]         |
| Bedrag:  [€ ______________ ]             |
| Doel:    [________________________]      |
| Methode: [Bankoverschrijving     ▼]      |
| Ref:     [________________________]      |
|                                          |
| [Annuleren]              [✓ Opslaan]     |
+------------------------------------------+
```

**Quick-form uitbetaling (modal/slide-over):**
```
+------------------------------------------+
| UITBETALING REGISTREREN               [X] |
+------------------------------------------+
| Zaak:    Van Dijk / Keizersgracht  (vast)|
| Beschikbaar: € 35.230,00                |
|                                          |
| Datum:       [20-02-2026        📅]     |
| Bedrag:      [€ ______________ ]         |
| Begunstigde: [________________________] |
| IBAN:        [NL__ ____ ____ ____ __]    |
| Doel:        [________________________]  |
|                                          |
| ☐ Dit betreft betaling advocaatkosten    |
|   → Client-akkoord uploaden: [Bestand]   |
|                                          |
| ⚠ Vereist goedkeuring 2e directeur      |
| [Annuleren]       [→ Ter goedkeuring]    |
+------------------------------------------+
```

---

## Feature A7: Financieel Overzicht per Zaak

### 1. Wat concurrenten doen

#### Clio
- **Layout:** Card-based matter dashboard met aparte secties per financieel thema.
- **KPI's:** Work in Progress (WIP), Outstanding Balance (openstaand), Trust Funds (derdengelden), Budget voortgang (progress bar), Total Time Entries, Total Expenses.
- **Visualisatie:** Kaarten met grote getallen, progress bar voor budget, timeline voor events. Configureerbaar per practice area.
- **Drill-down:** Klik op bedrag -> individuele facturen -> factuurregels -> urenregistraties.
- **AR Aging:** Aparte tab met aging-buckets (30/60/90/90+ dagen).
- **Bron:** [Clio Matter Overview](https://help.clio.com/hc/en-us/articles/9285920226075) | [Clio AR Dashboard](https://help.clio.com/hc/en-us/articles/21058568234267)

#### PracticePanther
- **KPI's:** Billable hours, billed amount, collected amount, trust balance, originating attorney, case profitability (incl. non-billable time).
- **Visualisatie:** "Bubbles" op hoofddashboard tonen real-time financiele status. Custom reports voor diepere analyse.
- **Uniek:** Case profitability tracking die zowel billable als non-billable uren meeneemt. Realization rate tracking.
- **AR Aging:** Filterbaar op contact of zaak, met customizable date ranges.
- **Bron:** [PracticePanther Custom Reports](https://www.practicepanther.com/blog/from-data-to-action-with-practicepanthers-custom-reports/) | [Case Profitability](https://www.practicepanther.com/assessing-true-case-profitability-in-practice-panther)

#### Smokeball
- **KPI's:** Total billed, total paid, unbilled, unpaid, cash retainer, expenses. Per zaak zichtbaar in Reports.
- **Visualisatie:** Tabellen met samenvattingen. Geintegreerd met billing cycle (invoice reminders, payment plans, rente-berekening).
- **Rapportages:** Trust, invoicing, matter overview, time/expenses als categorieën. Export naar PDF/CSV.
- **Bron:** [Smokeball Billing](https://www.smokeball.com/features/legal-billing-software)

#### Xero (Project View)
- **KPI's:** Project revenue, costs, profit, budget vs. actual, time tracked.
- **Visualisatie:** Profitability dashboard met progress indicators. "At-a-glance headline information."
- **Uniek:** Quote-to-invoice flow vanuit project. Progress payments. Project summary report voor vergelijking meerdere projecten.
- **Bron:** [Xero Projects](https://www.xero.com/us/accounting-software/track-projects/)

#### Exact Online
- **KPI's:** Project cost, revenue, budgeted vs. actual per periode.
- **Visualisatie:** Standaard rapportage-interface. Minder visueel dan Xero maar functioneel compleet.
- Goed voor Nederlandse markt vanwege lokale boekhoudintegratie.

#### HubSpot (Deal View)
- **Beperkt:** Alleen deal-waarde en closed/won status. Kan geen revenue over meerdere maanden spreiden. Geen trust accounting. Niet geschikt voor legal financial tracking.
- **Wel nuttig als referentie:** Clean card-layout, activity timeline, deal stage progress bar.
- **Bron:** [HubSpot Community](https://community.hubspot.com/t5/Dashboards-Reporting/Tracking-Revenue-Across-Multiple-Months/m-p/1101860)

### 2. Vergelijkende matrix: welke KPI's tonen concurrenten?

| KPI | Clio | PP | Smoke | Xero | Exact | HubSpot |
|-----|------|----|-------|------|-------|---------|
| Openstaand (AR) | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| Betaald | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Work in Progress | ✓ | ✓ | ✓ | ✓ | - | - |
| Derdengelden saldo | ✓ | ✓ | ✓ | - | - | - |
| Budget voortgang | ✓ | - | - | ✓ | ✓ | - |
| Kosten/verschotten | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| Winstgevendheid | - | ✓ | - | ✓ | - | - |
| Realisatiegraad | - | ✓ | - | - | - | - |
| AR Aging | ✓ | ✓ | ✓ | - | - | - |
| Non-billable time | - | ✓ | - | - | - | - |

### 3. Aanbevolen aanpak voor Luxis

#### Informatiehierarchie (boven de vouw)
1. **Vier hoofdkaarten** met de belangrijkste getallen:
   - Openstaand (wat de client nog moet betalen)
   - Betaald (wat al ontvangen is)
   - Onderhanden werk / WIP (nog te factureren uren + kosten)
   - Derdengelden saldo (link naar A6-tab)
2. **Budget progress bar** (indien budget ingesteld)
3. **Snelle acties** (Factuur maken, Uren boeken)

#### Onder de vouw
4. **Factuuroverzicht tabel** — alle facturen met status, bedrag, datum, aging
5. **Kosten/verschotten tabel** — doorbelastbare kosten apart
6. **Winstgevendheid kaart** (fase 2) — gefactureerd vs. werkelijke kosten

#### Design-principes
- Card-based layout (zoals Clio/HubSpot)
- Kleurcodering: groen = betaald, oranje = openstaand, rood = overdue
- Progressive disclosure: kaarten boven, tabellen onder, details via drill-down
- Configureerbaar per rechtsgebied (net als Clio practice area customization)

### 4. Benodigde velden en componenten

#### Hoofdkaarten (Summary Cards)
| Kaart | Waarde | Berekening | Kleur |
|---|---|---|---|
| Openstaand | EUR bedrag | Som onbetaalde factuurregels | Oranje (>30d: rood) |
| Betaald | EUR bedrag | Som ontvangen betalingen | Groen |
| Onderhanden werk | EUR bedrag | Uren x tarief + kosten (ongefactureerd) | Blauw |
| Derdengelden | EUR bedrag | Saldo derdengeldenrekening | Paars/blauw |

#### Budget Progress Bar
| Component | Details |
|---|---|
| Bar | Horizontale progress bar, kleur wijzigt bij >80% (oranje) en >100% (rood) |
| Label links | "Budget: € X.XXX" |
| Label rechts | "Besteed: € X.XXX (XX%)" |
| Tooltip | Breakdown: uren vs. kosten vs. verschotten |

#### Factuurtabel
| Kolom | Type |
|---|---|
| Factuurnummer | Link (drill-down naar factuur) |
| Datum | Date |
| Bedrag | Currency |
| Betaald | Currency |
| Openstaand | Currency |
| Status | Badge (Concept / Verzonden / Betaald / Overdue) |
| Ouderdom | Chip (Huidig / 30d / 60d / 90d+) |

#### Kosten/Verschotten tabel
| Kolom | Type |
|---|---|
| Datum | Date |
| Omschrijving | Text |
| Bedrag | Currency |
| Type | Badge (Griffierecht / Kadaster / Reiskosten / ...) |
| Gefactureerd | Boolean chip (Ja/Nee) |

### 5. Wireframe-beschrijving (tekstueel)

```
+------------------------------------------------------------------+
| ZAAK: Van Dijk / Overdracht Keizersgracht 123       [Status: ●]  |
+------------------------------------------------------------------+
| [▼ Overzicht] [Dossier] [Uren] [Derdengelden] [Facturen] [...]  |
+------------------------------------------------------------------+
|                                                                   |
|  FINANCIEEL OVERZICHT                                             |
|                                                                   |
|  +---------------+ +---------------+ +---------------+ +--------+ |
|  | OPENSTAAND    | | BETAALD       | | ONDERHANDEN   | | DERDEN | |
|  | € 3.450,00   | | € 12.800,00   | | € 2.150,00   | |€45.230 | |
|  | 🟠 2 facturen | | 🟢 4 facturen | | 🔵 8,5 uur   | | 🟣 →  | |
|  +---------------+ +---------------+ +---------------+ +--------+ |
|                                                                   |
|  BUDGET                                                           |
|  Vastgesteld: € 25.000                                            |
|  [████████████████████░░░░░░░░] 65% — € 16.250 besteed           |
|  Uren: € 12.800  |  Kosten: € 3.450                              |
|                                                                   |
|  +--------------------------------------------------------------+ |
|  | FACTUREN                                   [+ Nieuwe factuur] | |
|  +--------+------------+---------+---------+----------+---------+ |
|  | Nr.    | Datum      | Bedrag  | Betaald | Openst.  | Status  | |
|  +--------+------------+---------+---------+----------+---------+ |
|  | F-2024 | 15-02-2026 | 2.200   | 0       | 2.200    | 🟠 Verz.| |
|  | F-2019 | 01-02-2026 | 1.250   | 0       | 1.250    | 🔴 60d+ | |
|  | F-2015 | 15-01-2026 | 4.800   | 4.800   | 0        | 🟢 Bet. | |
|  | F-2010 | 01-01-2026 | 8.000   | 8.000   | 0        | 🟢 Bet. | |
|  +--------+------------+---------+---------+----------+---------+ |
|                                                                   |
|  +--------------------------------------------------------------+ |
|  | KOSTEN & VERSCHOTTEN                      [+ Kosten boeken]  | |
|  +----------+-------------------+---------+------+--------------+ |
|  | Datum    | Omschrijving      | Bedrag  | Type | Gefactureerd | |
|  +----------+-------------------+---------+------+--------------+ |
|  | 18-02    | Griffierecht KB   | 570,00  | Grif.| ✓ Ja (F-2024)| |
|  | 10-02    | Kadaster uittrek. | 15,00   | Kad. | ✗ Nee        | |
|  | 05-02    | Notariskosten     | 1.200,00| Not. | ✗ Nee        | |
|  +----------+-------------------+---------+------+--------------+ |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Samenvatting & Prioritering

### A6 (Derdengelden) — Essentieel voor compliance

| Prioriteit | Component | Reden |
|---|---|---|
| P0 | Saldo-weergave per zaak | Basisvereiste, moet altijd zichtbaar zijn |
| P0 | Storting/uitbetaling formulieren | Core workflow |
| P0 | Negatief-saldo blokkade | Wettelijke verplichting (NOvA) |
| P0 | Twee-directeurengoedkeuring | Wettelijke verplichting (NOvA) |
| P0 | Audittrail (wie, wat, wanneer) | Wettelijke verplichting |
| P1 | Client-akkoord bij advocaatkostenbetaling | Wettelijke verplichting |
| P1 | Protected/geoormerkte fondsen | Best practice (Clio, Smokeball, PP) |
| P1 | Drie-weg reconciliatie | Compliance best practice |
| P2 | iDEAL/betaallink integratie | Convenience, niet MVP |
| P2 | Bank-feed import | Automatisering, niet MVP |

### A7 (Financieel Overzicht) — Essentieel voor zaakbeheer

| Prioriteit | Component | Reden |
|---|---|---|
| P0 | Vier summary cards (openstaand, betaald, WIP, derdengelden) | Core informatiebehoefte |
| P0 | Factuurtabel met status + aging | Onmisbaar voor debiteurbeheer |
| P1 | Budget progress bar | Belangrijk voor fixed-fee zaken |
| P1 | Kosten/verschotten overzicht | Nodig voor doorbelasting |
| P1 | Drill-down naar individuele facturen/uren | Usability best practice |
| P2 | Winstgevendheid per zaak | Geavanceerd, fase 2 |
| P2 | Realisatiegraad | Geavanceerd, fase 2 |
| P2 | Grafieken/charts | Nice-to-have, kaarten zijn voldoende voor MVP |

---

## Bronnen

- [Clio Trust Accounting Guide](https://www.clio.com/resources/legal-accounting/law-firm-trust-accounting/)
- [Clio Reconciliation](https://help.clio.com/hc/en-us/articles/21058568234267)
- [Clio Matter Overview](https://help.clio.com/hc/en-us/articles/9285920226075)
- [LegalSense](https://legalsense.com)
- [PracticePanther Trust Accounting](https://www.practicepanther.com/legal-billing/trust-accounting-2/)
- [PracticePanther Custom Reports](https://www.practicepanther.com/blog/from-data-to-action-with-practicepanthers-custom-reports/)
- [PracticePanther Case Profitability](https://www.practicepanther.com/assessing-true-case-profitability-in-practice-panther)
- [Smokeball Trust Accounting Overview](https://support.smokeball.com/hc/en-us/articles/13801106657815)
- [Smokeball Trust Payment Requests](https://support.smokeball.com/hc/en-us/articles/32152852866199)
- [Smokeball Billing Software](https://www.smokeball.com/features/legal-billing-software)
- [Xero Projects](https://www.xero.com/us/accounting-software/track-projects/)
- [BaseNet (Capterra)](https://www.capterra.com/p/196696/BaseNet/)
- [HubSpot Revenue Tracking Discussion](https://community.hubspot.com/t5/Dashboards-Reporting/Tracking-Revenue-Across-Multiple-Months/m-p/1101860)
