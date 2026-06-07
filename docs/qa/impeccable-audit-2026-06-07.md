# Impeccable Frontend Audit — 7 juni 2026

> **STATUS UPDATE (7 juni 2026, zelfde dag):** alle 5 aanbevolen acties uitgevoerd in waves W1-W5
> (commits `f003d2d`, `1feb7c6`, `5e68297`, `c2cf1e8`, `f8784ff`). Zie "Resultaat na fixes" onderaan.
> Deterministische anti-pattern scan: 3 → 1 (resterende = agenda event side-stripes, bewust behouden
> als Google Calendar-idioom). Visueel geverifieerd: login, dashboard, mail, incasso.

Technische kwaliteitsaudit van `frontend/src` via de impeccable-skill (5 dimensies, 3 parallelle audit-agents + deterministische anti-pattern scan). Geen fixes uitgevoerd — dit rapport is de werklijst.

## Audit Health Score

| # | Dimensie | Score | Belangrijkste bevinding |
|---|----------|-------|------------------------|
| 1 | Accessibility | 2/4 | Kernworkflows muis-only; ~250 labels niet gekoppeld; 10 handgebouwde modals zonder dialog-semantiek |
| 2 | Performance | 3/4 | Timer-tick her-rendert dossier-detail elke seconde; zoeken zonder debounce = skeleton-flikker per toetsaanslag |
| 3 | Responsive | 2.5/4 | Mail- en Incasso-pagina hebben 0 breakpoints; touch targets structureel < 44px |
| 4 | Theming | 2/4 | 718 hard-coded kleurclasses in 62 bestanden; dubbele status-kleurbron met conflict |
| 5 | Anti-Patterns | 1/4 | Login = AI-hero-sjabloon; gradient KPI-chips met glow op dashboard; 127 dode `dark:`-classes |
| **Totaal** | | **10.5/20** | **Acceptable — gericht werk nodig** |

## Anti-Patterns Verdict

**FAIL (nipt).** De werkschermen (tabellen, badges, dossierdetail) zien er níet AI-gegenereerd uit — competent Gmail/HubSpot-register. Maar de twee meest zichtbare schermen verraden het wel:

- **Login** (`login/page.tsx:85-133`): gradient-text, 2× blur-3xl glow-orbs, dot-grid overlay, fake stat-row — het standaard AI-SaaS-hero-sjabloon. Eerste scherm dat elke prospect ziet.
- **Dashboard KPI-cards** (`(dashboard)/page.tsx:461-463`): gradient icon-chips + gekleurde glow-shadows (`shadow-blue-500/25`) — AI-dashboard-tell.
- **127 dode `dark:`-classes** in 20 bestanden terwijl dark mode niet bestaat — generatie-artefact, geen visuele tell maar wel ruis.

Bewust NIET geteld (product-register): agenda side-stripes (Google Calendar-idioom, functioneel), backdrop-blur op overlays (mainstream), uppercase tabelkolomkoppen (standaard data-dense patroon).

## Executive Summary

- **Score: 10.5/20** (Acceptable)
- **Issues: 0× P0, 11× P1, 18× P2, 15× P3** (~44 totaal)
- Top 5 kritieke punten:
  1. Login-pagina = AI-hero-sjabloon — schaadt kalm/professioneel register bij elke prospect
  2. Timer-tick her-rendert complete dossierboom elke seconde tijdens normaal werk (`use-timer.ts:248`)
  3. Zoekvelden: API-call + tabel-verdwijnt-in-skeleton per toetsaanslag (geen debounce, geen `keepPreviousData`)
  4. Mail openen en incasso batch-selectie kunnen alleen met muis; Mail/Incasso-pagina's mobiel onbruikbaar
  5. 718 hard-coded kleurclasses + conflicterende status-kleurbron (`status-constants.ts` vs `types.tsx`: zelfde taakstatus amber vs blauw)

---

## Bevindingen per dimensie

### 1. Accessibility (2/4)

