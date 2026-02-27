# UX Research — E2: Tarieven Vereenvoudigen

> **Datum:** 20 februari 2026
> **Status:** Research afgerond — klaar voor implementatie
> **Prioriteit:** Hoog (E2 in roadmap)

---

## 1. Wat er nu is

### De "Tarieven" pagina (`/tarieven`)

**Bestand:** `frontend/src/app/(dashboard)/tarieven/page.tsx` (187 regels)

Een **read-only** overzichtspagina die de historische rentetarieven toont uit de `interest_rates` databasetabel. De pagina:

- Haalt data op via `GET /api/interest-rates` (globale referentietabel, geen tenant-data)
- Toont 3 rentetypes: Wettelijke rente, Handelsrente, Overheidsrente
- Per type: huidig tarief + percentage + ingangsdatum
- Uitklapbaar: historische tarieven per periode (tabel met "vanaf", "tot", "tarief")
- **Geen bewerkfunctionaliteit** — puur informatief
- **Geen CRUD** — tarieven worden beheerd via seed-script (`scripts/seed_interest_rates.py`)

### Sidebar navigatie

**Bestand:** `frontend/src/components/layout/app-sidebar.tsx` (regel 40)

```typescript
{ name: "Tarieven", href: "/tarieven", icon: Scale, module: "incasso" },
```

- Alleen zichtbaar als de incasso-module actief is
- Staat tussen "Documenten" en "Instellingen"

### Andere plekken waar "Tarieven" voorkomt

| Bestand | Wat | Regel |
|---------|-----|-------|
| `components/command-palette.tsx` | Quick action in Ctrl+K zoek | 36 |
| `components/layout/breadcrumbs.tsx` | Breadcrumb label mapping | 19 |
| `components/layout/app-header.tsx` | Header page title mapping | 32 |

### Hoe interest_type al werkt op dossierniveau

**Het rentetype is al een dropdown op dossier-niveau.** Dit is het cruciale inzicht:

1. **Nieuwe zaak formulier** (`zaken/nieuw/page.tsx`, regels 206-250):
   - Sectie "Rente-instellingen" met dropdown voor type rente
   - Opties: Wettelijke rente, Handelsrente, Overheidsrente, Contractuele rente
   - Extra veld voor contractueel percentage als "contractual" is gekozen
   - **Alleen zichtbaar bij case_type === "incasso"** (BUG-2 fix)

2. **Backend Case model** (`cases/models.py`, regels 52-63):
   - `interest_type` veld: `String(30)`, default `"statutory"`
   - `contractual_rate`: `Numeric(5,2)`, nullable
   - `contractual_compound`: `Boolean`, default `True`
   - Validatie in `cases/service.py`: controleert geldig type + verplicht tarief bij contractueel

3. **Case detail pagina** (`zaken/[id]/page.tsx`, regel 527):
   - Toont het gekozen rentetype als **read-only label** in de Overzicht tab
   - Niet bewerkbaar vanuit de detailpagina

4. **Renteberekening** (`collections/interest.py`):
   - Gebruikt `case.interest_type` om het juiste tarief uit de `interest_rates` tabel op te halen
   - De tarieven-tabel is puur referentiedata — Lisanne hoeft daar nooit zelf iets in te wijzigen

### Backend API

**Endpoint:** `GET /api/interest-rates` (`collections/router.py`, `rates_router`)
- Globale referentiedata (geen tenant_id)
- Alleen read — geen POST/PUT/DELETE
- Wordt ALLEEN gebruikt door de tarieven-pagina in de frontend

---

## 2. Het probleem

Lisanne ziet "Tarieven" in de sidebar en verwacht daar iets in te moeten instellen. Maar:

1. **De pagina is puur informatief** — je kunt er niets mee doen
2. **Het rentetype wordt al gekozen bij het aanmaken van een dossier** — dat is waar het thuishoort
3. **De historische rentetarieven zijn systeemdata** — die veranderen per AMvB (Algemene Maatregel van Bestuur), niet door de gebruiker
4. **Een aparte pagina hiervoor is verwarrend** — het suggereert dat Lisanne iets moet beheren wat het systeem automatisch doet

**Conclusie:** De tarieven-pagina is overkill en verwarrend. Het rentetype hoort op dossierniveau (en staat daar al). De referentietarieven zijn systeemdata die niet door gebruikers beheerd worden.

---

## 3. Wat er moet veranderen

### Stap 1: Verwijder de "Tarieven" pagina en sidebar-link

De pagina voegt geen waarde toe voor Lisanne. De informatie die erop staat (huidige tarieven) kan eventueel als tooltip of info-icoon bij de rente-dropdown op het dossierformulier verschijnen, maar een aparte pagina is niet nodig.

### Stap 2: Verwijder "Tarieven" uit alle navigatie

- Sidebar link verwijderen
- Command palette quick action verwijderen
- Breadcrumb mapping verwijderen
- Header title mapping verwijderen

