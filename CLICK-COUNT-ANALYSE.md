# Click-Count Analyse — Luxis Frontend

**Datum:** 19 februari 2026
**Doel:** Per user flow het exacte aantal clicks meten en vergelijken met concurrenten (Clio, PracticePanther, Smokeball). Bottlenecks identificeren.

---

## Methode

Elke flow is geteld als: **navigatie-clicks + formulier-interacties + submit**. Keyboard shortcuts (Tab, Enter) tellen niet als click. Dropdown-openen + optie-kiezen = 2 clicks. Zoekveldinvoer = 0 clicks (typen). Datum-picker = 1 click (focus) + 1 click (datum kiezen) = 2 clicks.

---

## 1. Nieuwe relatie aanmaken

### Luxis (huidige situatie)
| Stap | Clicks |
|------|--------|
| Sidebar → "Relaties" | 1 |
| Klik "Nieuwe relatie" | 1 |
| Kies type (Bedrijf/Persoon) | 1 |
| Vul naam in | 0 (typen) |
| Vul e-mail in | 0 (typen) |
| Vul telefoon in | 0 (typen) |
| Vul KvK in (optioneel) | 0 (typen) |
| Vul adres in (optioneel) | 0 (typen) |
| Klik "Opslaan" | 1 |
| **Totaal** | **4 clicks** |

**Minimale flow (alleen verplicht):** 4 clicks (nav + nieuw + type + opslaan)
**Volledige flow (alle velden):** 4 clicks + typen

### Vergelijking
| Tool | Clicks (minimaal) | Opmerkingen |
|------|-------------------|-------------|
| **Luxis** | **4** | Type-selector is 1 extra click vs. concurrenten |
| Clio | 3-4 | "Contacts" → "Create" → minimal form → save |
| PracticePanther | 3-4 | "Contacts" → "Add Contact" → form → save |
| Smokeball | 4-5 | Aparte stap voor soort + meer verplichte velden |

**Verdict:** Goed. Vergelijkbaar met concurrenten. Type-selector (bedrijf/persoon) is visueel en duidelijk.

---

## 2. Nieuwe zaak aanmaken

### Luxis
| Stap | Clicks |
|------|--------|
| Sidebar → "Zaken" | 1 |
| Klik "Nieuwe zaak" | 1 |
| Kies zaaktype (dropdown) | 2 |
| Kies debiteurtype (auto-filled, maar aanpasbaar) | 0-2 |
| Datum picker | 2 |
| Zoek client (typen + selectie) | 1 (klik op resultaat) |
| Zoek wederpartij (typen + selectie) | 1 (klik op resultaat) |
| Vul beschrijving/referentie in | 0 (typen) |
| Kies rentetype (dropdown) | 2 |
| Klik "Aanmaken" | 1 |
| **Totaal** | **9-11 clicks** |

**Minimale flow (alleen verplicht):** 8 clicks (nav + nieuw + type + datum + client + rentetype + submit)

**Opmerkingen:**
- Zaaktype dropdown is altijd nodig — moet default hebben
- Conflict check draait automatisch op client/wederpartij selectie (geen extra click)
- KYC check draait automatisch op client selectie (geen extra click)
- Debiteurtype wordt automatisch afgeleid van zaaktype (slim)

### Vergelijking
| Tool | Clicks (minimaal) | Opmerkingen |
|------|-------------------|-------------|
| **Luxis** | **8-11** | Goed. Conflict/KYC checks zijn automatisch |
| Clio | 6-8 | "Matters" → "Create" → wizard (2 stappen) → save |
| PracticePanther | 7-9 | Quick-create modal OF full form |
| Smokeball | 8-12 | Multi-step wizard, veel verplichte velden |

**Verdict:** Vergelijkbaar. Het enige verbeterpunt is een snellere route: Quick-create dialog ipv pagina-navigatie. Maar voor incasso met conflict check is de huidige flow logisch.

---

## 3. Tijdregistratie (1 entry invoeren)

### Luxis (huidige situatie)
| Stap | Clicks |
|------|--------|
| Sidebar → "Uren" | 1 |
| Vul beschrijving in (inline form bovenaan) | 0 (typen) |
| Selecteer zaak (CaseSelector: klik → zoek → klik resultaat) | 2 |
| Vul duur in (minuten) | 0 (typen) |
| Kies declarabel toggle | 1 |
| Klik "Opslaan" | 1 |
| **Totaal** | **5 clicks** |

