# UX Research — D5: Agenda Events Aanmaken

> **Datum:** 20 februari 2026
> **Status:** Research afgerond — klaar voor plan & bouw
> **Doel:** Agenda uitbreiden van read-only (workflow taken + KYC) naar volledig event management

---

## 1. Concurrentieanalyse

### 1.1 Clio (marktleider juridische software)

**Bronnen:** [clio.com/features/calendar](https://www.clio.com/features/calendar/), [support.clio.com](https://support.clio.com/)

**Wat ze goed doen:**
- Twee-weg sync met Google Calendar, Outlook 365, en iCloud
- Events automatisch gekoppeld aan matters (zaken) — altijd contextbewust
- Court date calculator: berekent automatisch deadlines op basis van jurisdictie-specifieke regels (court rules)
- Drag-and-drop om events te verplaatsen in kalenderweergave
- Color coding per event type (afspraak, zitting, deadline, herinnering)
- Recurring events met uitgebreide opties (dagelijks, wekelijks, maandelijks, jaarlijks, custom)
- Herinneringen: meerdere per event (bijv. 1 week voor, 1 dag voor, 1 uur voor)
- Team calendar view: zie kalenders van alle medewerkers naast elkaar
- Time entry creatie direct vanuit calendar events

**Wat ze minder goed doen:**
- Complexe interface — veel opties die kleine kantoren niet nodig hebben
- Court rules database is US-focused, niet bruikbaar voor NL

**Relevantie voor Luxis:** Time entry vanuit event is zeer waardevol. Color coding en zaakkoppeling zijn essentieel. Court rules niet direct toepasbaar (NL kent geen court rules engine).

---

### 1.2 LegalSense (Nederlands)

**Bronnen:** [legalsense.nl](https://www.legalsense.nl/), demo-informatie

**Wat ze goed doen:**
- Volledige Outlook/Exchange integratie (twee-weg sync)
- Events gekoppeld aan dossiers en relaties
- Termijnbewaking geïntegreerd in kalender
- NL-specifiek: zittingsdagen, beroepstermijnen, verjaringstermijnen zichtbaar in agenda
- Herinnerings-workflow: escalatie als deadline nadert

**Wat ze minder goed doen:**
- Geen eigen kalenderweergave — leunt volledig op Outlook
- Beperkte mobiele ervaring

**Relevantie voor Luxis:** De koppeling tussen termijnbewaking en agenda is essentieel. Luxis heeft al verjaringstermijn-bewaking in de workflow module — deze moet zichtbaar worden in de kalender.

---

### 1.3 PracticePanther

**Bronnen:** [practicepanther.com/features/calendar](https://www.practicepanther.com/features/calendar/)

**Wat ze goed doen:**
- Eenvoudige event creatie: klik op tijdslot → formulier
- Elke event kan direct een time entry genereren ("Log time for this event")
- Color coding per event type EN per medewerker
- Drag-and-drop resize voor duur aanpassen
- Google Calendar en Outlook sync
- Custom event types definieerbaar door kantoor

**Wat ze minder goed doen:**
- Geen court rules engine
- Herinnerings-opties beperkt (alleen email, geen in-app)

**Relevantie voor Luxis:** "Klik op tijdslot → formulier" is de juiste UX. Time entry vanuit event is must-have.

---

### 1.4 Smokeball

**Bronnen:** [smokeball.com/features/legal-calendar](https://www.smokeball.com/features/legal-calendar-management-software/)

**Wat ze goed doen:**
- Auto-populatie van events bij statuswijziging (bijv. zaak naar "dagvaarding" → zittingsdatum event aangemaakt)
- Court rules calculator voor deadlines (US)
- Kalender events automatisch gelogd als activiteit op de zaak
- Conflict detection: waarschuwing bij dubbele boekingen
- Location field met Google Maps integratie

**Wat ze minder goed doen:**
- Zware software, vereist Windows desktop
- Minder geschikt voor kleine kantoren

**Relevantie voor Luxis:** Auto-events bij statuswijziging is interessant voor P1. Activity logging bij event creatie is een quick win.

---

### 1.5 Google Calendar / Outlook Calendar (benchmark voor UX)

**Bronnen:** Algemene kennis, interface-analyse

**Google Calendar — gouden standaard voor event creatie:**
- Quick create: klik op tijdslot → inline form (titel + tijd + opslaan)
- Full form: "Meer opties" → uitgebreid formulier
- Drag to create: sleep over tijdslots om duur te selecteren
- Recurring: eenvoudige presets (dagelijks, wekelijks op [dag], maandelijks) + custom
- Reminders: 10 min, 30 min, 1 dag default — aanpasbaar, meerdere per event
- Color coding: 12 kleuren, per event of per kalender
- All-day events vs. timed events
- Video call link generatie (Meet)

**Outlook Calendar:**
- Vergelijkbare functionaliteit als Google Calendar
- Sterke integratie met email (event vanuit email aanmaken)
- Beschikbaarheid checker voor meerdere deelnemers
- Categories met kleuren

**Relevantie voor Luxis:** De Google Calendar quick-create UX (klik → inline form → opslaan) is de benchmark. Lisanne kent dit patroon. Luxis moet dit gevoel benaderen.

---

### 1.6 Calendly (scheduling benchmark)

**Bronnen:** [calendly.com](https://calendly.com/)

**Relevant voor Luxis:** Niet direct — Calendly is voor externe scheduling. Maar het laat zien dat event types met standaard-duren (30 min consult, 60 min intake) de creatie versnellen. Dit concept (event type presets) is bruikbaar.

---

## 2. Synthese — Wat alle goede agenda's gemeen hebben

| Feature | Clio | Legal Sense | PP | Smoke ball | Google Cal | Essentieel? |
|---------|------|-------------|------|-----------|------------|-------------|
| Klik op tijdslot → event | ✅ | ❌ (Outlook) | ✅ | ✅ | ✅ | **Ja (P0)** |
| Zaak koppelen | ✅ | ✅ | ✅ | ✅ | N/A | **Ja (P0)** |
| Event types (afspraak, zitting, deadline) | ✅ | ✅ | ✅ | ✅ | ❌ | **Ja (P0)** |
| Color coding per type | ✅ | ❌ | ✅ | ✅ | ✅ | **Ja (P0)** |
| Recurring events | ✅ | ✅ | ✅ | ✅ | ✅ | **P1** |
| Herinneringen | ✅ | ✅ | ✅ | ✅ | ✅ | **P1** |
| Time entry vanuit event | ✅ | ❌ | ✅ | ✅ | N/A | **P1** |
| Relatie koppelen | ✅ | ✅ | ✅ | ✅ | N/A | **P1** |
| Drag-and-drop verplaatsen | ✅ | ❌ | ✅ | ❌ | ✅ | **P2** |
| Outlook/Google sync | ✅ | ✅ | ✅ | ❌ | N/A | **P2 (later)** |
| Court rules/termijnberekening | ✅ | ✅ | ❌ | ✅ | N/A | **P2 (NL-specifiek)** |
| Auto-events bij statuswijziging | ❌ | ❌ | ❌ | ✅ | N/A | **P2** |
| Conflict detection (dubbelboeking) | ❌ | ❌ | ❌ | ✅ | ✅ | **P2** |

---

## 3. Huidige Luxis Agenda — Analyse

### Backend (workflow module)
- **Endpoint:** `GET /api/workflow/calendar?date_from=&date_to=`
- **Bron:** Workflow tasks + KYC reviews (service.py `get_calendar_events`)
- **Schema:** `CalendarEvent` (id, title, date, event_type, status, case_id, case_number, contact_id, contact_name, assigned_to_name, task_type, color)
- **Geen eigen CalendarEvent model** — events zijn afgeleide data van workflow taken

### Frontend (`frontend/src/app/(dashboard)/agenda/page.tsx`)
- **955 regels** — volledig gebouwd, maar read-only
- **Views:** Maand-weergave (42-cel grid) + Week-weergave (7-kolom, uurblokken)
- **Day detail panel:** Klik op dag → sidebar met events van die dag
- **Color coding:** Per event type (task types: blauw, groen, paars, etc.)
- **Features:** Navigatie (vorige/volgende maand/week), vandaag-knop, view toggle
- **Event types:** Alleen `task` en `kyc_review`
- **Geen create/edit/delete functionaliteit**

### Hook (`frontend/src/hooks/use-calendar.ts`)
- `useCalendarEvents(dateFrom, dateTo)` — TanStack Query hook
- Haalt op van `/api/workflow/calendar`
- `CalendarEvent` interface: beperkt tot workflow-velden

### Wat mist
1. Geen CalendarEvent model (backend)
2. Geen CRUD endpoints voor events
3. Geen event creatie UI
4. Geen recurring events
5. Geen herinneringen/notificaties
6. Geen relatie-koppeling op events
7. Geen locatie-veld
8. Geen event types voor handmatige events (afspraak, zitting, herinnering)

---

## 4. Veldspecificaties — CalendarEvent Model

### Model: `CalendarEvent` (TenantBase)

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `title` | `String(255)` | Ja | Titel van het event |
| `description` | `Text` | Nee | Optionele toelichting/notities |
| `event_type` | `String(30)` | Ja | Type event (zie event types) |
| `start_time` | `DateTime(timezone=True)` | Ja | Starttijd (inclusief datum) |
| `end_time` | `DateTime(timezone=True)` | Ja | Eindtijd (inclusief datum) |
| `all_day` | `Boolean` | Ja (default: False) | Hele-dag event (bijv. deadline, vakantiedag) |
| `location` | `String(500)` | Nee | Locatie (vrij tekstveld: "Rechtbank Amsterdam", "Teams-call", etc.) |
| `case_id` | `UUID (FK → cases.id)` | Nee | Gekoppelde zaak |
| `contact_id` | `UUID (FK → contacts.id)` | Nee | Gekoppelde relatie (cliënt, wederpartij, etc.) |
| `color` | `String(20)` | Nee | Custom kleur override (default vanuit event_type) |
| `reminder_minutes` | `Integer` | Nee (default: 30) | Herinnering X minuten voor start. `null` = geen herinnering |
| `is_recurring` | `Boolean` | Ja (default: False) | Is dit een recurring event? |
| `recurrence_rule` | `String(255)` | Nee | iCal RRULE string (bijv. `FREQ=WEEKLY;BYDAY=MO`) |
| `recurrence_parent_id` | `UUID (FK → calendar_events.id)` | Nee | Verwijst naar parent bij recurring series |
| `created_by` | `UUID (FK → users.id)` | Ja | Wie heeft het event aangemaakt |

### Event Types

| Type | Label (NL) | Default kleur | Toelichting |
|------|-----------|---------------|-------------|
| `appointment` | Afspraak | `blue` | Cliëntgesprek, intakegesprek, bespreking |
| `hearing` | Zitting | `red` | Rechtbankzitting, comparitie, pleidooi |
| `deadline` | Deadline | `orange` | Processtermijn, beroepstermijn, verjaring |
| `reminder` | Herinnering | `yellow` | Persoonlijke herinnering, follow-up |
| `meeting` | Vergadering | `purple` | Interne vergadering, teamoverleg |
| `call` | Telefoongesprek | `green` | Gepland telefoongesprek |
| `other` | Overig | `gray` | Catch-all |

### Indexes

- `ix_calendar_events_tenant_id` — standaard tenant filter
- `ix_calendar_events_start_time` — voor date range queries
- `ix_calendar_events_case_id` — voor zaak-overzichten
- `ix_calendar_events_created_by` — voor "mijn agenda"

---

## 5. API Endpoints

### Nieuw: `/api/calendar/events`

| Method | Endpoint | Doel |
|--------|----------|------|
| `GET` | `/api/calendar/events?date_from=&date_to=&event_type=` | Events ophalen voor periode |
| `POST` | `/api/calendar/events` | Nieuw event aanmaken |
| `GET` | `/api/calendar/events/{id}` | Enkel event ophalen |
| `PATCH` | `/api/calendar/events/{id}` | Event bijwerken |
| `DELETE` | `/api/calendar/events/{id}` | Event verwijderen |

### Bestaand: `/api/workflow/calendar` (ongewijzigd)

De workflow calendar endpoint blijft bestaan. De frontend combineert beide bronnen:
1. **Workflow events** (taken, KYC reviews) — automatisch, read-only
2. **Calendar events** (handmatig aangemaakt) — full CRUD

De frontend hook combineert deze in één unified view.

---

## 6. Wireframe-beschrijving (tekstueel)

### 6.1 Maandweergave — Event creatie

```
┌─────────────────────────────────────────────────────────────┐
│  ◀  Februari 2026  ▶          [Maand] [Week]    [+ Event]   │
├─────┬─────┬─────┬─────┬─────┬─────┬─────┤
│ ma  │ di  │ wo  │ do  │ vr  │ za  │ zo  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│     │     │     │     │     │     │  1  │
│     │     │     │     │     │     │     │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  2  │  3  │  4  │  5  │  6  │  7  │  8  │
│🔵Cli│     │🔴Zit│🟡Tak│     │     │     │
│     │     │ ting│ en  │     │     │     │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  9  │ ...                                │
└─────────────────────────────────────────────────────────────┘
```

**Interacties:**
- **Klik op dag** → Day detail panel opent rechts (bestaand gedrag)
- **Klik op `[+ Event]`** → Event creation dialog opent
- **Klik op event chip** → Event detail popover met edit/delete knoppen

### 6.2 Weekweergave — Klik-op-tijdslot

```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Maandag  │ Dinsdag  │ Woensdag │ Donderdag│ Vrijdag  │
│ 3 feb    │ 4 feb    │ 5 feb    │ 6 feb    │ 7 feb    │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│ 08:00    │          │          │          │          │
│ 09:00    │ ████████ │          │          │          │
│ 10:00    │ Zitting  │          │ ████████ │          │
│ 11:00    │ Rb A'dam │          │ Cliënt-  │          │
│ 12:00    │          │          │ gesprek  │          │
│ 13:00    │          │          │          │          │
│ 14:00    │          │ ████████ │          │          │
│ 15:00    │          │ Deadline │          │          │
│ 16:00    │          │ Beroep   │          │          │
│ 17:00    │          │          │          │          │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

**Interacties:**
- **Klik op leeg tijdslot** → Quick-create popover (Google Calendar-stijl):
  ```
  ┌────────────────────────────┐
  │ Titel: [________________]  │
  │ Type:  [Afspraak ▾]        │
  │ Tijd:  09:00 - 10:00       │
  │ Zaak:  [Zoek zaak... ▾]    │
  │                             │
  │ [Meer opties]   [Opslaan]  │
  └────────────────────────────┘
  ```
- **"Meer opties"** → opent volledige event creation dialog

### 6.3 Event Creation Dialog (volledig formulier)

```
┌──────────────────────────────────────────────┐
│  Nieuw event                            [X]  │
├──────────────────────────────────────────────┤
│                                              │
│  Titel *          [________________________] │
│                                              │
│  Type *           [Afspraak           ▾]     │
│                   🔵 Afspraak                │
│                   🔴 Zitting                 │
│                   🟠 Deadline                │
│                   🟡 Herinnering             │
│                   🟣 Vergadering             │
│                   🟢 Telefoongesprek         │
│                   ⚪ Overig                  │
│                                              │
│  ☐ Hele dag                                  │
│                                              │
│  Datum *          [20-02-2026       📅]      │
│  Starttijd *      [09:00            🕐]      │
│  Eindtijd *       [10:00            🕐]      │
│                                              │
│  Locatie          [________________________] │
│                                              │
│  Zaak             [Zoek zaak...        🔍]   │
│                    → Kesting / Van Dam 2026   │
│                                              │
│  Relatie          [Zoek relatie...      🔍]   │
│                    → Van Dam Holding B.V.     │
│                                              │
│  Herinnering      [30 minuten voor   ▾]      │
│                   Geen                       │
│                   10 minuten voor             │
│                   30 minuten voor             │
│                   1 uur voor                  │
│                   1 dag voor                  │
│                   1 week voor                 │
│                                              │
│  Beschrijving     [________________________] │
│                   [________________________] │
│                   [________________________] │
│                                              │
│  ─── Herhaling (P1) ────────────────────     │
│  ☐ Herhalend event                           │
│                                              │
├──────────────────────────────────────────────┤
│              [Annuleren]    [Opslaan]         │
└──────────────────────────────────────────────┘
```

### 6.4 Day Detail Panel (bestaand, uitgebreid)

Het bestaande day detail panel (rechter sidebar bij klik op dag) wordt uitgebreid:

```
┌──────────────────────────────┐
│  Donderdag 6 februari        │
│  ─────────────────────────── │
│  + Event toevoegen           │  ← NIEUW: knop bovenaan
│                              │
│  09:00 - 10:00               │
│  🔵 Cliëntgesprek Van Dam   │  ← Handmatig event
│     📁 2026/001              │
│     [Bewerken] [Verwijderen] │  ← NIEUW: actieknoppen
│                              │
│  14:00                       │
│  🟡 Taak: Conclusie van     │  ← Workflow taak (read-only)
│     antwoord indienen        │
│     📁 2026/003              │
│     Status: Openstaand       │
│                              │
│  Geen andere events          │
└──────────────────────────────┘
```

---

## 7. Integratie met bestaande code

### Backend

1. **Nieuw module:** `backend/app/calendar/` met models.py, schemas.py, service.py, router.py
2. **Registratie:** Router toevoegen in `main.py`
3. **Alembic:** Migratie voor `calendar_events` tabel
4. **Geen wijzigingen aan workflow module** — `/api/workflow/calendar` blijft ongewijzigd

### Frontend

1. **Nieuwe hook:** `frontend/src/hooks/use-calendar-events.ts` — CRUD voor handmatige events
2. **Unified hook:** `use-calendar.ts` uitbreiden om zowel workflow events als calendar events te combineren
3. **Agenda pagina:** Uitbreiden met:
   - `[+ Event]` knop in header
   - Event creation dialog (shadcn Dialog + Form)
   - Quick-create popover bij klik op tijdslot (weekweergave)
   - Event detail popover met edit/delete
   - "Event toevoegen" knop in day detail panel
4. **CalendarEvent type** uitbreiden met nieuwe event_types
5. **Zaakdetail:** Events tab tonen op zaakdetail (events gekoppeld aan case_id)

---

## 8. Prioritering

### P0 — Eerste release (MVP)

Must-have voor bruikbare agenda. Zonder deze features is de agenda nog steeds read-only en onbruikbaar als dagelijks werktuig.

| Feature | Backend | Frontend | Complexiteit |
|---------|---------|----------|-------------|
| CalendarEvent model + migratie | Ja | — | Klein |
| CRUD endpoints (GET/POST/PATCH/DELETE) | Ja | — | Midden |
| Event creation dialog (volledig formulier) | — | Ja | Midden |
| Event bewerken/verwijderen | — | Ja | Klein |
| 7 event types met color coding | Beide | Beide | Klein |
| Zaak koppelen aan event | Beide | Beide | Klein |
| All-day events vs. timed events | Beide | Beide | Klein |
| Unified calendar view (workflow + handmatig) | — | Ja | Midden |
| `[+ Event]` knop in header | — | Ja | Klein |
| Event detail in day panel met edit/delete | — | Ja | Klein |

**Geschatte inspanning P0:** ~1 backend sessie + ~1-2 frontend sessies

### P1 — Tweede release (enhanced)

Waardevolle features die de agenda van "bruikbaar" naar "productief" brengen.

| Feature | Backend | Frontend | Complexiteit |
|---------|---------|----------|-------------|
| Relatie koppelen aan event | Beide | Beide | Klein |
| Herinneringen (reminder_minutes veld) | Backend | Frontend | Klein |
| Quick-create popover (klik op tijdslot, weekweergave) | — | Ja | Midden |
| Recurring events (basis: dagelijks, wekelijks, maandelijks) | Beide | Beide | Groot |
| Locatie-veld | Beide | Beide | Klein |
| Events op zaakdetail tab | — | Ja | Klein |
| Time entry aanmaken vanuit event ("Log uren") | — | Ja | Klein |
| Activity logging bij event creatie | Backend | — | Klein |

**Geschatte inspanning P1:** ~2 sessies

### P2 — Toekomst (nice-to-have)

Features die waarde toevoegen maar niet essentieel zijn voor dagelijks gebruik.

| Feature | Toelichting |
|---------|-------------|
| Drag-and-drop verplaatsen/resizen | Vereist complexe UI library (bijv. react-big-calendar of FullCalendar) |
| Outlook/Google Calendar sync (twee-weg) | Vereist OAuth flows + webhook/polling — apart traject (T3-gerelateerd) |
| In-app notificaties bij herinnering | Vereist WebSocket of polling + notificatie-systeem |
| Auto-events bij statuswijziging | Workflow rule uitbreiden: bij status X → event aanmaken |
| Conflict detection (dubbelboeking) | Waarschuwing bij overlappende events |
| Team calendar (meerdere gebruikers naast elkaar) | Relevant bij multi-user kantoren |
| iCal export/import (.ics) | Handmatige synchronisatie |
| Event templates (presets: "30 min consult", "60 min intake") | Versnelt event creatie |

---

## 9. Recurring Events — Technische aanpak (P1)

### Strategie: Hybrid (opslaan + genereren)

- **Parent event** slaat de `recurrence_rule` op (iCal RRULE format)
- **Instances** worden on-the-fly gegenereerd bij ophalen, niet vooraf in de database
- **Exceptions** (enkele instance gewijzigd/verwijderd) worden als losse records met `recurrence_parent_id` opgeslagen
- Dit voorkomt duizenden rijen voor een wekelijkse afspraak over een jaar

### RRULE voorbeelden

| Patroon | RRULE |
|---------|-------|
| Elke maandag | `FREQ=WEEKLY;BYDAY=MO` |
| Elke 2 weken op woensdag | `FREQ=WEEKLY;INTERVAL=2;BYDAY=WE` |
| Eerste maandag van de maand | `FREQ=MONTHLY;BYDAY=1MO` |
| Dagelijks tot 1 maart | `FREQ=DAILY;UNTIL=20260301T000000Z` |

### Python library

- `python-dateutil` (al in dependencies) heeft `rrule` module voor RRULE parsing en instance generatie
- Alternatief: `icalendar` package als we later .ics export willen

---

## 10. Aanbevelingen

### Bouw P0 eerst — dat is al enorm waardevol

De huidige agenda is nutteloos voor dagelijks gebruik: Lisanne kan er geen afspraken in zetten. Met P0 wordt het een werkbaar hulpmiddel. De stap van "read-only takenlijst" naar "echte agenda" is de belangrijkste.

### Houd het simpel

- Geen drag-and-drop in P0 — dat is een complexiteit-explosie
- Geen recurring events in P0 — de RRULE-logica is een apart traject
- Geen calendar sync in P0 — dat is een heel apart project (OAuth, webhooks, conflict resolution)

### Respecteer de Google Calendar UX

Lisanne kent Google Calendar en Outlook. De event creation flow moet vertrouwd aanvoelen:
1. Klik op `[+ Event]` of op een tijdslot
2. Vul titel en type in
3. Optioneel: koppel zaak, voeg locatie toe
4. Opslaan

Vier stappen, maximaal. Geen wizards, geen multi-step flows.

### Integreer met wat er is

- De workflow taken en KYC reviews blijven in de agenda — ze worden niet vervangen
- De nieuwe CalendarEvent is een aanvulling, geen vervanging
- De frontend combineert beide bronnen in één unified view
- Op de zaakdetail pagina verschijnen events in een bestaande of nieuwe tab

---

*Dit document is de UX research basis voor D5. De implementatie volgt de standaard werkwijze: plan → bouw → check → commit.*