### Stap 3: (Optioneel) Voeg tarief-info toe aan het dossierformulier

Bij de rente-dropdown op het "Nieuw dossier" formulier, een klein info-icoon of helptext dat het huidige tarief toont. Bijvoorbeeld:

```
Type rente: [Wettelijke rente (art. 6:119 BW) ▾]
             ℹ Huidig tarief: 6,00% (sinds 1 jan 2026)
```

Dit is een **nice-to-have** — de dropdown is ook zonder deze info prima bruikbaar.

### Backend

**Geen backend-wijzigingen nodig.** De `rates_router` en het `GET /api/interest-rates` endpoint kunnen blijven bestaan als referentie-API. Ze worden alleen niet meer door de frontend aangeroepen op een aparte pagina. Als we stap 3 implementeren (tarief-info bij dropdown), gebruikt die dezelfde API.

---

## 4. Bestanden die gewijzigd moeten worden

### Verwijderen

| Bestand | Actie |
|---------|-------|
| `frontend/src/app/(dashboard)/tarieven/page.tsx` | **Verwijder bestand** |

### Wijzigen

| Bestand | Wat | Regel(s) |
|---------|-----|----------|
| `frontend/src/components/layout/app-sidebar.tsx` | Verwijder `{ name: "Tarieven", ... }` uit `ALL_NAVIGATION` | 40 |
| `frontend/src/components/command-palette.tsx` | Verwijder `{ label: "Tarieven", href: "/tarieven", ... }` uit quick actions | 36 |
| `frontend/src/components/layout/breadcrumbs.tsx` | Verwijder `tarieven: "Tarieven"` uit label mapping | 19 |
| `frontend/src/components/layout/app-header.tsx` | Verwijder `"/tarieven": "Tarieven"` uit title mapping | 32 |

### Optioneel wijzigen (stap 3 — tarief-info bij dropdown)

| Bestand | Wat |
|---------|-----|
| `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` | Helptext onder rente-dropdown met huidig tarief |

### Niet wijzigen

| Bestand | Reden |
|---------|-------|
| `backend/app/collections/router.py` (`rates_router`) | API kan blijven bestaan — niet schadelijk, eventueel nuttig later |
| `backend/app/main.py` | `rates_router` blijft geregistreerd |
| `backend/app/collections/models.py` (`InterestRate`) | Model blijft — wordt gebruikt door renteberekening |
| `backend/app/cases/models.py` | `interest_type` veld op Case model blijft ongewijzigd |
| `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` | Rente-dropdown werkt al correct |

---

## 5. Bouwstappen

### Fase 1: Verwijderen (5 minuten)

1. Verwijder `frontend/src/app/(dashboard)/tarieven/page.tsx`
2. Verwijder tarieven-entry uit `app-sidebar.tsx` (regel 40)
3. Verwijder tarieven-entry uit `command-palette.tsx` (regel 36)
4. Verwijder tarieven-entry uit `breadcrumbs.tsx` (regel 19)
5. Verwijder tarieven-entry uit `app-header.tsx` (regel 32)
6. `npm run build` — check dat alles compileert
7. Commit: `fix(frontend): remove standalone tariff page (E2)`

### Fase 2: Optioneel — tarief-info bij dropdown (10 minuten)

1. In `zaken/nieuw/page.tsx`: fetch huidig tarief via `/api/interest-rates`
2. Toon als helptext onder de rente-dropdown: "Huidig tarief: X,XX% (sinds DD-MM-JJJJ)"
3. Alleen tonen bij niet-contractueel (bij contractueel vult gebruiker zelf het percentage in)
4. `npm run build` — check
5. Commit: `feat(frontend): show current rate info in case interest dropdown`

---

## 6. Risico-analyse

| Risico | Ernst | Mitigatie |
|--------|-------|-----------|
| Gebruiker had tarieven-pagina gebookmarked | Laag | Redirect 404 → dashboard, of Next.js vangt dit automatisch op |
| Backend `rates_router` niet meer nodig | Geen risico | Endpoint blijft, geen onderhoudslast |
| Interest rates niet meer zichtbaar | Laag | Ze zijn systeemdata, Lisanne hoeft ze niet te zien. Optioneel: toon bij dropdown (fase 2) |

---

## 7. Samenvatting

**Kernprobleem:** De "Tarieven" pagina is een read-only overzicht van systeemdata dat geen functie heeft voor de eindgebruiker. Het rentetype wordt al op dossierniveau gekozen — precies waar Lisanne het verwacht.

**Oplossing:** Verwijder de pagina en alle verwijzingen ernaar. Optioneel: toon het huidige tarief als helptext bij de rente-dropdown op het dossierformulier.

**Omvang:** Klein. 1 bestand verwijderen, 4 bestanden kleine edit (1 regel per bestand). Geen backend-wijzigingen.

---

*Dit document is het onderzoek en plan voor E2. De implementatie volgt de standaard werkwijze: plan → bouw → check → commit.*
