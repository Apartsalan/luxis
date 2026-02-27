# UX Research — E6: Debiteurenoverzicht

**Datum:** 20 februari 2026
**Status:** Onderzoek afgerond, wacht op goedkeuring

---

## 1. Huidige situatie

### Wat er nu is
- **Backend:** `GET /api/invoices/receivables` endpoint retourneert een volledig `ReceivablesSummary` met aging buckets (0-30, 31-60, 61-90, 90+ dagen) en per-contact breakdown
- **Frontend hook:** `useReceivables()` in `use-invoices.ts` is klaar, inclusief TypeScript types (`AgingBucket`, `ContactReceivable`, `ReceivablesSummary`)
- **Facturenpagina:** Flat lijst van facturen met zoeken, statusfilter en paginatie. Geen debiteurenoverzicht.

### Wat er mist
Lisanne heeft geen overzicht van:
- Hoeveel geld er totaal openstaat
- Welke cliënten het langst niet betaald hebben
- Waar het geld zit (recent vs. langdurig openstaand)
- Welke facturen direct actie nodig hebben (>90 dagen)

Dit is een **kernfunctie voor elke advocatenpraktijk**. Zonder dit overzicht moet Lisanne handmatig door facturen scrollen om te zien wie haar nog geld schuldig is.

---

## 2. Concurrentie-analyse

### Clio
- **A/R Aging Report:** Tabelvorm met kolommen voor cliëntnaam, originating attorney, responsible attorney, en aging buckets (Current, 1-30, 31-60, 61-90, 90+)
- **Dashboard:** KPI's bovenaan (total AR, bank balances, P&L). Accounts Receivable als primaire metric
- **Groepering:** Op cliënt achternaam, originating attorney, of responsible attorney
- **Sortering:** Op bedrag, cliëntnaam, of aging bucket

### PracticePanther
- **A/R Aging Report:** Gedetailleerde lijst per contact, gegroepeerd op ouderdom van facturen
- **Customizable:** Rapportage per assigned individual, contact, of matter
- **Acties:** Rente in rekening brengen op oude facturen, herinneringen sturen
- **Impact:** KKOS Lawyers reduceerde outstanding AR met 73% door actief dit rapport te gebruiken

### Smokeball
- **Rapportage:** WIP reports, billing realization reports, A/R aging summary
- **Account balance payments:** Overzicht van balansen en credit history
- **Click-to-pay:** Facturen via e-mail met directe betaallink (versnelt incasso)

### Xero / QuickBooks / Exact Online (boekhoudsoftware)
- **KPI-kaarten** bovenaan: totaal openstaand, gemiddeld betaaltermijn (DSO), % achterstallig
- **Staafdiagram** voor aging buckets: horizontale of verticale bars per bucket
- **Donut/pie chart** voor verdeling over buckets
- **Contacttabel** met per-cliënt breakdown, klikbaar voor detail
- **Kleurcodering:** groen (current), geel (31-60), oranje (61-90), rood (90+)

### Gemeenschappelijke patronen
1. **KPI-kaarten bovenaan** — totaal openstaand, totaal achterstallig, gemiddelde betaaltermijn
2. **Visueel aging overzicht** — staafdiagram of gestapelde balk per bucket
3. **Tabel gegroepeerd per cliënt** — met subtotalen per aging bucket
4. **Kleurcodering** — groen→geel→oranje→rood naarmate ouder
5. **Klikbare rijen** — doorklikken naar de specifieke facturen van die cliënt
6. **Geen complexe UI** — het is een lees-overzicht met één level deep (cliënt → facturen)

---

## 3. Aanbevolen aanpak voor Luxis

### Ontwerpprincipes
- **Tab op facturenpagina** — geen aparte pagina, maar een "Debiteuren" tab naast de facturenlijst
- **Scanbaar** — Lisanne moet in 5 seconden zien hoeveel er openstaat en wie de "probleemgevallen" zijn
- **Actiegericht** — de rode buckets moeten direct leiden tot actie (doorklikken naar factuur)
- **Geen overkill** — voor een solopraktijk geen DSO-berekening, geen grafieken. KPI's + tabel is genoeg.

### UI op facturenpagina

De facturenpagina krijgt twee tabs:

```
┌──────────────────────────────────────────────────────────┐
│  Facturen                                                │
│  [Facturen]  [Debiteuren]               [+ Nieuwe factuur] │
├──────────────────────────────────────────────────────────┤
```

**Tab "Debiteuren" — layout:**

```
┌──────────────────────────────────────────────────────────┐
│  KPI-kaarten                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐│
│  │ Openstaand  │ │ Achterstallig│ │ Aging balk           ││
│  │  €12.450    │ │  €3.200     │ │ ████░░░▓▓▓██         ││
│  │  8 facturen │ │  3 facturen │ │ 0-30 31-60 61-90 90+ ││
│  └─────────────┘ └─────────────┘ └──────────────────────┘│
├──────────────────────────────────────────────────────────┤
│  Per cliënt                                              │
│                                                          │
│  Bedrijf A                                    €5.200     │
│  ┌──────────────────────────────────────────────────────┐│
│  │ 0-30 d     31-60 d    61-90 d    90+ d    Totaal    ││
│  │ €2.000     €1.200     €0         €2.000   €5.200    ││
│  │ 1 factuur  1 factuur  -          1 factuur          ││
│  └──────────────────────────────────────────────────────┘│
│  Oudste vervaldatum: 15 nov 2025                         │
│                                                          │
│  Bedrijf B                                    €4.250     │
│  ┌──────────────────────────────────────────────────────┐│
│  │ 0-30 d     31-60 d    61-90 d    90+ d    Totaal    ││
│  │ €4.250     €0         €0         €0       €4.250    ││
│  │ 2 facturen -          -          -                   ││
│  └──────────────────────────────────────────────────────┘│
│  Oudste vervaldatum: 5 feb 2026                          │
│                                                          │
│  (geen cliënten met openstaand = leeg state)             │
└──────────────────────────────────────────────────────────┘
```

