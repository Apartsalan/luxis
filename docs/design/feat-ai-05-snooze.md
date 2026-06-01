# FEAT-AI-05 — Snooze op CaseActionFeed-kaarten (ontwerp, S148)

> Status: 📋 Ontwerp (S147). Geen code — uitvoering gepland S148.
> Doel: Lisanne kan een kaart in "Wat moet u doen?" tijdelijk wegklikken
> ("herinner me later") i.p.v. definitief afhandelen (`is_read`).

## Probleem

Vandaag heeft een feed-kaart twee toestanden: **wachtend** (`is_read=false`) of
**afgehandeld** (`is_read=true`, via de X / dismiss). Er is geen tussenvorm. Een
deadline die Lisanne "volgende week pas" wil oppakken moet ze óf laten staan
(blijft schreeuwen) óf wegklikken (verdwijnt uit "Wachtend", voelt als afgehandeld).
Snooze vult dat gat: kaart verdwijnt tijdelijk en komt vanzelf terug.

## DB-schema

Eén nullable kolom op `notifications`:

| Kolom | Type | Null | Default | Betekenis |
|---|---|---|---|---|
| `snoozed_until` | `TIMESTAMP WITH TIME ZONE` | ja | `NULL` | Verberg de kaart tot dit moment. `NULL` = niet gesnoozed. |

- `NULL` is de normale staat → geen backfill nodig, bestaande records blijven werken.
- Geen aparte `is_snoozed` bool: `snoozed_until > now()` is de enige bron van waarheid
  (voorkomt twee velden die uit sync raken — zelfde les als `task_id`-dedup, S146).
- Index uitbreiden voor de wachtend-query:
  `ix_notifications_user_unread (tenant_id, user_id, is_read, created_at)` →
  overweeg partial index of extra kolom `snoozed_until` toevoegen aan de index,
  alleen als de feed-query traag wordt (nu max 50 rows per user — waarschijnlijk niet nodig).

**Migratie:** puur additief (nieuwe nullable kolom) → `alembic revision --autogenerate`.
Geen risico op bestaande data.

## Backend

1. **Model** (`notifications/models.py`): kolom `snoozed_until: Mapped[datetime | None]`.
2. **Schema** (`notifications/schemas.py`): veld toevoegen aan `NotificationResponse`.
3. **Endpoint** — nieuw: `PUT /api/notifications/{id}/snooze` met body `{"hours": 24 | 72 | 168}`.
   Server berekent `snoozed_until = now() + interval` (server-side tijd, niet client —
   voorkomt klok-skew). Endpoint zet ook `is_read=false` (snoozen ≠ afhandelen).
   - Whitelist de toegestane intervallen server-side (24/72/168u) → geen vrije input.
4. **Unsnooze** — `PUT /api/notifications/{id}/snooze` met `{"hours": 0}` of aparte
   `DELETE .../snooze` zet `snoozed_until = NULL` (kaart komt direct terug).
5. **Lijst-endpoint** (`GET /api/notifications`): GEEN server-side filtering op snooze.
   De feed-hook filtert client-side (zie hieronder) zodat de bell-badge en de feed
   dezelfde dataset delen. (Alternatief — server-side filteren — overwegen als de
   notificatielijst ooit groot wordt; nu niet.)

## Frontend

1. **Type** (`use-notifications.ts`): `snoozed_until: string | null` op `Notification`.
2. **Hook** (`use-case-action-feed.ts`): in de `useMemo`-filter, bij filter
   `"wachtend"` ook uitsluiten wat gesnoozed is:
   ```ts
   const now = Date.now();
   // wachtend = niet gelezen, een actie-type, en niet (nog) gesnoozed
   filtered.filter(n =>
     !n.is_read &&
     WAITING_TYPES.has(n.type) &&
     !(n.snoozed_until && new Date(n.snoozed_until).getTime() > now)
   )
   ```
   - 30s-polling pikt het terugkomen vanzelf op (geen timer nodig in de UI).
   - Filter `"alles"` blijft alles tonen (ook gesnoozede) met een "Sluimert tot …"-label.
3. **UI** (`CaseActionFeed.tsx`, `CardShell`): naast de X-knop een klein dropdown-menu
   (klok-icoon) met "Snooze 24 uur / 3 dagen / 1 week". Mutatie `useSnoozeFeedItem(id, hours)`
   → invalidate `["notifications"]`. Optioneel klein label op gesnoozede kaart in "Alles".
4. **Mutatie-hook**: `useSnoozeFeedItem` analoog aan `useDismissFeedItem`.

## Pre-mortem — 3 faalredenen

1. **Tijdzone / klok-skew** — client berekent `snoozed_until` lokaal en stuurt timestamp →
   bij verkeerde tijdzone komt een kaart te vroeg/laat terug, of "Sluimert tot"-label klopt niet.
   *Mitigatie:* server berekent `now() + interval` met `TIMESTAMPTZ`; client stuurt alleen
   het aantal uren (whitelist 24/72/168). Frontend toont tijd altijd via bestaande
   `formatNotificationTime`-helper (tz-aware). → Toch juiste aanpak: één bron van tijd (server).

2. **Gesnoozede kaart raakt onbereikbaar** — Lisanne snoozet per ongeluk 1 week en kan
   'm niet terughalen → voelt als dataverlies, ondermijnt vertrouwen in de feed.
   *Mitigatie:* gesnoozede kaarten blijven zichtbaar onder filter "Alles" met "Sluimert tot …"
   + een "Nu tonen"-actie (unsnooze). Snooze is nooit destructief (`is_read` blijft false).
   → Toch juiste aanpak: snooze is reversibel by design, sluit aan op bestaande 3-filter-UX.

3. **Scope-creep naar per-type snooze-regels** — verleiding om deadline-kaarten
   andere snooze-opties te geven dan draft-kaarten, of "snooze tot betaaldatum" enz. →
   complexiteit explodeert, levert weinig op voor 1 gebruiker.
   *Mitigatie:* S148 levert exact 3 vaste intervallen voor álle kaart-types, geen
   type-specifieke logica. → Toch juiste aanpak: kleinste nuttige stap; uitbreiden alleen
   na bewezen gebruik (zelfde principe als CaseActionFeed zelf — eerst simpel, dan meten).

## Niet in scope (S148)

- Geen e-mail/push-reminder bij terugkomst (alleen in-app).
- Geen "snooze tot specifieke datum/tijd"-picker (alleen 24u/3d/1w).
- Geen snooze op de header-bell (alleen op CaseActionFeed-kaarten).
