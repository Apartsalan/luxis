# UX Verbeterplan — Luxis Practice Management System

> **⚠️ `LUXIS-ROADMAP.md` is de enige source of truth.** Dit document bevat alleen gedetailleerde bouw-instructies per feature. Voor status, prioriteit en het totaaloverzicht: zie de roadmap.

**Gebaseerd op:** UX-REVIEW.md (19 februari 2026)
**Werkwijze:** Features één of twee tegelijk, onderzoek → plan → bouw → check → commit

---

## Context

De backend is ~70% klaar, de frontend ~40%. Veel verbeteringen zijn puur frontend-werk omdat de API's er al zijn.

**Belangrijk principe:**
- Onderzoek eerst, bouw daarna. Kijk bij elke feature hoe Clio, PracticePanther, Smokeball, Linear, Toggl, Stripe of HubSpot het doen.
- Luxis is een product, niet een intern tool. Elk scherm moet eruitzien alsof het morgen gelanceerd wordt.
- Lisanne-toets: "Zou ze dit begrijpen zonder uitleg?" Zo nee, versimpel.

**Werkwijze per feature:**
1. Onderzoek concurrenten
2. Plan voorleggen
3. Bouwen
4. `npm run build` + handmatig checken
5. Committen
6. Pas dan door naar volgende feature

---

## Fase A: Quick Wins — Backend is al klaar (puur frontend)

### A1. Timer voor tijdschrijven 🔴 KRITIEK — ✅ GEBOUWD
**Status:** Al geïmplementeerd als floating timer met globale context

Wat er is:
- ✅ Floating timer component rechtsonder (altijd zichtbaar, collapsed pill wanneer actief)
- ✅ Start/stop knoppen met zaak-selectie dropdown
- ✅ Omschrijving invulveld
- ✅ Bij stop: automatisch tijdregistratie opslaan via `useCreateTimeEntry`
- ✅ Persistent via localStorage (`luxis_timer`) — overleeft page navigatie en refresh
- ✅ Globale context (`TimerContext`) via `use-timer.ts` — dezelfde timer op elke pagina
- ✅ Geïntegreerd op uren-pagina (vervangt lokale timer state)

Eventueel later verbeteren:
- Pauze-functie (nu alleen start/stop)
- Duur invoer als HH:MM of decimaal (1.5u) i.p.v. alleen minuten
- Rounding rules (6-minuten eenheden, configureerbaar)

---

### A2. Global search (Ctrl+K) 🔴 KRITIEK — ✅ GEBOUWD
**Status:** Al geïmplementeerd in `command-palette.tsx`

Wat er is:
- ✅ Ctrl+K / Cmd+K opent zoek-overlay vanuit elke pagina
- ✅ Zoekt via `/api/search?q={query}&limit=10` in zaken, relaties, documenten
- ✅ Resultaten gegroepeerd per type met iconen
- ✅ Keyboard navigatie (pijltjes + Enter + Escape)
- ✅ 10 quick actions voor navigatie
- ✅ 250ms debounce

Eventueel later verbeteren:
- Recente items tonen bij leeg zoekveld
- Facturen toevoegen aan zoekresultaten

---

### A3. "Mijn Taken" pagina 🔴 HOOG — ✅ GEBOUWD
**Status:** Al geimplementeerd in `taken/page.tsx`

Wat er is:
- ✅ Dedicated pagina in sidebar navigatie: "Mijn Taken" (met CheckSquare icoon)
- ✅ Gegroepeerd: Te laat / Vandaag / Deze week / Later / Afgerond
- ✅ Per taak: titel, zaak (clickable link naar zaakdetail), deadline (relatief), status badge, taaktype
- ✅ Taak afronden met een klik (circle → checkmark)
- ✅ Taak overslaan met een klik (hover: skip button)
- ✅ Filter: Openstaand / Alles / Afgerond (segmented control)
- ✅ Lege state: "Alles gedaan!" (motiverend) of "Nog geen afgeronde taken"
- ✅ Loading skeleton en error state
- ✅ Statistieken in header: openstaand, te laat, vandaag

**Nog bouwen (gepland):**
- ❌ **Handmatige taken aanmaken** — "+ Taak" knop op zowel taken-overzicht als zaakdetail. Velden: titel, omschrijving (optioneel), deadline, gekoppelde zaak. Nu worden taken alleen door workflow-triggers aangemaakt, maar advocaten willen ook ad-hoc taken ("Bel cliënt terug", "Stuk nakijken"). Zie `BUGS-EN-VERBETERPUNTEN.md` #4.
- Drag & drop prioritering