**Timer flow (al gebouwd!):**
| Stap | Clicks |
|------|--------|
| Sidebar → "Uren" | 1 |
| Selecteer zaak in timer | 2 |
| Klik "Start" | 1 |
| (werk...) | 0 |
| Klik "Stop" | 1 |
| **Totaal** | **5 clicks** |

**Bevinding:** Timer is al gebouwd als een card op de urenpagina. Het is NIET floating — navigeren weg van de pagina stopt de timer niet maar je ziet hem niet meer. Timer state gaat verloren bij page refresh (alleen React state, niet persisted).

### Vergelijking
| Tool | Clicks (minimaal) | Opmerkingen |
|------|-------------------|-------------|
| **Luxis** | **5** | Inline form is efficiënt |
| Clio | 2-3 | Floating timer op elke pagina + 1-click start vanuit zaak |
| Toggl Track | 1-2 | Global timer bar, 1 click start |
| PracticePanther | 3-4 | Timer in sidebar + manual entry |
| Smokeball | 1 (auto) | Automatische tijdregistratie (AI-driven) |

**Verdict:** Functioneel maar **niet concurrerend met Clio/Toggl**. Belangrijkste gaps:
1. Timer is niet floating/persistent (verdwijnt bij navigatie)
2. Geen quick-start vanuit zaakdetail
3. Geen timer in header/sidebar
4. Timer state niet persisted (localStorage/backend)

**Dit bevestigt A1 (Timer verbetering) als hoge prioriteit.**

---

## 4. Factuur aanmaken

### Luxis
| Stap | Clicks |
|------|--------|
| Sidebar → "Facturen" | 1 |
| Klik "Nieuwe factuur" | 1 |
| Zoek contact (typen + klik) | 1 |
| Zoek zaak (typen + klik) | 1 |
| Datum picker (2x: factuurdatum + vervaldatum) | 4 |
| Vul BTW-percentage in | 0 (heeft default) |
| Voeg factuurregel toe: beschrijving + aantal + prijs | 0 (typen) |
| "Importeer uren" (als zaak geselecteerd) | 1 |
| Selecteer uren om te importeren | 1-5 (per entry) |
| Klik "Aanmaken" | 1 |
| **Totaal** | **11-14 clicks** |

**Minimale flow (1 regel, handmatig):** 9 clicks
**Met uren-import:** 11-14 clicks

### Vergelijking
| Tool | Clicks (minimaal) | Opmerkingen |
|------|-------------------|-------------|
| **Luxis** | **9-14** | Dubbele datumpicker is veel |
| Clio | 6-8 | Auto-fills veel velden vanuit zaak, 1-click billable import |
| PracticePanther | 7-10 | "Generate from time entries" flow |
| Smokeball | 8-12 | Template-based, minder handmatige velden |

**Verdict:** Te veel clicks voor datums. Verbeterpunten:
1. Vervaldatum zou automatisch berekend moeten worden (factuurdatum + 14 of 30 dagen)
2. Uren-import zou standaard alle unbilled uren moeten selecteren
3. BTW-percentage zou van kantoorinstellingen moeten komen (nu handmatig)

**Opmerking:** `facturen/nieuw/page.tsx` gebruikt `parseFloat` voor berekeningen (regels 134-141). Dit is een financial precision issue — zou `Decimal` moeten zijn op de backend (de backend doet het correct, maar de frontend preview kan afrondingsfouten tonen).

---

## 5. Zaakstatus wijzigen

### Luxis
| Stap | Clicks |
|------|--------|
| Navigeer naar zaak (vanuit lijst of dashboard) | 1-2 |
| Klik op volgende status-knop (pipeline stepper) | 1 |
| Vul notitie in (prompt dialog) | 0 (typen) + 1 (OK) |
| **Totaal** | **3-4 clicks** |

### Vergelijking
| Tool | Clicks (minimaal) | Opmerkingen |
|------|-------------------|-------------|
| **Luxis** | **3-4** | Uitstekend. Pipeline stepper is visueel duidelijk |
| Clio | 3-5 | Status dropdown of drag-and-drop op Kanban |
| PracticePanther | 2-3 | Drag-and-drop op pipeline |
| Smokeball | 3-4 | Status-change via detail page |

**Verdict:** Goed. De pipeline stepper met beschikbare transities is duidelijk en efficiënt. Workflow tasks worden automatisch aangemaakt bij statuswijziging.

---

## 6. Document genereren

### Luxis
| Stap | Clicks |
|------|--------|
| Navigeer naar zaak | 1-2 |
| Klik tab "Documenten" | 1 |
| Klik op template (bijv. "14-dagenbrief") | 1 |
| Download start automatisch | 0 |
| **Totaal** | **3-4 clicks** |

