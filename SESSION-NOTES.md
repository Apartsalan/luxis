# Sessie Notities — Luxis

**Laatst bijgewerkt:** 27 feb 2026 (sessie 22 — volledige QA secties 1-10)
**Laatste feature/fix:** QA sessie 22 — 75/75 tests PASS, 0 nieuwe bugs, 5 bugfixes geverifieerd
**Volgende sessie (23):** Fix BUG-25/26/27 (uit sessie 21A/21B), dan verder bouwen (Incasso Workflow Automatisering P1).

## Wat er gedaan is (sessie 22 — 27 feb)

### Volledige QA Testing secties 1-10 via Playwright MCP ✅
- **75 tests uitgevoerd, 75 PASS, 0 FAIL, 0 nieuwe bugs**
- Geteste secties: Login, Dashboard, Relaties, Dossiers (lijst + nieuw + detail), Mijn Taken, Correspondentie, Incasso (werkstroom + stappen), Uren, Facturen, Documenten
- Resultaten: `docs/qa/QA-SESSIE-22-RESULTATEN.md`

### Geverifieerde bugfixes
- BUG-17 (velden leegmaken) ✅ — null waarden correct opgeslagen
- BUG-18 (taak navigatie) ✅ — taken zijn klikbare links
- BUG-22 (invoice 500 error) ✅ — factuur detail laadt correct
- BUG-23 (/notifications 404) ✅ — geen console errors
- BUG-24 (/api/users 404) ✅ — geen console errors

### Openstaande bugs (uit sessie 21A/21B)

| # | Bug | Ernst | Status |
|---|-----|-------|--------|
| BUG-25 | Timer FAB z-index overlap | Low | ❌ TODO |
| BUG-26 | Relaties laden niet in agenda event formulier (`/api/relations` 404) | Medium | ❌ TODO |
| BUG-27 | 404 pagina in het Engels zonder navigatie | Low | ❌ TODO |

### Bestanden gewijzigd sessie 22

**Nieuw (docs):**
- `docs/qa/QA-SESSIE-22-RESULTATEN.md` — volledige QA resultaten

### Status na sessie 22
- Secties 1-10: volledig getest, alles PASS
- Secties 11-14: getest in sessie 21A/21B (BUG-25/26/27 gevonden)
- Applicatie is stabiel, alle eerdere bugfixes werken op productie

---

## Wat er gedaan is (sessie 20 — 25 feb)

### QA Testing via Playwright MCP ✅
- Volledige QA van 14 secties uit QA-CHECKLIST.md via browser automation
- Geverifieerd: BUG-18 (taak links → dossier ✅), BUG-21 (advocaat wederpartij zichtbaar ✅)
- 3 nieuwe bugs gevonden: BUG-22, BUG-23, BUG-24

### BUG-22: Invoice detail 500 Internal Server Error ✅
- **Probleem:** `GET /api/invoices/{id}` gaf 500 error
- **Oorzaak:** Circulaire `lazy="selectin"` op Invoice self-referential relationships (`credit_notes` en `linked_invoice`). Invoice → credit_notes → linked_invoice → Invoice → ... (oneindige loop)
- **Fix:** `lazy="selectin"` → `lazy="noload"` op beide relaties + explicit `selectinload()` in `get_invoice()` en `list_invoices()`
- **Bestanden:** `backend/app/invoices/models.py`, `backend/app/invoices/service.py`

### BUG-23: /notifications endpoints 404 ✅
- **Probleem:** Frontend riep `/notifications` en `/notifications/unread-count` aan op elke pagina maar backend had geen notification module
- **Drie sub-issues gefixt:**
  1. Stub router aangemaakt (`backend/app/notifications/router.py`) met lege responses
  2. Import path fout: `from app.auth.dependencies` → `from app.dependencies` (veroorzaakte ImportError → backend crash)
  3. Frontend API prefix mismatch: `/notifications/...` → `/api/notifications/...` (Next.js proxy matcht alleen `/api/*`)
- **Bestanden:** `backend/app/notifications/__init__.py` (nieuw), `backend/app/notifications/router.py` (nieuw), `frontend/src/hooks/use-notifications.ts`, `backend/app/main.py`