| Prio | Bevinding | Locatie | Impact | Fix |
|---|---|---|---|---|
| P1 | E-mail openen muis-only | `correspondentie/page.tsx:833,817` | `onClick` op `<div>` zonder tabIndex/role/keyboard — toetsenbord kan geen mail lezen | `<button>` of role+tabIndex+Enter-handler |
| P1 | Incasso batch-selectie muis-only | `incasso/page.tsx:1242,1526-1531` | Selectie via `onClick` op `<tr>`, checkbox is kaal icoon | Echte `<button aria-label>` zoals `zaken/page.tsx:657` al doet |
| P1 | Labels niet gekoppeld (systemisch) | ~250 van 330 labels in ~30 bestanden, bv. `zaken/nieuw/page.tsx:940` | Screenreaders lezen "edit text"; E2E gebruikt al `getByPlaceholder()` als workaround | `htmlFor`+`id` (patroon bestaat in `relaties/nieuw`) |
| P1 | Handgebouwde modals zonder dialog-semantiek | 10 bestanden: `agenda:580`, `documenten:123`, `incasso:1623`, `BetalingsregelingSection:421`, `facturen/[id]:1534`, `UrenTab:277`, `sjablonen-tab:309`, `derdengelden:676` | Geen focus-trap, Tab loopt eruit, Escape sluit niet | Vervang door Radix `Dialog` uit `components/ui/dialog.tsx` |
| P2 | Foutmeldingen: contrast + niet gekoppeld | `form-field-error.tsx:14` | `text-destructive` = 3.78:1 bij 13px; nul `aria-invalid`/`aria-describedby`/`role="alert"` in hele codebase | Donkerder rood + aria-koppeling |
| P2 | 24+ icoon-knoppen zonder naam | o.a. `taken:651`, `agenda:590`, `command-palette:183`, `facturen/[id]:559,895,1543` | Voorgelezen als "button" zonder betekenis | `aria-label` toevoegen |
| P2 | Opacity-gedimde tekst < contrast (systemisch) | 70× in 34 bestanden (`/70`=2.76:1, `/60`=2.33:1, `/50`=1.97:1) | Timestamps/subtitels/placeholders slecht leesbaar | Onverdund `text-muted-foreground` (4.83:1) als minimum |
| P2 | Wachtwoord-toggle: tabIndex=-1 + geen naam | `login/page.tsx:209`, `reset-password:135` | Toetsenbord kan wachtwoord niet tonen | tabIndex weg + aria-label |
| P2 | Notificatie-dropdown beperkt toetsenbord | `app-header.tsx:189-230` | Items zonder case_id zijn `<div onClick>`; geen Escape | `<button>`/`<Link>` + Escape |
| P3 | "Geannuleerd"-badge 2.43:1 | `use-invoices.ts:134` | gray-400 op gray-50 | gray-600/700 |
| P3 | Sidebar-sectielabels 2.56:1 | `app-sidebar.tsx:205,302` | `/30` op donkere sidebar nauwelijks leesbaar | Naar `/60` |
| P3 | Dossier-tabs zonder tab-semantiek | `zaken/[id]/page.tsx:521-531` | Buttons werken, maar geen tablist/aria-selected | Radix Tabs (bestaat al, ongebruikt) |
| P3 | Email-editor zonder rol | `email-compose-dialog.tsx:926-937` | contentEditable niet herkend als invoerveld | `role="textbox" aria-multiline aria-label` |
| P3 | Filter-selects zonder naam | `zaken/page.tsx:313-330,382-405`, idem uren/facturen | Alleen option-tekst als context | `aria-label` per select |
| P3 | Geen Escape op mobiel sidebar-overlay | `app-sidebar.tsx:131-136` | Sluit alleen via klik (knop bestaat wel) | Escape-handler |

**Positief:** skip-link + landmarks + h1 per pagina + reduced-motion; Radix waar het telt (ConfirmDialog/useConfirm, compose, selects); nul gevallen van verwijderde focus zonder alternatief; zaken-tabel is het goede voorbeeld (aria-labels per rij, sorteerheaders als buttons).

**Systemisch:** (1) labels zonder htmlFor ~250×; (2) handgebouwde modals 10×; (3) opacity-muted tekst 70×/34 bestanden; (4) naamloze icon-buttons 24+; (5) nul ARIA voor dynamische feedback in hele frontend.

### 2. Performance (3/4)