### Vergelijking
| Tool | Clicks (minimaal) | Opmerkingen |
|------|-------------------|-------------|
| **Luxis** | **3-4** | Zeer efficiënt |
| Clio | 4-6 | Template selectie → merge fields → download |
| PracticePanther | 4-5 | Template → customize → download |
| Smokeball | 2-3 | Auto-generate vanuit workflow |

**Verdict:** Goed. 1-click generatie vanuit zaakdetail is efficiënt.

---

## 7. Vordering toevoegen (incasso)

### Luxis
| Stap | Clicks |
|------|--------|
| Navigeer naar zaak | 1-2 |
| Klik tab "Vorderingen" | 1 |
| Klik "Vordering toevoegen" | 1 |
| Vul beschrijving, bedrag, verzuimdatum | 0 (typen) + 2 (datumpicker) |
| Klik "Opslaan" | 1 |
| **Totaal** | **6-7 clicks** |

**Vergelijking:** Geen directe concurrent — dit is Luxis-specifiek (incassomodule). De flow is logisch en compact.

---

## 8. Betaling registreren

### Luxis
| Stap | Clicks |
|------|--------|
| Navigeer naar zaak | 1-2 |
| Klik tab "Betalingen" | 1 |
| Klik "Betaling registreren" | 1 |
| Vul bedrag in | 0 (typen) |
| Datum (default: vandaag) | 0 |
| Kies betaalwijze (dropdown) | 2 |
| Klik "Registreren" | 1 |
| **Totaal** | **6-7 clicks** |

**Opmerkingen:**
- Datum default vandaag (geen extra clicks nodig)
- Art. 6:44 BW imputatie draait automatisch (kosten → rente → hoofdsom)
- Geen handmatige verdeling nodig

**Verdict:** Goed. Default-waarden besparen clicks.

---

## 9. WWFT/KYC verificatie starten

### Luxis
| Stap | Clicks |
|------|--------|
| Navigeer naar relatie | 1-2 |
| Open WWFT-sectie (collapsible) | 1 |
| Klik "Verificatie starten" of "Bewerken" | 1 |
| Vul risicoclassificatie (dropdown) | 2 |
| Vul ID-document (dropdown + velden) | 2 + typen |
| Toggle PEP-controle | 1 |
| Toggle sanctielijst | 1 |
| Klik "Opslaan" | 1 |
| Klik "Verificatie afronden" (aparte stap) | 1 |
| **Totaal** | **11-13 clicks** |

### Vergelijking
| Tool | Clicks | Opmerkingen |
|------|--------|-------------|
| **Luxis** | **11-13** | Veel velden, maar wettelijk verplicht |
| Clio (met plugin) | 10-15 | Aparte KYC plugin, vaak meer stappen |
| PracticePanther | n/a | Geen ingebouwde KYC |

**Verdict:** Acceptabel — WWFT vereist nu eenmaal deze gegevens. De collapsible sectie op de relatiepagina is goed. Het 2-stappen model (opslaan + apart afronden) is bewust voor juridische zekerheid.

---

## 10. Dashboard → Zaak openen (navigatie)

### Luxis
| Stap | Clicks |
|------|--------|
| **Via KPI card** | 1 (klik op "Actieve zaken" card → zakenlijst) + 1 (klik zaak) = **2** |
| **Via recente activiteit** | 1 (klik op activiteit → direct naar zaak) = **1** |
| **Via pipeline "Actie nodig"** | 1 (klik op status → gefilterde lijst) + 1 (klik zaak) = **2** |
| **Via "Mijn taken"** | 1 (klik zaaknummer) = **1** |

### Vergelijking
| Tool | Clicks naar zaak | Opmerkingen |
|------|------------------|-------------|
| **Luxis** | **1-2** | Goed. Multiple snelle routes |
| Clio | 1-2 | Dashboard widgets linken direct |
| PracticePanther | 1-2 | Vergelijkbaar |

**Verdict:** Goed. Meerdere snelle routes naar zaken.

---

## Samenvatting: Click-Count Scorecard