---

### A4. Activity timeline op zaakdetail 🔴 HOOG — ✅ GEBOUWD
**Status:** Geïmplementeerd in `zaken/[id]/page.tsx`

Wat er is:
- ✅ Verbeterde OverzichtTab sidebar: timeline met verticale lijn, per-type gekleurde iconen, relatieve tijden ("5 min geleden", "Gisteren 14:30")
- ✅ ActiviteitenTab volledig herschreven met paginated data via `useCaseActivities` hook
- ✅ Inline "Notitie toevoegen" tekstveld bovenaan timeline (geen modal)
- ✅ Per activity type: uniek icoon + kleur (telefoon=groen, email=violet, notitie=amber, status=blauw, document=grijs, betaling=groen)
- ✅ Type badge per activiteit (Statuswijziging, Notitie, Telefoongesprek, etc.)
- ✅ User info getoond per activiteit ("· Jan de Vries")
- ✅ Paginatie met Vorige/Volgende knoppen
- ✅ Loading skeleton en lege state
- ✅ `formatRelativeTime` utility in `lib/utils.ts`

Eventueel later verbeteren:
- Filter op activity type
- Inline bewerken van notities
- Rich text voor notities

---

### A5. Contact-bedrijf koppelingen in UI 🟡 MIDDEN — ✅ GEBOUWD
**Status:** Geïmplementeerd in `components/relations/contact-links.tsx`

Wat er is:
- ✅ `ContactLinks` component op relatiedetail: "Gekoppelde bedrijven" (personen) of "Contactpersonen" (bedrijven)
- ✅ Koppeling toevoegen via zoek-dropdown met live search (debounced, 2+ tekens)
- ✅ Rol selectie: Directeur, Contactpersoon, Aandeelhouder, Bestuurder, Gemachtigde, Werknemer
- ✅ Click-through naar gekoppelde relatie
- ✅ Verwijderen met bevestiging
- ✅ Al-gekoppelde contacten worden gefilterd uit zoekresultaten
- ✅ Hooks: `useSearchRelations`, `useCreateContactLink`, `useDeleteContactLink`
- ✅ Backend endpoints: `POST/DELETE /api/relations/links`

---

### A6. Derdengelden UI verbeteren 🟡 MIDDEN
**API:** Complete derdengelden API met saldo bestaat al
**Complexiteit:** Klein

Wat bouwen:
- Op zaakdetail: derdengelden-saldo zichtbaar
- Transactieoverzicht per zaak (stortingen, uitbetalingen)
- Op dashboard: totaal derdengelden-saldo (alle zaken)

---

### A7. Financieel overzicht op zaak verbeteren 🟡 MIDDEN
**API:** `/api/cases/{id}/financial-summary` bestaat al
**Complexiteit:** Klein

Wat bouwen:
- Rijkere presentatie: vorderingen, rente, BIK, betalingen, openstaand — als overzichtelijke kaart
- Progress bar: % geïncasseerd
- Link naar gerelateerde facturen

---

## Fase B: Zaakdetail transformatie — Van infopagina naar werkhub

> Dit kan parallel met Fase C

### B1. Tabbed interface op zaakdetail 🔴 HOOG — ✅ GEBOUWD
**Status:** Al geïmplementeerd in `zaken/[id]/page.tsx`

Wat er is:
- ✅ 9 tabs: Overzicht | Taken | Vorderingen | Betalingen | Financieel | Derdengelden | Documenten | Activiteiten | Partijen
- ✅ Pipeline stepper met fase-visualisatie (Minnelijk, Regeling, Gerechtelijk, Executie, Afgerond)
- ✅ Workflow-driven status transities
- ✅ Verjaring badge (art. 3:307 BW)
- ✅ Claims CRUD, betalingen met art. 6:44 BW imputatie, financieel overzicht, derdengelden

Eventueel later verbeteren:
- Tab staat onthouden bij terugkeren (nu niet)
- Uren tab (tijdregistraties per zaak) ontbreekt
- Facturatie tab (facturen per zaak) ontbreekt

---

### B2. Quick actions bar op zaakdetail 🔴 HOOG — ✅ GEBOUWD
**Status:** Geïmplementeerd in `zaken/[id]/page.tsx`