### BUG-24: /api/users endpoint 404 ✅
- **Probleem:** Frontend riep `/api/users` aan voor dossierlijst filters maar endpoint bestond niet
- **Fix:** `users_router` toegevoegd in `backend/app/auth/router.py` met `/api/users` prefix, lijst alle users in tenant
- **Bestanden:** `backend/app/auth/router.py`, `backend/app/main.py`

### Deploy issues opgelost
- **`.env` ontbrak op VPS** — Docker Compose leest standaard `.env`, niet `.env.production`. Fix: `cp .env.production .env`
- **502 errors na deploy** — Backend crashte door ImportError in notifications router (verkeerd import pad)
- **Login credentials** — productiedatabase heeft user `seidony@kestinglegal.nl`, niet `arsalan@kestinglegal.nl`

### Bestanden gewijzigd sessie 20

**Nieuw (backend):**
- `backend/app/notifications/__init__.py` — leeg init bestand
- `backend/app/notifications/router.py` — stub notification router (4 endpoints)

**Gewijzigd (backend):**
- `backend/app/invoices/models.py` — `lazy="selectin"` → `lazy="noload"` op linked_invoice en credit_notes
- `backend/app/invoices/service.py` — explicit `selectinload()` in get_invoice en list_invoices
- `backend/app/auth/router.py` — `users_router` met `/api/users` prefix
- `backend/app/main.py` — notifications_router en users_router geregistreerd

**Gewijzigd (frontend):**
- `frontend/src/hooks/use-notifications.ts` — `/notifications/...` → `/api/notifications/...` (4 API calls)

### Commits sessie 20

| Hash | Beschrijving |
|------|-------------|
| `b955cbc` | fix: invoice circular loading, add notifications stub router, add users endpoint |
| `941aaad` | fix: correct import path and API prefix in notifications router |
| `08142dc` | fix: add /api/ prefix to notification API calls in frontend |

### Status na sessie 20
- Code gecommit en gepusht
- Backend opnieuw gedeployed ✅
- Frontend nog NIET opnieuw gebouwd/gedeployed (notification prefix fix in frontend)
- **Nog te doen:** Frontend rebuilden en deployen, dan BUG-22/23/24 verifiëren op productie

---

## Wat er gedaan is (sessie 19 — 25 feb)

### Feature: Inline advocaat wederpartij aanmaken bij nieuw dossier ✅
- **Probleem:** Advocaat wederpartij kon alleen gelinkt worden als de persoon al als relatie bestond. Geen inline aanmaak-optie.
- **Fix:** "+ Nieuwe advocaat aanmaken" knop toegevoegd aan Advocaat wederpartij sectie op nieuw dossier formulier.
  - State: `showNewLawyer`, `newLawyer` (default `contact_type: "person"`)
  - Extended `handleCreateInlineContact` voor `"lawyer"` role
  - Violet-themed inline form (naam + email)
- **Commit:** `0fd7899`

### Feature: Auto ContactLink tussen advocaat en wederpartij (bedrijf) ✅
- **Probleem:** Na aanmaken dossier met advocaat wederpartij en wederpartij (bedrijf) werd geen koppeling aangemaakt. Op de relatiepagina van de advocaat waren geen bedrijven zichtbaar.
- **Fix:** In `handleSubmit`, na toevoegen advocaat als CaseParty, auto-create ContactLink (person_id=advocaat, company_id=wederpartij, role="Advocaat"). Non-blocking: 409 bij bestaande link wordt genegeerd.
- **Bestand:** `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx`
- **Commit:** `1fdb663`

### Fix: Zaken niet zichtbaar op relatiepagina voor CaseParty-contacten ✅
- **Probleem:** Op de relatiepagina van een advocaat wederpartij waren dossiers niet zichtbaar, ondanks dat de advocaat als CaseParty was toegevoegd.
- **Root cause (2 lagen):**
  1. **Backend** `list_cases` service: `client_id` filter zocht alleen in `Case.client_id` en `Case.opposing_party_id` — NIET in `CaseParty.contact_id`
  2. **Frontend** relatiepagina: extra client-side filter `c.client?.id === id || c.opposing_party?.id === id` sloot CaseParty-matches uit
- **Fix backend (`cases/service.py`):** `Case.parties.any(CaseParty.contact_id == client_id)` toegevoegd aan de OR-clause
- **Fix frontend (`relaties/[id]/page.tsx`):** Strikte filter verwijderd (backend filtert al correct). Rol-label "Partij" in violet badge toegevoegd voor non-client/non-opposing-party contacten.
- **Commit:** `f469f65`

