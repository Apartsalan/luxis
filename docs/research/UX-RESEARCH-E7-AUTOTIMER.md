# UX Research — E7: Auto-timer bij openen dossier

> **Datum:** 20 februari 2026
> **Status:** Research afgerond — klaar voor implementatie
> **Prioriteit:** Midden (E7 in roadmap — na productie-feedback)
> **Complexiteit:** Midden

---

## 1. Wat er nu is

### Huidige timer-architectuur

De timer is een **handmatige start/stop stopwatch** die als floating widget rechtsonder in het scherm leeft. De hele implementatie is puur frontend — er is geen backend timer-state.

#### Bestanden

| Bestand | Regels | Doel |
|---------|--------|------|
| `frontend/src/hooks/use-timer.ts` | 212 | Timer state, context, persistence, start/stop/discard logica |
| `frontend/src/components/floating-timer.tsx` | 317 | Floating UI widget (compact pill + expanded panel) |
| `frontend/src/components/providers.tsx` | 66 | `TimerProvider` wrapper + `FloatingTimer` mount |

#### TimerState interface (`use-timer.ts`, regel 16-23)

```typescript
export interface TimerState {
  running: boolean;
  seconds: number;
  caseId: string;
  caseName: string;       // e.g. "2024-001 — Jansen B.V."
  description: string;
  startedAt: number | null; // timestamp voor persistence
}
```

#### Hoe de timer werkt

1. **Start:** Gebruiker klikt "Uren loggen" op dossierdetail (regel 580 in `zaken/[id]/page.tsx`) of kiest een dossier in de floating timer → `startTimer(caseId, caseName)` wordt aangeroepen (`use-timer.ts`, regel 142-158)
2. **Ticking:** `setInterval` van 1 seconde (`use-timer.ts`, regel 121-140). State wordt elke 10 seconden naar localStorage geschreven (regel 128)
3. **Stop & Opslaan:** `stopTimer()` (regel 160-179) berekent `Math.max(1, Math.round(timer.seconds / 60))` minuten en roept `POST /api/time-entries` aan met `activity_type: "other"` en `billable: true`
4. **Discard:** `discardTimer()` (regel 181-184) wist state en localStorage
5. **Persistence:** localStorage key `luxis_timer` (regel 36). Bij page load wordt de timer hersteld inclusief herberekening van verstreken tijd via `startedAt` timestamp (regel 68-84)

#### localStorage persistence detail (`use-timer.ts`, regels 68-98)

```typescript
const STORAGE_KEY = "luxis_timer";

function loadFromStorage(): TimerState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return defaultTimer;
  const saved = JSON.parse(raw) as TimerState;
  // Als timer liep, herbereken verstreken seconden
  if (saved.running && saved.startedAt) {
    const elapsed = Math.floor((Date.now() - saved.startedAt) / 1000);
    return { ...saved, seconds: elapsed };
  }
  return saved;
}
```

Dit betekent: als de browser crasht of het tabblad gesloten wordt terwijl de timer loopt, wordt bij heropenen de correcte verstreken tijd berekend. **Dit is al crash-recovery.**

#### Floating timer UI (`floating-timer.tsx`)

Drie visuele states:
1. **Collapsed + running** (regel 177-191): Groen pill rechtsonder met `h:mm:ss` en pulserende klok-icoon
2. **Collapsed + stopped** (regel 195-208): Neutraal pill met "Timer" label
3. **Expanded** (regel 211-316): Panel met:
   - Timer display (groot `h:mm:ss`, groen als running)
   - Dossierkiezer (`CompactCasePicker`, regel 30-149) — alleen als timer NIET loopt
   - Omschrijvingsveld — alleen als timer WEL loopt
   - Start / Stop & Opslaan / Verwijderen knoppen
   - Link naar urenregistratie pagina

#### Context en Provider (`providers.tsx`)

De timer zit in de `TimerProvider` (regel 16-23) die bovenin de componentboom staat, binnen `AuthProvider` en `QueryClientProvider`. De `FloatingTimer` wordt als sibling van `{children}` gerenderd (regel 52), waardoor hij op ALLE dashboard-pagina's zichtbaar is.

#### Dossierdetail integratie (`zaken/[id]/page.tsx`)