Wat er is:
- ✅ Quick actions bar boven de tabs op zaakdetail
- ✅ [⏱ Uren loggen] — start floating timer via `useTimer` context (toont "Timer loopt..." als al actief)
- ✅ [💬 Notitie] — schakelt naar Activiteiten tab (met inline notitie invoerveld)
- ✅ [📄 Document] — schakelt naar Documenten tab
- ✅ [🧾 Factuur] — navigeert naar `/facturen/nieuw?case_id=...`
- ✅ [💰 Renteoverzicht] — contextueel, alleen bij incasso-zaken, schakelt naar Financieel tab
- ✅ Consistent styling met gekleurde iconen per actie

---

### B3. Notities verbeteren 🟡 MIDDEN
**Complexiteit:** Klein

Wat bouwen:
- Op Overzicht-tab: prominent notitie-toevoegveld (altijd zichtbaar, niet achter knop)
- Rich text (bold, italic, bullet points — niet overdreven)
- Notities verschijnen in de timeline

---

## Fase C: Dashboard & Facturatie verbeteren

> Kan parallel met Fase B

### C1. Dashboard verbeteren 🔴 HOOG — ✅ GEBOUWD
**Status:** Al grotendeels geïmplementeerd in `(dashboard)/page.tsx` (895 regels)

Wat er is:
- ✅ Persoonlijke begroeting ("Goedemorgen, Jan")
- ✅ KPI-kaarten: Actieve zaken, Openstaande facturen (€), Uren deze week, Taken openstaand
- ✅ Pipeline bar: visuele verdeling zaken per status
- ✅ KYC/WWFT waarschuwingen widget
- ✅ Mijn Taken widget (top 5 taken, met link naar /taken pagina)
- ✅ Weekoverzicht: uren, facturen, nieuwe zaken
- ✅ Recente facturen widget
- ✅ Recente activiteit widget
- ✅ Loading skeletons

Eventueel later verbeteren:
- Grafieken (uren per week bar chart, factuur-aging)
- Quick actions balk bovenaan

---

### C2. Betalingstracking op facturen 🔴 HOOG
**Complexiteit:** Groot (nieuw database model + API + frontend)

Wat bouwen:
- Deelbetalingen registreren op facturen
- Betalingsdatum en betaalmethode vastleggen
- Status automatisch: concept → goedgekeurd → verzonden → deels betaald → betaald
- Factuuroverzicht met aging: 0-30 / 31-60 / 61-90 / 90+ dagen
- Op dashboard: totaal openstaand met aging-breakdown

---

### C3. Credit nota's 🟡 MIDDEN
**Complexiteit:** Midden

Wat bouwen:
- Credit nota aanmaken gekoppeld aan originele factuur
- Negatief bedrag, zelfde layout als factuur
- PDF generatie
- Verwerking in financieel overzicht

---

## Fase D: Algemene UX polish

### D1. Wachtwoord vergeten flow 🔴 HOOG — ✅ GEBOUWD
**Status:** Geïmplementeerd in `reset-password/page.tsx` + `login/page.tsx`

Wat er is:
- ✅ "Wachtwoord vergeten?" link op loginpagina
- ✅ Login pagina stuurt `POST /api/auth/forgot-password` met e-mail
- ✅ Reset-pagina (`/reset-password?token=...`) met 3-staps flow:
  - Formulier: nieuw wachtwoord + bevestiging (min 8 tekens, eye-toggle)
  - Succes: bevestigingsscherm met "Naar inloggen" knop
  - Ongeldige link: foutmelding met "Terug naar inloggen"
- ✅ Backend: `POST /api/auth/reset-password` met token validatie
- ✅ Loading states, error handling, Suspense boundary

---

### D2. Gebruikersbeheer 🟡 MIDDEN
**Complexiteit:** Groot (rollen, rechten, multi-user impact op hele app)

Wat bouwen:
- Instellingen → Gebruikers: lijst, toevoegen, bewerken, deactiveren
- Rollen: Admin, Advocaat, Secretaresse (met verschillende rechten)
- Uurtarief per gebruiker
- Belangrijk voor de toekomst, niet urgent nu

---

### D3. Navigatie-verbeteringen 🟡 MIDDEN
**Complexiteit:** Klein

Wat bouwen:
- Betere breadcrumbs (Zaken > Jansen B.V. > Documenten)
- "Terug" knoppen die consistent werken
- Actieve pagina duidelijker markeren in sidebar

---

### D4. Empty states en loading states 🟢 LAAG
**Complexiteit:** Klein