### Componenten

**1. KPI-kaarten (bovenaan)**

| KPI | Waarde | Toelichting |
|-----|--------|-------------|
| Totaal openstaand | `total_outstanding` | Alle openstaande facturen |
| Achterstallig | `total_overdue` | Facturen >30 dagen over vervaldatum |
| Aantal cliënten | `contacts.length` | Met openstaande facturen |

**2. Aging balk (visueel)**
- Horizontale gestapelde balk met 4 segmenten
- Kleuren: blauw (0-30), geel (31-60), oranje (61-90), rood (90+)
- Proportioneel op basis van bedrag
- Hover toont exact bedrag + aantal

**3. Contacttabel**
- Gesorteerd op `total_outstanding` (hoogste eerst) — zo zit het al in de backend
- Per contact: naam, totaal openstaand, en per bucket het bedrag + aantal facturen
- Klikbare rij → linkt naar facturenpagina gefilterd op die cliënt (via bestaande `search` param)
- Oudste vervaldatum als extra context
- Kleurcodering op de rode buckets (61-90, 90+)

**4. Leeg state**
- "Geen openstaande facturen" met een check-icoon
- "Alle facturen zijn betaald of in concept" als subtekst

---

## 4. Backend status

**Volledig klaar.** Geen backend-werk nodig.

| Component | Status |
|-----------|--------|
| `GET /api/invoices/receivables` | ✅ Klaar |
| `ReceivablesSummary` schema | ✅ Klaar |
| `AgingBucket` schema | ✅ Klaar |
| `ContactReceivable` schema | ✅ Klaar |
| `useReceivables()` hook | ✅ Klaar |
| Frontend types | ✅ Klaar |

De backend berekent al:
- Outstanding per factuur (totaal - betalingen)
- Aging bucket op basis van `due_date`
- Groepering per contact
- Sortering op `total_outstanding` (hoogste eerst)
- Totalen voor alle buckets

---

## 5. Frontend plan

### Wijzigingen aan bestaande code

**`facturen/page.tsx`** — Tabs toevoegen:
- Twee tabs: "Facturen" (bestaande lijst) en "Debiteuren" (nieuw)
- Huidige content verplaatsen naar een `FacturenTab` component (of inline met conditional render)
- Nieuwe `DebiteurenTab` component

### Nieuwe componenten

**`DebiteurenTab`** (in `facturen/page.tsx` of apart bestand):
1. `useReceivables()` hook aanroepen
2. KPI-kaarten renderen (3 kaarten)
3. Aging balk renderen (horizontale gestapelde balk met CSS)
4. Contacttabel renderen (map over `contacts`)
5. Skeleton loader voor loading state
6. Empty state voor geen openstaande facturen

### Geen nieuwe hooks nodig
Alles zit al in `use-invoices.ts`:
- `useReceivables()` — haalt data op
- `ReceivablesSummary`, `ContactReceivable`, `AgingBucket` — types

### Formattering
- Bedragen: `formatCurrency()` uit `@/lib/utils`
- Datums: `formatDateShort()` uit `@/lib/utils`
- Percentages: voor aging balk proportionele berekening

---

## 6. Bouwstappen

| # | Stap | Geschatte omvang | Details |
|---|------|-----------------|---------|
| 1 | Tab-structuur toevoegen aan facturen/page.tsx | Klein | Twee tabs, active state, URL param voor tab |
| 2 | Bestaande facturenlijst wrappen in tab | Klein | Conditional render of component extract |
| 3 | DebiteurenTab component bouwen | Midden | KPI-kaarten + aging balk + contacttabel |
| 4 | Skeleton loader voor debiteuren | Klein | 3 skeleton kaarten + tabel skeleton |
| 5 | Empty state voor geen openstaande facturen | Klein | Check-icoon + tekst |
| 6 | Build + test | Klein | `npm run build`, handmatig checken |

**Totaal geschat:** ~1 sessie (puur frontend)

---

## 7. Risico-analyse

| Risico | Ernst | Mitigatie |
|--------|-------|-----------|
| Veel cliënten → lange lijst | Laag | Backend sorteert al op bedrag, top 10-20 zijn relevant |
| Aging balk bij €0 openstaand | Laag | Toon "Geen openstaande facturen" in plaats van lege balk |
| Performance bij veel facturen | Laag | Backend doet de berekening, frontend rendert alleen het resultaat |
| Tab-state verlies bij navigatie | Laag | URL parameter `?tab=debiteuren` voor deep linking |

---

## 8. Toekomstige uitbreidingen (NIET nu bouwen)

- **Export naar CSV/PDF** — debiteurenoverzicht printen/mailen
- **Herinneringen sturen** — direct vanuit overzicht een betalingsherinnering per e-mail
- **DSO (Days Sales Outstanding)** — gemiddelde betaaltermijn KPI
- **Trend grafiek** — openstaand bedrag over tijd
- **Crediteurenoverzicht** — (niet relevant voor advocatenkantoor, skip)

---

*Dit document is het onderzoeksresultaat voor E6. Wacht op goedkeuring voordat implementatie begint.*