De Quick Actions bar (regel 574) bevat een "Uren loggen" knop:
```typescript
const { startTimer, timer } = useTimer();
// ...
onClick={() => {
  const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
  startTimer(zaak.id, label);
}}
disabled={timer.running && timer.caseId === zaak.id}
```
- Als de timer al loopt voor DIT dossier: knop disabled met tekst "Timer loopt..."
- Als de timer loopt voor een ANDER dossier: knop enabled — start nieuwe timer (overschrijft de oude zonder waarschuwing!)

#### Backend time entries (`time_entries/router.py`)

- `POST /api/time-entries` — aanmaken (regel 46-59)
- `GET /api/time-entries/my/today` — vandaag-entries voor timer widget (regel 124-132)
- Model: `TimeEntry` met `user_id`, `case_id`, `date`, `duration_minutes`, `description`, `activity_type`, `billable`, `invoiced`, `hourly_rate`
- **Geen timer-gerelateerde backend state** — de timer is 100% frontend

#### Wat er NIET is

| Ontbrekend | Impact |
|-----------|--------|
| **Geen auto-start bij openen dossier** | Lisanne moet elke keer handmatig de timer starten |
| **Geen pauze-functie** | Alleen start en stop (stop = meteen opslaan) |
| **Geen waarschuwing bij vergeten timer** | Timer kan urenlang doorlopen zonder notificatie |
| **Geen idle detection** | Geen detectie van inactiviteit |
| **Geen instelling handmatig/automatisch** | Geen user preferences voor timermodus |
| **Geen waarschuwing bij dossierwisseling** | Timer overschrijft zonder bevestiging |
| **Geen activity type selectie** | Altijd `activity_type: "other"` (regel 168) |

---

## 2. Wat Lisanne nodig heeft

### Kernbehoefte

> "Als ik een dossier open, wil ik dat de timer automatisch start. Als ik naar een ander dossier ga, wil ik dat de tijd voor het vorige dossier wordt opgeslagen en de timer voor het nieuwe dossier start."

### Use cases

| Scenario | Frequentie | Gewenst gedrag |
|----------|-----------|----------------|
| Dossier openen om te werken | Dagelijks, 10-20x | Timer start automatisch |
| Wisselen naar ander dossier | Dagelijks, 5-10x | Vorige timer opslaan, nieuwe starten |
| Even snel iets opzoeken in ander dossier | Regelmatig | Korte bezoeken (<1-2 min) niet registreren |
| Vergeten timer na werkdag | Wekelijks | Waarschuwing of automatisch stoppen |
| Dossier bekijken zonder werk (bijv. status checken) | Vaak | Optie om auto-timer uit te zetten |
| Browser crasht terwijl timer loopt | Zeldzaam | Timer herstellen bij heropenen (WERKT AL) |

### Twee modi

Lisanne moet kunnen kiezen tussen:

1. **Handmatig** (huidige modus): Timer start alleen bij klik op "Uren loggen"
2. **Automatisch**: Timer start bij openen dossier, pauzeet/stopt bij navigatie weg

De keuze wordt opgeslagen als **user preference** in localStorage (geen backend nodig).

---

## 3. Hoe concurrenten dit doen

### Smokeball — AutoTime (volledig passief)

Smokeball's AutoTime is het meest geavanceerde systeem: **volledig passief, geen timer nodig**.

**Hoe het werkt:**
- AutoTime draait constant op de achtergrond (desktop app vereist)
- Monitort automatisch: documenten (Word), e-mails (Outlook), kalenderbesprekingen, taken, memo's, telefoongesprekken (RingCentral)
- Koppelt tijd automatisch aan het juiste dossier via bestandsassociaties
- Elke nacht (of handmatig) worden activiteiten verwerkt tot tijdregistraties
- Gebruiker reviewt entries voordat ze op facturen komen