### Bestanden gewijzigd sessie 19
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — inline advocaat aanmaken + auto ContactLink + opponentContactType tracking
- `backend/app/cases/service.py` — CaseParty filter in list_cases
- `frontend/src/app/(dashboard)/relaties/[id]/page.tsx` — filter verwijderd + "Partij" rol label

---

## Wat er gedaan is (sessie 18 — 25 feb)

### BUG-18: Taak klik navigeert niet naar dossier ✅
- **Probleem:** In dashboard "Mijn Taken" widget en op `/taken` pagina, klik op taak navigeerde niet naar dossier.
- **Oorzaak:** Taak-titel was een `<p>` element zonder link.
- **Fix:** `<p>` vervangen door `<Link href={/zaken/${task.case_id}}>` in zowel `page.tsx` (dashboard widget) als `taken/page.tsx`.

### BUG-19: Factuur aanmaken → "fout bij laden" ✅
- **Probleem:** Na aanmaken van factuur, redirect naar detailpagina toonde "Fout bij laden van gegevens".
- **Oorzaak:** Race condition: `get_db` dependency commit na response verzonden. Snel client-side navigatie kon GET sturen voordat transactie gecommit was.
- **Fix backend:** Explicit `await db.commit()` + `await db.refresh(invoice)` in `create_invoice` route handler.
- **Fix frontend:** `setQueryData` in `useCreateInvoice` onSuccess om React Query cache te pre-populaten met POST response data.

### BUG-20: Budget module onbekend ✅
- **Probleem:** Bij instellingen → modules → "budget" aanzetten gaf foutmelding.
- **Oorzaak:** `VALID_MODULES` in `backend/app/settings/schemas.py` miste `"budget"`.
- **Fix:** `"budget"` toegevoegd aan de tuple.

### BUG-21: Advocaat wederpartij + budget niet zichtbaar na aanmaken dossier ✅
- **Probleem:** Na aanmaken dossier: advocaat wederpartij niet zichtbaar (ook niet na bewerken), budget niet opgeslagen.
- **Eerste poging:** Explicit `db.commit()` in router handlers — werkte niet, probleem bleef bestaan.
- **Echte oorzaken (2):**
  1. `create_case` service miste `budget`, `court_case_number`, `court_name`, `judge_name`, `chamber`, `procedure_type`, `procedure_phase`, `billing_contact_id` in de Case constructor — velden werden geaccepteerd door schema maar nooit doorgezet naar de database.
  2. `get_case` en `add_case_party` hadden geen explicit `selectinload` voor nested `Case.parties → CaseParty.contact` relatie. In async SQLAlchemy wordt nested `lazy="selectin"` niet automatisch geketend — de contact data was dus altijd `null` in de JSON response.
- **Fix backend:**
  - Alle ontbrekende velden toegevoegd aan Case constructor in `create_case`
  - `selectinload(Case.parties).selectinload(CaseParty.contact)` toegevoegd aan `get_case` query
  - `add_case_party`: `db.refresh(party)` vervangen door re-query met explicit `selectinload(CaseParty.contact)`

### Bestanden gewijzigd sessie 18
- `backend/app/settings/schemas.py` — "budget" toegevoegd aan VALID_MODULES
- `backend/app/invoices/router.py` — explicit commit in create_invoice
- `backend/app/cases/router.py` — explicit commit in create_case en add_party
- `backend/app/cases/service.py` — missing fields in create_case + selectinload in get_case + add_case_party
- `frontend/src/app/(dashboard)/page.tsx` — taak-titel als Link in dashboard widget
- `frontend/src/app/(dashboard)/taken/page.tsx` — taak-titel als Link in Mijn Taken
- `frontend/src/hooks/use-invoices.ts` — setQueryData in useCreateInvoice onSuccess

---

## Wat er gedaan is (sessie 17 — 25 feb)

### BUG-15: Reset-password — DEPLOYED + GETEST ✅
- Frontend container opnieuw gebouwd op VPS met Next.js rewrite proxy
- Password reset flow getest: login → wachtwoord vergeten → email → link → nieuw wachtwoord → werkt ✅