| Flow | Luxis | Clio | PP | Smokeball | Score |
|------|-------|------|----|-----------|-------|
| Nieuwe relatie | 4 | 3-4 | 3-4 | 4-5 | Goed |
| Nieuwe zaak | 8-11 | 6-8 | 7-9 | 8-12 | Goed |
| Tijdregistratie | 5 | 2-3 | 3-4 | 1 | **Matig** |
| Factuur aanmaken | 9-14 | 6-8 | 7-10 | 8-12 | **Matig** |
| Status wijzigen | 3-4 | 3-5 | 2-3 | 3-4 | Goed |
| Document genereren | 3-4 | 4-6 | 4-5 | 2-3 | Goed |
| Vordering toevoegen | 6-7 | n/a | n/a | n/a | n/a |
| Betaling registreren | 6-7 | n/a | n/a | n/a | n/a |
| KYC verificatie | 11-13 | 10-15 | n/a | n/a | Goed |
| Navigatie dashboard→zaak | 1-2 | 1-2 | 1-2 | 1-2 | Goed |

---

## Top 5 Bottlenecks (geprioriteerd)

### 1. Timer niet persistent/floating (HOOG)
**Huidige situatie:** Timer bestaat maar is embedded in urenpagina, niet zichtbaar op andere pagina's, state gaat verloren bij refresh.
**Impact:** Elke dag 10-20 extra clicks om naar uren-pagina te navigeren voor start/stop.
**Benchmark:** Clio/Toggl hebben floating timer op elke pagina.
**Actie:** Feature A1 in UX-VERBETERPLAN.md

### 2. Factuur vervaldatum handmatig (MIDDEN)
**Huidige situatie:** 2 extra clicks voor datumpicker bij vervaldatum.
**Impact:** Bij elke factuur 2 onnodige clicks.
**Benchmark:** Clio auto-fills vervaldatum (factuurdatum + betalingstermijn uit instellingen).
**Actie:** Auto-calculate due_date = invoice_date + tenant.payment_terms_days (default 30).

### 3. Geen global search / command palette (HOOG)
**Huidige situatie:** Om iets te zoeken moet je eerst naar de juiste pagina navigeren en daar het zoekveld gebruiken.
**Impact:** 2-3 extra clicks per zoekopdracht. Bij 50+ zoekopdrachten per dag is dat significant.
**Benchmark:** Clio heeft Ctrl+K global search. Linear, Notion, Stripe — allemaal.
**Actie:** Feature A2 in UX-VERBETERPLAN.md. `command-palette.tsx` component bestaat al maar is nog niet geactiveerd.

### 4. Uren-import bij factuur niet slim genoeg (LAAG)
**Huidige situatie:** Knop "Importeer uren" toont alle unbilled uren; gebruiker moet elk selecteren.
**Impact:** 1-5 extra clicks per uur-entry bij facturatie.
**Benchmark:** Clio importeert automatisch alle unbilled uren van de geselecteerde zaak.
**Actie:** Auto-select all unbilled entries + "Deselecteer" voor uitzonderingen.

### 5. Geen quick-create vanaf zaakdetail (LAAG)
**Huidige situatie:** Om een tijdregistratie of factuur aan te maken vanuit een zaak, moet je naar de aparte pagina navigeren.
**Impact:** 1-2 extra clicks per actie.
**Benchmark:** Clio/PracticePanther hebben quick-action buttons op zaakdetail.
**Actie:** Feature B2 (Quick actions bar) in UX-VERBETERPLAN.md.

---

## Overige Bevindingen

### Positief
- **Automatische conflict check** bij zaak aanmaken — geen extra clicks, draait op achtergrond
- **Automatische KYC check** bij client selectie — idem
- **Art. 6:44 BW imputatie** automatisch bij betaling registreren — geen handmatige verdeling
- **Pipeline stepper** op zaakdetail — visueel duidelijk, minimale clicks
- **Workflow tasks** automatisch bij statuswijziging — geen handmatig aanmaken nodig
- **Tabbed interface** op zaakdetail — al gebouwd (B1 uit UX-VERBETERPLAN is al geimplementeerd!)

### Aandachtspunten
- `command-palette.tsx` bestaat als component maar is niet actief in de layout
- `parseFloat` in `facturen/nieuw/page.tsx` (regels 134-141) voor financiele berekeningen — frontend preview kan afrondingsfouten tonen (backend is correct met Decimal)
- Timer in `uren/page.tsx` (regels 308-350) is alleen React state (`useState`/`setInterval`) — geen persistence
- CaseSelector component (regels 72-265 in uren/page.tsx) is goed gebouwd met grouped-by-client en zoekfunctie — kan hergebruikt worden voor global search

---

*Dit document is onderdeel van de pre-build verificatie. Zie ook: INCASSO-VERIFICATIE.md en CODE-REVIEW.md.*