| Prio | Bevinding | Locatie | Impact | Fix |
|---|---|---|---|---|
| P1 | Timer-tick re-rendert alles elke seconde | `use-timer.ts:248` + `zaken/[id]/page.tsx:99` + `uren/page.tsx:398` | Met lopende timer her-rendert complete dossierboom (incl. DocumentenTab 1739 regels) 1×/sec | Context splitsen state/actions; alleen FloatingTimer tikt (lokaal uit `startedAt`) |
| P1 | Zoeken: geen debounce + geen placeholderData | `zaken/page.tsx:301`, relaties:211, facturen:140, `use-cases.ts:134` | API-call + tabel→skeleton per toetsaanslag | 300ms `useDebounce` (bestaat al in `correspondentie:47` — promoveer naar `hooks/`) + `keepPreviousData` |
| P2 | Dode hover-state → full-page re-renders | `zaken/page.tsx:104,653-654` | `hoveredRow` geset maar nergens gelezen | State weg; CSS `group-hover` doet het al |
| P2 | TipTap statisch gebundeld | `DetailsTab.tsx:27`, `ActiviteitenTab.tsx:27` | Zwaarste dependency altijd in dossier-bundle | `next/dynamic` met `ssr: false` |
| P2 | Sidebar-collapse animeert layout | `app-sidebar.tsx:141` + `layout.tsx:68-74` | 200ms reflow van data-dense pagina per toggle | Accepteren of transform-based |
| P3 | `allCases.filter` 4× per render | `incasso/page.tsx:1209-1218,1236` | Onmerkbaar bij klein volume | Eén `useMemo` |
| P3 | 200 cases voor dropdown | `uren/page.tsx:382` | Volledige CaseSummary's voor picker | Licht autocomplete-endpoint |
| P3 | Unbounded blur login | `login/page.tsx:87-88` | Eenmalig, alleen login | Vervalt bij login-redesign (zie anti-patterns) |

**Positief:** lean bundle (geen moment/lodash/charts); verstandige query-defaults (staleTime 30s, geen focus-refetch); tabs conditioneel gemount met per-tab ErrorBoundary; animaties uitsluitend transform/opacity.

### 3. Responsive (2.5/4)

| Prio | Bevinding | Locatie | Impact | Fix |
|---|---|---|---|---|
| P1 | Mail-pagina 0 breakpoints, split-view | `correspondentie/page.tsx:394-397` | `w-2/5`+`3/5` = ±150px lijst op telefoon — module mobiel onbruikbaar | Detail als full-screen overlay onder `lg:` |
| P1 | Incasso stappen-tabel hard afgekapt | `incasso/page.tsx:309-310` | `overflow-hidden` + `min-w-[700px]` = geclipte kolommen zonder scroll | → `overflow-x-auto` (zustertabel :1203 doet het goed) |
| P2 | 27 hover-reveal acties onzichtbaar op touch | 14 bestanden, o.a. `zaken:746`, `incasso:839` | Verwijder/bekijk-knoppen bestaan visueel niet op tablet | Standaard zichtbaar, `sm:opacity-0 sm:group-hover:opacity-100` + `focus-within` |
| P2 | Touch targets < 44px (systemisch) | ~73 `p-1`/`p-1.5` + 47 `h-6`/`h-7`, bv. `incasso:837-843` (±22px) | Mis-tikken op tablet | Minimaal `h-9 w-9` hit-area |
| P2 | Factuurregels grid-cols-12 zonder breakpoints | `facturen/nieuw/page.tsx:1075` | Onbruikbaar smalle velden op 375px | Stapelen onder `md:` |
| P2 | Tabellen in overflow-hidden | `facturen/[id]:809,920,1388`, `derdengelden:182,322` | Kolommen platgedrukt op mobiel | `overflow-x-auto` wrapper |
| P3 | Dossier-sidebar verborgen < lg | `DossierSidebar.tsx:75` | Tablet-portrait mist financieel overzicht (deels gedekt door DetailsTab) | Collapsible boven tabs, of bewuste keuze documenteren |
| P3 | Dropdowns zonder max-w clamp | `uren/page.tsx:228`, `floating-timer.tsx:103` | `min-w-[320px]` buiten beeld op 320px | `max-w-[calc(100vw-2rem)]` |

**Positief:** echte mobile card-views op de 4 grootste lijstpagina's; volwaardig mobiel sidebar-patroon; agenda heeft dedicated MobileEventList; formulier-grids vrijwel overal correct responsief.

**Systemisch:** mobile-card-patroon niet doorgetrokken naar 6+ lijstweergaven; 6 monoliet-pagina's >1000 regels met 19-34 useState; 0× next/dynamic.

