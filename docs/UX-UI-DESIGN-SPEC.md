# Luxis UX/UI Design Specificatie

> Gebaseerd op UX research van: Clio (#1 legal PMS), PracticePanther, MyCase, Kolleno, Onguard CaseControl, WIK-wetgeving, en SaaS dashboard best practices.

---

## Design Principes

1. **"Wat moet ik NU doen?"** — Dashboard toont taken/deadlines eerst, KPI's zijn secundair
2. **Progressive Disclosure** — Max 4-7 items per scherm (Miller's Law). Details bij klik
3. **Status = kleur** — Consistent overal, nooit alleen tekst
4. **One-click acties** — Geen formulier openen voor statuswijziging
5. **Lege states leiden** — Nooit een lege pagina, altijd uitleg + CTA
6. **Micro-interacties** — Bevestiging bij verwijderen, toast bij succes, waarschuwing bij ongebruikelijk

---

## Kleurenpalet

| Kleur | Hex | Gebruik |
|---|---|---|
| Navy | `#0f172a` | Sidebar achtergrond |
| Slate 600 | `#475569` | Secundaire tekst, borders |
| White | `#ffffff` | Content area achtergrond |
| Blue 500 | `#3b82f6` | Actief, nieuw, links, primaire actie |
| Emerald 500 | `#10b981` | Betaald, succes, afgerond |
| Amber 500 | `#f59e0b` | Waarschuwing, wachtend, bijna deadline |
| Rose 500 | `#f43f5e` | Overdue, urgent, fout |
| Purple 500 | `#8b5cf6` | Gerechtelijk traject (dagvaarding, vonnis, executie) |

### Status Kleurcodering (Incasso)

| Status | Kleur | Badge |
|---|---|---|
| Nieuw | Blue `#3b82f6` | 🆕 blauw |
| 14-dagenbrief | Blue `#3b82f6` | 🔵 blauw |
| 14-dagen verstreken | Amber `#f59e0b` | ⚠️ amber |
| Sommatie | Amber `#f59e0b` | 🟡 amber |
| Sommatie verstreken | Rose `#f43f5e` | 🔴 rood |
| Dagvaarding | Purple `#8b5cf6` | 🟣 paars |
| Vonnis | Purple `#8b5cf6` | 🟣 paars |
| Executie | Purple `#8b5cf6` | 🟣 paars |
| Betaald | Emerald `#10b981` | ✅ groen |
| Afgesloten | Slate `#64748b` | ⚪ grijs |

---

## PMS Module — Pagina Layouts

### Dashboard (Hoofdpagina)

Bron: Clio "Today's Agenda" + PracticePanther sidebar + 10 SaaS Dashboard Strategies

```
┌──────────────────────────────────────────────────────────────────┐
│  Goedemorgen, [Naam] 👋                        [datum]          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌── Openstaand ───┐  ┌── Deze Week ────┐  ┌── Omzet MTD ────┐ │
│  │  €127.450       │  │  4 deadlines    │  │  €18.200        │ │
│  │  23 zaken       │  │  2 acties ⚠️     │  │  ↑12% vs jan    │ │
│  │  ~~sparkline~~  │  │                 │  │  ~~sparkline~~  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                  │
│  ┌── Vandaag ────────────────────┐  ┌── Recente Activiteit ───┐│
│  │  📋 Taken                     │  │  ● 14:23 Betaling       ││
│  │  ☐ Sommatie versturen         │  │    INC-042 €1.000       ││
│  │    INC-042  ⚠️ verstreken     │  │  ● 11:45 Zaak geopend  ││
│  │  ☐ Brief klaarzetten          │  │    INC-055 Firma XYZ    ││
│  │    INC-051  📋 vandaag        │  │  ● 09:30 Document       ││
│  │                               │  │    14-dagenbrief gen.   ││
│  │  📅 Agenda                    │  │  ● gisteren Relatie     ││
│  │  10:00 Bespreking Jansen      │  │    XYZ Handel toegev.   ││
│  │  14:00 Zitting Rb Amsterdam   │  │                         ││
│  └───────────────────────────────┘  └─────────────────────────┘│
│                                                                  │
│  ┌── Pipeline Verdeling (stacked bar) ──────────────────────────┐
│  │ ████ 14-dagen (8) ███ Sommatie (4) ██ Dagvaarding (2) ...   │
│  └──────────────────────────────────────────────────────────────┘
│                                                                  │
│  ┌── Actie Nodig ───────────────────────────────────────────────┐
│  │ ⚠️ INC-042  14-dagenbrief verstreken    3 dagen    [→]      │
│  │ ⚠️ INC-038  Sommatie verstreken         1 dag      [→]      │
│  └──────────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────────┘
```

### Zaken-overzicht (Lijst)

Bron: PracticePanther Modern Matters Grid

- Tabel met instelbare kolommen (toggle)
- Status-badges met kleur + icoon
- Bulk-acties via checkboxes
- Rij-hover toont mini-acties
- Filters: zoeken, type, status
- Export naar CSV
- Verstreken deadlines in amber/rood highlight

### Zaakdetail

Bron: Clio Matter Dashboard (tabs + financieel zijpaneel)

**Tabs:** `Overzicht` | `Documenten` | `Betalingen` | `Activiteit` | `Notities`

**Overzicht tab — twee-kolom layout:**
- Links: zaakgegevens + partijen (cliënt, wederpartij)
- Rechts: financieel overzicht (auto-berekend) + deadline tracker

**Status Pipeline Stepper** bovenaan elke zaakdetailpagina (zie incasso sectie).

### Relaties-overzicht

- Tabel met icoon (🏢 bedrijf / 👤 persoon)
- Kolommen: naam, e-mail, telefoon, plaats, aantal zaken
- Snelfilter op type + zoeken

### Relatiedetail

Bron: Clio Contact Dashboard

**Layout:**
- Header: naam + type badge + [Bewerken] knop
- Twee-kolom: contactgegevens links, financieel overzicht rechts
- Tabs: `Zaken` | `Documenten` | `Communicatie`
- Zaken-tab toont gekoppelde zaken met status-badges

### Documenten Pagina

- Tabel met document-icoon + naam + gekoppelde zaak + status + datum
- Document statussen: Concept → Definitief → Verstuurd → Bijlage
- [+ Genereer document] knop → kiest template op basis van zaakstatus
- Filters: zoeken, type, zaak

### Instellingen

Tabs: `Profiel` | `Kantoor` | `Meldingen` | `Weergave`
- Profiel: naam wijzigen, wachtwoord wijzigen (met show/hide toggle)
- Kantoor: bedrijfsnaam, KvK, BTW, adres (geladen uit API)
- Meldingen: toekomstig
- Weergave: toekomstig (dark mode)

---

## Incasso Module — Specifiek

### Status Pipeline (Stepper Component)

Horizontaal op desktop, verticaal op mobiel. Bovenaan zaakdetailpagina.

```
[1. Nieuw] → [2. 14-dagenbrief] → [3. Sommatie] → [4. Dagvaarding] → [5. Vonnis] → [6. Executie] → [7. Betaald]
```

Per stap:
- ✅ Afgerond = groen + vinkje
- 🔵 Actief = blauw + pulserende dot
- ⏳ Wachtend = grijs
- ⚠️ Deadline verstreken = amber/rood badge
- 🟣 Gerechtelijk = paars (visueel verschil)

### Contextgevoelige Acties

| Huidige status | Beschikbare acties |
|---|---|
| Nieuw | "Genereer 14-dagenbrief", "Bewerk gegevens" |
| 14-dagenbrief | "Markeer als verstuurd", "Registreer betaling" |
| 14-dagenbrief verstreken | **"Escaleer naar sommatie"** (prominent), "Registreer betaling" |
| Sommatie | "Markeer als verstuurd", "Registreer betaling" |
| Sommatie verstreken | **"Start dagvaarding"** (prominent), "Registreer betaling" |
| Dagvaarding | "Upload vonnis", "Registreer betaling" |
| Vonnis | **"Start executie"**, "Registreer betaling" |
| Executie | "Registreer betaling", "Sluit zaak" |

### Financieel Panel (altijd zichtbaar)

```
Hoofdsom                        €4.250,00
+ BIK-kosten (WIK staffel)       €637,50   ℹ️
+ Wettelijke rente (5,25%)         €83,12   ℹ️
─────────────────────────────────────────────
Totaalvordering                 €4.970,62
Ontvangen                          €0,00
Resterend                       €4.970,62
```

ℹ️ tooltip toont berekening details.

### BIK-Kosten Staffel (WIK)

| Schijf | Percentage |
|---|---|
| Eerste €2.500 | 15% |
| Volgende €2.500 | 10% |
| Volgende €5.000 | 5% |
| Volgende €190.000 | 1% |
| Boven €200.000 | 0,5% |
| **Minimum** | **€40** |
| **Maximum** | **€6.775** |

### Deadline Tracker

Automatische deadlines per status:
- **14-dagenbrief**: +16 dagen na verzending
- **Sommatie**: +7 dagen na verzending
- **Dagvaarding**: proceduretijd (handmatig)
- **Vonnis**: +14 dagen voor vrijwillige betaling

Visuele countdown badge:
- 🟢 `12 dagen resterend` — groen
- 🟡 `3 dagen resterend` — amber
- 🔴 `Verstreken (-5 dagen)` — rood, pulserend

### Betalingen Tab

Timeline-weergave met:
- Datum, bedrag, methode, status
- Lopend resterend bedrag na elke betaling
- Deelbetalingen ondersteuning

### Documenten Tab (per zaak)

Timeline-weergave:
- Chronologisch: nieuwste bovenaan
- Per document: naam, datum, status (Concept/Verstuurd/Bijlage)
- One-click "Genereer document" → pakt juiste template op basis van status

---

## Component Patronen

| Component | Patroon |
|---|---|
| **Sidebar** | Donker, collapsible, overlay op mobiel |
| **Header** | Sticky, hamburger op mobiel, page title + zoekbalk + user menu |
| **KPI Kaarten** | 3-5 max, waarde + label + delta indicator + sparkline |
| **Tabellen** | Instelbare kolommen, status-badges, hover-acties, horizontaal scrollbaar op mobiel |
| **Detail pagina** | Header (titel + acties dropdown), twee-kolom, tabs |
| **Lege states** | Icoon + uitleg tekst + prominente CTA knop |
| **Formulieren** | Labels boven velden, inline validatie (Zod), autofocus eerste veld |
| **Toasts** | Rechtsonder via Sonner. Groen=succes, Rood=error, Amber=warning |
| **Modals** | Bevestiging bij destructieve acties |
| **Stepper** | Horizontaal desktop, verticaal mobiel, kleur per status |
| **Badges** | Rounded-full, kleur-achtergrond met donkere tekst |
| **Tooltips** | Bij ℹ️ iconen, berekeningen, uitleg |

---

## Bronnen

- [Clio — #1 Legal PMS, Matter Dashboard](https://help.clio.com/hc/en-us/articles/16681289917595)
- [PracticePanther — Dashboard & Matters Grid](https://support.practicepanther.com/en/articles/629220-dashboard-tutorial)
- [Lazarev — 6 UX/UI Principles Legal Tech](https://www.lazarev.agency/articles/legaltech-design)
- [Kolleno — Collections & AR Management](https://www.kolleno.com/collections-automation/)
- [Onguard — CaseControl Incasso](https://www.onguard.com/solutions/casecontrol/)
- [FinView — Case Manager](https://www.finview.ai/debt-collection-software-overview/case-manager)
- [PatternFly — Progress Stepper](https://www.patternfly.org/components/progress-stepper/design-guidelines/)
- [AufaitUX — 10 SaaS Dashboard Strategies](https://www.aufaitux.com/blog/top-saas-dashboard-ui-ux-design-strategies-kpi-driven-engagement/)
- [Spyro-Soft — Debt Collection UX](https://spyro-soft.com/blog/fintech/online-debt-collector-designing-better-ux-for-financial-products)
- [Incassoadvocaten.nl — Incassoprocedure](https://www.incassoadvocaten.nl/hoe-werkt-een-incassoprocedure/)
- [Maak Advocaten — WIK Incassokosten Staffel](https://www.maakadvocaten.nl/incasso/wat-zijn-de-incassokosten-en-de-voorwaarden-voor-het-in-rekening-brengen-ervan/)
