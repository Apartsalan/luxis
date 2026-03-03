# Sessie 29 Prompt — Fix 20 Pre-existing Test Failures + Playwright E2E

## Repo
`C:\Users\arsal\Documents\luxis`

## Lees bij start
1. CLAUDE.md (automatisch geladen)
2. Gebruik `luxis-researcher` subagent om `LUXIS-ROADMAP.md` en `SESSION-NOTES.md` te lezen (context besparen)
3. `backend/tests/test_auth.py`
4. `backend/tests/test_integration_api.py`
5. `backend/tests/test_cases.py` (regels 190-265)
6. `backend/tests/test_dashboard.py` (regels 25-63)
7. `backend/tests/test_documents.py` (regels 488-506)
8. `backend/tests/test_relations.py` (regels 300-331)

## Context
Sessie 28 heeft P1 QA afgerond: 35 nieuwe backend tests (alle PASSED), 9 Playwright E2E tests, smoke test checklist. Bij de regressietest bleken 20 oudere tests te falen door verouderde URL paden, schema-wijzigingen, en business logic changes. Dit moet nu gefixt worden.

## Taak 1: Fix 20 pre-existing test failures (BUG-30 t/m BUG-35)

### BUG-30: test_auth.py — 7 tests (S fix)
**Probleem:** Alle URLs gebruiken `/auth/login`, `/auth/me`, `/auth/refresh` maar de auth router heeft `prefix="/api/auth"`.
**Fix:** Vervang in alle 7 tests:
- `/auth/login` → `/api/auth/login`
- `/auth/me` → `/api/auth/me`
- `/auth/refresh` → `/api/auth/refresh`

### BUG-31: test_integration_api.py — 8 tests (S fix)
**Probleem:** `login()` helper op regel 66 gebruikt `/auth/login` → 404.
**Fix:** Verander regel 67 van `/auth/login` naar `/api/auth/login`. Alle 8 tests zullen dan weer slagen.

### BUG-32: test_cases.py — 2 tests (S fix)
**Probleem:** Status transitions gebruiken database-driven workflow engine (`WorkflowTransition` tabel). De test verwacht directe paden die niet bestaan:
- `test_status_workflow`: `nieuw → 14_dagenbrief` geeft 409
- `test_status_change_sets_date_closed`: `nieuw → afgesloten` geeft 409

**Fix:** Check welke transitions bestaan in de WorkflowTransition tabel. Lees `backend/app/workflow/service.py` en `backend/app/workflow/models.py` om geldige paden te bepalen. Update de tests naar geldige transitiepaden.

Alternatief als er GEEN `nieuw → afgesloten` transitie is: maak de transitie via meerdere stappen (bijv. `nieuw → aanmaning → betaald`) of voeg de ontbrekende transitie toe aan de seed data als dat logisch is.

### BUG-33: test_dashboard.py — 1 test (S fix)
**Probleem:** Cases aangemaakt met `date_opened: "2026-02-17"` maar `cases_this_month` filter checkt de huidige maand. Faalt in maart.
**Fix:** Gebruik `date.today().isoformat()` i.p.v. hardcoded datum:
```python
from datetime import date
# ...
"date_opened": date.today().isoformat(),
```

### BUG-34: test_documents.py — 1 test (S fix)
**Probleem:** `test_list_docx_templates` verwacht `len(data) == 3` maar er zijn nu 7 templates (herinnering, aanmaning, tweede_sommatie, dagvaarding zijn toegevoegd).
**Fix:** Update assertion:
```python
assert len(data) >= 3  # Meer templates toegevoegd in latere sessies
# En update de types check:
assert {"14_dagenbrief", "sommatie", "renteoverzicht"}.issubset(types)
```

### BUG-35: test_relations.py — 1 test (S fix)
**Probleem:** `test_get_contact_with_links` verwacht `data["linked_companies"][0]["name"]` maar response is `LinkedContactInfo` met nested `contact` object.
**Fix:** Verander:
```python
# Oud:
assert data["linked_companies"][0]["name"] == "Acme B.V."
# Nieuw:
assert data["linked_companies"][0]["contact"]["name"] == "Acme B.V."

# En:
assert data["linked_persons"][0]["name"] == "Jan de Vries"
# Wordt:
assert data["linked_persons"][0]["contact"]["name"] == "Jan de Vries"
```

## Taak 2: Draai Playwright E2E tests

1. `cd frontend && npm install` (installeert @playwright/test)
2. `npx playwright install chromium`
3. Zorg dat dev omgeving draait (frontend + backend + db)
4. `npx playwright test e2e/incasso-pipeline.spec.ts`
5. Fix eventuele failures

## Verificatie

```bash
# Alle backend tests (316 tests, alles moet PASSED zijn)
docker compose exec backend pytest tests/ -v

# Lint
docker compose exec backend ruff check app/

# Playwright
cd frontend && npx playwright test
```

## Na afronding

1. Commit: `test: fix 20 pre-existing test failures (BUG-30 to BUG-35)`
2. Push: `git push origin main`
3. Update LUXIS-ROADMAP.md: markeer BUG-30 t/m BUG-35 als ✅ Gefixt
4. Geen deploy nodig (alleen test fixes)