**Instellingen (per gebruiker, opt-in):**
- Master toggle: "Automatisch tijdregistraties aanmaken" (standaard UIT)
- Per activiteittype aan/uit (e-mail, documenten, admin, memo's, etc.)
- Groepering: activiteiten samenvoegen tot één entry of apart houden
- E-mail notificatie bij aanmaak entries
- Geen entries voor gesloten dossiers
- Afrondingsregels configureerbaar

**Vergeten timer:** Probleem bestaat niet — er IS geen timer. Het systeem vangt alles passief op.

**Dossierwisseling:** Automatisch — Smokeball detecteert via file/email metadata welk dossier actief is.

**Smokeball claimt:** "AutoTime-gebruikers factureren 10-30% meer doordat ze meer tijd accuraat vastleggen."

**Relevant voor Luxis:** Smokeball's model vereist een desktop app en diepgaande OS-integratie. Niet haalbaar voor een web-app. Maar het **principe** (minimale gebruikersactie, automatische dossierkoppeling) is de gouden standaard.

### Clio — Handmatige timer

Clio gebruikt een **handmatig timermodel** zonder auto-start.

**Hoe het werkt:**
- Play-knop in de header op elke pagina (vergelijkbaar met onze floating timer)
- Klik play → timer start (zonder dossier)
- Klik op "Edit entry" om dossier te koppelen
- Als je de timer start vanuit een dossierpagina, wordt het dossier automatisch ingevuld
- Klik pause → time entry modal opent → invullen en opslaan

**Meerdere timers:** Slechts één tegelijk. Nieuwe timer auto-pauzeet de vorige.

**Idle detection:** GEEN ingebouwde idle detectie. Clio vertrouwt op third-party integraties:
- **Faster Time (Faster Law)**: Passief tracken, 5 min idle → automatisch pauzeren, AI-suggesties voor dossiertoewijzing
- **WiseTime**: Privacy-first passieve tracker, window title matching
- **Chrometa**: Start bij boot, trackt alles

**Vergeten timer:** Clio heeft GEEN waarschuwing voor vergeten timers.

**Relevant voor Luxis:** Clio's benadering (één timer tegelijk, auto-pauze bij nieuwe) is het dichtstbij wat wij al hebben. De ontbrekende idle detection en vergeten-timer-waarschuwing zijn bekende zwakheden.

### Harvest — Timer met idle detection

Harvest biedt een **handmatige timer met robuuste safety nets**.

**Hoe het werkt:**
- Selecteer project + taak → klik "Start timer"
- Twee modi (account-breed): Duration mode (uren invoeren) of Start/End Times mode
- Timer zichtbaar in de interface tijdens navigatie

**Idle detection (desktop apps):**
- Monitort toetsenbord- en muisactiviteit
- Na X minuten inactiviteit: notificatie met 4 opties:
  1. "Stop timer en verwijder X minuten" — stopt en trekt idle tijd af
  2. "Ga door en verwijder X minuten" — timer loopt door, idle afgetrokken
  3. "Voeg X minuten toe als nieuwe entry" — splitst de tijd
  4. "Negeer" — alles blijft zoals het is
- Timeout configureerbaar per gebruiker

**Vergeten timer:**
- E-mail notificatie als timer te lang draait
- In-app notificatie
- Mobiel: "Herinner me na X minuten" met push-notificatie

**Dagelijkse herinneringen:**
- Configureerbaar per dag van de week
- Instelbare tijd ("Heb je al je uren ingevuld?")

**Dossierwisseling:** Volledig handmatig — stop huidige, start nieuwe.

**Relevant voor Luxis:** Harvest's idle detection en vergeten-timer-waarschuwingen zijn direct toepasbaar. De 4-optie idle dialog is een goed UX-patroon.

### Synthese — Wat wij overnemen

| Feature | Bron | Toepassing in Luxis |
|---------|------|---------------------|
| Auto-start bij openen dossier | Smokeball-principe (vereenvoudigd) | Timer start bij navigatie naar `/zaken/[id]` |
| Auto-pauze bij dossierwisseling | Smokeball + Clio | Vorige timer opslaan, nieuwe starten |
| Idle detection | Harvest | Detectie via `visibilitychange` + `mousemove`/`keydown` |
| Vergeten timer waarschuwing | Harvest | Notificatie na configureerbare tijd (bijv. 2 uur) |
| Opt-in instelling | Smokeball | Toggle in floating timer panel |
| Minimale frictie | Smokeball | Zo min mogelijk klikken, automatisch dossier koppelen |

---

## 4. Frontend plan

### 4.1 Auto-start logica

**Waar:** Nieuwe hook `useAutoTimer` of uitbreiding van `use-timer.ts`

**Trigger:** Detecteren dat de gebruiker op een dossierpagina navigeert (`/zaken/[id]`).

**Implementatie-opties:**

#### Optie A: Hook in `zaken/[id]/page.tsx` (aanbevolen)

Voeg een `useEffect` toe aan de dossierdetail pagina die reageert op de `id` parameter:

```typescript
// In zaken/[id]/page.tsx
const { startTimer, stopTimer, timer } = useTimer();
const autoTimerEnabled = useAutoTimerPreference(); // localStorage

useEffect(() => {
  if (!autoTimerEnabled || !zaak) return;

  // Als er al een timer loopt voor DIT dossier, niets doen
  if (timer.running && timer.caseId === zaak.id) return;

  // Als er een timer loopt voor een ANDER dossier
  if (timer.running && timer.caseId !== zaak.id) {
    // Sla de lopende timer op als time entry (als > 1 min)
    if (timer.seconds >= 60) {
      stopTimer(); // async — slaat op als time entry
    } else {
      discardTimer(); // < 1 min — verwijder
    }
  }

  // Start timer voor dit dossier
  const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
  startTimer(zaak.id, label);
}, [zaak?.id, autoTimerEnabled]);
```

#### Optie B: Route-change listener in de timer provider

Een `usePathname()` hook in de `TimerProvider` die monitort wanneer de URL verandert naar `/zaken/[id]`. Nadeel: vereist case data fetching in de provider.

**Aanbeveling: Optie A** — eenvoudiger, geen extra data fetching, logica zit waar de data al beschikbaar is.

### 4.2 Auto-timer instelling (handmatig vs. automatisch)

**Opslag:** localStorage key `luxis_auto_timer` (boolean).

**UI-locatie:** Toggle in de floating timer panel (expanded state), onder de timer display:

```
[🔄 Automatisch]  ← toggle switch
Automatisch starten bij openen dossier
```

**Hook:**

```typescript
// Nieuwe hook of toevoegen aan use-timer.ts
const AUTO_TIMER_KEY = "luxis_auto_timer";

export function useAutoTimerPreference(): [boolean, (v: boolean) => void] {
  const [enabled, setEnabled] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(AUTO_TIMER_KEY) === "true";
  });

  const toggle = useCallback((value: boolean) => {
    setEnabled(value);
    localStorage.setItem(AUTO_TIMER_KEY, String(value));
  }, []);

  return [enabled, toggle];
}
```

**Standaard: UIT** (opt-in, consistent met Smokeball en industrie-consensus).

### 4.3 Dossierwisselingslogica

Wanneer de gebruiker van dossier A naar dossier B navigeert:

```
Dossier A open, timer loopt (3:45)
  → Gebruiker klikt op dossier B
  → Timer A: seconds >= 60? → stopTimer() → opslaan als time entry (4 min)
  → Timer B: startTimer(B.id, B.label)
  → Toast: "3:45 opgeslagen voor 2024-001 — Jansen B.V."
```

**Drempel voor opslaan:** 60 seconden (1 minuut). Korter dan 1 minuut = automatisch verwijderen. Dit voorkomt dat korte "even snel kijken" bezoeken als tijdregistratie worden opgeslagen.

**Navigatie weg van dossier (naar dashboard, relaties, etc.):**
- Timer loopt door (huidige gedrag) — de floating timer blijft zichtbaar
- NIET automatisch stoppen, want Lisanne kan werk doen gerelateerd aan het dossier (bijv. een relatie opzoeken)

### 4.4 Vergeten timer waarschuwing

**Trigger:** Timer loopt langer dan een configureerbare drempel (default: 2 uur).

**Implementatie:** In de tick-interval van `use-timer.ts`:

```typescript
// In useTimerProvider, binnen het tick-interval effect
const FORGOTTEN_THRESHOLD = 2 * 60 * 60; // 2 uur in seconden
const hasWarned = useRef(false);

useEffect(() => {
  if (timer.running && timer.seconds >= FORGOTTEN_THRESHOLD && !hasWarned.current) {
    hasWarned.current = true;
    toast.warning(
      `Timer loopt al ${Math.floor(timer.seconds / 3600)} uur voor ${timer.caseName}`,
      {
        action: {
          label: "Stop & Opslaan",
          onClick: () => stopTimer(),
        },
        duration: 10000, // 10 seconden zichtbaar
      }
    );
  }
  // Reset warning als timer stopt
  if (!timer.running) hasWarned.current = false;
}, [timer.seconds, timer.running]);
```

**Herhalende waarschuwing:** Optioneel elke 30 minuten na de eerste waarschuwing. Of alleen éénmalig (eenvoudiger).

### 4.5 Idle detection (optioneel, fase 2)

**Wat:** Detecteer dat de gebruiker inactief is (geen muis/toetsenbord) en pauzeer de timer.

**Browser API's:**
- `document.visibilityState` — detecteert tab-wisseling
- `mousemove` / `keydown` events — detecteert activiteit

```typescript
// Conceptueel — idle detection hook
function useIdleDetection(timeoutMinutes: number = 15) {
  const [isIdle, setIsIdle] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    const resetTimer = () => {
      setIsIdle(false);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setIsIdle(true), timeoutMinutes * 60 * 1000);
    };

    window.addEventListener("mousemove", resetTimer);
    window.addEventListener("keydown", resetTimer);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) setIsIdle(true);
      else resetTimer();
    });

    resetTimer();
    return () => {
      // cleanup listeners
    };
  }, [timeoutMinutes]);

  return isIdle;
}
```

**Aanbeveling:** Idle detection is complex en kan frustrerend zijn (vals positieven bij lezen). **Fase 2** — eerst auto-start en vergeten-timer bouwen, idle detection later toevoegen op basis van feedback.

### 4.6 Meerdere tabs

**Probleem:** Gebruiker opent dossier A in tab 1 en dossier B in tab 2. Beide triggeren auto-start.

**Oplossing:** localStorage is al gedeeld tussen tabs. De `startTimer()` functie overschrijft de state. De tab die als laatste een dossier opent "wint". Dit is acceptabel gedrag:
- De timer staat altijd op het laatst geopende dossier
- De `storage` event kan gebruikt worden om andere tabs te synchroniseren

```typescript
// Optioneel: luister naar storage changes van andere tabs
useEffect(() => {
  const handleStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY && e.newValue) {
      setTimer(JSON.parse(e.newValue));
    }
  };
  window.addEventListener("storage", handleStorage);
  return () => window.removeEventListener("storage", handleStorage);
}, []);
```

### 4.7 Activity type selectie

Momenteel wordt altijd `activity_type: "other"` gebruikt (regel 168 in `use-timer.ts`). Verbetering:

- Voeg een activity type dropdown toe aan het expanded timer panel
- Default: "other" (of de laatst gebruikte)
- Opties: Correspondentie, Bespreking, Telefonisch, Onderzoek, Zitting, Reistijd, Opstellen stukken, Overig

Dit is een quick win die los staat van de auto-timer maar de timer als geheel verbetert.

---

## 5. Backend plan

### Geen backend-wijzigingen nodig voor fase 1

De auto-timer is een puur **frontend feature**. De bestaande backend endpoints zijn voldoende:

| Endpoint | Gebruik | Wijziging nodig? |
|----------|---------|-----------------|
| `POST /api/time-entries` | Opslaan van timer als time entry | Nee |
| `GET /api/time-entries/my/today` | Widget met vandaag-entries | Nee |

De timer state blijft in localStorage. De user preference (auto/handmatig) blijft in localStorage.

### Mogelijke backend uitbreiding (fase 2)

Als we user preferences server-side willen opslaan (voor synchronisatie tussen apparaten):

```python
# Nieuw endpoint
PUT /api/settings/user-preferences
{
  "auto_timer_enabled": true,
  "auto_timer_min_seconds": 60,
  "forgotten_timer_threshold_minutes": 120
}
```

**Maar dit is NIET nodig voor fase 1.** Lisanne gebruikt één apparaat. localStorage is voldoende.

---

## 6. Bouwstappen

### Fase 1: Auto-start bij openen dossier (1-1,5 uur)

1. Voeg `useAutoTimerPreference` hook toe aan `use-timer.ts` — localStorage-backed boolean state
2. Voeg auto-start `useEffect` toe aan `zaken/[id]/page.tsx`:
   - Check of auto-timer enabled is
   - Check of timer al loopt voor dit dossier (skip als ja)
   - Als timer loopt voor ander dossier: stop & save (>60s) of discard (<60s)
   - Start nieuwe timer voor huidig dossier
3. Voeg auto-timer toggle toe aan floating timer panel (`floating-timer.tsx`):
   - Switch/toggle onder de timer display
   - Label: "Automatisch starten bij dossier"
   - Alleen zichtbaar in expanded state
4. `npm run build` — check
5. Commit: `feat(timer): auto-start timer on case detail page (E7)`

### Fase 2: Vergeten timer waarschuwing (30 min)

1. Voeg threshold constante toe aan `use-timer.ts` (default 2 uur)
2. Voeg `hasWarned` ref toe aan `useTimerProvider`
3. Voeg check toe in het tick-interval effect: als `seconds >= threshold && !hasWarned`
4. Toon toast.warning met "Stop & Opslaan" action button
5. Reset warning bij timer stop
6. `npm run build` — check
7. Commit: `feat(timer): add forgotten timer warning after 2 hours`

### Fase 3: Dossierwisseling afhandeling (30 min)

1. Pas de auto-start `useEffect` aan om bij dossierwisseling:
   - Vorige timer op te slaan (>60s) of te discarden (<60s)
   - Toast te tonen met opgeslagen tijd: "X:XX opgeslagen voor [dossiernaam]"
2. Test scenario's:
   - A → B (timer A saved, timer B starts)
   - A → dashboard → B (timer A loopt door, bij B: A saved, B starts)
   - A → A (dezelfde pagina herladen: timer loopt gewoon door)
3. `npm run build` — check
4. Commit: `feat(timer): auto-save on case switch with notification`

### Fase 4: Activity type selectie (30 min)

1. Voeg `activityType` toe aan `TimerState` interface (default: `"other"`)
2. Voeg activity type dropdown toe aan expanded floating timer panel
3. Pas `stopTimer` aan om `timer.activityType` te gebruiken i.p.v. hardcoded `"other"`
4. Persist activity type in localStorage met rest van timer state
5. `npm run build` — check
6. Commit: `feat(timer): add activity type selection to floating timer`

### Fase 5: Multi-tab sync (15 min)

1. Voeg `storage` event listener toe aan `useTimerProvider`
2. Bij storage change op `STORAGE_KEY`: update local state
3. Test: open twee tabs, start timer in tab 1 → tab 2 synchroniseert
4. `npm run build` — check
5. Commit: `feat(timer): sync timer state across browser tabs`

### Fase 6: Polish & edge cases (30 min)

1. Test alle scenario's:
   - Browser refresh terwijl timer loopt (WERKT AL via startedAt)
   - Meerdere tabs open (fase 5)
   - Uitloggen met lopende timer (waarschuwing tonen?)
   - Navigatie naar niet-dossier pagina's
2. Edge case: dossier verwijderd terwijl timer loopt → graceful handling
3. Animatie/transitie bij auto-start (subtiele pulse op floating timer)
4. Commit: `fix(timer): handle edge cases in auto-timer flow`

---

## 7. Risico-analyse

| Risico | Ernst | Mitigatie |
|--------|-------|-----------|
| **Vergeten timer** — Timer loopt uren door zonder dat Lisanne het merkt | Hoog | Waarschuwing na 2 uur (fase 2). Toast met action button. |
| **Kort dossierbezoek → ongewenste tijdregistratie** | Midden | 60-seconden drempel: bezoeken <1 min worden automatisch verworpen bij dossierwisseling |
| **Meerdere tabs** — Timer raakt in inconsistente state | Midden | localStorage `storage` event sync (fase 5). Eén timer wint altijd. |
| **Browser crash** — Lopende timer gaat verloren | Laag | **AL OPGELOST**: `startedAt` timestamp in localStorage, herberekening bij laden (regel 76-79 in `use-timer.ts`) |
| **Privacy** — Automatisch tracken zonder medeweten | Laag | Opt-in (standaard UIT). Duidelijke visuele feedback (groene pill). Toggle gemakkelijk bereikbaar. |
| **Onnauwkeurige tijd** — Auto-timer registreert tijd die niet aan werk besteed is | Midden | Review-mogelijkheid: entries verschijnen op de urenregistratie pagina en kunnen bewerkt worden. Plus: vergeten-timer-waarschuwing. |
| **stopTimer() is async** — Race condition bij snelle dossierwisseling | Midden | Debounce de auto-start effect, of wacht op stopTimer() completion voordat startTimer() wordt aangeroepen |
| **Uitloggen met lopende timer** — Timer data verloren | Laag | Bij uitloggen: waarschuwen als timer loopt. Optie: "Opslaan en uitloggen" of "Uitloggen zonder opslaan" |
| **Activity type verlies** — Altijd "other" bij auto-save | Laag | Default naar "other" is acceptabel. Gebruiker kan later aanpassen op urenregistratie pagina. Fase 4 voegt selectie toe. |

---

## 8. UX-beslissingen

### Opt-in vs. Opt-out

**Beslissing: Opt-in (standaard UIT)**

Redenen:
- Industrie-consensus: Smokeball, Harvest — allemaal opt-in
- Automatisch time tracking kan overweldigend zijn voor nieuwe gebruikers
- Lisanne moet bewust kiezen om deze modus te activeren
- Eerste gebruik: handmatige timer (vertrouwd) → later upgraden naar auto

### Visuele feedback bij auto-start

Wanneer de timer automatisch start bij het openen van een dossier:

1. Floating timer pill verschijnt rechtsonder (al bestaand gedrag)
2. Korte toast: "Timer gestart voor [dossiernaam]" (2 sec, niet-intrusief)
3. Groene pulsatie op de timer pill (al bestaand)

**Geen blocking dialog of pop-up** — dat zou het doel (minimale frictie) ondermijnen.

### Minimale frictie

| Actie | Huidige klikken | Met auto-timer |
|-------|----------------|----------------|
| Timer starten voor dossier | 2-3 (open dossier → Uren loggen) | 0 (automatisch bij openen) |
| Timer stoppen bij dossierwisseling | 3 (floating timer → stop → bevestig) | 0 (automatisch bij navigatie) |
| Timer stoppen bij klaar | 1-2 (floating timer → stop) | 1-2 (ongewijzigd) |

### Drempel voor opslaan

**Beslissing: 60 seconden minimum**

- < 60 seconden = automatisch verwijderen (waarschijnlijk "even kijken")
- ≥ 60 seconden = opslaan als time entry (afgerond naar dichtstbijzijnde minuut)
- Dit is configureerbaar gemaakt in de code voor toekomstige aanpassing

### Waar de toggle staat

**Beslissing: In de floating timer (expanded state)**

Redenen:
- Logische plek: de toggle hoort bij de timer
- Altijd bereikbaar (floating timer is op elke pagina)
- Niet in de instellingen-pagina verstoppen — te ver weg
- Instellingen-pagina is voor kantoor-brede settings, de timer-modus is persoonlijk

### Wat er NIET gebouwd wordt (bewust)

| Feature | Reden om NIET te bouwen |
|---------|------------------------|
| **Volledig passieve tracking (Smokeball-stijl)** | Vereist desktop app + OS-integratie. Niet haalbaar voor web-app. |
| **Idle detection met dialog (Harvest-stijl)** | Complex, vals positieven bij lezen/nadenken. Fase 2 na feedback. |
| **Server-side timer state** | Overkill voor 1 gebruiker op 1 apparaat. localStorage is voldoende. |
| **Meerdere gelijktijdige timers** | Clio en Harvest staan dit ook niet toe. Één timer is eenvoudiger. |
| **Automatisch stoppen bij inactiviteit** | Te agressief. Advocaten lezen en denken na — dat is ook werk. |

---

## 9. Samenvatting

**Kernprobleem:** De huidige timer is volledig handmatig. Lisanne moet bij elk dossier bewust de timer starten en stoppen. Dit leidt tot gemiste uren en extra klikken.

**Oplossing:** Opt-in auto-start modus die de timer automatisch start bij navigatie naar een dossierdetail pagina, met automatisch opslaan bij dossierwisseling en een vergeten-timer-waarschuwing.

**Benchmark:** Smokeball's AutoTime-principe (minimale gebruikersactie) + Harvest's safety nets (vergeten-timer-waarschuwing, idle detection als fase 2)

**Omvang:** Midden. Puur frontend — geen backend wijzigingen. 6 fasen, geschat 3-4 uur totaal.

**Geen backend deploy nodig.** Alleen frontend.

---

*Dit document is het onderzoek en plan voor E7. De implementatie volgt de standaard werkwijze: plan → bouw → check → commit.*