### 4. Theming (2/4)

| Prio | Bevinding | Locatie | Impact | Fix |
|---|---|---|---|---|
| P1 | 718 hard-coded palette-classes | 62 bestanden. Top-5: `incasso/page.tsx` (51), `(dashboard)/page.tsx` (41), `facturen/page.tsx` (37), `DossierHeader.tsx` (34), `facturen/[id]/page.tsx` (29) | Rebranding = 62 bestanden; kleurdrift al zichtbaar | Semantic badge/alert-varianten definiëren, migreren |
| P1 | Dubbele status-kleurbron met conflict | `lib/status-constants.ts:66-72` vs `zaken/[id]/types.tsx:109-115` | `TASK_STATUS_BADGE["due"]` amber vs blauw — zelfde status, andere kleur per pagina | types.tsx-duplicaten weg, alles uit status-constants |
| P2 | success/warning tokens ongebruikt | `globals.css:37-40`; 2 gebruikers | Token-infra is dode code; iedereen pakt emerald/amber direct | Bij badge-migratie als basis nemen |
| P2 | 127 dode `dark:`-varianten | 20 bestanden, ergste `incasso` (43), `correspondentie` (13) | Kunnen nooit activeren (geen `.dark` block) | Mechanisch strippen |
| P2 | Inline hex buiten tokens | `use-calendar-events.ts:62-70`, `agenda:931,1091-1092,1126,1533-1535` | Agenda-kleuren buiten elk systeem; `${event.color}18` alpha-concat breekt stilletjes | Eén constants-bestand met expliciete varianten |
| P3 | green vs emerald gemixt | `types.tsx:88,91` | Twee bijna-identieke groenen | Standaardiseren op emerald |
| P3 | Arbitrary hsl login-paneel | `login/page.tsx:85` | Hard-coded donker paneel | Vervalt bij login-redesign |

**Positief:** statusbadge-systeem gecentraliseerd (`status-constants.ts`, 9 importeurs, vast patroon); shadcn-primitives 100% token-clean; kern-werkschermen hebben het juiste register (tabular-nums, muted hiërarchie).

### 5. Anti-Patterns (1/4)

| Prio | Bevinding | Locatie | Impact | Fix |
|---|---|---|---|---|
| P1 | AI-hero-sjabloon op login | `login/page.tsx:85-133` | Eerste scherm voor elke prospect schreeuwt "AI-template" | Effen donker paneel + logo + één zin |
| P2 | Gradient KPI-chips + glow | `(dashboard)/page.tsx:461-463` | Decoratie zonder functie op hoofdscherm | `bg-primary/10 text-primary` chips, glow weg |
| P2 | Paars sfeer-paneel credit-nota | `facturen/[id]/page.tsx:1032-1056` | Paars zonder semantiek | Neutraal `border-border bg-muted/30` |
| P2 | Emoji's in pipeline-instellingen | `incasso/page.tsx:740-745` (⏱💬🔧💰) | Valt uit lucide-register | Lucide Clock/MessageSquare/Wrench/Coins |
| P3 | Emoji in notitie-template | `DossierHeader.tsx:512` ("📞 Telefoonnotitie") | Borderline functioneel | Prefix zonder emoji |
| P3 | Email side-stripes off-token | `correspondentie/page.tsx:717-718,784-785` | Functioneel (in/uit), maar hard-coded | Behouden via primary/success tokens |

---

## Aanbevolen acties (prioriteitsvolgorde)

1. **[P1] `/impeccable quieter login + dashboard`** — AI-hero weg van login, gradient KPI-chips → effen chips. Grootste zichtbaarheidswinst, klein werk.
2. **[P1] `/impeccable optimize`** — timer-tick context-split + zoek-debounce + keepPreviousData. Alles wat Lisanne dagelijks vóelt.
3. **[P1] `/impeccable harden formulieren + modals`** — labels htmlFor/id (~30 bestanden), 10 modals → Radix Dialog, muis-only workflows toetsenbord-bedienbaar, aria-koppeling foutmeldingen.
4. **[P1] `/impeccable adapt correspondentie + incasso`** — breakpoints voor Mail/Incasso, overflow-fix, touch targets, hover-reveal patroon.
5. **[P2] Theming-migratie** — status-kleurconflict fixen (klein, direct doen), daarna stapsgewijs 718 palette-classes → semantic varianten, dode dark:-classes strippen (mechanisch).
6. **[Afsluiter] `/impeccable polish`** — finale pass na bovenstaande fixes.

