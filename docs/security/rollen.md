# Rollen & autorisatie — Luxis

*Opgesteld S184 (8 juli 2026). Bron: `require_role(...)` in de routers + `get_current_user`.
Bijwerken zodra een route van rol-eis verandert.*

## Security-regels (HARD — audit S183)

Deze gelden ALTIJD, ook zonder dat de opdracht ze noemt. Horen ook in `CLAUDE.md` (die
sectie staat klaar maar wacht op het opschonen van eerdere niet-afgestemde CLAUDE.md-wijzigingen).

- **Nieuwe tabel met `tenant_id` → RLS in DEZELFDE migratie** via `apply_rls(op.get_bind())`
  (idempotent). Vergeet je het, dan blokkeert de opstartcontrole (`app.main.lifespan`, faalt
  dicht in productie) + de drift-guard-test
  (`tests/test_rls_isolation.py::test_drift_guard_flags_tenant_table_without_rls`) de deploy.
  `learned_answers` ontsnapte hier ooit aan (S183-1). Uitzondering: `users` (`app/security/rls.py`).
- **Nieuwe route → auth verplicht** (`Depends(get_current_user)` of `require_role(...)`),
  tenzij het echt publiek moet (login/OAuth) — dan expliciet + rate-limit.
- **Na een `db.commit()` binnen één request** worden tenant + rol automatisch her-toegepast
  (`after_begin`-event, S183-2) — vertrouw daar niet blind op, filter altijd óók op `tenant_id`.
- **Nooit secrets/sleutels in code** — alleen uit env (`app/config.py`); gebruikers-OAuth-tokens
  versleuteld; geen `NEXT_PUBLIC_*` met secrets (alle externe/AI-calls lopen server-side).
- **Uploads** alleen via de bestaande gevalideerde helpers (extensie-whitelist + grootte-cap
  + magic-byte-check).

Luxis kent **3 rollen** (`app/auth/schemas.py`, `ROLES`): `admin`, `advocaat`, `medewerker`.
Autorisatie is expliciet per route via FastAPI-dependencies — er is geen impliciete toegang.

## Basisregel

- **Elke ingelogde route** vereist `Depends(get_current_user)` → geldige JWT + actieve
  gebruiker + tenant-context (RLS). Zonder token → 401.
- **Alles is tenant-gescoped**: een gebruiker ziet/muteert alleen data van het eigen
  kantoor (afgedwongen door RLS + middleware). Geen enkele rol kan cross-tenant.
- **Publiek (geen login)**: alleen `/api/auth/login`, `/refresh`, `/forgot-password`,
  `/reset-password` (allemaal rate-limited) en de OAuth-callbacks (HMAC-state + nonce).

## Wat mag welke rol

| Resource / actie | admin | advocaat | medewerker |
|---|---|---|---|
| Zaken, relaties, betalingen, documenten genereren, e-mail, agenda, tijd, incasso-pijplijn, derdengelden, facturen | ✅ | ✅ | ✅ |
| Gebruikers aanmaken/beheren (`/auth/register`) | ✅ | ❌ | ❌ |
| Kantoorgegevens wijzigen (`/auth/tenant`) | ✅ | ❌ | ❌ |
| Instellingen (`/settings`) | ✅ | ❌ | ❌ |
| DOCX-sjablonen uploaden/wijzigen/verwijderen (`/documents/docx/templates`) | ✅ | ❌ | ❌ |
| Boekhoudkoppeling Exact Online verbinden/beheren (`/exact-online`) | ✅ | ❌ | ❌ |
| Workflow-inrichting: statussen/transities/regels (`/workflow` beheer) | ✅ | ❌ | ❌ |

**Kort:** `advocaat` en `medewerker` mogen al het dagelijkse dossierwerk; **inrichting en
beheer** (gebruikers, kantoor, instellingen, sjablonen, boekhoudkoppeling, workflow-config)
is **admin-only** (22 routes, `require_role("admin")`). Eén interne dependency staat
`admin` + `advocaat` toe als voorbeeld (`dependencies.py`), niet actief op een route.

## Bij een nieuwe route

1. Standaard: `Depends(get_current_user)`.
2. Beheer/inrichting die het hele kantoor raakt → `require_role("admin")`.
3. Moet het écht publiek? Dan expliciet + rate-limit + reden in de code.

Zie ook de security-sectie in `CLAUDE.md`.