### BUG-16: Dashboard "Mijn Taken" widget toonde geen taken ✅
- **Oorzaak:** `useMyOpenTasks` gebruikte `/api/workflow/tasks?status=due` — toonde alleen taken met status "due". Taken met status "pending" of "overdue" waren onzichtbaar.
- **Fix:** Endpoint gewijzigd naar `/api/dashboard/my-tasks` (zelfde als Mijn Taken pagina) — toont nu alle open taken.
- **Bestand:** `frontend/src/hooks/use-workflow.ts`

### BUG-17: Velden leegmaken + opslaan werkte niet (site-breed) ✅
- **Oorzaak:** `|| undefined` in form handlers → JSON.stringify dropt de key → backend `exclude_unset=True` slaat update over. Velden met lege waarde behielden hun oude inhoud.
- **Fix:** `|| undefined` → `|| null` in alle form handlers. Null wordt wél meegestuurd in JSON.
- **Scope:** 51 instances in 18 bestanden: relaties (31 velden), facturen (7), uren (2), agenda (4), email compose (4), timer (1), incasso (1), contact links (1)
- **Interfaces ook bijgewerkt:** `string | null` i.p.v. `string | undefined` voor nullable velden

### CLAUDE.md bijgewerkt
- Nieuwe sectie "Kwaliteitsstandaard" toegevoegd: verificatie voor done, autonoom bugfixen, elegantie gebalanceerd, self-improvement, simplicity first.

### Bestanden gewijzigd sessie 17
**Gewijzigd (frontend):**
- `frontend/src/hooks/use-workflow.ts` — useMyOpenTasks endpoint fix
- `frontend/src/hooks/use-relations.ts` — `|| undefined` → `|| null` (31 velden)
- `frontend/src/hooks/use-invoices.ts` — `|| undefined` → `|| null` (7 velden)
- `frontend/src/hooks/use-time-entries.ts` — `|| undefined` → `|| null` (2 velden)
- `frontend/src/hooks/use-calendar.ts` — `|| undefined` → `|| null` (4 velden)
- `frontend/src/hooks/use-email-sync.ts` — `|| undefined` → `|| null` (4 velden)
- `frontend/src/hooks/use-timer.ts` — `|| undefined` → `|| null` (1 veld)
- `frontend/src/hooks/use-incasso.ts` — `|| undefined` → `|| null` (1 veld)
- `frontend/src/hooks/use-contact-links.ts` — `|| undefined` → `|| null` (1 veld)
- `frontend/src/app/(dashboard)/relaties/[id]/page.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/relaties/nieuw/page.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/facturatie/nieuw/page.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/facturatie/[id]/page.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/tijdschrijven/page.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/agenda/page.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx` — interface `string | null`
- `frontend/src/app/(dashboard)/zaken/[id]/components/DetailsTab.tsx` — interface `string | null`

**Gewijzigd (docs):**
- `CLAUDE.md` — kwaliteitsstandaard sectie toegevoegd

---


---

### Openstaande bugs einde sessie 17

| # | Bug | Ernst | Status |
|---|-----|-------|--------|
| BUG-18 | Klik op taak in dashboard/Mijn Taken navigeert niet naar het juiste dossier | Midden | ❌ TODO |
| BUG-19 | Factuur aanmaken → redirect naar factuurpagina geeft "fout bij laden" | Hoog | ❌ TODO |
| BUG-20 | Budget module onbekend: "Onbekende modules: budget" — niet geregistreerd als geldige module in backend | Hoog | ❌ TODO |
| BUG-21 | Advocaat wederpartij niet zichtbaar na aanmaken dossier (B2C en B2B) | Midden | ❌ TODO |

### Nog te deployen
- BUG-16 + BUG-17 fixes zijn gecommit en gepusht maar **nog NIET gedeployed** op VPS
- Deploy commando (frontend only, geen migraties):
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production build --no-cache frontend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d frontend
```

### Plan volgende sessie (18)
1. Deploy BUG-16+17 naar VPS
2. Fix BUG-18 t/m BUG-21
3. Grondige QA via browser (Playwright/Claude in Chrome)

### Feature requests (backlog)
- Relaties — inline contactpersoon aanmaken vanuit koppeldialoog
- Advocaat wederpartij — klikbare detailweergave met gekoppelde zaken
- Incasso Workflow Automatisering (P1) — template editor, batch brief+email, auto-complete taken, auto-advance pipeline, deadline kleuren, instelbare dagen

---


---

> **Eerdere sessies (1-16)** staan in `SESSION-ARCHIVE.md` — alleen lezen als je historische context nodig hebt.
