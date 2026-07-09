# Sessie 30 — Vervolg QA of nieuwe feature work

## Setup

**Repo:** `C:\Users\arsal\Documents\luxis`

### Lees bij start:
1. Gebruik `luxis-researcher` subagent om `LUXIS-ROADMAP.md` en `SESSION-NOTES.md` te lezen
2. Lees dit bestand: `docs/prompts/sessie-30-prompt.md`

## Context

Sessie 29 heeft alle 20 pre-existing test failures gefixt (BUG-30 t/m BUG-35). **316/316 backend tests PASSED.** Geen openstaande bugs.

### Huidige testdekking per module:

| Module | Tests | Status |
|--------|-------|--------|
| Auth | 8 | Passing |
| Relations/Contacts | 25 | Passing |
| Cases | 16 | Passing |
| Dashboard | 6 | Passing |
| Documents/Templates | 21 | Passing |
| Integration API | 10 | Passing |
| Interest (rente) | 15 + 30 edge cases | Passing |
| WIK (BIK) | 20 + 30 edge cases | Passing |
| Payment Distribution | 11 + 20 extended | Passing |
| Payment Allocation | 8 | Passing |
| Invoice Payments | 18 | Passing |
| Trust Funds | 15 | Passing |
| Incasso Pipeline | 35 + 9 E2E | Passing |
| **Email/Sync** | **0** | **Geen tests** |
| **Workflow/Taken** | **0** | **Geen tests** |
| **Facturatie** | **0** | **Geen tests** |
| **Tijdregistratie** | **0** | **Geen tests** |

### Openstaande QA items (QA-1 t/m QA-9):
- **QA-1 t/m QA-3, QA-8, QA-9:** Bestaande tests passing, maar kunnen uitgebreid worden
- **QA-4 (Email/Sync):** 0 tests, hoog risico module — OAuth, inbox sync, auto-koppeling, compose, bijlagen
- **QA-5 (Workflow/Taken):** 0 tests — taak CRUD, status transitions, toewijzing, deadline tracking
- **QA-6 (Facturatie):** 0 tests — invoice CRUD, creditnota's, PDF generatie, status workflow
- **QA-7 (Tijdregistratie):** 0 tests — timer, handmatige entries, rapportage

## Keuze voor de gebruiker

Vraag de gebruiker wat ze willen doen:

**Optie A: QA doorzetten** — Tests schrijven voor modules zonder testdekking (QA-4 t/m QA-7). Prioriteit: QA-4 (Email/Sync) is hoog risico.

**Optie B: Nieuwe feature** — Vraag welke feature ze willen bouwen. Check de roadmap voor openstaande items.

**Optie C: Playwright E2E tests** — De 9 E2E tests uit sessie 28 draaien en valideren.

## Verificatie

```bash
# Backend tests (moeten allemaal PASSED zijn)
docker compose exec backend pytest tests/ -v

# Lint
docker compose exec backend ruff check app/
```

## Na afronding

- Commit + push (`git push origin main`)
- `LUXIS-ROADMAP.md` updaten
- `SESSION-NOTES.md` updaten
- Geen deploy nodig tenzij productie-code wijzigt