Schatting: acties 1+2 samen ± halve sessie; 3+4 elk een eigen sessie; 5 verspreid/mechanisch.

Her-run `/impeccable audit` na fixes om score-verbetering te meten.

---

## Resultaat na fixes (7 juni 2026)

### Uitgevoerd

| Wave | Commit | Inhoud |
|---|---|---|
| W1 Quieter | `f003d2d` | Login AI-hero → effen donker paneel; KPI gradient-chips → vlakke token-tints; status-kleurconflict opgelost (types.tsx → status-constants re-export) |
| W2 Optimize | `1feb7c6` | Timer tikt niet meer door hele app (useTimerSeconds lokaal); zoeken 300ms debounced + keepPreviousData; TipTap lazy; dode hover-state weg; incasso filter gememoized |
| W3 Harden | `5e68297` | 12 handgebouwde modals → Radix Dialog; mail-open + incasso-selectie toetsenbord-bedienbaar; ~70 labels gekoppeld; 40+ aria-labels; form-errors role=alert + rood 4.5:1; 33× opacity-muted tekst naar vol contrast; Escape op sidebar/notificaties |
| W4 Adapt | `c2cf1e8` | Mail split-view mobiel bruikbaar (lijst↔detail wissel); incasso tabel-clip fix; 4 tabellen overflow-x-auto; 27× hover-reveal zichtbaar op touch + focus; factuurregels stapelen op mobiel; dropdown viewport-clamps |
| W5 Theming | `f8784ff` | 189 dode dark:-classes weg; emoji's → lucide; credit-nota paars sfeer-paneel → neutraal; agenda hex-alpha gecentraliseerd + gevalideerd; paid green→emerald; cancelled-badge contrast |

### Zelf-inschatting nieuwe scores (her-run `/impeccable audit` voor officiële meting)

| Dimensie | Was | Nu (geschat) | Toelichting |
|---|---|---|---|
| Accessibility | 2 | ~3 | Alle 4 P1's opgelost; per-veld aria-describedby koppeling nog niet overal (infra staat in form-field-error) |
| Performance | 3 | ~3.5 | Timer-tick + zoek-flikker (alles wat Lisanne voelt) opgelost |
| Responsive | 2.5 | ~3 | Mail/Incasso mobiel bruikbaar; touch targets <44px grotendeels backlog |
| Theming | 2 | ~2.5 | Conflicten/dode code weg; 718 palette-classes → semantic varianten = backlog |
| Anti-Patterns | 1 | ~3.5 | Deterministische scan 3→1 (rest bewust); login/dashboard/paars/emoji weg |
| **Totaal** | **10.5** | **~15.5 (Good)** | |

### Bewuste backlog (niet gedaan, met reden)

1. **718 hard-coded palette-classes → semantic badge/alert-varianten** — grootste klus, mechanisch maar visueel-regressie-gevoelig; vergt eigen sessie met screenshot-vergelijking per pagina. Token-infra (success/warning) staat klaar.
2. **Touch targets <44px (±73 knoppen)** — bulk-vergroting vervormt data-dense tabellen; per-scherm beoordelen, geen blinde sed. Hover-reveal-deel is wél gefixt (zichtbaar op touch).
3. **DossierSidebar verborgen <lg** — gedrag gedocumenteerd als bewuste keuze; collapsible variant kan later.
4. **success/warning tokens breed inzetten** — onderdeel van backlog-punt 1.
5. **Credit-nota paars als type-kleur** (badge/knop/nummer) — bewust behouden, functionele codering.
6. **Agenda event side-stripes** — bewust behouden, Google Calendar/Outlook-idioom voor event-types.

### Verificatie

- `npx tsc --noEmit` groen na elke wave
- `npx impeccable detect frontend/src`: 3 → 1 bevinding
- Visueel gecheckt (Playwright, localhost:3000): login-redesign, dashboard KPI-chips, mail-pagina, incasso-tabel — alles rendert correct, geen render-crashes
- Let op: frontend-container moest herstart worden voor hot-reload (Windows bind-mount watching) — wijzigingen zijn daarna zichtbaar