Wat bouwen:
- Elk leeg scherm heeft een helpende tekst + actie-knop ("Nog geen zaken. Maak je eerste zaak aan →")
- Loading skeletons i.p.v. spinners
- Error states met duidelijke uitleg en retry-knop

---

### D5. Agenda — events aanmaken 🟡 MIDDEN
**Complexiteit:** Midden (nieuw backend model + CRUD + frontend)

**Probleem:** De agenda is read-only. Je kunt geen afspraken, zittingen of herinneringen inplannen.

Wat bouwen:
- Klikken op datum/tijdslot opent formulier voor nieuw event
- Velden: titel, datum/tijd, duur, zaak (optioneel), type (afspraak, zitting, herinnering, deadline)
- Events verschijnen naast workflow-deadlines in de kalender
- Bewerken en verwijderen van handmatige events

Backend nodig:
- Nieuw model: `CalendarEvent` (title, start, end, type, case_id, user_id, tenant_id)
- CRUD endpoints: `GET/POST/PATCH/DELETE /api/calendar/events`
- Alembic migratie

Zie `BUGS-EN-VERBETERPUNTEN.md` #5.

---

## Bugs — Nu fixen (volgende sessie)

> Zie `BUGS-EN-VERBETERPUNTEN.md` voor complete beschrijving met bestanden en fix-instructies.

| # | Bug | Ernst | Fix-grootte |
|---|-----|-------|-------------|
| BUG-1 | Relatie niet automatisch gekoppeld bij nieuwe zaak | Hoog | Klein (URL params + form pre-fill) |
| BUG-2 | Rente-velden zichtbaar bij niet-incasso zaaktypes | Midden | Klein (conditional render) |
| BUG-3 | Renteberekening per documentdatum controleren | Hoog | Verificatie nodig (lijkt al te werken) |

---

## Volgordesamenvatting

| # | Feature | Fase | Type | Complexiteit |
|---|---------|------|------|-------------|
| 1 | Timer voor tijdschrijven | A1 | ✅ Gebouwd | — |
| 2 | Global search (Ctrl+K) | A2 | ✅ Gebouwd | — |
| 3 | Mijn Taken pagina | A3 | ✅ Gebouwd | — |
| 4 | Activity timeline zaakdetail | A4 | ✅ Gebouwd | — |
| 5 | Dashboard verbeteren | C1 | ✅ Gebouwd | — |
| 6 | Zaakdetail tabs (B1) + quick actions (B2) | B1+B2 | ✅ Gebouwd | — |
| 7 | Betalingstracking facturen | C2 | Frontend + backend | Groot |
| 8 | Wachtwoord vergeten | D1 | ✅ Gebouwd | — |
| 9 | Contact-bedrijf links UI | A5 | ✅ Gebouwd | — |
| 10 | Notities verbeteren | B3 | Frontend only | Klein |
| 11 | Derdengelden UI | A6 | Frontend only | Klein |
| 12 | Financieel overzicht zaak | A7 | Frontend only | Klein |
| 13 | Credit nota's | C3 | Frontend + backend | Midden |
| 14 | Gebruikersbeheer | D2 | Frontend + backend | Groot |
| 15 | Navigatie-verbeteringen | D3 | Frontend only | Klein |
| 16 | Empty/loading states | D4 | Frontend only | Klein |
| 17 | Agenda events aanmaken | D5 | Frontend + backend | Midden |

### Apart traject (na B1)

| # | Feature | Ref | Type | Complexiteit |
|---|---------|-----|------|-------------|
| T1 | Templates op zaakdetail (status-filtered) | PROMPT-TEMPLATES-IN-WORKFLOW.md | Frontend | Midden |
| T2 | Workflow-suggesties bij statuswijziging | PROMPT-TEMPLATES-IN-WORKFLOW.md | Frontend | Klein-Midden |
| T3 | E-mail versturen vanuit Luxis (SMTP) | PROMPT-TEMPLATES-IN-WORKFLOW.md | Frontend + backend | Groot |

---

## Notities

- Fase B en C kunnen parallel lopen
- Features worden één of twee tegelijk opgepakt, niet als bulk
- Na elke feature: build check, handmatig testen, committen
- Complexiteitsschattingen zijn realistisch bijgesteld (niet optimistisch)
- Templates-in-workflow (T1/T2/T3) is een apart traject, zie `PROMPT-TEMPLATES-IN-WORKFLOW.md`. Dependency: B1 (zaakdetail tabs) moet eerst af
